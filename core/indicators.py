import pandas as pd

def sma(series, period):
    return series.rolling(period).mean()

def rsi(series, period=14):
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
    score = 0
    # RSI
    if row["RSI"] < 30: rsi_act, score = "קנייה (מכירת יתר)", score + 1
    elif row["RSI"] > 70: rsi_act, score = "מכירה (קניית יתר)", score - 1
    else: rsi_act = "המתנה / נייטרלי"

    # MACD
    if row["MACD"] > row["MACD_SIGNAL"]: macd_act, score = "קנייה (מומנטום חיובי)", score + 1
    else: macd_act, score = "מכירה (מומנטום שלילי)", score - 1

    # Trend
    if row["Close"] > row["SMA50"]: trend_act, score = "מגמה עולה (מעל ממוצע 50)", score + 1
    else: trend_act, score = "מגמה יורדת (מתחת לממוצע 50)", score - 1

    # Final Score
    if score >= 2: summary = "קנייה חזקה 🟢"
    elif score == 1: summary = "קנייה 🟢"
    elif score == -1: summary = "מכירה 🔴"
    elif score <= -2: summary = "מכירה חזקה 🔴"
    else: summary = "נייטרלי ⚪"

    return {"score": score, "summary": summary, "rsi": rsi_act, "macd": macd_act, "trend": trend_act}
