import yfinance as yf
import pandas as pd

def load_stock_data(ticker):
    try:
        # שימוש באובייקט Ticker שהוא יציב יותר
        stock = yf.Ticker(ticker)
        
        # משיכת היסטוריה של שנתיים (כדי שיהיה מספיק לממוצע 200)
        df = stock.history(period="2y")
        
        if df.empty:
            return None, None, None
            
        # מידע פונדמנטלי (פרופיל חברה)
        info = stock.info
        
        # ניסיון לחלץ שם מלא
        full_name = info.get('longName', ticker)
        
        return df, info, full_name
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None, None, None
