import streamlit as st
import pandas as pd

from core.data import load_stock_data
from core.indicators import sma, rsi, macd
from utils.export import to_excel

st.set_page_config(page_title="Stock Tracker", layout="wide")
st.title("📈 Stock Tracker – Professional Edition")

# ========= Sidebar =========
st.sidebar.header("Settings")

ticker = st.sidebar.text_input("Ticker", "AAPL")
start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")

# ========= Main =========
if st.sidebar.button("Load Data"):
    df = load_stock_data(ticker, start_date, end_date)

    if df.empty:
        st.error("No data returned.")
        st.stop()

    # Indicators
    df["SMA20"] = sma(df["Close"], 20)
    df["SMA50"] = sma(df["Close"], 50)
    df["RSI"] = rsi(df["Close"])
    df["MACD"], df["MACD_SIGNAL"] = macd(df["Close"])

    st.subheader("📊 Price & Indicators")
    st.dataframe(df.tail(20), use_container_width=True)

    # Journal
    journal = df.reset_index()[[
        "Date", "Open", "High", "Low", "Close",
        "Volume", "RSI", "MACD", "MACD_SIGNAL"
    ]]

    excel_file = to_excel(journal)

    st.download_button(
        "📥 Download Trading Journal (Excel)",
        data=excel_file,
        file_name=f"{ticker}_journal.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
