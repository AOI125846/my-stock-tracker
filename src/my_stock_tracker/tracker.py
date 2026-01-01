import os
from functools import lru_cache
from typing import Dict, List, Optional
import requests

API_KEY = os.getenv("STOCK_API_KEY")

ALLOWED_RANGES = ["1m", "5m", "15m", "1h", "4h", "1d"]

@lru_cache(maxsize=128)
def fetch_chart_data(symbol: str, range_key: str) -> List[Dict]:
    """
    מחזיר רשימת נקודות OHLCV לפי טווח מוגבל.
    אם אין API_KEY — מחזיר נתוני דמה.
    """
    symbol = symbol.upper().strip()
    if range_key not in ALLOWED_RANGES:
        raise ValueError("טווח לא נתמך")

    if API_KEY:
        try:
            resp = requests.get(
                "https://example-stock-api.local/chart",
                params={"symbol": symbol, "range": range_key, "apikey": API_KEY},
                timeout=5,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            pass

    # נתוני דמה
    import random
    from datetime import datetime, timedelta

    points = []
    now = datetime.utcnow()
    step = {"1m":1,"5m":5,"15m":15,"1h":60,"4h":240,"1d":1440}[range_key]
    base = 100.0 + random.random() * 20
    for i in range(100):
        t = now - timedelta(minutes=step * (100 - i))
        open_p = base + random.uniform(-1, 1)
        close_p = open_p + random.uniform(-1, 1)
        high_p = max(open_p, close_p) + random.random() * 0.5
        low_p = min(open_p, close_p) - random.random() * 0.5
        vol = random.randint(1000, 10000)
        points.append({
            "time": int(t.timestamp()),
            "open": round(open_p,2),
            "high": round(high_p,2),
            "low": round(low_p,2),
            "close": round(close_p,2),
            "volume": vol
        })
    return points

def compute_sma(values: List[float], period: int) -> List[Optional[float]]:
    result = []
    for i in range(len(values)):
        if i+1 < period:
            result.append(None)
        else:
            window = values[i+1-period:i+1]
            result.append(sum(window)/period)
    return result

def compute_ema(values: List[float], period: int) -> List[Optional[float]]:
    result = []
    k = 2/(period+1)
    ema = None
    for i, v in enumerate(values):
        if ema is None:
            ema = v
        else:
            ema = v * k + ema * (1-k)
        result.append(round(ema,4))
    return result

def compute_rsi(values: List[float], period: int=14) -> List[Optional[float]]:
    gains = []
    losses = []
    result = []
    for i in range(len(values)):
        if i==0:
            result.append(None)
            continue
        change = values[i] - values[i-1]
        gain = max(0, change)
        loss = max(0, -change)
        gains.append(gain)
        losses.append(loss)
        if len(gains) < period:
            result.append(None)
        else:
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain/avg_loss
                rsi = 100 - (100/(1+rs))
            result.append(round(rsi,2))
    return result

def compute_macd(values: List[float], fast: int=12, slow: int=26, signal: int=9):
    ema_fast = compute_ema(values, fast)
    ema_slow = compute_ema(values, slow)
    macd_line = []
    for a,b in zip(ema_fast, ema_slow):
        if a is None or b is None:
            macd_line.append(None)
        else:
            macd_line.append(round(a-b,4))
    flat = [x for x in macd_line if x is not None]
    if flat:
        sig = compute_ema(flat, signal)
        pad = len(macd_line) - len(sig)
        signal_line = [None]*pad + sig
    else:
        signal_line = [None]*len(macd_line)
    hist = []
    for m,s in zip(macd_line, signal_line):
        if m is None or s is None:
            hist.append(None)
        else:
            hist.append(round(m-s,4))
    return {"macd": macd_line, "signal": signal_line, "histogram": hist}

def analyze_indicators(symbol: str, range_key: str="1d") -> Dict:
    data = fetch_chart_data(symbol, range_key)
    closes = [p["close"] for p in data]

    sma10 = compute_sma(closes, 10)[-1] if len(closes)>=10 else None
    sma50 = compute_sma(closes, 50)[-1] if len(closes)>=50 else None
    ema20 = compute_ema(closes,20)[-1] if closes else None
    rsi = compute_rsi(closes)[-1] if closes else None
    macd = compute_macd(closes)
    macd_hist = macd["histogram"][-1] if macd["histogram"] else None

    score = 50
    notes = []

    if sma10 is not None and sma50 is not None:
        if sma10 > sma50:
            score += 10
            notes.append("SMA קצר עולה מעל SMA ארוך — מגמה חיובית לטווח הבינוני.")
        else:
            score -= 10
            notes.append("SMA קצר מתחת ל־SMA ארוך — לחץ מכירה לטווח הבינוני.")

    if rsi is not None:
        if rsi > 70:
            score -= 10
            notes.append(f"RSI גבוה ({rsi}) — ייתכן שהמניה בקניית יתר; שקול לקיחת רווחים.")
        elif rsi < 30:
            score += 10
            notes.append(f"RSI נמוך ({rsi}) — ייתכן שהמניה במצב מכירת יתר; בדוק סגמנטים קנייה.")
        else:
            notes.append(f"RSI נייטרלי ({rsi}).")

    if macd_hist is not None:
        if macd_hist > 0:
            score += 5
            notes.append("MACD חיובי — מומנטום עולה.")
        else:
            score -=5
            notes.append("MACD שלילי — מומנטום יורד.")

    score = max(0, min(100, score))
    recommendation = "המתן"
    if score >= 65:
        recommendation = "קנה"
    elif score <= 35:
        recommendation = "מכור"

    upcoming = [{"date":"2026-02-15","type":"Earnings","details":"דוח רבעוני"}]

    return {
        "symbol": symbol.upper(),
        "score": int(score),
        "recommendation": recommendation,
        "notes": notes,
        "sma10": sma10,
        "sma50": sma50,
        "ema20": ema20,
        "rsi": rsi,
        "macd_hist": macd_hist,
        "upcoming_reports": upcoming,
    }
