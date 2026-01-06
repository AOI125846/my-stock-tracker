import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.data import load_stock_data
from core.indicators import rsi, macd, analyze_tech_signals
from utils.export import to_excel

st.set_page_config(page_title="מערכת מעקב מניות", layout="wide")

# אתחול יומן טריידים בזיכרון אם לא קיים
if 'trades' not in st.session_state:
    st.session_state.trades = []

st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    .stTabs [data-baseweb="tab-list"] { direction: rtl; }
    .signal-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-right: 5px solid #007bff; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 מערכת ניתוח ומעקב מניות")

# סרגל צדי
with st.sidebar:
    st.header("🔍 הגדרות")
    ticker_symbol = st.text_input("סימול מניה", "AAPL").upper()
    ma_choice = st.selectbox("בחר טווח ממוצעים נעים", ["טווח קצר (9, 20, 50)", "טווח ארוך (100, 150, 200)"])
    analyze_btn = st.button("בצע ניתוח")

if analyze_btn:
    with st.spinner('טוען נתונים...'):
        df, full_name, earnings, levels = load_stock_data(ticker_symbol)
    
    if not df.empty:
        st.subheader(f"📊 {full_name} ({ticker_symbol})")
        st.write(f"📅 דוחות קרובים: **{earnings}**")

        # חישובים
        df['RSI'] = rsi(df['Close'])
        df['MACD'], df['MACD_Signal'] = macd(df['Close'])
        ma_list = [9, 20, 50] if "קצר" in ma_choice else [100, 150, 200]
        for p in ma_list:
            df[f'SMA_{p}'] = df['Close'].rolling(p).mean()

        tab1, tab2, tab3 = st.tabs(["🚦 אינדיקטורים והסברים", "📈 גרף טכני", "📝 ניהול ויומן טריידים"])

        with tab1:
            st.markdown("### ניתוח טכני והסברי פעולה")
            signals = analyze_tech_signals(df, ma_list, levels)
            for s in signals:
                st.markdown(f"<div class='signal-box' style='margin-bottom:10px;'>{s}</div>", unsafe_allow_html=True)

        with tab2:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='מחיר'))
            for p in ma_list:
                fig.add_trace(go.Scatter(x=df.index, y=df[f'SMA_{p}'], name=f'SMA {p}', line=dict(width=1.5)))
            fig.update_layout(height=600, xaxis_rangeslider_visible=False, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.subheader("שמירת טרייד חדש")
            c1, c2, c3 = st.columns(3)
            entry_p = c1.number_input("מחיר כניסה", value=float(df['Close'].iloc[-1]))
            target_p = c2.number_input("מחיר יעד", value=entry_p * 1.1)
            stop_p = c3.number_input("סטופ לוס", value=entry_p * 0.95)
            
            if st.button("שמור טרייד ליומן"):
                new_trade = {"מניה": ticker_symbol, "כניסה": entry_p, "יעד": target_p, "סטופ": stop_p, "תאריך": pd.to_datetime("today").strftime('%d/%m/%Y')}
                st.session_state.trades.append(new_trade)
                st.success("הטרייד נשמר!")

            if st.session_state.trades:
                st.markdown("---")
                st.subheader("הטריידים שלי")
                st.table(pd.DataFrame(st.session_state.trades))
