import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import os

# הגדרות דף
st.set_page_config(page_title="Market Trend Tracker", layout="wide")
st.title("מערכת מעקב מגמות וביצועים")

# פונקציה לניהול קובץ הנתונים
DB_FILE = "trading_journal.csv"
if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=["תאריך", "סימול", "מחיר כניסה", "מחיר יציאה", "רווח/הפסד %"])
    df_init.to_csv(DB_FILE, index=False)

# סרגל צד - הזנת נתונים
st.sidebar.header("הוספת טרייד ליומן")
with st.sidebar.form("trade_form"):
    ticker_input = st.text_input("סימול מניה:", "AAPL")
    buy_p = st.number_input("מחיר כניסה:", step=0.01)
    sell_p = st.number_input("מחיר יציאה:", step=0.01)
    submitted = st.form_submit_button("שמור טרייד")

if submitted:
    profit_pct = ((sell_p - buy_p) / buy_p) * 100 if buy_p > 0 else 0
    new_data = pd.DataFrame([[pd.Timestamp.now().date(), ticker_input, buy_p, sell_p, f"{profit_pct:.2f}%"]], 
                            columns=["תאריך", "סימול", "מחיר כניסה", "מחיר יציאה", "רווח/הפסד %"])
    new_data.to_csv(DB_FILE, mode='a', header=False, index=False)
    st.sidebar.success("הטרייד נשמר!")

# הצגת נתוני שוק ומגמות
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"ניתוח מגמה: {ticker_input}")
    data = yf.download(ticker_input, period="1y")
    
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                    open=data['Open'], high=data['High'],
                    low=data['Low'], close=data['Close'], name="מחיר")])
    
    # הוספת ממוצעים נעים לזיהוי מגמה
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name="SMA 50", line=dict(color='orange')))
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("יומן ביצועים")
    history_df = pd.read_csv(DB_FILE)
    st.dataframe(history_df.tail(10), use_container_width=True)

# מבט על השוק הכללי
st.divider()
st.subheader("מגמת שוק כללית (S&P 500 & Nasdaq)")
indices = yf.download(["SPY", "QQQ"], period="5d")['Close']

st.line_chart(indices)
