import yfinance as yf
import pandas as pd

def load_stock_data(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        
        if df.empty:
            return pd.DataFrame()

        # תיקון למבנה הנתונים החדש של yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df.loc[:, ~df.columns.duplicated()]
        
        if 'Adj Close' in df.columns:
            df['Close'] = df['Adj Close']
            
        return df
    except Exception as e:
        return pd.DataFrame()
