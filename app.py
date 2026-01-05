import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core.data import load_stock_data
from core.indicators import sma, rsi, macd, analyze_signals
from utils.export import to_excel

# הגדרות תצוגה בעברית ויישור לימין
st.set_page_config(page_title="סורק מניות מקצועי", layout="wide")
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 מערכת מעקב מניות - מהדורת Micha Stocks")

# תפריט צד
st.sidebar.header("⚙️ הגדרות")
ticker = st.sidebar.text_input("סימול מניה (למשל TSLA)", "AAPL").upper()
start_date = st.sidebar.date_input("תאריך התחלה", pd.to_datetime("2024-01-01"))
end_date = st.sidebar.date_input("תאריך סיום")

st.sidebar.markdown("---")
st.sidebar.write("⚠️ **תזכורת עמלות:**")
st.sidebar.write("6$ קנייה | 6$ מכירה")

if st.sidebar.button("נתח מניה"):
    df = load_stock_data(ticker, start_date, end_date)
    
    if df.empty:
        st.error("לא נמצאו נתונים. בדוק את הסימול.")
    else:
        # חישובים
        df["SMA20"] = sma(df["Close"], 20)
        df["SMA50"] = sma(df["Close"], 50)
        df["RSI"] = rsi(df["Close"])
        df["MACD"], df["MACD_SIGNAL"] = macd(df["Close"])
        
        res = analyze_signals(df.iloc[-1])
        
        # תצוגת ציון כללי
        st.metric("ציון פעולה משוקלל", res["summary"], f"ניקוד: {res['score']}")

        tab1, tab2, tab3 = st.tabs(["🚦 איתותים ופעולה", "📊 גרף טכני", "📋 נתונים להורדה"])

        with tab1:
            col1, col2, col3 = st.columns(3)
            col1.info(f"**RSI**\n\n{res['rsi']}")
            col2.info(f"**MACD**\n\n{res['macd']}")
            col3.info(f"**מגמה**\n\n{res['trend']}")

        with tab2:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05)
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='מחיר'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name='ממוצע 50', line=dict(color='blue')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='purple')), row=2, col=1)
            fig.update_layout(height=600, template="plotly_white", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.dataframe(df.tail(10).iloc[::-1])
            excel_data = to_excel(df)
            st.download_button("📥 הורד יומן מסחר לאקסל", data=excel_data, file_name=f"{ticker}_trading_log.xlsx")

else:
    st.info("הזן סימול מניה בצד ימין ולחץ על 'נתח מניה' כדי להתחיל.")
