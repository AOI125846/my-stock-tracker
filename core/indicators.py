import pandas as pd

def calculate_indicators(df, ma_period_type):
    """
    מחשב אינדיקטורים ומוסיף אותם ל-DataFrame
    """
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

    # ממוצעים נעים לפי בחירה
    if ma_period_type == "טווח קצר (סווינג מהיר)":
        periods = [9, 20, 50]
    else: # טווח ארוך
        periods = [100, 150, 200]
        
    for p in periods:
        df[f'SMA_{p}'] = df['Close'].rolling(p).mean()
        
    return df, periods

def generate_explanations(df, periods, levels):
    """
    מייצר הסברים מילוליים לסוחר
    """
    last = df.iloc[-1]
    prev = df.iloc[-2]
    explanations = []
    
    # 1. ניתוח RSI
    rsi_val = last['RSI']
    if rsi_val > 70:
        explanations.append(f"⚠️ **RSI גבוה ({rsi_val:.1f}):** המניה ב'קניית יתר' (Overbought). מבחינה סטטיסטית, הסיכוי לתיקון למטה גובר. היזהר מכניסה לונג עכשיו.")
    elif rsi_val < 30:
        explanations.append(f"✅ **RSI נמוך ({rsi_val:.1f}):** המניה ב'מכירת יתר' (Oversold). ייתכן שהירידות מוצו ויש הזדמנות לעליות בקרוב.")
    else:
        explanations.append(f"ℹ️ **RSI נייטרלי ({rsi_val:.1f}):** אין איתות קיצון כרגע.")

    # 2. ניתוח MACD
    if last['MACD'] > last['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']:
        explanations.append("✅ **חציית MACD חיובית:** קו ה-MACD חצה את הסיגנל כלפי מעלה. זהו איתות שורי (חיובי) מובהק למומנטום.")
    elif last['MACD'] < last['MACD_Signal']:
        explanations.append("🔻 **מומנטום שלילי (MACD):** קו ה-MACD נמצא מתחת לסיגנל. המומנטום כרגע עם המוכרים.")

    # 3. ניתוח ממוצעים נעים
    price = last['Close']
    trends = []
    for p in periods:
        sma_val = last[f'SMA_{p}']
        if price > sma_val:
            trends.append(f"מעל ממוצע {p}")
        else:
            trends.append(f"מתחת לממוצע {p}")
    
    trend_summary = ", ".join(trends)
    explanations.append(f"📊 **מצב ממוצעים ({periods}):** המחיר כרגע {trend_summary}.")
    
    # הסבר ספציפי לממוצע הקצר ביותר
    shortest_ma = periods[0]
    if price > last[f'SMA_{shortest_ma}']:
        explanations.append(f"💡 **משמעות:** המניה שומרת על מומנטום חיובי בטווח המיידי (מעל ממוצע {shortest_ma}).")
    else:
        explanations.append(f"💡 **משמעות:** המניה נחלשה בטווח המיידי (שברה את ממוצע {shortest_ma}).")

    # 4. רמות תמיכה/התנגדות
    explanations.append("---") # קו מפריד
    for level in levels:
        explanations.append(f"🛡️ {level}")

    return explanations
