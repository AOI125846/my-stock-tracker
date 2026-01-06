import yfinance as yf
import pandas as pd

def load_stock_data(ticker_symbol, start, end):
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(start=start, end=end)
    
    # תיקון מבנה נתונים
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    info = ticker.info
    full_name = info.get('longName', ticker_symbol)
    
    # שליפת תאריך דוחות קרוב
    calendar = ticker.calendar
    next_earnings = "לא ידוע"
    if calendar is not None and not calendar.empty:
        next_earnings = calendar.iloc[0, 0].strftime('%d/%m/%Y') if hasattr(calendar.iloc[0,0], 'strftime') else "בקרוב"

    return df, full_name, next_earnings
