import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.data import load_stock_data
from core.indicators import calculate_all_indicators, get_smart_analysis, calculate_final_score
import uuid

st.set_page_config(page_title="מערכת מסחר ישראל", layout="wide")

# אתחול יומן טריידים
if 'trades' not in st.session_state:
    st.session_state.trades = {}

st.title("🦅 מערכת הניתוח המקצועית")

# חיפוש מניה
col_search_1, col_search_2, col_search_3 = st.columns([1, 1, 1])
with col_search_2:
    ticker = st.text_input("הזן סימול מניה (למשל NVDA)", value="").upper()

ma_option = st.radio("בחר טווח ממוצעים:", ["קצר (9,20,50)", "ארוך (100,150,200)"], horizontal=True)
ma_type = "קצר" if "קצר" in ma_option else "ארוך"

if ticker:
    df, full_name, earnings, levels = load_stock_data(ticker)
    
    if df is not None and not df.empty:
        df, periods = calculate_all_indicators(df, ma_type)
        last_price = df['Close'].iloc[-1]

        # יצירת לשוניות
        tab_chart, tab_analysis, tab_journal = st.tabs(["📈 גרף נקי", "🧠 פרשנות חכמה", "📓 יומן טריידים"])

        with tab_chart:
            # גרף עם נרות וממוצעים בלבד
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="מחיר")])
            for p in periods:
                fig.add_trace(go.Scatter(x=df.index, y=df[f'SMA_{p}'], name=f'ממוצע {p}', line=dict(width=1.5)))
            fig.update_layout(height=600, template="plotly_white", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        
        with tab_analysis:
            st.subheader(f"ניתוח טכני עבור {full_name}")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("### 📋 איתותים פעילים")
                signals = get_smart_analysis(df, periods)
                for s in signals: st.info(s)
            with col_b:
                st.markdown("### 🛡️ רמות ומגמה")
                st.write(f"תאריך דוחות: {earnings}")
                for lvl in levels: st.success(lvl)

        with tab_journal:
            st.subheader("ניהול עסקאות")
            
            # הוספת טרייד
            with st.expander("➕ הוסף טרייד חדש"):
                c1, c2, c3 = st.columns(3)
                in_p = c1.number_input("מחיר כניסה", value=float(last_price))
                qty = c2.number_input("כמות", value=10)
                if st.button("שמור טרייד"):
                    t_id = str(uuid.uuid4())
                    st.session_state.trades[t_id] = {
                        "ticker": ticker, "price": in_p, "qty": qty, "status": "פתוח", "pnl": 0.0
                    }
                    st.rerun()

            # הצגת טריידים
            for t_id, t_data in list(st.session_state.trades.items()):
                with st.container():
                    col_t1, col_t2, col_t3, col_t4 = st.columns([2,2,2,1])
                    col_t1.write(f"**{t_data['ticker']}** | כמות: {t_data['qty']}")
                    col_t2.write(f"כניסה: ${t_data['price']}")
                    
                    if t_data['status'] == "פתוח":
                        exit_p = col_t3.number_input("מחיר יציאה", value=float(last_price), key=f"exit_{t_id}")
                        if col_t4.button("מכור", key=f"sell_{t_id}"):
                            # חישוב: (יציאה-כניסה)*כמות פחות 12$ עמלה
                            profit = ((exit_p - t_data['price']) * t_data['qty']) - 12
                            st.session_state.trades[t_id]['status'] = "סגור"
                            st.session_state.trades[t_id]['pnl'] = profit
                            st.rerun()
                    else:
                        color = "green" if t_data['pnl'] > 0 else "red"
                        col_t3.markdown(f"<b style='color:{color}'>רווח נקי: ${t_data['pnl']:.2f}</b>", unsafe_allow_html=True)
                        if col_t4.button("מחק", key=f"del_{t_id}"):
                            del st.session_state.trades[t_id]
                            st.rerun()
                    st.divider()

    elif ticker:
        st.error("לא נמצאו נתונים עבור הסימול שהזנת.")
