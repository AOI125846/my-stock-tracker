import pandas as pd

def sma(series, period):
    return series.rolling(period).mean()

def rsi(series, period=14):
    """
    RSI with Wilder's Smoothing (Standard for TradingView/ThinkOrSwim)
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # שימוש ב-ewm (Exponential Weighted Mean) עם com=period-1 מדמה את Wilder's Smoothing
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()

    return macd_line, signal_line
