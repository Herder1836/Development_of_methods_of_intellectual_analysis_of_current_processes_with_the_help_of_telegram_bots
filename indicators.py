"""
Технічні індикатори (ознаки для аналізу ринкового процесу):
SMA, EMA, RSI.
"""

import numpy as np


def calc_sma(prices: np.ndarray, window: int = 5) -> np.ndarray:
    """Просте ковзне середнє (Simple Moving Average)."""
    return np.convolve(prices, np.ones(window) / window, mode="valid")


def calc_ema(prices: np.ndarray, span: int = 5) -> np.ndarray:
    """Експоненційне ковзне середнє (Exponential Moving Average)."""
    alpha = 2 / (span + 1)
    ema = np.zeros_like(prices, dtype=float)
    ema[0] = prices[0]
    for i in range(1, len(prices)):
        ema[i] = alpha * prices[i] + (1 - alpha) * ema[i - 1]
    return ema


def calc_rsi(prices: np.ndarray, period: int = 14) -> float:
    """
    Індекс відносної сили (Relative Strength Index, Wilder, 1978).
    Повертає останнє значення RSI (0-100).
    RSI > 70 умовно означає "перекупленість", RSI < 30 -- "перепроданість".
    """
    if len(prices) < period + 1:
        return 50.0  # недостатньо даних -- нейтральне значення

    deltas = np.diff(prices[-(period + 1):])
    gains = deltas[deltas > 0].sum()
    losses = -deltas[deltas < 0].sum()

    if losses == 0:
        return 100.0
    rs = gains / losses
    return 100 - (100 / (1 + rs))
