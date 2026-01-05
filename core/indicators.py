import pandas as pd

def sma(series, period):
    return series.rolling(period).mean()

def rsi(series, period=14):
    """ RSI with Wilder's Smoothing """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
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

def analyze_signals(row):
    """
    מחזיר מילון עם ניתוח הפעולה לכל אינדיקטור
    """
    signals = {
        "score": 0,
        "rsi_action": "Hold",
        "macd_action": "Hold",
        "trend_action": "Hold",
        "summary": "Neutral"
    }
    
    # 1. ניתוח RSI
    r = row["RSI"]
    if r < 30:
        signals["rsi_action"] = "BUY (Oversold)"
        signals["score"] += 1
    elif r > 70:
        signals["rsi_action"] = "SELL (Overbought)"
        signals["score"] -= 1
    else:
        signals["rsi_action"] = "Wait / Neutral"

    # 2. ניתוח MACD
    if row["MACD"] > row["MACD_SIGNAL"]:
        signals["macd_action"] = "BUY (Momentum Up)"
        signals["score"] += 1
    else:
        signals["macd_action"] = "SELL (Momentum Down)"
        signals["score"] -= 1

    # 3. ניתוח מגמה (SMA50)
    price = row["Close"]
    sma50 = row["SMA50"]
    if price > sma50:
        signals["trend_action"] = "Bullish Trend (Price > SMA50)"
        signals["score"] += 1
    else:
        signals["trend_action"] = "Bearish Trend (Price < SMA50)"
        signals["score"] -= 1

    # סיכום כללי
    if signals["score"] >= 2:
        signals["summary"] = "STRONG BUY 🟢"
    elif signals["score"] == 1:
        signals["summary"] = "BUY 🟢"
    elif signals["score"] == -1:
        signals["summary"] = "SELL 🔴"
    elif signals["score"] <= -2:
        signals["summary"] = "STRONG SELL 🔴"
    else:
        signals["summary"] = "NEUTRAL ⚪"

    return signals
