import yfinance as yf
import pandas as pd
import streamlit as st

# שימוש ב-Cache כדי למנוע חסימות של Yahoo ולשפר מהירות
@st.cache_data(ttl=3600)
def load_stock_data(ticker):
    try:
        # 1. משיכת נתוני מחיר (השיטה הישנה והאמינה)
        df = yf.download(ticker, period="2y", auto_adjust=True, progress=False)
        
        # תיקון למבנה הנתונים החדש של yfinance (אם יש MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # בדיקה אם חזר מידע ריק
        if df.empty or len(df) < 10:
            return None, None, None

        # 2. משיכת נתונים פנדמנטליים (בנפרד, כדי לא להכשיל את הגרף)
        info = {}
        full_name = ticker
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            full_name = info.get('longName', ticker)
        except Exception:
            # אם נכשל להביא מידע פנדמנטלי, נמשיך עם הגרף בלבד
            print(f"Could not fetch fundamental info for {ticker}")

        return df, info, full_name
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None, None, None
