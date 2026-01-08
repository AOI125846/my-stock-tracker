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
    
    # הגבלת ערכי RSI בין 0-100
    df_calc['RSI'] = df_calc['RSI'].clip(0, 100)
    
    # חישוב MACD (Moving Average Convergence Divergence)
    ema12 = df_calc['Close'].ewm(span=12, adjust=False, min_periods=1).mean()
    ema26 = df_calc['Close'].ewm(span=26, adjust=False, min_periods=1).mean()
    df_calc['MACD'] = ema12 - ema26
    df_calc['MACD_Signal'] = df_calc['MACD'].ewm(span=9, adjust=False, min_periods=1).mean()
    
    # חישוב Bollinger Bands
    df_calc['BB_Mid'] = df_calc['Close'].rolling(window=20, min_periods=1).mean()
    df_calc['BB_Std'] = df_calc['Close'].rolling(window=20, min_periods=1).std()
    df_calc['BB_Upper'] = df_calc['BB_Mid'] + (2 * df_calc['BB_Std'])
    df_calc['BB_Lower'] = df_calc['BB_Mid'] - (2 * df_calc['BB_Std'])
    
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
    score = 50  # ציון התחלתי
    
    # RSI - 30 נקודות
    if 'RSI' in row and not pd.isna(row['RSI']):
        if row['RSI'] < 30:
            score += 15  # מכירת יתר - הזדמנות קנייה
        elif row['RSI'] > 70:
            score -= 15  # קניית יתר - הז
