import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# הגדרות דף ועיצוב צבעוני
st.set_page_config(page_title="Global Market Terminal", layout="wide")

# עיצוב CSS כדי להפוך את האתר למרשים
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    </style>
    """, unsafe_allow_html=True)

# כותרת האתר
st.markdown("<h1 style='text-align: center; color: #00D1FF;'>🌐 טרמינל מסחר גלובלי - Pro Insight</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>ניתוח מגמות, קריפטו, סחורות ומדדים בזמן אמת</p>", unsafe_allow_html=True)

# --- פונקציות עזר ---
@st.cache_data(ttl=300)
def load_data(symbol, period="1y"):
    df = yf.download(symbol, period=period)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # חישוב אינדיקטורים
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    return df

# --- סרגל צד ---
st.sidebar.header("🚀 מרכז שליטה")
ticker = st.sidebar.text_input("חיפוש מניה/מדד:", "NVDA").upper()
show_ma = st.sidebar.checkbox("הצג ממוצעים נעים", value=True)

# --- אזור המגמות הכלליות (Top Bar) ---
st.markdown("### 🌍 מגמות עולמיות (Market Snapshot)")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

# רשימת נכסים למעקב כללי
global_assets = {
    "S&P 500": "SPY",
    "ביטקוין (BTC)": "BTC-USD",
    "זהב (Gold)": "GC=F",
    "נפט (Oil)": "CL=F"
}

cols = [m_col1, m_col2, m_col3, m_col4]
for (name, sym), col in zip(global_assets.items(), cols):
    g_data = yf.download(sym, period="2d")
    if not g_data.empty:
        if isinstance(g_data.columns, pd.MultiIndex): g_data.columns = g_data.columns.get_level_values(0)
        price = g_data['Close'].iloc[-1]
        change = price - g_data['Close'].iloc[0]
        col.metric(name, f"${price:,.2f}", f"{change:,.2f}")

st.divider()

# --- אזור הגרף הראשי ---
tab_main, tab_crypto, tab_journal = st.tabs(["📈 גרף נרות וניתוח", "🪙 עולם הקריפטו וסחורות", "📋 יומן וביצועים"])

with tab_main:
    data = load_data(ticker)
    if data is not None:
        col_info, col_chart = st.columns([1, 4])
        
        with col_info:
            st.markdown(f"**נתוני {ticker}**")
            curr_p = data['Close'].iloc[-1]
            st.write(f"מחיר סגירה: **${curr_p:.2f}**")
            st.write(f"גבוה שנתי: ${data['High'].max():.2f}")
            st.write(f"נמוך שנתי: ${data['Low'].min():.2f}")
            
            # ציון מגמה (לוגיקה של Micha Stocks)
            if curr_p > data['SMA50'].iloc[-1] > data['SMA200'].iloc[-1]:
                st.success("מגמה: קנייה חזקה 🔥")
            elif curr_p < data['SMA50'].iloc[-1]:
                st.error("מגמה: הימנעות ❌")
            else:
                st.warning("מגמה: דשדוש 🟡")

        with col_chart:
            # גרף נרות יפניים מקצועי
            fig = go.Figure(data=[go.Candlestick(
                x=data.index,
                open=data['Open'], high=data['High'],
                low=data['Low'], close=data['Close'],
                increasing_line_color='#00ff00', decreasing_line_color='#ff0000',
                name="נרות יפניים"
            )])
            
            if show_ma:
                fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name="SMA 50", line=dict(color='orange', width=1.5)))
                fig.add_trace(go.Scatter(x=data.index, y=data['SMA200'], name="SMA 200", line=dict(color='blue', width=1.5)))
            
            fig.update_layout(height=500, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
            

with tab_crypto:
    st.subheader("📊 השוואת סחורות ומטבעות דיגיטליים")
    # גרף השוואתי
    crypto_list = ["BTC-USD", "ETH-USD", "GC=F", "CL=F"]
    c_data = yf.download(crypto_list, period="1mo")['Close']
    if isinstance(c_data.columns, pd.MultiIndex): c_data.columns = c_data.columns.get_level_values(0)
    
    # נרמול הגרף כדי לראות אחוזי שינוי
    c_data_norm = c_data / c_data.iloc[0] * 100
    st.line_chart(c_data_norm)
    st.caption("גרף באחוזים (השוואתי - בסיס 100)")

with tab_journal:
    st.subheader("💰 ניהול תיק אישי")
    c1, c2, c3 = st.columns(3)
    buy_price = c1.number_input("מחיר קנייה ($)", value=0.0)
    amount = c2.number_input("כמות מניות", value=1)
    usd_rate = yf.download("ILS=X", period="1d")['Close'].iloc[-1]
    
    if buy_price > 0:
        profit_usd = (data['Close'].iloc[-1] - buy_price) * amount
        st.metric("רווח/הפסד מצטבר", f"${profit_usd:.2f}", f"₪{profit_usd * usd_rate:.2f}")

st.divider()
st.caption("הנתונים נמשכים מ-Yahoo Finance. השימוש על אחריות המשתמש בלבד.")
