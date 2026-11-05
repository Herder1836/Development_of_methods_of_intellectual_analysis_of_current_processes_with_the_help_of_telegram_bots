from datetime import date, timedelta

import numpy as np

from config import ASSET_NAMES, FORECAST_DAYS
from database import get_daily_series
from evaluation import best_method, evaluate_methods_on_ticker
from forecasting import METHODS
from indicators import calc_rsi, calc_sma

SMA_WINDOW = 7
DISCLAIMER = "Навчальна розробка, а не фінансова порада."


def _pct_change(prices: np.ndarray, days: int):
    """Зміна ціни за останні `days` днів, у відсотках (None, якщо даних замало)."""
    if len(prices) <= days:
        return None
    return round(float((prices[-1] / prices[-1 - days] - 1) * 100), 2)


def _rsi_label(value: float) -> str:
    if value >= 70:
        return "перекупленість"
    if value <= 30:
        return "перепроданість"
    return "нейтральна зона"


def analyze(ticker: str):
    """Повертає словник з аналізом активу або None, якщо даних немає."""
    dates, prices_list = get_daily_series(ticker)
    if len(prices_list) < 2:
        return None
    prices = np.array(prices_list, dtype=float)

    name, kind = ASSET_NAMES.get(ticker, (ticker, "crypto"))
    rsi = round(float(calc_rsi(prices)), 1)

    # SMA(7), вирівняна по довжині ряду (перші точки -- None)
    sma_values = []
    if len(prices) >= SMA_WINDOW:
        sma = calc_sma(prices, SMA_WINDOW)
        sma_values = [None] * (SMA_WINDOW - 1) + [round(float(v), 4) for v in sma]

    metrics = evaluate_methods_on_ticker(ticker)
    best = best_method(metrics)

    forecast = None
    if best and len(prices) >= 20:
        values = METHODS[best](prices, FORECAST_DAYS)
        last_day = date.fromisoformat(dates[-1])
        forecast = {
            "method": best,
            "dates": [(last_day + timedelta(days=i + 1)).isoformat() for i in range(FORECAST_DAYS)],
            "values": [round(float(v), 4) for v in values],
        }

    return {
        "ticker": ticker,
        "name": name,
        "kind": kind,
        "currency_label": "USD" if kind == "crypto" else "грн",
        "last_price": round(float(prices[-1]), 4),
        "last_date": dates[-1],
        "change_1d_pct": _pct_change(prices, 1),
        "change_7d_pct": _pct_change(prices, 7),
        "rsi": rsi,
        "rsi_label": _rsi_label(rsi),
        "history": {"dates": dates, "prices": [round(float(p), 4) for p in prices], "sma7": sma_values},
        "metrics": metrics,
        "best_method": best,
        "forecast": forecast,
        "disclaimer": DISCLAIMER,
    }
