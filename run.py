"""
Єдиний запуск усієї системи:

  1) створює БД і, якщо вона порожня, довантажує історію;
  2) у фоні кожні COLLECT_INTERVAL_MIN хвилин оновлює курси;
  3) у фоні піднімає веб-сервер (API + міні-застосунок) на PORT;
  4) запускає телеграм-бота.

Запуск:  python run.py
"""

import threading
import time

from api import run_api
from bot import build_app
from collector import backfill_history, collect_data_once
from config import ALL_TICKERS, COLLECT_INTERVAL_MIN, PORT, WEBAPP_URL
from database import get_daily_series, init_db


def collector_loop():
    """Фонове оновлення курсів. Помилки мережі не зупиняють цикл."""
    while True:
        time.sleep(COLLECT_INTERVAL_MIN * 60)
        try:
            collect_data_once()
        except Exception as e:  # noqa: BLE001 -- цикл має жити, що б не сталося
            print(f"[ПОМИЛКА] фоновий збір: {e}")


def main():
    init_db()
    if not any(get_daily_series(t)[1] for t in ALL_TICKERS):
        print("БД порожня -- довантажую історію...")
        backfill_history()
    else:
        collect_data_once()

    threading.Thread(target=collector_loop, daemon=True).start()
    threading.Thread(target=run_api, daemon=True).start()
    print(f"Веб-сервер: http://localhost:{PORT}")
    print(f"Міні-застосунок у Telegram: {WEBAPP_URL or 'НЕ НАЛАШТОВАНО (задайте WEBAPP_URL)'}")

    build_app().run_polling()


if __name__ == "__main__":
    main()
