import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# הגדרות עיצוב ודף
st.set_page_config(page_title="Pro Trader Dashboard", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 מערכת מסחר חכמה - Pro Insight")

# סרגל צד - ניהול הגדרות
st.sidebar.header("🔍 חיפוש והגדרות")
ticker = st.sidebar.text_input("הכנס סימול מניה:", "NVDA").upper()

# שאיבת שער דולר עדכני (לצורך חישוב בשקלים)
usd_ils = yf.Ticker("ILS=X").history(period="1d")['Close'].iloc[-1]

# פונקציה למשיכת נתונים ואינדיקטורים
@st.cache_data
def get_full_data(ticker):
    data = yf.download(ticker, period="2y", interval="1d")
    if data.empty: return None
    # ממוצעים נעים
    for period in [9, 20, 50, 100, 150, 200]:
        data[f'SMA{period}'] = data['Close'].rolling(window=period).mean()
    
    # RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = data['EMA12'] - data['EMA26']
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    
    return data

stock_data = get_full_data(ticker)

if stock_data is not None:
    # יצירת לשוניות למעבר נח (Tabs)
    tab1, tab2, tab3, tab4 = st.tabs(["📈 ניתוח טכני", "📊 אינדיקטורים", "📰 חדשות ואנליסטים", "💼 תיק השקעות"])

    with tab1:
        st.subheader(f"גרף מחיר - {ticker}")
        
        # בחירת ממוצעים להצגה
        col_sma1, col_sma2 = st.columns(2)
        with col_sma1:
            short_term = st.multiselect("טווח קצר", ["SMA9", "SMA20", "SMA50"], default=["SMA20"])
        with col_sma2:
            long_term = st.multiselect("טווח ארוך", ["SMA100", "SMA150", "SMA200"], default=["SMA200"])
        
        fig = go.Figure(data=[go.Candlestick(x=stock_data.index, open=stock_data['Open'], 
                                            high=stock_data['High'], low=stock_data['Low'], 
                                            close=stock_data['Close'], name="מחיר")])
        
        for sma in short_term + long_term:
            fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data[sma], name=sma))
        
        fig.update_layout(height=600, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col_rsi, col_macd = st.columns(2)
        with col_rsi:
            st.subheader("RSI (מדד עוצמה יחסית)")
            st.line_chart(stock_data['RSI'].tail(100))
            st.info("מעל 70: קניית יתר | מתחת 30: מכירת יתר")
            
        with col_macd:
            st.subheader("MACD")
            st.line_chart(stock_data[['MACD', 'Signal']].tail(100))

    with tab3:
        st.subheader("תחזית אנליסטים וחדשות")
        info = yf.Ticker(ticker).info
        
        c1, c2, c3 = st.columns(3)
        c1.metric("מחיר יעד ממוצע", f"${info.get('targetMeanPrice', 'N/A')}")
        c2.metric("המלצה", info.get('recommendationKey', 'N/A').upper())
        c3.metric("שווי שוק", f"{info.get('marketCap', 0):,}")
        
        st.write("---")
        st.write("📰 **כותרות אחרונות:**")
        news = yf.Ticker(ticker).news
        for item in news[:5]:
            st.write(f"- [{item['title']}]({item['link']})")

    with tab4:
        st.subheader("ניהול תיק השקעות (ביצועים)")
        # נתונים לדוגמה (ניתן לחבר לקובץ ה-CSV שלך)
        trade_data = pd.DataFrame({
            "מניה": [ticker],
            "כמות": [10],
            "מחיר קנייה": [stock_data['Close'].iloc[-100]], # דוגמה
            "מחיר נוכחי": [stock_data['Close'].iloc[-1]]
        })
        
        trade_data['רווח ב-$'] = (trade_data['מחיר נוכחי'] - trade_data['מחיר קנייה']) * trade_data['כמות']
        trade_data['רווח ב-₪'] = trade_data['רווח ב-$'] * usd_ils
        
        st.table(trade_data.style.format({"רווח ב-$": "{:.2f}$", "רווח ב-₪": "₪{:.2f}"}))
        st.write(f"💵 שער דולר נוכחי: **{usd_ils:.3f} ₪**")

else:
    st.error("לא הצלחנו למצוא את המניה. וודא שהסימול נכון.")
