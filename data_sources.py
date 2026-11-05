"""
Отримання даних із зовнішніх API:
  - CoinGecko  -- криптовалюти (поточна ціна та історія);
  - НБУ        -- офіційний курс валют (поточний та історія).

Модуль лише завантажує й повертає дані. Зберігання в БД -- у collector.py.
"""

from datetime import datetime, timedelta

import requests

from config import HISTORY_DAYS, HTTP_HEADERS


# ---------------------------------------------------------------------
# CoinGecko (крипта)
# ---------------------------------------------------------------------

def fetch_crypto_prices(tickers: list) -> dict:
    """
    Отримує поточні ціни декількох криптовалют ОДНИМ запитом до CoinGecko
    (економніше для rate limit, ніж окремий запит на кожен тікер).
    tickers: наприклад ['bitcoin', 'ethereum'].
    Повертає словник {ticker: price_in_usd}.
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": ",".join(tickers), "vs_currencies": "usd"}
    response = requests.get(url, params=params, headers=HTTP_HEADERS, timeout=10)

    if response.status_code == 429:
        raise RuntimeError(
            "CoinGecko: перевищено ліміт запитів (429 Too Many Requests). "
            "Зробіть довшу паузу між запитами (30-60 сек)."
        )

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError(
            f"CoinGecko повернув не-JSON відповідь (код {response.status_code}): "
            f"{response.text[:200]}"
        )

    result = {}
    for ticker in tickers:
        if ticker in data:
            result[ticker] = data[ticker]["usd"]
        else:
            print(f"[ПОМИЛКА] {ticker}: відсутній у відповіді CoinGecko")
    return result


def fetch_crypto_history(ticker: str = "bitcoin", days: int = HISTORY_DAYS) -> list:
    """
    Завантажує історію цін криптовалюти за останні `days` днів
    одним запитом (endpoint market_chart).
    Повертає список кортежів (timestamp_iso, price).
    """
    url = f"https://api.coingecko.com/api/v3/coins/{ticker}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    response = requests.get(url, params=params, headers=HTTP_HEADERS, timeout=15)

    if response.status_code == 429:
        raise RuntimeError("CoinGecko: перевищено ліміт запитів під час завантаження історії.")

    data = response.json()
    if "prices" not in data:
        raise RuntimeError(
            f"CoinGecko: несподівана відповідь при завантаженні історії: {str(data)[:200]}"
        )

    result = []
    for timestamp_ms, price in data["prices"]:
        dt = datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
        result.append((dt, price))
    return result


# ---------------------------------------------------------------------
# НБУ (валюти)
# ---------------------------------------------------------------------

def fetch_currency_rate(ticker: str = "USD") -> float:
    """
    Отримує поточний офіційний курс валюти через API НБУ (без ключа).
    Ендпоінт exchangenew з параметром valcode повертає список з одного запису.
    """
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchangenew"
    params = {"json": "", "valcode": ticker}
    response = requests.get(url, params=params, headers=HTTP_HEADERS, timeout=10)

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError(
            f"НБУ API повернув не-JSON відповідь (код {response.status_code}): "
            f"{response.text[:200]}"
        )

    if not data:
        raise ValueError(f"НБУ API не повернув даних для валюти {ticker}")

    record = data[0]
    print(f"[INFO] {ticker}: курс НБУ встановлено на {record.get('exchangedate', '?')}")
    return record["rate"]


def fetch_currency_history(ticker: str = "USD", start_date: str = None,
                           end_date: str = None) -> list:
    """
    Завантажує історію офіційного курсу валюти НБУ за діапазон дат.
    Дати у форматі YYYYMMDD; якщо не вказані -- останні HISTORY_DAYS днів.
    Повертає список кортежів (timestamp_iso, price).

    Для діапазону дат потрібен ендпоінт exchange_site (exchangenew повертає
    лише одне значення). Параметр json передається БЕЗ "=", тому URL
    збирається вручну -- інакше НБУ ігнорує діапазон дат.
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=HISTORY_DAYS)).strftime("%Y%m%d")

    url = (
        "https://bank.gov.ua/NBU_Exchange/exchange_site"
        f"?start={start_date}&end={end_date}"
        f"&valcode={ticker.lower()}&sort=exchangedate&order=asc&json"
    )
    response = requests.get(url, headers=HTTP_HEADERS, timeout=15)

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError(f"НБУ API: не-JSON відповідь при завантаженні історії {ticker}")

    if not isinstance(data, list):
        raise RuntimeError(
            f"НБУ API (історія {ticker}): несподівана структура відповіді: {str(data)[:200]}"
        )

    result = []
    for record in data:
        day, month, year = record["exchangedate"].split(".")
        result.append((f"{year}-{month}-{day}T00:00:00", record["rate"]))
    return result
