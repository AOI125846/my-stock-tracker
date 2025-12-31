import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# הגדרות דף
st.set_page_config(page_title="Professional Trading Terminal", layout="wide")

# עיצוב כהה ומרשים
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stNumberInput, .stTextInput { background-color: #161b22; }
    </style>
    """, unsafe_allow_html=True)

# פונקציה לשער דולר
@st.cache_data(ttl=3600)
def get_usd_rate():
    try:
        d = yf.download("ILS=X", period="1d", interval="1m")
        return float(d['Close'].iloc[-1])
    except:
        return 3.70

usd_rate = get_usd_rate()

# --- כותרת וחיפוש מרכזי ---
st.markdown("<h1 style='text-align: center; color: #00D1FF;'>💎 Pro Insight - מסוף מסחר</h1>", unsafe_allow_html=True)
ticker = st.text_input("🔍 חפש מניה או מדד (למשל: AAPL, TSLA, BTC-USD):", "NVDA").upper()

# פונקציה למשיכת נתונים
@st.cache_data(ttl=300)
def get_all_data(symbol):
    try:
        df = yf.download(symbol, period="2y")
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
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

data = get_all_data(ticker)

if data is not None:
    # --- שורת מדדים עליונה ---
    curr_p = float(data['Close'].iloc[-1])
    st.markdown(f"### נתוני זמן אמת: {ticker} | מחיר נוכחי: **${curr_p:.2f}**")
    
    # --- לשוניות עבודה ---
    tab1, tab2, tab3 = st.tabs(["📊 גרף טכני ואינדיקטורים", "💰 מחשבון טרייד וביצועים", "🌍 מגמות עולם"])
    
    with tab1:
        col_ctrl, col_chart = st.columns([1, 4])
        with col_ctrl:
            st.write("🔧 **הגדרות גרף**")
            selected_ma = st.multiselect("ממוצעים נעים:", [9, 20, 50, 100, 150, 200], default=[50, 200])
            st.divider()
            st.write("**מדדי עוצמה:**")
            st.metric("RSI", f"{data['RSI'].iloc[-1]:.2f}")
            
        with col_chart:
            fig = go.Figure(data=[go.Candlestick(
                x=data.index, open=data['Open'], high=data['High'],
                low=data['Low'], close=data['Close'], name="מחיר"
            )])
            for m in selected_ma:
                fig.add_trace(go.Scatter(x=data.index, y=data[f'SMA{m}'], name=f"SMA {m}"))
            
            fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("MACD (מומנטום)")
            st.line_chart(data[['MACD', 'Signal']].tail(100))

    with tab2:
        st.subheader("📝 ניהול טרייד ספציפי")
        
        # כפתור איפוס
        if st.button("🗑️ נקה נתונים"):
            st.rerun()

        c1, c2, c3 = st.columns(3)
        buy_p = c1.number_input("שער קנייה ($)", min_value=0.0, step=0.01, key="buy")
        sell_p = c2.number_input("שער מכירה / יעד ($)", min_value=0.0, step=0.01, key="sell")
        qty = c3.number_input("כמות מניות", min_value=0, step=1, key="qty")
        
        if qty > 0:
            st.divider()
            # חישוב לפי שער המכירה אם הוזן, אחרת לפי מחיר נוכחי
            target_p = sell_p if sell_p > 0 else curr_p
            status_text = "רווח/הפסד (לפי שער מכירה)" if sell_p > 0 else "רווח/הפסד (רעיוני - טרייד פתוח)"
            
            profit_usd = (target_p - buy_p) * qty
            profit_ils = profit_usd * usd_rate
            profit_pct = ((target_p - buy_p) / buy_p * 100) if buy_p > 0 else 0
            
            st.markdown(f"#### {status_text}")
            res1, res2, res3 = st.columns(3)
            res1.metric("רווח/הפסד ($)", f"${profit_usd:,.2f}", f"{profit_pct:.2f}%")
            res2.metric("רווח/הפסד (₪)", f"₪{profit_ils:,.2f}")
            res3.metric("שווי פוזיציה", f"${(target_p * qty):,.2f}")

    with tab3:
        st.subheader("🌐 מגמות גלובליות")
        indices = {"S&P 500": "SPY", "נאסד"ק": "QQQ", "ביטקוין": "BTC-USD", "זהב": "GC=F"}
        compare_df = pd.DataFrame()
        for name, sym in indices.items():
            temp = yf.download(sym, period="1mo")['Close']
            if isinstance(temp, pd.DataFrame): temp = temp.iloc[:, 0]
            compare_df[name] = (temp / temp.iloc[0]) * 100
        st.line_chart(compare_df)

else:
    st.error("לא נמצאו נתונים. וודא שסימול המניה נכון.")
