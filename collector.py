"""
Збір даних: поєднує завантаження з API (data_sources) та запис у БД (database).

  - collect_data_once() -- один цикл збору "живих" поточних курсів;
  - backfill_history()  -- одноразове наповнення БД історією за N днів.
"""

from config import CRYPTO_ASSETS, CURRENCY_ASSETS, HISTORY_DAYS
from data_sources import (
    fetch_crypto_history,
    fetch_crypto_prices,
    fetch_currency_history,
    fetch_currency_rate,
)
from database import save_rate, save_rate_with_timestamp


def collect_data_once():
    """Один цикл збору поточних даних: крипта + валюти -> зберегти в БД."""
    # Одним запитом -- усі криптовалюти (економія ліміту CoinGecko)
    try:
        prices = fetch_crypto_prices(list(CRYPTO_ASSETS.keys()))
        for api_id, short_ticker in CRYPTO_ASSETS.items():
            if api_id in prices:
                save_rate("crypto", short_ticker, prices[api_id])
                print(f"[OK] {short_ticker}: {prices[api_id]}")
    except Exception as e:
        print(f"[ПОМИЛКА] crypto: {e}")

    for ticker in CURRENCY_ASSETS:
        try:
            rate = fetch_currency_rate(ticker)
            save_rate("currency", ticker, rate)
            print(f"[OK] {ticker}: {rate}")
        except Exception as e:
            print(f"[ПОМИЛКА] {ticker}: {e}")


def backfill_history(days: int = HISTORY_DAYS):
    """
    Одноразово наповнює БД історичними даними за `days` днів для всіх
    активів -- достатньо спостережень для графіків і порівняння методів
    без тижнів очікування накопичення "живих" даних.
    Повторний запуск безпечний: дублікати ігноруються на рівні БД.
    """
    print(f"=== Довантаження історії за {days} днів ===")

    for api_id, short_ticker in CRYPTO_ASSETS.items():
        try:
            history = fetch_crypto_history(api_id, days)
            for dt, price in history:
                save_rate_with_timestamp("crypto", short_ticker, price, dt)
            print(f"[OK] {short_ticker}: завантажено {len(history)} точок історії")
        except Exception as e:
            print(f"[ПОМИЛКА] історія {short_ticker}: {e}")

    for ticker in CURRENCY_ASSETS:
        try:
            history = fetch_currency_history(ticker)
            for dt, price in history:
                save_rate_with_timestamp("currency", ticker, price, dt)
            print(f"[OK] {ticker}: завантажено {len(history)} точок історії")
        except Exception as e:
            print(f"[ПОМИЛКА] історія {ticker}: {e}")
