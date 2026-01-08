"""
מודול ליצוא נתונים לפורמטים שונים
"""

import io
import pandas as pd

def to_excel(df):
    """
    ממיר DataFrame לקובץ Excel
    
    פרמטרים:
    ----------
    df : pandas.DataFrame
        DataFrame לייצוא
    
    מחזיר:
    -------
    BytesIO : buffer עם קובץ Excel
    """
    buffer = io.BytesIO()
    
    # יצירת Excel writer
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Portfolio')
    
    buffer.seek(0)
    return buffer


def to_csv(df):
    """
    ממיר DataFrame לקובץ CSV
    
    פרמטרים:
    ----------
    df : pandas.DataFrame
        DataFrame לייצוא
    
    מחזיר:
    -------
    str : מחרוזת CSV
    """
    return df.to_csv(index=False, encoding='utf-8-sig')


def format_portfolio_summary(df_portfolio, latest_prices):
    """
    מעצב סיכום פורטפוליו לתצוגה
    
    פרמטרים:
    ----------
    df_portfolio : pandas.DataFrame
        DataFrame עם פוזיציות
    latest_prices : dict
        מילון עם מחירים עדכניים
    
    מחזיר:
    -------
    pandas.DataFrame : DataFrame מעוצב
    """
    if df_portfolio.empty:
        return pd.DataFrame()
    
    # יצירת עותק
    df_summary = df_portfolio.copy()
    
    # הוספת מחירים נוכחיים
    df_summary['CurrentPrice'] = df_summary['Ticker'].map(latest_prices)
    
    # חישוב ערכים
    df_summary['Invested'] = df_summary['EntryPrice'] * df_summary['Shares']
    df_summary['CurrentValue'] = df_summary['CurrentPrice'] * df_summary['Shares']
    df_summary['P&L ($)'] = df_summary['CurrentValue'] - df_summary['Invested']
    df_summary['P&L (%)'] = (df_summary['P&L ($)'] / df_summary['Invested']) * 100
    
    return df_summary
