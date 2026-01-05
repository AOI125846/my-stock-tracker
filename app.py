import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.data import load_stock_data
from core.indicators import sma, rsi, macd, analyze_signals
from utils.export import to_excel

st.set_page_config(page_title="Stock Tracker Pro", layout="wide", page_icon="📈")

# כותרת
st.markdown("""
    <h1 style='text-align: center; color: #4F8BF9;'>📈 Stock Tracker – Professional Edition</h1>
    """, unsafe_allow_html=True)

# ========= Sidebar =========
st.sidebar.header("⚙️ Settings")
ticker = st.sidebar.text_input("Ticker Symbol", "AAPL").upper()
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("today") - pd.DateOffset(years=1))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

st.sidebar.markdown("---")
st.sidebar.info(f"**Micha Stocks Rules:**\n\nFEES: **$6** Buy / **$6** Sell.\nTotal **$12** round trip.")

# ========= Main Logic =========
if st.sidebar.button("🚀 Analyze Stock", use_container_width=True):
    with st.spinner('Fetching market data...'):
        df = load_stock_data(ticker, start_date, end_date)

    if df.empty:
        st.error(f"Could not load data for {ticker}. Check symbol.")
        st.stop()

    # חישוב אינדיקטורים
    df["SMA20"] = sma(df["Close"], 20)
    df["SMA50"] = sma(df["Close"], 50)
    df["RSI"] = rsi(df["Close"])
    df["MACD"], df["MACD_SIGNAL"] = macd(df["Close"])

    # ניתוח נתונים אחרונים
    last_row = df.iloc[-1]
    signals = analyze_signals(last_row)
    
    # --- תצוגת ציון ראשי ---
    st.markdown("---")
    col_main1, col_main2, col_main3 = st.columns([1, 2, 1])
    with col_main2:
        st.metric(label="📢 AI RECOMMENDATION", value=signals["summary"], delta=f"Score: {signals['score']}/3")

    # --- טאבים ---
    tab1, tab2, tab3 = st.tabs(["🚦 Signals & Action", "📉 Live Charts", "💾 Data Journal"])

    # === TAB 1: פרשנות לפעולה ===
    with tab1:
        st.subheader("📋 Action Plan (Based on Indicators)")
        
        c1, c2, c3 = st.columns(3)
        
        # RSI Card
        c1.info(f"**RSI (Momentum)**")
        c1.write(f"Value: **{last_row['RSI']:.2f}**")
        c1.markdown(f"👉 **Action: {signals['rsi_action']}**")
        c1.caption("Low (<30) = Buy | High (>70) = Sell")

        # MACD Card
        c2.info(f"**MACD (Trend Change)**")
        c2.write(f"Line vs Signal")
        c2.markdown(f"👉 **Action: {signals['macd_action']}**")
        c2.caption("Line crosses above Signal = Buy")

        # SMA Card
        c3.info(f"**Trend (SMA 50)**")
        c3.write(f"Price: ${last_row['Close']:.2f}")
        c3.markdown(f"👉 **Status: {signals['trend_action']}**")
        c3.caption("Price above SMA50 = Bullish")

    # === TAB 2: גרפים ===
    with tab2:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        
        # Candles
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='blue', width=1.5), name='SMA 50'), row=1, col=1)

        # MACD
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='purple'), name='MACD'), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_SIGNAL'], line=dict(color='orange'), name='Signal'), row=2, col=1)
        
        fig.update_layout(height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    # === TAB 3: יומן מסחר ===
    with tab3:
        st.write("Export data for your Excel Journal:")
        journal_df = df.reset_index()[["Date", "Close", "RSI", "MACD", "SMA50"]]
        excel_file = to_excel(journal_df)
        st.download_button("📥 Download Excel", data=excel_file, file_name=f"{ticker}_analysis.xlsx")

else:
    st.info("👈 Enter a ticker (e.g., TSLA, NVDA) and click Analyze.")
