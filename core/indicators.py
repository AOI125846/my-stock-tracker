import pandas as pd
import numpy as np

def calculate_all_indicators(df, ma_type):
    # ממוצעים נעים לפי בחירה
    periods = [9, 20, 50] if "קצר" in ma_type else [100, 150, 200]
    for p in periods:
        df[f'SMA_{p}'] = df['Close'].rolling(window=p).mean()

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    df['BB_Mid'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Mid'] + (2 * df['BB_Std'])
    df['BB_Lower'] = df['BB_Mid'] - (2 * df['BB_Std'])

    # Stochastic Oscillator
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    df['Stoch'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    
    return df, periods

def calculate_final_score(row, periods):
    """
    מחשב ציון משוקלל (0-100) למצב המניה
    """
    score = 50 # נקודת התחלה
    
    # 1. RSI
    if row['RSI'] < 30: score += 15
    elif row['RSI'] > 70: score -= 15
    
    # 2. MACD
    if row['MACD'] > row['MACD_Signal']: score += 15
    else: score -= 15
    
    # 3. מגמה ראשית (ממוצע ארוך)
    long_ma = periods[-1]
    if row['Close'] > row[f'SMA_{long_ma}']: score += 10
    else: score -= 10
    
    # 4. בולינגר
    if row['Close'] < row['BB_Lower']: score += 10
    elif row['Close'] > row['BB_Upper']: score -= 10
    
    # גבולות
    score = max(0, min(100, score))
    
    # טקסט וצבע
    if score >= 80: return score, "קנייה חזקה 🚀", "green"
    elif score >= 60: return score, "קנייה ✅", "#90ee90" # ירוק בהיר
    elif score <= 20: return score, "מכירה חזקה 📉", "red"
    elif score <= 40: return score, "מכירה 🔻", "orange"
    else: return score, "המתנה / נייטרלי ✋", "gray"

def get_smart_analysis(df, periods):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    analysis = []

    # RSI
    if last['RSI'] > 70: analysis.append(f"🔴 **RSI ({last['RSI']:.1f}):** קניית יתר. סיכון לתיקון מטה.")
    elif last['RSI'] < 30: analysis.append(f"🟢 **RSI ({last['RSI']:.1f}):** מכירת יתר. הזדמנות טכנית לעליות.")
    
    # MACD
    if last['MACD'] > last['MACD_Signal']:
        analysis.append("🚀 **MACD:** מומנטום חיובי (הקו הכחול מעל הכתום).")
    else:
        analysis.append("📉 **MACD:** מומנטום שלילי (הקו הכחול מתחת לכתום).")

    # Bollinger
    if last['Close'] > last['BB_Upper']: analysis.append("⚠️ **בולינגר:** המחיר חורג מהרצועה העליונה (יקר סטטיסטית).")
    elif last['Close'] < last['BB_Lower']: analysis.append("💰 **בולינגר:** המחיר מתחת לרצועה התחתונה (זול סטטיסטית).")
    
    # ממוצעים
    ma_trend = "מעל" if last['Close'] > last[f'SMA_{periods[1]}'] else "מתחת"
    analysis.append(f"📊 **מגמה:** המחיר {ma_trend} ממוצע {periods[1]}.")

    return analysis
