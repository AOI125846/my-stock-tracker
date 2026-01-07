import pandas as pd
import numpy as np

# --- חישובים טכניים ---
def calculate_all_indicators(df, ma_type):
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

    # Bollinger
    df['BB_Mid'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Mid'] + (2 * df['BB_Std'])
    df['BB_Lower'] = df['BB_Mid'] - (2 * df['BB_Std'])

    # Stochastic
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    df['Stoch'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    
    return df, periods

# --- חישוב ציון טכני ---
def calculate_final_score(row, periods):
    score = 50
    # RSI
    if row['RSI'] < 30: score += 15
    elif row['RSI'] > 70: score -= 15
    # MACD
    if row['MACD'] > row['MACD_Signal']: score += 15
    else: score -= 15
    # Trend
    long_ma = periods[-1]
    if row['Close'] > row[f'SMA_{long_ma}']: score += 10
    else: score -= 10
    
    score = max(0, min(100, score))
    
    if score >= 80: return score, "קנייה חזקה 🚀", "green"
    elif score >= 60: return score, "קנייה ✅", "#90ee90"
    elif score <= 20: return score, "מכירה חזקה 📉", "red"
    elif score <= 40: return score, "מכירה 🔻", "orange"
    else: return score, "נייטרלי ✋", "gray"

# --- פרשנות טכנית ---
def get_smart_analysis(df, periods):
    last = df.iloc[-1]
    analysis = []
    
    if last['RSI'] > 70: analysis.append(f"🔴 **RSI ({last['RSI']:.1f}):** קניית יתר. המחיר 'מתוח' מדי.")
    elif last['RSI'] < 30: analysis.append(f"🟢 **RSI ({last['RSI']:.1f}):** מכירת יתר. הזדמנות לכניסה.")
    
    if last['MACD'] > last['MACD_Signal']: analysis.append("🚀 **MACD:** מומנטום חיובי ומתחזק.")
    else: analysis.append("📉 **MACD:** המומנטום נחלש (שלילי).")

    if last['Close'] > last['BB_Upper']: analysis.append("⚠️ **בולינגר:** המחיר חורג מהרצועה העליונה.")
    
    return analysis

# --- פרשנות פונדמנטלית (חדש!) ---
def analyze_fundamentals(info):
    insights = []
    
    # מכפיל רווח (PE)
    pe = info.get('forwardPE', None)
    if pe:
        if pe < 15: insights.append(f"✅ **מכפיל רווח ({pe:.2f}):** המניה נחשבת זולה ביחס לרווחיה (Value).")
        elif pe > 40: insights.append(f"⚠️ **מכפיל רווח ({pe:.2f}):** המניה מתומחרת יקר מאוד (צמיחה גבוהה נדרשת להצדקה).")
        else: insights.append(f"ℹ️ **מכפיל רווח ({pe:.2f}):** תמחור סביר וממוצע לשוק.")
    
    # יעד אנליסטים
    current_price = info.get('currentPrice', 0)
    target_price = info.get('targetMeanPrice', 0)
    if current_price and target_price:
        upside = ((target_price - current_price) / current_price) * 100
        if upside > 10: insights.append(f"🎯 **תחזית אנליסטים:** צופים עלייה של {upside:.1f}% למחיר {target_price}$.")
        elif upside < 0: insights.append(f"🔻 **תחזית אנליסטים:** המחיר הנוכחי גבוה ממחיר היעד הממוצע ({target_price}$).")

    # רווחיות
    margins = info.get('profitMargins', 0)
    if margins > 0.2: insights.append(f"💎 **רווחיות:** החברה רווחית מאוד (שולי רווח של {margins*100:.1f}%).")
    elif margins < 0: insights.append(f"⚠️ **סיכון:** החברה מפסידה כסף כרגע (שולי רווח שליליים).")

    return insights
