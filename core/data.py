import yfinance as yf
import pandas as pd
import time

def load_stock_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        # שימוש בתקופה קבועה של שנתיים כדי לחשב ממוצעים ארוכים ותמיכה/התנגדות
        df = ticker.history(period="2y")
        
        if df.empty:
            return pd.DataFrame(), ticker_symbol, "לא ידוע", []

        info = ticker.info
        full_name = info.get('longName', ticker_symbol)
        
        # תאריך דוחות
        calendar = ticker.calendar
        next_earnings = "לא ידוע"
        if calendar is not None and not calendar.empty:
            if isinstance(calendar, pd.DataFrame) and 'Earnings Date' in calendar.index:
                 next_earnings = calendar.loc['Earnings Date'][0].strftime('%d/%m/%Y')
            else:
                 next_earnings = "בקרוב"

        # חישוב רמות תמיכה והתנגדות בסיסיות (נקודות קיצון)
        support = df['Low'].min()
        resistance = df['High'].max()
        levels = [f"תמיכה היסטורית: {support:.2f}$", f"התנגדות היסטורית: {resistance:.2f}$"]

        return df, full_name, next_earnings, levels
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame(), ticker_symbol, "שגיאה בטעינה", []
