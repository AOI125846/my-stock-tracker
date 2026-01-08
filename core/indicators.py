"""
מודול לחישוב אינדיקטורים טכניים
"""

import pandas as pd
import numpy as np

# --- חישובים טכניים ---
def calculate_all_indicators(df, ma_type):
    """
    מחשב את כל האינדיקטורים הטכניים עבור DataFrame של מחירי מניות
    
    פרמטרים:
    ----------
    df : pandas.DataFrame
        DataFrame עם עמודות Open, High, Low, Close, Volume
    ma_type : str
        סוג הממוצעים הנעים
    
    מחזיר:
    -------
    tuple : (DataFrame עם אינדיקטורים, רשימת תקופות SMA)
    """
    # יצירת עותק כדי לא לשנות את המקור
    df_calc = df.copy()
    
    # ניקוי עמודות כפולות
    if isinstance(df_calc.columns, pd.MultiIndex):
        df_calc.columns = df_calc.columns.get_level_values(0)
    df_calc = df_calc.loc[:, ~df_calc.columns.duplicated()]
    
    # וידוא שיש עמודת Close
    if 'Close' not in df_calc.columns:
        raise ValueError("DataFrame חייב לכלול עמודת 'Close'")
    
    # בחירת תקופות SMA לפי סוג
    if "קצר" in ma_type:
        periods = [9, 20, 50]
    else:
        periods = [100, 150, 200]
    
    # חישוב Simple Moving Averages
    for p in periods:
        df_calc[f'SMA_{p}'] = df_calc['Close'].rolling(window=p, min_periods=1).mean()
    
    # חישוב RSI (Relative Strength Index)
    delta = df_calc['Close'].diff()
    
    # יצירת סדרות של רווחים והפסדים
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # חישוב ממוצע נע מעריכי
    avg_gain = gain.rolling(window=14, min_periods=1).mean()
    avg_loss = loss.rolling(window=14, min_periods=1).mean()
    
    # חישוב RS ו-RSI (עם הגנה מפני חלוקה באפס)
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df_calc['RSI'] = 100 - (100 / (1 + rs))
    
    # הגבלת ערכי RSI בין 0-100 והחלפת NaN ב-50
    df_calc['RSI'] = df_calc['RSI'].clip(0, 100).fillna(50)
    
    # חישוב MACD (Moving Average Convergence Divergence)
    ema12 = df_calc['Close'].ewm(span=12, adjust=False, min_periods=1).mean()
    ema26 = df_calc['Close'].ewm(span=26, adjust=False, min_periods=1).mean()
    df_calc['MACD'] = ema12 - ema26
    df_calc['MACD_Signal'] = df_calc['MACD'].ewm(span=9, adjust=False, min_periods=1).mean()
    df_calc['MACD_Histogram'] = df_calc['MACD'] - df_calc['MACD_Signal']
    
    # חישוב Bollinger Bands
    df_calc['BB_Mid'] = df_calc['Close'].rolling(window=20, min_periods=1).mean()
    df_calc['BB_Std'] = df_calc['Close'].rolling(window=20, min_periods=1).std()
    df_calc['BB_Upper'] = df_calc['BB_Mid'] + (2 * df_calc['BB_Std'])
    df_calc['BB_Lower'] = df_calc['BB_Mid'] - (2 * df_calc['BB_Std'])
    df_calc['BB_Width'] = (df_calc['BB_Upper'] - df_calc['BB_Lower']) / df_calc['BB_Mid']
    
    # חישוב ממוצעים נעים מעריכיים נוספים
    df_calc['EMA_20'] = df_calc['Close'].ewm(span=20, adjust=False, min_periods=1).mean()
    df_calc['EMA_50'] = df_calc['Close'].ewm(span=50, adjust=False, min_periods=1).mean()
    
    return df_calc, periods


