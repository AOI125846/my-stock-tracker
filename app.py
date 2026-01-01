import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import io

# =====================
# Technical Indicators
# =====================

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line


# =====================
# Main App
# =====================

def main():
    st.title("📈 Stock Tracker")

    ticker = st.text_input("Ticker", "AAPL")
    start = st.date_input("Start Date")
    end = st.date_input("End Date")

    if st.button("Load Data"):
        df = yf.download(ticker, start=start, end=end)

        if df.empty:
            st.error("No data found")
            return

        df["SMA20"] = df["Close"].rolling(20).mean()
        df["SMA50"] = df["Close"].rolling(50).mean()
        df["RSI"] = rsi(df["Close"])
        df["MACD"], df["MACD_SIGNAL"] = macd(df["Close"])

        st.subheader("📊 Data Preview")
        st.dataframe(df.tail())

        # ===== Journal =====
        journal = df.reset_index()[[
            "Date", "Open", "High", "Low", "Close", "Volume",
            "RSI", "MACD", "MACD_SIGNAL"
        ]]

        # ===== Excel Export =====
        output = io.BytesIO()
        journal.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            "📥 Download Trading Journal (Excel)",
            data=output,
            file_name=f"{ticker}_journal.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


if __name__ == "__main__":
    main()
