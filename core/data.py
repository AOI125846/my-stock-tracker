import yfinance as yf
import pandas as pd

def load_stock_data(ticker, start, end):
    try:
        # הורדת נתונים
        df = yf.download(ticker, start=start, end=end, progress=False)
        
        if df.empty:
            return pd.DataFrame()

        # === תיקון קריטי לגרסאות חדשות של yfinance ===
        # אם יש כותרת כפולה (למשל Ticker מעל Close), נעיף אותה
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # וודא שאין עמודות כפולות ושמות העמודות נקיים
        df = df.loc[:, ~df.columns.duplicated()]
        
        # המרת עמודת Adj Close ל-Close לניתוח טכני אם צריך
        if 'Adj Close' in df.columns and 'Close' not in df.columns:
            df['Close'] = df['Adj Close']
            
        return df

    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()
