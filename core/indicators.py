import pandas as pd
import numpy as np

def calculate_indicators(df, ma_period_type):
    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (2 * df['BB_Std'])
    df['BB_Lower'] = df['BB_Middle'] - (2 * df['BB_Std'])

    # Stochastic Oscillator
    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    df['Stoch_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    
    # ממוצעים נעים
    periods = [9, 20, 50] if "קצר" in ma_period_type else [100, 150, 200]
    for p in periods:
        df[f'SMA_{p}'] = df['Close'].rolling(p).mean()
        
    return df, periods

def calculate_final_score(row, periods):
    score = 50
    # לוגיקת ניקוד (RSI, MACD, MA)
    if row['RSI'] < 30: score += 15
    elif row['RSI'] > 70: score -= 15
    if row['MACD'] > row['MACD_Signal']: score += 15
    else: score -= 15
    
    score = max(0, min(100, score))
    if score >= 70: return score, "קנייה ✅", "green"
    elif score <= 30: return score, "מכירה 🔻", "red"
    return score, "נייטרלי ✋", "gray"

def generate_explanations(df, periods):
    last = df.iloc[-1]
    exps = []
    # RSI
    if last['RSI'] > 70: exps.append(f"🔴 **RSI ({last['RSI']:.1f}):** קניית יתר - המחיר גבוה מדי.")
    elif last['RSI'] < 30: exps.append(f"🟢 **RSI ({last['RSI']:.1f}):** מכירת יתר - הזדמנות קנייה.")
    # MACD
    if last['MACD'] > last['MACD_Signal']: exps.append("🚀 **MACD:** מומנטום חיובי (קו חוצה סיגנל מעלה).")
    else: exps.append("📉 **MACD:** מומנטום שלילי.")
    # Bollinger
    if last['Close'] > last['BB_Upper']: exps.append("⚠️ **בולינגר:** המחיר חורג מהרצועה העליונה - תמחור גבוה.")
    elif last['Close'] < last['BB_Lower']: exps.append("💰 **בולינגר:** המחיר מתחת לרצועה התחתונה - זול טכנית.")
    # Stochastic
    if last['Stoch_K'] > 80: exps.append("⚡ **סטוכסטיק:** מהירות המחיר גבוהה מאוד, ייתכן שינוי כיוון.")
    
    return exps
