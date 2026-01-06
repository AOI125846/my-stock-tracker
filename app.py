import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.data import load_stock_data
from core.indicators import calculate_indicators, calculate_final_score, generate_explanations
import uuid # ליצירת מזהה ייחודי לכל טרייד

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
    st.session_state.trades = [] # רשימת הטריידים

# === כותרת ===
st.markdown("<h1 style='text-align: center; color: #004085;'>🦅 מערכת המסחר המקצועית</h1>", unsafe_allow_html=True)

# === שורת חיפוש ממורכזת וקצרה ===
col_spacer1, col_search, col_spacer2 = st.columns([1, 2, 1])
with col_search:
    with st.form(key='search_form'):
        ticker_input = st.text_input("הקלד סימול (למשל TSLA) ולחץ Enter", placeholder="🔎 חיפוש מניה").upper()
        # כפתור מוסתר כדי שהטופס יעבוד עם אנטר, אך לא יתפוס מקום ויזואלי מיותר
        submit = st.form_submit_button("חפש", use_container_width=True)

# בחירת ממוצעים (מופיע תמיד)
ma_type = st.radio("", ["טווח קצר (סווינג מהיר)", "טווח ארוך (השקעה/מגמה)"], horizontal=True)

# === לוגיקה ראשית ===
if ticker_input:
    # 1. טעינת נתונים
    df, full_name, next_earnings, levels = load_stock_data(ticker_input)
    
    if df is not None and not df.empty:
        # 2. חישוב אינדיקטורים וציונים
        df, periods = calculate_indicators(df, ma_type)
        last_row = df.iloc[-1]
        score, recommendation, color = calculate_final_score(last_row, periods)
        
        # 3. הצגת כרטיס מידע ראשי
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
            # נרות
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='מחיר'))
            # ממוצעים
            for p in periods:
                fig.add_trace(go.Scatter(x=df.index, y=df[f'SMA_{p}'], name=f'SMA {p}', line=dict(width=1)))
            # Bollinger Bands
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

        # --- טאב יומן מסחר (חדש ומשודרג!) ---
        with tab_journal:
            st.subheader("ניהול פוזיציות למניה זו")
            
            # טופס פתיחת עסקה חדשה
            with st.expander("➕ פתח עסקה חדשה", expanded=True):
                c_new1, c_new2, c_new3 = st.columns(3)
                buy_price = c_new1.number_input("מחיר קנייה", value=float(last_row['Close']), format="%.2f")
                qty = c_new2.number_input("כמות מניות", value=10, min_value=1)
                notes = c_new3.text_input("הערות (למה נכנסתי?)")
                
                if st.button("בצע רכישה והוסף ליומן 💾"):
                    new_trade = {
                        "id": str(uuid.uuid4()), # מזהה ייחודי
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
                # לולאה להצגת הטריידים עם אפשרות ניהול
                for i, trade in enumerate(st.session_state.trades):
                    # מציג רק טריידים ששייכים למניה הנוכחית או את כולם? נציג את כולם לנוחות
                    with st.container():
                        c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 2, 2, 1, 1])
                        c1.write(f"**{trade['ticker']}** ({trade['date_open']})")
                        c2.write(f"קנייה: ${trade['buy_price']} (כמות: {trade['qty']})")
                        
                        # חישוב רווח "על הנייר" אם פתוח
                        current_val = trade['qty'] * last_row['Close']
                        cost_val = trade['qty'] * trade['buy_price']
                        
                        if trade['status'] == "פתוח 🟢":
                            # כפתור סגירה
                            close_p = c3.number_input(f"מחיר יציאה", value=float(last_row['Close']), key=f"p_{trade['id']}")
                            if c4.button("סגור עסקה 💰", key=f"close_{trade['id']}"):
                                # חישוב: רווח גולמי פחות 12 דולר עמלות
                                gross_pnl = (close_p - trade['buy_price']) * trade['qty']
                                net_pnl = gross_pnl - 12 
                                
                                st.session_state.trades[i]['status'] = "סגור 🔴"
                                st.session_state.trades[i]['close_price'] = close_p
                                st.session_state.trades[i]['profit'] = net_pnl
                                st.rerun()
                        else:
                            # אם סגור
                            pnl = trade['profit']
                            color_pnl = "green" if pnl > 0 else "red"
                            c3.markdown(f"נסגר ב: ${trade['close_price']}")
                            c4.markdown(f"רווח נקי: <span style='color:{color_pnl}; font-weight:bold'>${pnl:.2f}</span> (כולל עמלות)", unsafe_allow_html=True)

                        # כפתור מחיקה
                        if c6.button("🗑️", key=f"del_{trade['id']}"):
                            st.session_state.trades.pop(i)
                            st.rerun()
                        
                        st.markdown("---")

    elif ticker_input:
        st.error("לא נמצאו נתונים. נסה סימול אחר.")
