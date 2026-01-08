"""
מודול לטעינת נתוני מניות
"""

import yfinance as yf
import pandas as pd
import streamlit as st

@st.cache_data(ttl=3600)
def load_stock_data(ticker):
    """
    טוען נתוני מניות מ-yfinance
    
    פרמטרים:
    ----------
    ticker : str
        סימול המניה (למשל: AAPL, TSLA)
    
    מחזיר:
    -------
    tuple : (DataFrame עם נתוני מחיר, dict עם מידע, str עם שם החברה)
    """
    try:
        # שימוש ב-download עם תקופת זמן ארוכה יותר
        df = yf.download(
            ticker, 
            period="2y", 
            auto_adjust=True, 
            progress=False,
            timeout=10
        )
        
        # טיפול ב-MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        if df.empty or len(df) < 5:
            st.warning(f"⚠️  נתונים מוגבלים או ריקים עבור {ticker}")
            return None, None, ticker
        
        # משיכת מידע נוסף בנפרד
        info = {}
        full_name = ticker
        
        try:
            t_obj = yf.Ticker(ticker)
            info = t_obj.info
            
            # שם מלא של החברה
            full_name = info.get('longName', info.get('shortName', ticker))
            
        except Exception as e:
            st.warning(f"⚠️  לא הצלחנו לקבל מידע נוסף: {str(e)}")
        
        return df, info, full_name
        
    except Exception as e:
        st.error(f"❌ שגיאה בטעינת נתונים עבור {ticker}: {str(e)}")
        
        # הצעה לסימולים חלופיים אם יש שגיאה
        st.info("""
        **טיפים:**
        1. ודא שהסימול תקין (לדוגמה: AAPL, TSLA, GOOGL)
        2. נסה להוסיף את השוק (למשל: TSLA, AAPL, MSFT)
        3. המתין מספר שניות ונסה שוב
        """)
        
        return None, None, ticker
