"""
Веб-сервер: віддає сторінку міні-застосунку Telegram та JSON API з аналізом.

  GET /                      -- сторінка міні-застосунку (webapp/index.html)
  GET /api/tickers           -- список активів
  GET /api/analysis/<ticker> -- повний аналіз активу (див. analysis.analyze)

Сервер лише читає БД; дані туди кладе collector.
"""

from flask import Flask, jsonify, send_from_directory

from analysis import analyze
from config import ALL_TICKERS, ASSET_NAMES, PORT, WEBAPP_DIR

app = Flask(__name__, static_folder=None)


@app.after_request
def no_cache(response):
    """Дані змінюються щохвилини -- не даємо браузеру кешувати API."""
    if response.mimetype == "application/json":
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def index():
    return send_from_directory(WEBAPP_DIR, "index.html")


@app.get("/api/tickers")
def tickers():
    return jsonify([
        {"ticker": t, "name": ASSET_NAMES[t][0], "kind": ASSET_NAMES[t][1]}
        for t in ALL_TICKERS
    ])


@app.get("/api/analysis/<ticker>")
def analysis(ticker):
    ticker = ticker.upper()
    if ticker not in ALL_TICKERS:
        return jsonify({"error": "unknown ticker"}), 404
    result = analyze(ticker)
    if result is None:
        return jsonify({"error": "no data yet"}), 404
    return jsonify(result)


def run_api():
    """Запуск сервера (викликається з run.py в окремому потоці)."""
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)


if __name__ == "__main__":
    run_api()
