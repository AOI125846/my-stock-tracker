import pandas as pd

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def macd(series):
    exp1 = series.ewm(span=12, adjust=False).mean()
    exp2 = series.ewm(span=26, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line, signal_line

def analyze_tech_signals(df, ma_periods, historical_levels):
    last_row = df.iloc[-1]
    explanations = []
    
    # ניתוח RSI
    r_val = last_row['RSI']
    if r_val > 70:
        explanations.append(f"🔴 מכירה: RSI בערך {r_val:.1f} מעיד על 'קניית יתר' - המחיר מתוח מדי למעלה.")
    elif r_val < 30:
        explanations.append(f"🟢 קנייה: RSI בערך {r_val:.1f} מעיד על 'מכירת יתר' - הזדמנות לכניסה בנמוך.")
    
    # ניתוח MACD
    if last_row['MACD'] > last_row['MACD_Signal']:
        explanations.append("🟢 קנייה: קו ה-MACD חצה מעל קו הסיגנל (קו חוצה סיגנל) - מומנטום חיובי מתחזק.")
    else:
        explanations.append("🔴 מכירה: קו ה-MACD מתחת לסיגנל - המומנטום נחלש.")

    # ניתוח ממוצעים נעים (MA)
    price = last_row['Close']
    for p in ma_periods:
        ma_val = last_row[f'SMA_{p}']
        if price > ma_val:
            explanations.append(f"📈 מגמה עולה: המחיר מעל ממוצע {p}. הממוצע משמש כרגע כתמיכה.")
        else:
            explanations.append(f"📉 מגמה יורדת: המחיר מתחת לממוצע {p}. הממוצע מהווה התנגדות.")

    # הוספת רמות היסטוריות כטקסט
    explanations.extend(historical_levels)
    
    return explanations