# --- חישוב ציון טכני ---
def calculate_final_score(row, periods):
    """
    מחשב ציון טכני כולל עבור שורה בודדת
    
    פרמטרים:
    ----------
    row : pandas.Series
        שורה עם ערכים של אינדיקטורים
    periods : list
        רשימת תקופות SMA
    
    מחזיר:
    -------
    tuple : (ציון מספרי, המלצה, צבע)
    """
    score = 50  # ציון התחלתי ניטרלי
    
    # בדיקה אם האינדיקטורים קיימים
    try:
        # RSI - 30 נקודות
        if 'RSI' in row and not pd.isna(row['RSI']):
            if row['RSI'] < 30:
                score += 15  # מכירת יתר - הזדמנות קנייה
            elif row['RSI'] > 70:
                score -= 15  # קניית יתר - הזדמנות מכירה
        
        # MACD - 30 נקודות
        if 'MACD' in row and 'MACD_Signal' in row:
            if not pd.isna(row['MACD']) and not pd.isna(row['MACD_Signal']):
                if row['MACD'] > row['MACD_Signal']:
                    score += 15  # MACD מעל סיגנל - מגמה חיובית
                else:
                    score -= 15  # MACD מתחת לסיגנל - מגמה שלילית
        
        # מגמה - 20 נקודות (מחיר vs SMA ארוך טווח)
        long_ma = periods[-1]
        sma_key = f'SMA_{long_ma}'
        if sma_key in row and 'Close' in row:
            if not pd.isna(row[sma_key]) and not pd.isna(row['Close']):
                if row['Close'] > row[sma_key]:
                    score += 10  # מחיר מעל SMA - מגמה עולה
                else:
                    score -= 10  # מחיר מתחת ל-SMA - מגמה יורדת
        
        # Bollinger Bands - 10 נקודות
        if 'Close' in row and 'BB_Upper' in row and 'BB_Lower' in row:
            if not pd.isna(row['Close']) and not pd.isna(row['BB_Upper']) and not pd.isna(row['BB_Lower']):
                if row['Close'] < row['BB_Lower']:
                    score += 5  # מחיר מתחת לרצועה תחתונה - הזדמנות קנייה
                elif row['Close'] > row['BB_Upper']:
                    score -= 5  # מחיר מעל רצועה עליונה - יתר קנייה
        
    except (KeyError, TypeError):
        # אם חסרים אינדיקטורים, נחזיר ציון ניטרלי
        pass
    
    # הגבלת הציון לטווח 0-100
    score = max(0, min(100, score))
    
    # קביעת המלצה וצבע לפי הציון
    if score >= 80:
        return score, "קנייה חזקה 🚀", "green"
    elif score >= 60:
        return score, "קנייה ✅", "#90ee90"
    elif score <= 20:
        return score, "מכירה חזקה 📉", "red"
    elif score <= 40:
        return score, "מכירה 🔻", "orange"
    else:
        return score, "נייטרלי ✋", "gray"


# --- פרשנות טכנית ---
def get_smart_analysis(df, periods):
    """
    מחזיר רשימה של פרשנויות טכניות חכמות
    
    פרמטרים:
    ----------
    df : pandas.DataFrame
        DataFrame עם אינדיקטורים
    periods : list
        רשימת תקופות SMA
    
    מחזיר:
    -------
    list : רשימה של פרשנויות טכניות
    """
    analysis = []
    
    if df.empty:
        return ["אין מספיק נתונים לניתוח"]
    
    last = df.iloc[-1]
    
    # ניתוח RSI
    if 'RSI' in last and not pd.isna(last['RSI']):
        rsi_val = last['RSI']
        if rsi_val > 70:
            analysis.append(f"🔴 **RSI ({rsi_val:.1f}):** קניית יתר. המחיר 'מתוח' מדי וייתכן תיקון.")
        elif rsi_val < 30:
            analysis.append(f"🟢 **RSI ({rsi_val:.1f}):** מכירת יתר. הזדמנות לכניסה עם פוטנציאל לעלייה.")
        elif 30 <= rsi_val <= 70:
            analysis.append(f"⚪ **RSI ({rsi_val:.1f}):** בטווח נורמלי. אין איתותי קיצון.")
    
    # ניתוח MACD
    if 'MACD' in last and 'MACD_Signal' in last:
        if not pd.isna(last['MACD']) and not pd.isna(last['MACD_Signal']):
            if last['MACD'] > last['MACD_Signal']:
                analysis.append("🚀 **MACD:** מומנטום חיובי ומתחזק - סימן למגמת עלייה.")
            else:
                analysis.append("📉 **MACD:** המומנטום נחלש - סימן למגמת ירידה או התארגנות.")
    
    # ניתוח מגמה לפי SMA
    if periods:
        long_ma = periods[-1]
        sma_key = f'SMA_{long_ma}'
        if sma_key in last and 'Close' in last:
            if not pd.isna(last[sma_key]) and not pd.isna(last['Close']):
                if last['Close'] > last[sma_key]:
                    analysis.append(f"📈 **מגמה ({long_ma} ימים):** המחיר מעל הממוצע - מגמת עלייה.")
                else:
                    analysis.append(f"📊 **מגמה ({long_ma} ימים):** המחיר מתחת לממוצע - מגמת ירידה.")
    
    # ניתוח Bollinger Bands
    if 'Close' in last and 'BB_Upper' in last and 'BB_Lower' in last:
        if not pd.isna(last['Close']) and not pd.isna(last['BB_Upper']) and not pd.isna(last['BB_Lower']):
            if last['Close'] > last['BB_Upper']:
                analysis.append("⚠️ **בולינגר:** המחיר חורג מהרצועה העליונה - יתר קנייה.")
            elif last['Close'] < last['BB_Lower']:
                analysis.append("💎 **בולינגר:** המחיר חורג מהרצועה התחתונה - הזדמנות קנייה.")
            else:
                # בדיקת רוחב הרצועות
                if 'BB_Width' in last and not pd.isna(last['BB_Width']):
                    if last['BB_Width'] > last['BB_Width'].mean() if 'BB_Width' in df.columns else 0.1:
                        analysis.append("⚡ **בולינגר:** רוחב רצועות גבוה - תנודתיות מוגברת.")
                    else:
                        analysis.append("🔍 **בולינגר:** רוחב רצועות נורמלי - יציבות יחסית.")
    
    # ניתוח נפח
    if 'Volume' in df.columns and len(df) > 1:
        last_volume = df['Volume'].iloc[-1]
        avg_volume = df['Volume'].iloc[-20:].mean() if len(df) >= 20 else df['Volume'].mean()
        if last_volume > avg_volume * 1.5:
            analysis.append("📦 **נפח:** נפח מסחר גבוה מהממוצע - עניין מוגבר במניה.")
        elif last_volume < avg_volume * 0.5:
            analysis.append("📦 **נפח:** נפח מסחר נמוך מהממוצע - מיעוט עניין.")
    
    # אם אין ניתוחים, נוסיף הודעה כללית
    if not analysis:
        analysis.append("ℹ️ **מידע כללי:** אין איתותים טכניים ברורים. המשך מעקב.")
    
    return analysis


