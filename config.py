"""
Конфігурація проекту: шляхи, перелік активів, параметри запитів і аналізу.

Усі "налаштування" зібрані тут, щоб їх можна було змінювати в одному місці,
не чіпаючи решту коду.
"""

import os
from pathlib import Path

# --- Шляхи -------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "rates.db"
CHARTS_DIR = BASE_DIR / "charts"
WEBAPP_DIR = BASE_DIR / "webapp"

# --- Активи ------------------------------------------------------------
# Криптовалюти: ідентифікатор у CoinGecko
CRYPTO_ASSETS = {"bitcoin": "BTC", "ethereum": "ETH"}
# Валюти (офіційний курс НБУ)
CURRENCY_ASSETS = ["USD", "EUR"]
# Усі тікери, з якими працює система
ALL_TICKERS = list(CRYPTO_ASSETS.values()) + CURRENCY_ASSETS

# --- Параметри даних та аналізу ---------------------------------------
HISTORY_DAYS = 60      # за скільки днів завантажувати історію
MIN_TRAIN_DAYS = 20    # мінімум днів історії для навчання методу
N_ORIGINS = 14         # скільки "точок прогнозу" в walk-forward перевірці (днів)
FORECAST_DAYS = 7      # на скільки днів уперед будується прогноз
TEST_STEPS = 7         # довжина відкладеного відрізка для ілюстрації на графіку
COLLECT_INTERVAL_MIN = 30  # як часто фоново оновлювати курси (хв)

# --- HTTP --------------------------------------------------------------
# Деякі сервери блокують запити без User-Agent.
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

# --- Telegram ----------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# URL міні-застосунку.
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://phoney-padding-gown.ngrok-free.dev")
# Порт локального веб-сервера (API + сторінка міні-застосунку).
PORT = int(os.getenv("PORT", "8000"))

# Людські назви активів для інтерфейсу
ASSET_NAMES = {
    "BTC": ("Bitcoin", "crypto"),
    "ETH": ("Ethereum", "crypto"),
    "USD": ("Долар США", "currency"),
    "EUR": ("Євро", "currency"),
}
