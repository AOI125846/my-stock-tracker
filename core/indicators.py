import pandas as pd
import numpy as np

def calculate_all_indicators(df, ma_type):
    # ממוצעים נעים
    periods = [9, 20, 50] if ma_type == "קצר" else [100, 150, 200]
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

    # Stochastic
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    df['Stoch'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    
    return df, periods

def get_smart_analysis(df, periods):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    analysis = []

    # פרשנות RSI
    if last['RSI'] > 70: analysis.append("🔴 **קניית יתר (RSI):** המניה מתוחה למעלה, סיכון לתיקון.")
    elif last['RSI'] < 30: analysis.append("🟢 **מכירת יתר (RSI):** המניה נמוכה מאוד, פוטנציאל להיפוך.")
    
    # פרשנות MACD
    if last['MACD'] > last['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']:
        analysis.append("🚀 **איתות קנייה (MACD):** קו חוצה סיגנל כלפי מעלה.")
    elif last['MACD'] < last['MACD_Signal']:
        analysis.append("🔻 **מומנטום שלילי (MACD):** המגמה כרגע נחלשת.")

    # פרשנות בולינגר
    if last['Close'] > last['BB_Upper']: analysis.append("⚠️ **תמחור גבוה:** המחיר מעל רצועת בולינגר העליונה.")
    elif last['Close'] < last['BB_Lower']: analysis.append("💰 **תמחור נמוך:** המחיר מתחת לרצועת בולינגר התחתונה.")

    # פרשנות סטוכסטיק
    if last['Stoch'] > 80: analysis.append("⚡ **סטוכסטיק גבוה:** המניה במומנטום חזק אך מתקרבת למיצוי.")
    
    return analysis
