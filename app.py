import streamlit as st
import pandas as pd
from streamlit_tradingview_chart import streamlit_tradingview_chart as st_tv
from core.data import load_stock_data
from core.indicators import calculate_all_indicators, get_smart_analysis, calculate_final_score, analyze_fundamentals
import uuid

# הגדרות דף ועיצוב רקע
st.set_page_config(page_title="מערכת מסחר מקצועית", layout="wide")

def add_bg_and_style():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.9)), 
                        url("https://images.unsplash.com/photo-1611974717482-589252c8465f?q=80&w=2070");
            background-size: cover;
        }}
        .main {{ direction: rtl; text-align: right; }}
        div.stButton > button:first-child {{ border-radius: 20px; }}
        </style>
        """,
        unsafe_allow_html=True
    )

add_bg_and_style()

if 'trades' not in st.session_state:
    st.session_state.trades = {}

st.title("📊 מערכת Micha Stocks - מהדורת פרימיום")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    ticker_input = st.text_input("הזן סימול מניה (AAPL, TSLA, MARA)", value="").upper()

if ticker_input:
    df, info, full_name = load_stock_data(ticker_input)
    
    if df is not None and not df.empty:
        st.markdown("---")
        ma_option = st.radio("סוג ניתוח מבוקש:", ["טווח קצר (סווינג)", "טווח ארוך (השקעה)"], horizontal=True)
        
        df, periods = calculate_all_indicators(df, ma_option)
        last_row = df.iloc[-1]
        score, rec_text, color = calculate_final_score(last_row, periods)
        
        st.markdown(f"<div style='background:{color}; padding:15px; border-radius:15px; text-align:center; color:white;'>"
                    f"<h2>{full_name} | ציון: {score}/100 - {rec_text}</h2></div>", unsafe_allow_html=True)

        tab_chart, tab_tech, tab_fund, tab_journal = st.tabs(["📈 גרף TradingView", "🧠 ניתוח טכני", "🏢 פונדמנטלי", "📓 יומן טריידים"])

        with tab_chart:
            st.subheader("גרף ניתוח טכני מתקדם")
            # הטמעת גרף TradingView אמיתי
            st_tv(symbol=f"NASDAQ:{ticker_input}" if "NASDAQ" in str(info.get('exchange')) else ticker_input,
                  height=500, autosize=True)
            
        with tab_tech:
            st.subheader("פרשנות אינדיקטורים")
            for msg in get_smart_analysis(df, periods):
                st.info(msg)

        with tab_fund:
            st.subheader("ניתוח בריאות החברה")
            for insight in analyze_fundamentals(info):
                st.success(insight)

        with tab_journal:
            st.subheader("ניהול עסקאות")
            # טופס הוספה
            with st.expander("➕ הוסף טרייד חדש"):
                c1, c2 = st.columns(2)
                p_in = c1.number_input("מחיר כניסה", value=float(last_row['Open']))
                q_in = c2.number_input("כמות מניות", value=1, min_value=1)
                if st.button("שמור פוזיציה"):
                    tid = str(uuid.uuid4())
                    st.session_state.trades[tid] = {"ticker": ticker_input, "price": p_in, "qty": q_in, "status": "פתוח", "pnl": 0}
                    st.rerun()

            st.markdown("---")
            for tid, t in list(st.session_state.trades.items()):
                with st.container():
                    r1, r2, r3, r4, r5 = st.columns([1, 2, 1, 1, 0.5])
                    r1.write(f"**{t['ticker']}**")
                    r2.write(f"כניסה: ${t['price']} | כמות: {t['qty']}")
                    
                    if t['status'] == "פתוח":
                        exit_p = r3.number_input("יציאה", key=f"ex_{tid}", label_visibility="collapsed", value=float(last_row['Close']))
                        if r4.button("מכור", key=f"s_{tid}"):
                            st.session_state.trades[tid]['status'] = "סגור"
                            st.session_state.trades[tid]['pnl'] = (exit_p - t['price']) * t['qty'] - 12
                            st.rerun()
                    else:
                        r3.write(f"רווח נקי: ${t['pnl']:.2f}")
                        r4.write("✅ סגור")
                    
                    # כפתור מחיקה (חדש)
                    if r5.button("🗑️", key=f"del_{tid}"):
                        del st.session_state.trades[tid]
                        st.rerun()
                st.divider()
    else:
        st.error(f"לא נמצאו נתונים עבור '{ticker_input}'.")
