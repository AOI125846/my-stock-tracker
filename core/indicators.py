import pandas as pd
import numpy as np

def calculate_indicators(df, ma_period_type):
    # RSI - מדד העוצמה היחסית
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD - מומנטום
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Bollinger Bands - רצועות בולינגר (תנודתיות וקיצון)
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (2 * df['BB_Std'])
    df['BB_Lower'] = df['BB_Middle'] - (2 * df['BB_Std'])

    # Stochastic Oscillator - מהירות המחיר
    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    df['Stoch_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    
    # ממוצעים נעים
    periods = [9, 20, 50] if "קצר" in ma_period_type else [100, 150, 200]
    for p in periods:
        df[f'SMA_{p}'] = df['Close'].rolling(p).mean()
        
    return df, periods

def generate_explanations(df, periods):
    last = df.iloc[-1]
    explanations = []
    
    # ניתוח RSI
    if last['RSI'] > 70:
        explanations.append(f"🔴 **RSI ({last['RSI']:.1f}):** קניית יתר קיצונית. המחיר 'מתוח' מדי למעלה ועלול לבצע תיקון.")
    elif last['RSI'] < 30:
        explanations.append(f"🟢 **RSI ({last['RSI']:.1f}):** מכירת יתר. המניה זולה סטטיסטית, הזדמנות להיפוך מעלה.")
    else:
        explanations.append(f"⚪ **RSI ({last['RSI']:.1f}):** מצב נייטרלי, אין קיצון כרגע.")

    # ניתוח MACD
    if last['MACD'] > last['MACD_Signal']:
        explanations.append("🚀 **MACD:** קו המומנטום מעל קו הסיגנל. המגמה כרגע חיובית.")
    else:
        explanations.append("📉 **MACD:** קו המומנטום מתחת לסיגנל. היזהר, המומנטום כרגע שלילי.")

    # ניתוח בולינגר
    if last['Close'] > last['BB_Upper']:
        explanations.append("⚠️ **רצועות בולינגר:** המחיר נוגע ברצועה העליונה. תמחור גבוה ביחס לממוצע.")
    elif last['Close'] < last['BB_Lower']:
        explanations.append("💰 **רצועות בולינגר:** המחיר פרץ את הרצועה התחתונה. הזדמנות קנייה טכנית.")

    # ניתוח ממוצעים נעים
    main_ma = periods[1] # ממוצע 20 או 150
    if last['Close'] > last[f'SMA_{main_ma}']:
        explanations.append(f"📈 **מגמה:** המניה נסחרת מעל ממוצע {main_ma}, מה שמעיד על כוח של קונים.")
    else:
        explanations.append(f"📉 **מגמה:** המניה מתחת לממוצע {main_ma}. המגמה בטווח זה נחשבת שלילית.")

    return explanations
