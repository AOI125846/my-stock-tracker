import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

# --- הגדרות מערכת ועיצוב ---
st.set_page_config(page_title="Titanium Trading Terminal", layout="wide", initial_sidebar_state="collapsed")

# הזרקת CSS לעיצוב יוקרתי ומקצועי
st.markdown("""
    <style>
    /* רקע כללי כהה עם גרדיאנט עדין */
    .stApp {
        background: linear-gradient(to bottom right, #0e1117, #1c2025);
        color: #ffffff;
    }
    /* כרטיסיות נתונים */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #00d4ff;
    }
    /* עיצוב טבלאות */
    .stDataFrame {
        border: 1px solid #30363d;
        border-radius: 5px;
    }
    /* כותרות */
    h1, h2, h3 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans_serif;
        color: #e6e6e6;
    }
    /* כפתורים */
    .stButton>button {
        background-color: #238636;
        color: white;
        border: none;
        border-radius: 4px;
    }
    .stButton>button:hover {
        background-color: #2ea043;
    }
    </style>
    """, unsafe_allow_html=True)

# --- פונקציות ליבה ---

# 1. ניהול יומן מסחר (CSV)
JOURNAL_FILE = "trading_journal.csv"

def load_journal():
    if not os.path.exists(JOURNAL_FILE):
        df = pd.DataFrame(columns=["תאריך", "סימול", "קנייה ($)", "מכירה ($)", "כמות", "רווח ($)", "רווח (₪)", "תשואה (%)"])
        df.to_csv(JOURNAL_FILE, index=False)
        return df
    return pd.read_csv(JOURNAL_FILE)

def save_trade(date, symbol, buy, sell, qty, usd_rate):
    profit_usd = (sell - buy) * qty
    profit_ils = profit_usd * usd_rate
    profit_pct = ((sell - buy) / buy) * 100 if buy > 0 else 0
    
    new_row = pd.DataFrame([{
        "תאריך": date,
        "סימול": symbol,
        "קנייה ($)": round(buy, 2),
        "מכירה ($)": round(sell, 2),
        "כמות": qty,
        "רווח ($)": round(profit_usd, 2),
        "רווח (₪)": round(profit_ils, 2),
        "תשואה (%)": f"{profit_pct:.2f}%"
    }])
    
    # טעינה, הוספה ושמירה
    df = load_journal()
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(JOURNAL_FILE, index=False)
    return df

# 2. משיכת שער דולר
@st.cache_data(ttl=3600)
def get_usd_rate():
    try:
        ticker = yf.Ticker("ILS=X")
        return ticker.history(period="1d")['Close'].iloc[-1]
    except:
        return 3.65

# 3. ניתוח טכני וחישוב ציון
def analyze_stock(symbol):
    try:
        df = yf.download(symbol, period="2y", interval="1d")
        if df.empty: return None, 0, "אין נתונים"
        
        # MultiIndex Fix
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # חישוב אינדיקטורים
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain/loss)))
        
        # MACD
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # חישוב ציון (Score)
        score = 50
        last = df.iloc[-1]
        
        if last['Close'] > last['SMA200']: score += 20 # מגמה ראשית חיובית
        if last['SMA50'] > last['SMA200']: score += 10 # Golden Cross
        if last['MACD'] > last['Signal']: score += 10 # מומנטום חיובי
        if 30 < last['RSI'] < 70: score += 10 # לא במצבי קיצון
        if last['RSI'] > 70: score -= 10 # קניית יתר (סיכון)
        
        # הגבלת ציון 0-100
        score = max(0, min(100, score))
        
        return df, score
    except Exception as e:
        return None, 0, str(e)

# --- ממשק משתמש (UI) ---

# כותרת ראשית ומגמות שוק
st.markdown("<h1 style='text-align: center; color: #d4af37; letter-spacing: 2px;'>TITANIUM TRADING TERMINAL</h1>", unsafe_allow_html=True)

# שורת מדדים עליונה
usd_val = get_usd_rate()
indices = {"S&P 500": "SPY", "NASDAQ": "QQQ", "GOLD": "GC=F", "BITCOIN": "BTC-USD"}
cols = st.columns(len(indices) + 1)
cols[0].metric("USD/ILS", f"₪{usd_val:.3f}")

for i, (name, sym) in enumerate(indices.items(), 1):
    try:
        d = yf.Ticker(sym).history(period="2d")
        if not d.empty:
            curr = d['Close'].iloc[-1]
            prev = d['Close'].iloc[-2]
            delta = ((curr - prev)/prev)*100
            cols[i].metric(name, f"{curr:,.2f}", f"{delta:.2f}%")
    except:
        cols[i].metric(name, "N/A", "0%")

st.divider()

# אזור עבודה ראשי
col_search
