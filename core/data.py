import yfinance as yf
import pandas as pd
import streamlit as st

@st.cache_data(ttl=3600)
def load_stock_data(ticker):
    try:
        # שימוש ב-download לאמינות מקסימלית במשיכת מחירים
        df = yf.download(ticker, period="2y", auto_adjust=True, progress=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df.empty:
            return None, None, None

        # משיכת מידע נוסף בנפרד
        info = {}
        full_name = ticker
        try:
            t_obj = yf.Ticker(ticker)
            info = t_obj.info
            full_name = info.get('longName', ticker)
        except:
            pass

        return df, info, full_name
    except Exception as e:
        st.error(f"שגיאת מערכת בטעינה: {e}")
        return None, None, None
