import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# הגדרות דף
st.set_page_config(page_title="Global Market Pro", layout="wide")

# עיצוב כהה ויוקרתי
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #161b22; border-radius: 5px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# פונקציית שער דולר חסינה
@st.cache_data(ttl=3600)
def get_usd_rate():
    try:
        d = yf.download("ILS=X", period="1d", interval="1m")
        return float(d['Close'].iloc[-1])
    except:
        return 3.70

usd_rate = get_usd_rate()

# פונקציה למשיכת כל מניה וחישוב כל האינדיקטורים
@st.cache_data(ttl=300)
def get_all_data(symbol):
    try:
        df = yf.download(symbol, period="2y")
        if df.empty: return None
        # שיטוח כותרות למניעת KeyError
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # חישוב כל הממוצעים שביקשת
        for m in [9, 20, 50, 100, 150, 200]:
            df[f'SMA{m}'] = df['Close'].rolling(window=m).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain/loss)))
        
        # MACD
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        return df
    except:
        return None

# סרגל צד - בחירת מניה
st.sidebar.title("🔍 חיפוש שוק")
# כאן אתה יכול להזין כל מניה (למשל: TSLA, AMZN, MSFT, או 2812.HK)
ticker = st.sidebar.text_input("הכנס סימול מניה (כל מניה מהשוק):", "AAPL").upper()

data = get_all_data(ticker)

if data is not None:
    st.title(f"📊 ניתוח מקצועי: {ticker}")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📈 גרף נרות", "🛠️ אינדיקטורים", "💰 יומן וביצועים", "🌐 מגמות עולם"])
    
    with tab1:
        # בחירת ממוצעים להצגה על הגרף
        selected_ma = st.multiselect("בחר ממוצעים להצגה:", [9, 20, 50, 100, 150, 200], default=[50, 200])
        
        fig = go.Figure(data=[go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'],
            low=data['Low'], close=data['Close'], name="מחיר"
        )])
        
        for m in selected_ma:
            fig.add_trace(go.Scatter(x=data.index, y=data[f'SMA{m}'], name=f"SMA {m}"))
        
        fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col_rsi, col_macd = st.columns(2)
        with col_rsi:
            st.subheader("RSI (מדד עוצמה)")
            st.line_chart(data['RSI'].tail(150))
            
        with col_macd:
            st.subheader("MACD (מומנטום)")
            st.line_chart(data[['MACD', 'Signal']].tail(150))
            

    with tab3:
        st.subheader("תיעוד וחישוב רווחים")
        c1, c2 = st.columns(2)
        buy_p = c1.number_input("מחיר קנייה ($)", min_value=0.0, step=0.01)
        qty = c2.number_input("כמות מניות", min_value=1, step=1)
        
        if buy_p > 0:
            current_p = float(data['Close'].iloc[-1])
            profit_usd = (current_p - buy_p) * qty
            profit_ils = profit_usd * usd_rate
            
            st.metric("רווח/הפסד בדולר", f"${profit_usd:,.2f}")
            st.metric("רווח/הפסד בשקל", f"₪{profit_ils:,.2f}")
            st.caption(f"שער דולר מחושב: {usd_rate:.3f}")

    with tab4:
        st.subheader("מגמות עולמיות - השוואה")
        # קריפטו, זהב, נפט
        indices = {"ביטקוין": "BTC-USD", "זהב": "GC=F", "נפט": "CL=F", "S&P 500": "SPY"}
        idx_choice = st.multiselect("בחר נכסים להשוואה:", list(indices.keys()), default=["S&P 500", "ביטקוין"])
        
        if idx_choice:
            compare_df = pd.DataFrame()
            for name in idx_choice:
                temp_data = yf.download(indices[name], period="1mo")['Close']
                if isinstance(temp_data, pd.DataFrame): temp_data = temp_data.iloc[:, 0]
                compare_df[name] = temp_data / temp_data.iloc[0] # נרמול ל-100%
            
            st.line_chart(compare_df * 100)
            st.info("הגרף מציג שינוי באחוזים מתחילת החודש")

else:
    st.error(f"לא הצלחנו למצוא נתונים עבור '{ticker}'. וודא שהסימול נכון (למשל AAPL למניית אפל).")
