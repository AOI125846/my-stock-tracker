import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import io
import requests
import streamlit.components.v1 as components
import uuid

# --- הגדרות דף ---
st.set_page_config(page_title="התיק החכם", layout="wide")

# עיצוב CSS לרקע ויישור לימין
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-image: url("https://images.unsplash.com/photo-1611974717482-589252c8465f?q=80&w=2070");
        background-size: cover;
        background-attachment: fixed;
    }
    .main .block-container {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 20px;
        margin-top: 2rem;
        direction: rtl;
    }
    div.stButton > button { width: 100%; }
    .stTextInput input { text-align: center; }
    </style>
""", unsafe_allow_html=True)

# פונקציית טעינת נתונים חסינה
def get_stock_data(symbol):
    try:
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        stock = yf.Ticker(symbol, session=session)
        df = stock.history(period="1y")
        if df.empty:
            df = yf.download(symbol, period="1y", progress=False)
        return df, stock.info
    except:
        return None, None

# ניהול מצב (Session)
if 'my_trades' not in st.session_state:
    st.session_state.my_trades = {}

# --- ממשק משתמש ---
st.title("📈 התיק החכם")

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    ticker = st.text_input("הזן סימול מניה (למשל TSLA):", "AAPL").upper()

if ticker:
    df, info = get_stock_data(ticker)
    
    if df is not None and not df.empty:
        st.subheader(f"ניתוח מניית {ticker}")
        
        tab_chart, tab_info, tab_journal = st.tabs(["📊 גרף טכני", "🏢 אודות", "📓 יומן אישי"])
        
        with tab_chart:
            # הטמעת TradingView ללא ספריות חיצוניות
            tv_html = f"""
            <div style="height:500px;">
                <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                <script type="text/javascript">
                new TradingView.widget({{
                  "width": "100%", "height": 500, "symbol": "{ticker}",
                  "interval": "D", "timezone": "Etc/UTC", "theme": "light",
                  "style": "1", "locale": "he_IL", "container_id": "tv_chart_id"
                }});
                </script>
                <div id="tv_chart_id"></div>
            </div>
            """
            components.html(tv_html, height=520)

        with tab_info:
            if info:
                st.write(f"**שם החברה:** {info.get('longName', ticker)}")
                st.write(f"**ענף:** {info.get('industry', 'לא ידוע')}")
                st.write(info.get('longBusinessSummary', 'אין תיאור זמין.'))
            else:
                st.warning("לא הצלחנו למשוך מידע פונדמנטלי, אך הגרף זמין.")

        with tab_journal:
            st.markdown("### ניהול פוזיציות")
            if st.button(f"הוסף את {ticker} ליומן"):
                trade_id = str(uuid.uuid4())[:8]
                st.session_state.my_trades[trade_id] = {
                    "מניה": ticker,
                    "מחיר": df['Close'].iloc[-1],
                    "תאריך": str(pd.Timestamp.now().date())
                }
                st.success("נשמר!")
            
            if st.session_state.my_trades:
                for tid, t in list(st.session_state.my_trades.items()):
                    c1, c2 = st.columns([4, 1])
                    c1.info(f"📌 {t['מניה']} | מחיר: ${t['מחיר']:.2f} | תאריך: {t['תאריך']}")
                    if c2.button("מחק", key=tid):
                        del st.session_state.my_trades[tid]
                        st.rerun()
    else:
        st.error(f"לא נמצאו נתונים עבור {ticker}. וודא שהסימול נכון.")
