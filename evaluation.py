"""
Оцінка якості методів прогнозу -- ядро методики.

Перевірка методом ковзного вікна (walk-forward): для кожного з останніх
N днів метод бачить лише попередню історію, прогнозує наступний день, і цей
прогноз порівнюється з фактом. Так оцінка спирається на 14 прогнозів,
а не на один короткий відрізок, тому результат стійкіший.

Метрики: MAE, RMSE, MAPE (у %, порівнянна між активами різного масштабу)
та точність напрямку руху курсу.
"""

import numpy as np

from config import MIN_TRAIN_DAYS, N_ORIGINS
from database import get_daily_series
from forecasting import METHODS


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Середня абсолютна похибка (Mean Absolute Error)."""
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Корінь із середньоквадратичної похибки (Root Mean Squared Error)."""
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Середня абсолютна похибка у відсотках (Mean Absolute Percentage Error)."""
    return float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)


def direction_accuracy(y_true: np.ndarray, y_pred: np.ndarray, last_known: np.ndarray) -> float:
    """
    Частка правильно вгаданого напрямку руху курсу (зростання/падіння)
    відносно останнього відомого значення, у відсотках.
    """
    true_direction = np.sign(y_true - last_known)
    pred_direction = np.sign(y_pred - last_known)
    return float(np.mean(true_direction == pred_direction) * 100)


def evaluate_methods_on_ticker(ticker: str, n_origins: int = N_ORIGINS) -> list:
    """
    Walk-forward оцінка всіх методів з METHODS для одного активу.
    Повертає список словників (по одному на метод); порожній список --
    якщо даних замало.
    """
    _, prices_list = get_daily_series(ticker)
    prices = np.array(prices_list, dtype=float)

    n_origins = min(n_origins, len(prices) - MIN_TRAIN_DAYS)
    if n_origins < 3:
        print(f"Недостатньо даних для {ticker}: потрібно щонайменше "
              f"{MIN_TRAIN_DAYS + 3} днів, є {len(prices)}")
        return []

    first = len(prices) - n_origins
    actual = prices[first:]
    last_known = prices[first - 1:-1]

    results = []
    for method_name, method_func in METHODS.items():
        predicted = np.array([method_func(prices[:i], 1)[0] for i in range(first, len(prices))])
        results.append({
            "ticker": ticker,
            "method": method_name,
            "MAE": round(mae(actual, predicted), 4),
            "RMSE": round(rmse(actual, predicted), 4),
            "MAPE_%": round(mape(actual, predicted), 3),
            "accuracy_%": round(direction_accuracy(actual, predicted, last_known), 1),
            "n_forecasts": int(n_origins),
        })
    return results


def best_method(results: list) -> str:
    """Назва методу з найменшою відсотковою похибкою (MAPE)."""
    return min(results, key=lambda r: r["MAPE_%"])["method"] if results else ""


def print_comparison_table(results: list):
    """Друкує результати порівняння методів у вигляді простої таблиці."""
    print(f"{'Тікер':<7}{'Метод':<35}{'MAE':<11}{'RMSE':<11}{'MAPE, %':<10}{'Напрямок, %':<12}")
    for r in results:
        print(f"{r['ticker']:<7}{r['method']:<35}{r['MAE']:<11}{r['RMSE']:<11}"
              f"{r['MAPE_%']:<10}{r['accuracy_%']:<12}")
