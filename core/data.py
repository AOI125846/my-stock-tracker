import yfinance as yf
import pandas as pd

def load_stock_data(ticker, start, end):
    # הורדת נתונים
    df = yf.download(ticker, start=start, end=end, progress=False)
    
    if df.empty:
        return df

    # תיקון קריטי: אם העמודות הן MultiIndex (למשל ('Close', 'AAPL')), נשטח אותן לרמה אחת
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # וידוא שמות עמודות תקינים (לפעמים זה מגיע כ-Adj Close)
    if 'Adj Close' in df.columns:
        df['Close'] = df['Adj Close'] # נשתמש ב-Adj Close כברירת מחדל לניתוח טכני
        
    return df
