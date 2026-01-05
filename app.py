import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.data import load_stock_data
from core.indicators import sma, rsi, macd
from utils.export import to_excel

# הגדרת עמוד רחב
st.set_page_config(page_title="Stock Tracker Pro", layout="wide", page_icon="📈")

# כותרת ראשית מעוצבת
st.markdown("""
    <h1 style='text-align: center; color: #4F8BF9;'>📈 Stock Tracker – Professional Edition</h1>
    <p style='text-align: center;'>Advanced Technical Analysis & Journaling</p>
    """, unsafe_allow_html=True)

# ========= Sidebar =========
st.sidebar.header("⚙️ Settings")

ticker = st.sidebar.text_input("Ticker Symbol", "AAPL").upper()
# תאריכים דינמיים כברירת מחדל
default_start = pd.to_datetime("today") - pd.DateOffset(years=1)
default_end = pd.to_datetime("today")

start_date = st.sidebar.date_input("Start Date", default_start)
end_date = st.sidebar.date_input("End Date", default_end)

st.sidebar.markdown("---")
st.sidebar.info(f"**Trading Fees:**\n\nRemember strictly: **$6** Buy / **$6** Sell per trade.")

# ========= Main Logic =========
if st.sidebar.button("🚀 Analyze Stock", use_container_width=True):
    with st.spinner('Fetching market data...'):
        df = load_stock_data(ticker, start_date, end_date)

    if df.empty:
        st.error(f"No data found for ticker **{ticker}**. Please check the symbol or date range.")
        st.stop()

    # חישוב אינדיקטורים
    df["SMA20"] = sma(df["Close"], 20)
    df["SMA50"] = sma(df["Close"], 50)
    df["RSI"] = rsi(df["Close"])
    df["MACD"], df["MACD_SIGNAL"] = macd(df["Close"])

    # --- Top Metrics Row ---
    last_close = df["Close"].iloc[-1]
    prev_close = df["Close"].iloc[-2]
    change = last_close - prev_close
    pct_change = (change / prev_close) * 100
    last_volume = df["Volume"].iloc[-1]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Last Price", f"${last_close:.2f}", f"{change:.2f} ({pct_change:.2f}%)")
    col2.metric("RSI (14)", f"{df['RSI'].iloc[-1]:.2f}")
    col3.metric("Volume", f"{last_volume:,.0f}")
    col4.metric("Trend (SMA50)", "Bullish" if last_close > df["SMA50"].iloc[-1] else "Bearish")

    # --- Interactive Charts (Plotly) ---
    st.markdown("---")
    
    # יצירת תת-גרפים: מחיר למעלה, MACD למטה
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, row_heights=[0.7, 0.3])

    # 1. Candlestick Chart
    fig.add_trace(go.Candlestick(x=df.index,
                    open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'],
                    name='Price'), row=1, col=1)

    # SMAs
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1), name='SMA 20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='blue', width=1), name='SMA 50'), row=1, col=1)

    # 2. MACD Chart
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='purple', width=1), name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_SIGNAL'], line=dict(color='orange', width=1), name='Signal'), row=2, col=1)
    
    # Histogram colors
    colors = ['green' if val >= 0 else 'red' for val in (df['MACD'] - df['MACD_SIGNAL'])]
    fig.add_trace(go.Bar(x=df.index, y=(df['MACD'] - df['MACD_SIGNAL']), marker_color=colors, name='Hist'), row=2, col=1)

    # Layout updates
    fig.update_layout(
        title=f"{ticker} Technical Analysis",
        xaxis_rangeslider_visible=False,
        height=600,
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- Tabs for Data & Journal ---
    tab1, tab2 = st.tabs(["📊 Raw Data", "📥 Trading Journal"])

    with tab1:
        st.dataframe(df.tail(20).style.format("{:.2f}"), use_container_width=True)

    with tab2:
        st.write("Download the processed data for your Excel Journal.")
        
        journal = df.reset_index()[[
            "Date", "Open", "High", "Low", "Close",
            "Volume", "SMA20", "SMA50", "RSI", "MACD"
        ]]
        
        excel_file = to_excel(journal)
        
        st.download_button(
            "📥 Download Excel Journal",
            data=excel_file,
            file_name=f"{ticker}_journal.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("👈 Enter a ticker symbol and click 'Analyze Stock' to start.")
