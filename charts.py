from datetime import date

import matplotlib

matplotlib.use("Agg")  # зберігати у файл, не відкриваючи вікно
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

from config import CHARTS_DIR, CRYPTO_ASSETS, TEST_STEPS
from database import get_daily_series
from forecasting import METHODS

CHARTS_DIR.mkdir(exist_ok=True)

BLUE, ORANGE, AQUA, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#6b6a66"

# Кольори методів (фіксований порядок -> той самий колір скрізь)
METHOD_COLORS = dict(zip(METHODS, [BLUE, ORANGE, AQUA]))


def _style(ax):
    """Спільне оформлення осей: легка сітка, без зайвих рамок, дати знизу."""
    ax.grid(True, alpha=0.25)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))


def _to_dates(date_strings):
    return [date.fromisoformat(d) for d in date_strings]


def _unit(ticker: str) -> str:
    return "Ціна, USD" if ticker in CRYPTO_ASSETS.values() else "Курс, грн"


def _save(name: str):
    path = CHARTS_DIR / name
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[OK] Графік збережено: {path}")


def plot_price_history(ticker: str):
    """Динаміка курсу за денним рядом з датами на осі X."""
    dates, prices = get_daily_series(ticker)
    if not prices:
        print(f"Немає даних для побудови графіка {ticker}")
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(_to_dates(dates), prices, color=BLUE, linewidth=2)
    ax.set_title(f"Динаміка курсу {ticker} (денні значення)")
    ax.set_xlabel("Дата")
    ax.set_ylabel(_unit(ticker))
    _style(ax)
    fig.tight_layout()
    _save(f"history_{ticker}.png")


def plot_forecast_comparison(ticker: str, test_steps: int = TEST_STEPS):
    """
    Реальні дані проти прогнозу кожного методу на відкладених `test_steps`
    днях: наочно видно, який метод точніше відтворює реальну поведінку.
    """
    dates, prices_list = get_daily_series(ticker)
    if len(prices_list) < test_steps + 20:
        print(f"Недостатньо даних для графіка прогнозу {ticker}")
        return

    prices = np.array(prices_list, dtype=float)
    d = _to_dates(dates)
    train, real = prices[:-test_steps], prices[-test_steps:]
    x_train, x_test = d[:-test_steps], d[-test_steps:]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x_train[-30:], train[-30:], color=GRAY, linewidth=1.8, label="Історичні дані")
    ax.plot(x_test, real, color="#111", linewidth=2.2, marker="o", label="Реальні значення")
    for name, func in METHODS.items():
        ax.plot(x_test, func(train, test_steps), "--", color=METHOD_COLORS[name],
                linewidth=1.8, marker="x", label=name)
    ax.set_title(f"Порівняння методів прогнозу для {ticker} (відкладені {test_steps} днів)")
    ax.set_xlabel("Дата")
    ax.set_ylabel(_unit(ticker))
    ax.legend(fontsize=8, frameon=False)
    _style(ax)
    fig.tight_layout()
    _save(f"forecast_{ticker}.png")


def plot_methods_metrics_bar(results: list, ticker: str):
    """Стовпчики MAE та RMSE методів для одного активу."""
    if not results:
        return
    methods = [r["method"] for r in results]
    x = np.arange(len(methods))
    w = 0.36

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - w / 2, [r["MAE"] for r in results], w, label="MAE", color=BLUE)
    ax.bar(x + w / 2, [r["RMSE"] for r in results], w, label="RMSE", color=ORANGE)
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=12, ha="right", fontsize=8)
    ax.set_ylabel("Похибка")
    ax.set_title(f"Похибки методів для {ticker} (walk-forward, {results[0]['n_forecasts']} прогнозів)")
    ax.legend(frameon=False)
    ax.grid(True, alpha=0.25, axis="y")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    _save(f"metrics_{ticker}.png")


def plot_mape_all_assets(all_results: dict):

    tickers = [t for t, r in all_results.items() if r]
    if not tickers:
        return
    methods = list(METHODS)
    x = np.arange(len(tickers))
    w = 0.8 / len(methods)

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, m in enumerate(methods):
        vals = [next(r["MAPE_%"] for r in all_results[t] if r["method"] == m) for t in tickers]
        ax.bar(x + (i - (len(methods) - 1) / 2) * w, vals, w, label=m, color=METHOD_COLORS[m])
    ax.set_xticks(x)
    ax.set_xticklabels(tickers)
    ax.set_ylabel("MAPE, %")
    ax.set_title("Похибка прогнозу на добу вперед: криптовалюти й валюти")
    ax.legend(fontsize=8, frameon=False)
    ax.grid(True, alpha=0.25, axis="y")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    _save("mape_all_assets.png")
