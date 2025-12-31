import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

# --- הגדרות מערכת ועיצוב ---
st.set_page_config(page_title="מערכת מסחר מקצועית", layout="wide", initial_sidebar_state="collapsed")

# הזרקת CSS לעיצוב יוקרתי ומקצועי בעברית (RTL)
st.markdown("""
    <style>
    /* הגדרת כיוון טקסט מימין לשמאל */
    .stApp {
        direction: rtl;
        text-align: right;
        background: linear-gradient(to bottom right, #0e1117, #1c2025);
        color: #e0e0e0;
    }
    /* כרטיסיות נתונים */
    div[data-testid="stMetricValue"] {
        font-size: 20px;
        color: #00d4ff;
    }
    div[data-testid="stMetricLabel"] {
        direction: rtl;
        text-align: right;
    }
    /* התאמת כותרות */
    h1, h2, h3, p, span, div {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans_serif;
    }
    /* כפתורים */
    .stButton>button {
        background-color: #238636;
        color: white;
        border: none;
        border-radius: 4px;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #2ea043;
    }
    </style>
    """, unsafe_allow_html=True)

# --- פונקציות ליבה ---

# 1. ניהול יומן מסחר (CSV) עם תמיכה בעברית
JOURNAL_FILE = "trading_journal.csv"

def load_journal():
    if not os.path.exists(JOURNAL_FILE):
        df = pd.DataFrame(columns=["תאריך", "סימול", "קנייה ($)", "מכירה ($)", "כמות", "רווח ($)", "רווח (₪)", "תשואה (%)"])
        df.to_csv(JOURNAL_FILE, index=False, encoding='utf-8-sig')
        return df
    return pd.read_csv(JOURNAL_FILE, encoding='utf-8-sig')

def save_trade(date, symbol, buy, sell, qty, usd_rate):
    profit_usd = (sell - buy) * qty
    profit_ils = profit_usd * usd_rate
    profit_pct = ((sell - buy) / buy) * 100 if buy > 0 else 0
    
    new_row = pd.DataFrame([{
        "תאריך": date,
        "סימול": symbol,
        "קנייה ($)": round(buy, 2),
        "מכירה ($)": round(sell, 2),
        "כמות": qty,
        "רווח ($)": round(profit_usd, 2),
        "רווח (₪)": round(profit_ils, 2),
        "תשואה (%)": f"{profit_pct:.2f}%"
    }])
    
    df = load_journal()
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(JOURNAL_FILE, index=False, encoding='utf-8-sig')
    return df

# 2. משיכת שער דולר
@st.cache_data(ttl=3600)
def get_usd_rate():
    try:
        ticker = yf.Ticker("ILS=X")
        return ticker.history(period="1d")['Close'].iloc[-1]
    except:
        return 3.65

# 3. ניתוח טכני (כאן היה התיקון החשוב)
def analyze_stock(symbol):
    try:
        df = yf.download(symbol, period="2y", interval="1d")
        if df.empty: return None, 0, "לא נמצאו נתונים"
        
        # תיקון המבנה של yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # חישוב אינדיקטורים
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()
        
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

        # חישוב ציון טכני
        score = 50
        last = df.iloc[-1]
        
        if last['Close'] > last['SMA200']: score += 20
        if last['SMA50'] > last['SMA200']: score += 10
        if last['MACD'] > last['Signal']: score += 10
        if 30 < last['RSI'] < 70: score += 10
        if last['RSI'] > 70 or last['RSI'] < 30: score -= 10
        
        score = max(0, min(100, score))
        
        # התיקון: החזרת 3 משתנים תמיד
        return df, score, None
        
    except Exception as e:
        return None, 0, str(e)

# --- ממשק משתמש (UI) ---

st.markdown("<h1 style='text-align: center; color: #d4af37;'>מערכת מסחר מקצועית - Pro Terminal</h1>", unsafe_allow_html=True)

# שורת מדדים עליונה
usd_val = get_usd_rate()
indices = {"S&P 500": "SPY", "נאסד\"ק": "QQQ", "זהב": "GC=F", "ביטקוין": "BTC-USD"}
cols = st.columns(len(indices) + 1)

# כרטיס שער דולר
cols[len(indices)].metric("שער הדולר", f"₪{usd_val:.3f}")

# כרטיסי מדדים
for i, (name, sym) in enumerate(indices.items()):
    try:
        d = yf.Ticker(sym).history(period="2d")
        if not d.empty:
            curr = d['Close'].iloc[-1]
            prev = d['Close'].iloc[-2]
            delta = ((curr - prev)/prev)*100
            cols[i].metric(name, f"{curr:,.2f}", f"{delta:.2f}%")
    except:
        cols[i].metric(name, "טוען...", "0%")

st.divider()

# תיבת חיפוש
col_search, col_space = st.columns([1, 2])
with col_search:
    ticker = st.text_input("הכנס סימול מניה (למשל NVDA):", "NVDA").upper()

