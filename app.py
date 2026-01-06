import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.data import load_stock_data
from core.indicators import rsi, macd, get_detailed_signal
from utils.export import to_excel

# הגדרות עיצוב ו-RTL
st.set_page_config(page_title="סורק מניות מקצועי", layout="wide")
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    div.stButton > button { background-color: #007bff; color: white; border-radius: 20px; padding: 10px 25px; }
    .stock-card { background-color: #f8f9fa; border-radius: 15px; padding: 20px; border-right: 5px solid #007bff; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 מערכת מעקב וניתוח מניות")

# סרגל צדי - הזנת מניה בלבד
with st.sidebar:
    st.header("🔍 חיפוש מניה")
    ticker_input = st.text_input("הזן סימול מניה (למשל NVDA)", "AAPL").upper()
    ma_type = st.radio("בחר טווח ממוצעים נעים:", ["טווח קצר (9, 20, 50)", "טווח ארוך (100, 150, 200)"])
    analyze_btn = st.button("נתח מניה")

if analyze_btn:
    # טעינת נתונים (ברירת מחדל לשנה אחרונה לניתוח טכני)
    start_date = pd.to_datetime("today") - pd.DateOffset(years=1)
    df, full_name, next_earnings = load_stock_data(ticker_input, start_date, pd.to_datetime("today"))
    
    if df.empty:
        st.error("לא נמצאו נתונים עבור הסימול שהוזן.")
    else:
        # הצגת שם מלא ופרטי מניה
        st.markdown(f"""
            <div class="stock-card">
                <h2>{full_name} ({ticker_input})</h2>
                <p><b>תאריך דוחות קרוב:</b> {next_earnings}</p>
            </div>
            """, unsafe_allow_html=True)

        # חישוב אינדיקטורים
        df['RSI'] = rsi(df['Close'])
        df['MACD'], df['MACD_Signal'] = macd(df['Close'])
        
        # בחירת ממוצעים לפי בחירת המשתמש
        ma_periods = [9, 20, 50] if "קצר" in ma_type else [100, 150, 200]
        for p in ma_periods:
            df[f'SMA_{p}'] = df['Close'].rolling(p).mean()

        tab1, tab2, tab3 = st.tabs(["🚦 איתותי פעולה", "📈 גרף אינטראקטיבי", "📝 יומן טריידים ומעקב"])

        with tab1:
            summary, reasons = get_detailed_signal(df.iloc[-1])
            st.subheader(f"המלצת מערכת: {summary}")
            for r in reasons:
                st.write(f"• {r}")
            
            st.info("💡 **מה זה אומר?** הממוצעים הנעים עוזרים לזהות את כיוון המגמה. פריצה של מחיר מעל ממוצע נחשבת לאיתות כניסה חיובי.")

        with tab2:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='מחיר'))
            for p in ma_periods:
                fig.add_trace(go.Scatter(x=df.index, y=df[f'SMA_{p}'], name=f'ממוצע {p}'))
            fig.update_layout(xaxis_rangeslider_visible=False, height=600, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.subheader("מעקב אחר טריידים")
            col1, col2 = st.columns(2)
            trade_start = col1.date_input("תאריך כניסה לטרייד")
            trade_end = col2.date_input("תאריך יעד/יציאה")
            st.write(f"מעקב אחר המניה בטווח שבין {trade_start} ל-{trade_end}")
            
            # הורדה לאקסל
            excel_data = to_excel(df.tail(30))
            st.download_button("📥 הורד נתוני תקופה לאקסל", data=excel_data, file_name=f"{ticker_input}_tracker.xlsx")
