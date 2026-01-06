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

    # Bollinger Bands (רצועות בולינגר)
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (2 * df['BB_Std'])
    df['BB_Lower'] = df['BB_Middle'] - (2 * df['BB_Std'])

    # Stochastic Oscillator
    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    df['Stoch_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()

    # ממוצעים נעים לפי בחירה
    if ma_period_type == "טווח קצר (סווינג מהיר)":
        periods = [9, 20, 50]
    else:
        periods = [100, 150, 200]
        
    for p in periods:
        df[f'SMA_{p}'] = df['Close'].rolling(p).mean()
        
    return df, periods

def calculate_final_score(row, periods):
    """
    מחשב ציון מ-0 עד 100 ומחזיר המלצה
    """
    score = 50 # נקודת מוצא נייטרלית
    
    # 1. RSI (מקסימום 20 נקודות)
    if row['RSI'] < 30: score += 15 # מכירת יתר - איתות קנייה
    elif row['RSI'] > 70: score -= 15 # קניית יתר - איתות מכירה
    
    # 2. MACD (מקסימום 20 נקודות)
    if row['MACD'] > row['MACD_Signal']: score += 15
    else: score -= 15

    # 3. ממוצעים נעים (מקסימום 20 נקודות) - בדיקת המגמה הראשית
    main_ma = periods[-1] # הממוצע הארוך ביותר בחבילה
    if row['Close'] > row[f'SMA_{main_ma}']: score += 10
    else: score -= 10

    # 4. רצועות בולינגר (הזדמנויות קיצון)
    if row['Close'] < row['BB_Lower']: score += 10 # מחיר זול מאוד
    elif row['Close'] > row['BB_Upper']: score -= 10 # מחיר יקר מאוד

    # 5. סטוכסטיק
    if row['Stoch_K'] < 20: score += 5
    elif row['Stoch_K'] > 80: score -= 5

    # גבולות הציון
    score = max(0, min(100, score))
    
    # קביעת המלצה טקסטואלית וצבע
    if score >= 80: return score, "קנייה חזקה 🚀", "green"
    elif score >= 60: return score, "קנייה ✅", "lightgreen"
    elif score <= 20: return score, "מכירה חזקה 📉", "red"
    elif score <= 40: return score, "מכירה 🔻", "orange"
    else: return score, "המתנה / נייטרלי ✋", "gray"

def generate_explanations(df, periods):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    explanations = []
    
    # MACD
    if last['MACD'] > last['MACD_Signal']:
        status = "חיובי" if last['MACD'] > 0 else "חיובי (בתחתית)"
        explanations.append(f"🔹 **MACD:** הקו הכחול מעל הכתום ({status}). המומנטום תומך בעליות.")
    else:
        explanations.append(f"🔸 **MACD:** הקו הכחול מתחת לכתום. המומנטום שלילי.")

    # Bollinger
    if last['Close'] > last['BB_Upper']:
        explanations.append("⚠️ **בולינגר:** המחיר פרץ את הרצועה העליונה - המניה יקרה סטטיסטית (סיכון לתיקון).")
    elif last['Close'] < last['BB_Lower']:
        explanations.append("💎 **בולינגר:** המחיר מתחת לרצועה התחתונה - המניה זולה סטטיסטית (הזדמנות).")

    # RSI
    if last['RSI'] > 70:
        explanations.append(f"⚠️ **RSI ({last['RSI']:.0f}):** רמת קניית יתר קיצונית.")
    elif last['RSI'] < 30:
        explanations.append(f"✅ **RSI ({last['RSI']:.0f}):** רמת מכירת יתר - המוכרים התעייפו.")

    return explanations
