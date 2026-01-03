import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Stock Tracker – Professional Edition",
    layout="wide"
)

st.title("📈 Stock Tracker – Professional Edition")

# -------------------------------------------------
# Sidebar – Settings
# -------------------------------------------------
with st.sidebar:
    st.header("Settings")

    ticker = st.text_input("Ticker", "AAPL").upper()

    today = date.today()

    start_date = st.date_input(
        "Start Date",
        value=today - timedelta(days=365),
        max_value=today
    )

    end_date = st.date_input(
        "End Date",
        value=today,
        max_value=today
    )

# -------------------------------------------------
# Data loading
# -------------------------------------------------
@st.cache_data(ttl=300)
def load_data(symbol, start, end):
    df = yf.download(symbol, start=start, end=end, progress=False)
    return df

df = load_data(ticker, start_date, end_date)

# -------------------------------------------------
# Validation
# -------------------------------------------------
if df is None or df.empty:
    st.warning("No data found for the selected ticker or date range.")
    st.stop()

required_cols = {"Open", "High", "Low", "Close", "Volume"}
if not required_cols.issubset(df.columns):
    st.error("Invalid data structure received from data provider.")
    st.stop()

# -------------------------------------------------
# Indicators
# -------------------------------------------------
df = df.copy()

# SMA
df["SMA20"] = df["Close"].rolling(20).mean()
df["SMA50"] = df["Close"].rolling(50).mean()
df["SMA200"] = df["Close"].rolling(200).mean()

# RSI
delta = df["Close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss.replace(0, np.nan)
df["RSI"] = 100 - (100 / (1 + rs))
df["RSI"] = df["RSI"].fillna(50)

# MACD
ema12 = df["Close"].ewm(span=12, adjust=False).mean()
ema26 = df["Close"].ewm(span=26, adjust=False).mean()

df["MACD"] = ema12 - ema26
df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

# -------------------------------------------------
# Header metrics
# -------------------------------------------------
last_price = df["Close"].iloc[-1]
prev_price = df["Close"].iloc[-2]
change_pct = (last_price - prev_price) / prev_price * 100

c1, c2, c3 = st.columns(3)
c1.metric("Last Price", f"${last_price:.2f}", f"{change_pct:.2f}%")
c2.metric("RSI", f"{df['RSI'].iloc[-1]:.1f}")
c3.metric("Volume", f"{int(df['Volume'].iloc[-1]):,}")

# -------------------------------------------------
# Price chart
# -------------------------------------------------
fig = go.Figure()

fig.add_candlestick(
    x=df.index,
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    name="Price"
)

fig.add_scatter(x=df.index, y=df["SMA50"], name="SMA 50")
fig.add_scatter(x=df.index, y=df["SMA200"], name="SMA 200")

fig.update_layout(
    height=600,
    xaxis_rangeslider_visible=False,
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# RSI & MACD
# -------------------------------------------------
st.subheader("RSI")
st.line_chart(df["RSI"])

st.subheader("MACD")
st.line_chart(df[["MACD", "Signal"]])

# -------------------------------------------------
# Data table & export
# -------------------------------------------------
with st.expander("Show raw data"):
    st.dataframe(df, use_container_width=True)

csv = df.to_csv().encode("utf-8")
st.download_button(
    "Download data as CSV",
    data=csv,
    file_name=f"{ticker}_data.csv",
    mime="text/csv"
)
