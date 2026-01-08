import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import io
import requests
import streamlit.components.v1 as components
import uuid

# הגדרות דף
st.set_page_config(page_title="התיק החכם", layout="wide")

# עיצוב מתקדם עם תמונת רקע
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
    h1, h2, h3 { text-align: center; color: #1E1E1E; }
    .stTextInput { width: 50% !important; margin: 0 auto; }
    </style>
""", unsafe_allow_html=True)

# פונקציית טעינה עם מנגנון "ניסיון חוזר"
def fetch_stock_data(symbol):
    try:
        s = requests.Session()
        s.headers.update({'User-Agent': 'Mozilla/5.0'})
        ticker = yf.Ticker(symbol, session=s)
        # ניסיון משיכה ראשון
        df = ticker.history(period="1y")
        if df.empty:
            # ניסיון משיכה שני בשיטה חלופית
            df = yf.download(symbol, period="1y", progress=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df, ticker.info if not df.empty else None
    except:
        return None, None

if 'trades' not in st.session_state:
    st.session_state.trades = {}

st.title("📈 התיק החכם")

# שורת חיפוש ממרכזת
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    ticker_input = st.text_input("הזן סימול מניה (למשל AAPL, TSLA):", "AAPL").upper()

if ticker_input:
    with st.spinner('מתחבר לבורסה...'):
        df, info = fetch_stock_data(ticker_input)

    if df is not None and not df.empty:
        st.success(f"נתוני {ticker_input} נטענו בהצלחה")
        
        t1, t2, t3 = st.tabs(["📊 גרף טכני", "🏢 נתוני חברה", "📓 יומן עסקאות"])
        
        with t1:
            # הטמעת הגרף של TradingView
            html_chart = f"""
            <div style="height:500px;">
                <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                <script type="text/javascript">
                new TradingView.widget({{
                  "width": "100%", "height": 500, "symbol": "{ticker_input}",
                  "interval": "D", "timezone": "Etc/UTC", "theme": "light",
                  "style": "1", "locale": "he_IL", "enable_publishing": false,
                  "hide_top_toolbar": false, "save_image": false, "container_id": "tv_chart"
                }});
                </script>
                <div id="tv_chart"></div>
            </div>
            """
            components.html(html_chart, height=520)

        with t2:
            if info:
                st.subheader(f"מידע על {info.get('longName', ticker_input)}")
                st.write(info.get('longBusinessSummary', 'אין תיאור זמין.'))
            else:
                st.info("מידע פונדמנטלי לא זמין כרגע, אך הגרף תקין.")

        with t3:
            # מערכת היומן עם כפתור מחיקה וייצוא
            st.subheader("ניהול תיק אישי")
            if st.button("➕ הוסף פוזיציה נוכחית"):
                id = str(uuid.uuid4())
                st.session_state.trades[id] = {"מניה": ticker_input, "מחיר": df['Close'].iloc[-1]}
                st.rerun()

            for tid, t in list(st.session_state.trades.items()):
                c1, c2 = st.columns([4, 1])
                c1.write(f"עסקה ב-{t['מניה']} במחיר ${t['מחיר']:.2f}")
                if c2.button("🗑️", key=tid):
                    del st.session_state.trades[tid]
                    st.rerun()
    else:
        st.error(f"לא הצלחנו למשוך נתונים עבור {ticker_input}. ייתכן שיש עומס על השרת, נסה שוב בעוד רגע.")
