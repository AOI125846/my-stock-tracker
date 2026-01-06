import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.data import load_stock_data
from core.indicators import calculate_indicators, calculate_final_score, generate_explanations
import uuid

st.set_page_config(page_title="מערכת המסחר המקצועית", layout="wide")

# עיצוב RTL
st.markdown("""<style>.main { direction: rtl; text-align: right; }</style>""", unsafe_allow_html=True)

if 'trades' not in st.session_state:
    st.session_state.trades = []

st.title("🦅 מערכת הניתוח המקצועית")

# חיפוש
col_spacer1, col_search, col_spacer2 = st.columns([1, 2, 1])
with col_search:
    with st.form(key='search_form'):
        ticker_input = st.text_input("סימול מניה", placeholder="למשל: AAPL").upper()
        submit = st.form_submit_button("נתח מניה")

ma_type = st.radio("טווח ממוצעים", ["קצר", "ארוך"], horizontal=True)

if ticker_input:
    df, full_name, next_earnings, levels = load_stock_data(ticker_input)
    
    if df is not None and not df.empty:
        df, periods = calculate_indicators(df, ma_type)
        last_row = df.iloc[-1]
        score, rec, color = calculate_final_score(last_row, periods)

        # תצוגת ציון
        st.markdown(f"<div style='text-align:center; background:{color}; padding:10px; border-radius:10px; color:white;'><h2>ציון: {score}/100 | {rec}</h2></div>", unsafe_allow_html=True)

        # יצירת הטאבים - חשוב שזה יהיה לפני השימוש בהם!
        tab_chart, tab_info, tab_journal = st.tabs(["📊 גרף", "🧠 פרשנות חכמה", "📓 יומן טריידים"])

        with tab_chart:
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(height=500, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        
        with tab_info:
            st.subheader("ניתוח אינדיקטורים מלא")
            col1, col2 = st.columns(2)
            with col1:
                exps = generate_explanations(df, periods)
                for e in exps: st.info(e)
            with col2:
                st.write(f"📅 דוחות קרובים: {next_earnings}")
                for l in levels: st.success(l)

        with tab_journal:
            # כאן מופיע קוד ניהול הטריידים והמחיקה (כפי שכתבנו קודם)
            st.write("ניהול פוזיציות ויומן מסחר...")
            # (המשך הקוד של ניהול הטריידים שכתבנו קודם)
