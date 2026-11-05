"""
Робота з базою даних SQLite.
"""

import sqlite3
from datetime import datetime

from config import DB_PATH


def init_db():
    """Створює таблицю для зберігання курсів, якщо її ще немає."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_type TEXT,       -- 'crypto' або 'currency'
            ticker TEXT,           -- BTC, ETH, USD, EUR ...
            price REAL,
            timestamp TEXT,
            UNIQUE (ticker, timestamp)  -- захист від дублікатів при повторному запуску
        )
    """)
    conn.commit()
    conn.close()


def save_rate(asset_type: str, ticker: str, price: float):
    """Зберігає один запис курсу в БД (з поточним часом)."""
    save_rate_with_timestamp(asset_type, ticker, price, datetime.now().isoformat())


def save_rate_with_timestamp(asset_type: str, ticker: str, price: float, timestamp: str):
    """Зберігає запис курсу із заданою часовою міткою (для історичних даних)."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO rates (asset_type, ticker, price, timestamp) "
        "VALUES (?, ?, ?, ?)",
        (asset_type, ticker, price, timestamp)
    )
    conn.commit()
    conn.close()


def get_history(ticker: str, limit: int = 1000):
    """
    Повертає останні N записів курсу за тікером у хронологічному порядку
    (від старих до нових) як список кортежів (price, timestamp).
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT price, timestamp FROM rates WHERE ticker = ? "
        "ORDER BY timestamp DESC LIMIT ?",
        (ticker, limit)
    )
    rows = cur.fetchall()
    conn.close()
    rows.reverse()
    return rows


def get_daily_series(ticker: str):
    """
    Повертає денний ряд курсу: для кожної календарної дати -- ОСТАННЄ значення
    за день. Це приводить крипту (точки щогодини) і валюти НБУ (раз на добу)
    до однакової частоти, тому методи й активи можна порівнювати чесно.

    Повертає два списки: dates (рядки 'YYYY-MM-DD') і prices (float).
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT price, timestamp FROM rates WHERE ticker = ? ORDER BY timestamp ASC",
        (ticker,)
    )
    rows = cur.fetchall()
    conn.close()

    by_day = {}
    for price, ts in rows:
        by_day[ts[:10]] = price   # пізніший запис дня перезаписує ранній
    dates = sorted(by_day)
    return dates, [by_day[d] for d in dates]
