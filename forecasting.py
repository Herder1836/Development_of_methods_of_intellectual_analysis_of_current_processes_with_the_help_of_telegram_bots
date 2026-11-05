"""
Методи прогнозування курсу.

Кожен метод має однаковий інтерфейс: (prices, steps_ahead) -> масив прогнозу.
Щоб додати новий метод, достатньо написати функцію й внести її в METHODS --
решта системи (порівняння, графіки, бот) підхопить її автоматично.
"""

import numpy as np

from indicators import calc_sma


def method_polynomial(prices: np.ndarray, steps_ahead: int, degree: int = 2) -> np.ndarray:
    """Метод 1: поліноміальна апроксимація (numpy.polyfit)."""
    t = np.arange(len(prices))
    coeffs = np.polyfit(t, prices, degree)
    poly = np.poly1d(coeffs)
    future_t = np.arange(len(prices), len(prices) + steps_ahead)
    return poly(future_t)


def method_moving_average(prices: np.ndarray, steps_ahead: int, window: int = 5) -> np.ndarray:
    """Метод 2: наївний прогноз -- останнє значення SMA, продовжене вперед."""
    sma = calc_sma(prices, window)
    return np.full(steps_ahead, sma[-1])


def method_linear_regression(prices: np.ndarray, steps_ahead: int) -> np.ndarray:
    """Метод 3: лінійна регресія (поліном 1-го ступеня)."""
    return method_polynomial(prices, steps_ahead, degree=1)


# Реєстр методів: назва (для таблиць і графіків) -> функція
METHODS = {
    "Поліноміальна апроксимація": method_polynomial,
    "Ковзне середнє (наївний прогноз)": method_moving_average,
    "Лінійна регресія": method_linear_regression,
}