# --- פרשנות פונדמנטלית ---
def analyze_fundamentals(info):
    """
    מנתח נתונים פונדמנטליים של מניה
    
    פרמטרים:
    ----------
    info : dict
        מילון עם נתונים פונדמנטליים מ-yfinance
    
    מחזיר:
    -------
    list : רשימה של תובנות פונדמנטליות
    """
    insights = []
    
    if not info:
        return ["אין נתונים פונדמנטליים זמינים למניה זו."]
    
    try:
        # מכפיל רווח (P/E Ratio)
        pe = info.get('forwardPE', info.get('trailingPE', None))
        if pe:
            if pe < 15:
                insights.append(f"✅ **מכפיל רווח ({pe:.1f}):** המניה זולה ביחס לרווחיה (Value).")
            elif pe > 40:
                insights.append(f"⚠️ **מכפיל רווח ({pe:.1f}):** המניה יקרה (Growth) - צפייה לצמיחה גבוהה.")
            else:
                insights.append(f"ℹ️ **מכפיל רווח ({pe:.1f}):** תמחור סביר ביחס לשוק.")
        
        # יעד אנליסטים
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        target_price = info.get('targetMeanPrice', info.get('targetMedianPrice', 0))
        
        if current_price and target_price and current_price > 0:
            upside = ((target_price - current_price) / current_price) * 100
            if upside > 15:
                insights.append(f"🎯 **תחזית אנליסטים:** צופים עלייה של {upside:.1f}% למחיר {target_price:.2f}$.")
            elif upside > 0:
                insights.append(f"📊 **תחזית אנליסטים:** צופים עלייה מתונה של {upside:.1f}%.")
            elif upside < -10:
                insights.append(f"🔻 **תחזית אנליסטים:** המחיר כרגע גבוה ב-{abs(upside):.1f}% ממחיר היעד.")
        
        # רווחיות
        margins = info.get('profitMargins', 0)
        if margins:
            if margins > 0.2:
                insights.append(f"💎 **רווחיות:** החברה רווחית מאוד (שולי רווח של {margins*100:.1f}%).")
            elif margins > 0.1:
                insights.append(f"👍 **רווחיות:** החברה רווחית (שולי רווח של {margins*100:.1f}%).")
            elif margins < 0:
                insights.append(f"⚠️ **סיכון:** החברה מפסידה כסף כרגע.")
        
        # חוב
        debt_to_equity = info.get('debtToEquity', None)
        if debt_to_equity:
            if debt_to_equity > 2:
                insights.append(f"🏦 **מבנה הון:** יחס חוב להון גבוה ({debt_to_equity:.1f}) - סיכון פיננסי.")
            elif debt_to_equity < 0.5:
                insights.append(f"💪 **מבנה הון:** מבנה הון שמרני (חוב נמוך).")
        
        # דיבידנד
        dividend_yield = info.get('dividendYield', 0)
        if dividend_yield and dividend_yield > 0:
            insights.append(f"💰 **דיבידנד:** תשואת דיבידנד של {dividend_yield*100:.2f}%.")
        
        # צמיחה
        revenue_growth = info.get('revenueGrowth', None)
        if revenue_growth:
            if revenue_growth > 0.2:
                insights.append(f"📈 **צמיחה:** צמיחת הכנסות גבוהה ({revenue_growth*100:.1f}%).")
            elif revenue_growth < 0:
                insights.append(f"📉 **צמיחה:** ירידה בהכנסות ({revenue_growth*100:.1f}%).")
    
    except Exception as e:
        insights.append(f"⚠️ **שגיאה בניתוח פונדמנטלי:** {str(e)}")
    
    # אם אין תובנות, נוסיף הודעה כללית
    if not insights:
        insights.append("ℹ️ **מידע פונדמנטלי:** אין מספיק נתונים לניתוח מעמיק.")
    
    return insights