# הפעלת הניתוח
df, score, err = analyze_stock(ticker)

if err:
    st.error(f"שגיאה בטעינת הנתונים: {err}")
elif df is not None:
    # לשוניות
    tab_chart, tab_journal, tab_info = st.tabs(["📈 גרף מסחר", "📓 יומן עסקאות", "ℹ️ מידע ודירוג"])

    # --- לשונית 1: גרף ---
    with tab_chart:
        c_score1, c_score2 = st.columns([1, 4])
        with c_score1:
             st.markdown(f"### דירוג טכני: **{score}/100**")
        with c_score2:
             st.progress(score)

        # יצירת גרף משולב
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.03, row_heights=[0.7, 0.3],
                            subplot_titles=("מחיר", "מומנטום (MACD)"))

        # נרות יפניים
        fig.add_trace(go.Candlestick(x=df.index,
                                     open=df['Open'], high=df['High'],
                                     low=df['Low'], close=df['Close'],
                                     name="נרות"), row=1, col=1)

        # בחירת ממוצעים
        st.markdown("##### הגדרות תצוגה")
        show_smas = st.multiselect("בחר ממוצעים להצגה:", [50, 200], default=[50, 200])
        colors = {50: '#ffa500', 200: '#00d4ff'} # כתום וכחול בוהק
        
        for ma in show_smas:
            fig.add_trace(go.Scatter(x=df.index, y=df[f'SMA{ma}'], 
                                     line=dict(color=colors.get(ma, 'white'), width=1.5), 
                                     name=f"ממוצע {ma}"), row=1, col=1)

        # אינדיקטורים למטה
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='#00ff00', width=1), name="MACD"), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], line=dict(color='#ff0000', width=1), name="Signal"), row=2, col=1)

        # הגדרות עיצוב גרף מקצועי
        fig.update_layout(
            height=650,
            template="plotly_dark",
            showlegend=True,
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=30, b=10),
            dragmode='pan',  # ברירת מחדל גרירה
            hovermode='x unified' # תצוגת רחף נוחה
        )
        
        # אפשור זום וגלילה
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
        st.caption("💡 טיפ: השתמש בגלגלת העכבר לזום פנימה/החוצה, וגרור את הגרף כדי לזוז בזמן.")

    # --- לשונית 2: יומן מסחר ---
    with tab_journal:
        st.subheader("תיעוד טריידים")
        
        with st.form("trade_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            buy_price = c1.number_input("שער כניסה ($)", min_value=0.0, step=0.1)
            sell_price = c2.number_input("שער יציאה ($)", min_value=0.0, step=0.1)
            quantity = c3.number_input("כמות יחידות", min_value=1, step=1)
            trade_date = c4.date_input("תאריך הטרייד")
            
            submitted = st.form_submit_button("💾 שמור ביומן")
            
            if submitted:
                if buy_price > 0 and quantity > 0:
                    save_trade(trade_date, ticker, buy_price, sell_price, quantity, usd_val)
                    st.success("הטרייד נשמר בהצלחה!")
                    st.rerun() # רענון כדי לראות את הטבלה מתעדכנת
                else:
                    st.error("נא להזין נתונים תקינים")

        st.divider()
        
        journal_df = load_journal()
        if not journal_df.empty:
            st.markdown("### היסטוריית ביצועים")
            st.dataframe(journal_df, use_container_width=True)
            
            total_profit = journal_df['רווח (₪)'].sum()
            color = "#00ff00" if total_profit >= 0 else "#ff0000"
            st.markdown(f"<h3 style='text-align: center;'>רווח כולל: <span style='color:{color}'>₪{total_profit:,.2f}</span></h3>", unsafe_allow_html=True)
        else:
            st.info("אין עדיין טריידים מתועדים.")

    # --- לשונית 3: מידע ---
    with tab_info:
        last_close = df['Close'].iloc[-1]
        c_inf1, c_inf2 = st.columns(2)
        
        c_inf1.write(f"**מחיר אחרון:** ${last_close:.2f}")
        c_inf1.write(f"**נמוך שנתי:** ${df['Low'].min():.2f}")
        c_inf1.write(f"**גבוה שנתי:** ${df['High'].max():.2f}")
        
        # פרשנות ציון בעברית
        st.write("---")
        st.write("### ניתוח אוטומטי")
        if score > 80:
            st.success("📈 דירוג: קנייה חזקה (Strong Buy) - המניה במומנטום חיובי חזק.")
        elif score > 60:
            st.info("↗️ דירוג: חיובי (Buy) - המניה במגמת עלייה.")
        elif score < 40:
            st.error("📉 דירוג: שלילי (Sell) - המניה מתחת לממוצעים, מסוכן לקנות.")
        else:
            st.warning("➡️ דירוג: ניטרלי (Hold) - אין כיוון ברור.")

else:
    st.info("אנא המתן לטעינת הנתונים...")
