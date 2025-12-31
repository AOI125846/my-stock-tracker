import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# הגדרות דף
st.set_page_config(page_title="Trend Tracker - Micha Stocks Method", layout="wide")
st.title("📊 מערכת מעקב מגמות וביצועים")

# סרגל צד לחיפוש
st.sidebar.header("חיפוש וניתוח")
ticker = st.sidebar.text_input("הכנס סימול מניה (למשל SPY, NVDA):", "SPY").upper()

# פונקציה למשיכת נתונים וחישוב אינדיקטורים
def get_stock_data(ticker):
    data = yf.download(ticker, period="1y", interval="1d")
    if not data.empty:
        # חישוב ממוצעים נעים
        data['SMA50'] = data['Close'].rolling(window=50).mean()
        data['SMA200'] = data['Close'].rolling(window=200).mean()
        return data
    return None

data = get_stock_data(ticker)

if data is not None:
    # אזור המדדים העליון
    col1, col2, col3, col4 = st.columns(4)
    current_price = data['Close'].iloc[-1]
    sma50 = data['SMA50'].iloc[-1]
    sma200 = data['SMA200'].iloc[-1]
    
    col1.metric("מחיר עכשיו", f"${current_price:.2f}")
    col2.metric("SMA 50", f"${sma50:.2f}")
    col3.metric("SMA 200", f"${sma200:.2f}")
    
    # קביעת מצב מגמה לפי הקובץ שלך
    if current_price > sma50 and sma50 > sma200:
        trend_status = "🔥 פריצה / קנייה חזקה"
        color = "green"
    elif current_price < sma50:
        trend_status = "❌ להימנע / מגמה יורדת"
        color = "red"
    else:
        trend_status = "🟡 מגמה לא ברורה"
        color = "orange"
        
    col4.markdown(f"**סטטוס:** <span style='color:{color}'>{trend_status}</span>", unsafe_allow_html=True)

    # גרף נרות יפניים אינטראקטיבי
    st.subheader(f"גרף מגמה - {ticker}")
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                    open=data['Open'], high=data['High'],
                    low=data['Low'], close=data['Close'], name="מחיר")])
    
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name="SMA 50", line=dict(color='orange', width=1.5)))
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA200'], name="SMA 200", line=dict(color='blue', width=1.5)))
    
    st.plotly_chart(fig, use_container_width=True)

    # הצגת טבלת נתונים אחרונים
    st.subheader("נתונים אחרונים")
    st.dataframe(data.tail(10))
else:
    st.error("לא ניתן היה למשוך נתונים עבור הסימול שהוזן.")

# מבט שוק כללי בתחתית
st.divider()
st.subheader("מבט על השוק הכללי")
m_col1, m_col2 = st.columns(2)
m_col1.write("**S&P 500 (SPY)**")
m_col1.line_chart(yf.download("SPY", period="1mo")['Close'])
m_col2.write("**NASDAQ (QQQ)**")
m_col2.line_chart(yf.download("QQQ", period="1mo")['Close'])
