import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.data import load_stock_data
from core.indicators import calculate_indicators, calculate_final_score, generate_explanations
from utils.export import to_excel
import uuid 

# === הגדרות עמוד ===
st.set_page_config(page_title="מערכת המסחר של ישראל", layout="wide", page_icon="🇮🇱")

# CSS לעיצוב נקי ויישור לימין
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    .stTextInput > div > div > input { text-align: center; direction: ltr; font-weight: bold; font-size: 20px; }
    div[data-testid="stMetricValue"] { text-align: center; }
    .big-score { font-size: 40px; font-weight: bold; text-align: center; display: block; }
    </style>
    """, unsafe_allow_html=True)

# === ניהול זיכרון (Session State) ===
if 'trades' not in st.session_state:
    st.session_state.trades = [] 

# === כותרת ===
st.markdown("<h1 style='text-align: center; color: #004085;'>🦅 מערכת המסחר המקצועית</h1>", unsafe_allow_html=True)

# === סרגל צדי - איפוס והגדרות ===
with st.sidebar:
    st.header("⚙️ ניהול מערכת")
    if st.button("🗑️ מחק נתונים ואפס מערכת", type="primary"):
        st.session_state.trades = []
        st.session_state.clear()
        st.rerun()
    st.info("אם נתקלת בשגיאה, לחץ על הכפתור למעלה לאיפוס.")

# === שורת חיפוש ממורכזת וקצרה ===
col_spacer1, col_search, col_spacer2 = st.columns([1, 2, 1])
with col_search:
    with st.form(key='search_form'):
        ticker_input = st.text_input("הקלד סימול (למשל TSLA) ולחץ Enter", placeholder="🔎 חיפוש מניה").upper()
        submit = st.form_submit_button("חפש", use_container_width=True)

# בחירת ממוצעים
ma_type = st.radio("", ["טווח קצר (סווינג מהיר)", "טווח ארוך (השקעה/מגמה)"], horizontal=True)

# === לוגיקה ראשית ===
if ticker_input:
    # 1. טעינת נתונים
    df, full_name, next_earnings, levels = load_stock_data(ticker_input)
    
    if df is not None and not df.empty:
        # 2. חישוב אינדיקטורים
        df, periods = calculate_indicators(df, ma_type)
        last_row = df.iloc[-1]
        score, recommendation, color = calculate_final_score(last_row, periods)
        
        # 3. כרטיס מידע ראשי
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("מחיר אחרון", f"${last_row['Close']:.2f}", f"{last_row['Close'] - df.iloc[-2]['Close']:.2f}")
        c2.markdown(f"<div style='color:{color}; text-align:center;'><h3>{recommendation}</h3><span class='big-score'>{score}/100</span></div>", unsafe_allow_html=True)
        c3.metric("דוחות הבאים", next_earnings)

        # 4. טאבים
        tab_chart, tab_info, tab_journal = st.tabs(["📊 גרף מתקדם", "🧠 ניתוח חכם", "📓 יומן מסחר"])

        # --- טאב גרף ---
        with tab_chart:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='מחיר'))
            for p in periods:
                fig.add_trace(go.Scatter(x=df.index, y=df[f'SMA_{p}'], name=f'SMA {p}', line=dict(width=1)))
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='gray', width=1, dash='dot'), name='B-Upper'))
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='gray', width=1, dash='dot'), fill='tonexty', name='B-Lower'))
            fig.update_layout(height=600, xaxis_rangeslider_visible=False, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        # --- טאב ניתוח ---
        with tab_info:
            explanations = generate_explanations(df, periods)
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                st.subheader("📋 הסבר איתותים")
                for exp in explanations:
                    st.info(exp)
            with col_exp2:
                st.subheader("🛡️ תמיכה והתנגדות")
                for lvl in levels:
                    st.write(f"• {lvl}")

        # --- טאב יומן מסחר ---
        with tab_journal:
            st.subheader("ניהול פוזיציות למניה זו")
            
            # טופס פתיחה
            with st.expander("➕ פתח עסקה חדשה", expanded=True):
                c_new1, c_new2, c_new3 = st.columns(3)
                buy_price = c_new1.number_input("מחיר קנייה", value=float(last_row['Close']), format="%.2f")
                qty = c_new2.number_input("כמות מניות", value=10, min_value=1)
                notes = c_new3.text_input("הערות")
                
                if st.button("בצע רכישה 💾"):
                    new_trade = {
                        "id": str(uuid.uuid4()),
                        "ticker": ticker_input,
                        "date_open": pd.Timestamp.now().strftime("%d/%m/%Y"),
                        "buy_price": buy_price,
                        "qty": qty,
                        "status": "פתוח 🟢",
                        "close_price": 0.0,
                        "profit": 0.0,
                        "notes": notes
                    }
                    st.session_state.trades.append(new_trade)
                    st.success("העסקה נרשמה!")
                    st.rerun()

            st.markdown("---")
            st.subheader("📜 העסקאות שלי")

            if not st.session_state.trades:
                st.info("עדיין אין עסקאות מתועדות.")
            else:
                # מחיקת טריידים פגומים (תיקון לשגיאה שלך)
                valid_trades = [t for t in st.session_state.trades if 'ticker' in t]
                if len(valid_trades) < len(st.session_state.trades):
                    st.session_state.trades = valid_trades
                    st.rerun()

                for i, trade in enumerate(st.session_state.trades):
                    with st.container():
                        c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 2, 2, 1, 1])
                        
                        # שימוש ב-get כדי למנוע קריסה
                        ticker_display = trade.get('ticker', 'Unknown')
                        date_display = trade.get('date_open', '-')
                        
                        c1.write(f"**{ticker_display}** ({date_display})")
                        c2.write(f"קנייה: ${trade.get('buy_price', 0)} ({trade.get('qty', 0)} יח')")
                        
                        status = trade.get('status', 'סגור 🔴')
                        
                        if status == "פתוח 🟢":
                            close_p = c3.number_input("יציאה", value=float(last_row['Close']), key=f"p_{i}")
                            if c4.button("סגור 💰", key=f"close_{i}"):
                                gross_pnl = (close_p - trade['buy_price']) * trade['qty']
                                net_pnl = gross_pnl - 12
                                st.session_state.trades[i]['status'] = "סגור 🔴"
                                st.session_state.trades[i]['close_price'] = close_p
                                st.session_state.trades[i]['profit'] = net_pnl
                                st.rerun()
                        else:
                            pnl = trade.get('profit', 0)
                            color_pnl = "green" if pnl > 0 else "red"
                            c3.markdown(f"נסגר ב: ${trade.get('close_price', 0)}")
                            c4.markdown(f"רווח: <span style='color:{color_pnl}'>${pnl:.2f}</span>", unsafe_allow_html=True)

                        if c6.button("🗑️", key=f"del_{i}"):
                            st.session_state.trades.pop(i)
                            st.rerun()
                        st.markdown("---")

    elif ticker_input:
        st.error("לא נמצאו נתונים. נסה סימול אחר.")
