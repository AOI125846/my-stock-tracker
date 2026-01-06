import yfinance as yf
import pandas as pd
import streamlit as st

# שימוש ב-Cache מונע קריאות מיותרות לשרת וחסימות
@st.cache_data(ttl=3600)  # שומר נתונים בזיכרון למשך שעה
def load_stock_data(ticker_symbol):
    try:
        if not ticker_symbol:
            return None, None, None, []
            
        ticker = yf.Ticker(ticker_symbol)
        
        # הורדת נתונים - תקופה של שנתיים לחישוב ממוצעים ארוכים
        df = ticker.history(period="2y")
        
        if df.empty:
            return pd.DataFrame(), ticker_symbol, "לא נמצא", []

        # תיקון שמות עמודות (למקרה של MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # מידע כללי
        info = ticker.info
        full_name = info.get('longName', ticker_symbol)
        
        # תאריך דוחות קרוב
        try:
            calendar = ticker.calendar
            next_earnings = "לא ידוע"
            if calendar is not None and not calendar.empty:
                # בדיקה אם זה מילון או DataFrame (משתנה בין גרסאות)
                if isinstance(calendar, dict) and 'Earnings Date' in calendar:
                    next_earnings = str(calendar['Earnings Date'][0])
                elif isinstance(calendar, pd.DataFrame):
                    # ניסיון לחלץ תאריך ראשון
                    next_earnings = calendar.iloc[0, 0].strftime('%d/%m/%Y') if hasattr(calendar.iloc[0,0], 'strftime') else "בקרוב"
        except Exception:
            next_earnings = "לא זמין"

        # חישוב רמות תמיכה והתנגדות (לפי 6 חודשים אחרונים)
        recent_df = df.tail(126) # חצי שנת מסחר
        support = recent_df['Low'].min()
        resistance = recent_df['High'].max()
        levels = [
            f"קו תמיכה חזק (חצי שנתי): {support:.2f}$", 
            f"קו התנגדות (שיא חצי שנתי): {resistance:.2f}$"
        ]

        return df, full_name, next_earnings, levels

    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame(), ticker_symbol, "שגיאה", []
