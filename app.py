import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.data import load_stock_data
from core.indicators import calculate_all_indicators, get_smart_analysis, calculate_final_score
import uuid

st.set_page_config(page_title="מערכת מסחר ישראל", layout="wide")

# CSS ליישור לימין
st.markdown("""<style>.main { direction: rtl; text-align: right; }</style>""", unsafe_allow_html=True)

# אתחול יומן טריידים כמילון (יותר יציב מרשימה)
if 'trades' not in st.session_state:
    st.session_state.trades = {}

st.title("🦅 מערכת הניתוח המקצועית")

# כפתור איפוס חירום (למקרה של תקלות בזיכרון)
with st.sidebar:
    st.header("ניהול")
    if st.button("אפס מערכת ומחק נתונים"):
        st.session_state.trades = {}
        st.session_state.clear()
        st.rerun()

# אזור חיפוש
col_search_1, col_search_2, col_search_3 = st.columns([1, 2, 1])
with col_search_2:
    ticker = st.text_input("הזן סימול מניה (למשל TSLA)", value="").upper()

ma_option = st.radio("בחר סוג ניתוח:", ["טווח קצר (9,20,50)", "טווח ארוך (100,150,200)"], horizontal=True)

if ticker:
    # טעינת נתונים
    df, full_name, earnings, levels = load_stock_data(ticker)
    
    if df is not None and not df.empty:
        # חישובים
        df, periods = calculate_all_indicators(df, ma_option)
        last_row = df.iloc[-1]
        last_price = last_row['Close']
        
        # חישוב ציון סופי
        score, rec_text, color = calculate_final_score(last_row, periods)

        # תצוגה ראשית - ציון
        st.markdown(f"""
        <div style="background-color:{color}; padding:15px; border-radius:10px; text-align:center; color:white; margin-bottom:20px;">
            <h1 style="margin:0;">{rec_text}</h1>
            <h3 style="margin:0;">ציון משוקלל: {score}/100</h3>
            <p style="margin:0;">מחיר אחרון: ${last_price:.2f}</p>
        </div>
        """, unsafe_allow_html=True)

        # לשוניות
        tab_chart, tab_analysis, tab_journal = st.tabs(["📈 גרף נקי", "🧠 פרשנות חכמה", "📓 יומן טריידים"])

        # --- טאב 1: גרף נקי ---
        with tab_chart:
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="מחיר")])
            # הוספת ממוצעים נעים בלבד
            colors = ['#FFA500', '#0000FF', '#800080'] # כתום, כחול, סגול
            for i, p in enumerate(periods):
                fig.add_trace(go.Scatter(x=df.index, y=df[f'SMA_{p}'], name=f'ממוצע {p}', line=dict(color=colors[i], width=1.5)))
            
            fig.update_layout(height=600, template="plotly_white", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        
        # --- טאב 2: פרשנות חכמה ---
        with tab_analysis:
            st.subheader("ניתוח עומק")
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("### 🤖 מה האלגוריתם אומר?")
                analysis_lines = get_smart_analysis(df, periods)
                for line in analysis_lines:
                    st.info(line)
            
            with c2:
                st.markdown("### 📅 נתונים נוספים")
                st.write(f"**דוחות קרובים:** {earnings}")
                st.markdown("---")
                st.write("**רמות מפתח:**")
                for lvl in levels:
                    st.success(lvl)

        # --- טאב 3: יומן טריידים ---
        with tab_journal:
            st.subheader("ניהול תיק מסחר")
            
            # טופס הוספה
            with st.expander("➕ הוסף פוזיציה חדשה", expanded=False):
                c_in1, c_in2, c_in3 = st.columns(3)
                in_price = c_in1.number_input("מחיר כניסה", value=float(last_price))
                in_qty = c_in2.number_input("כמות", value=10, min_value=1)
                
                if st.button("שמור טרייד 💾"):
                    new_id = str(uuid.uuid4())
                    st.session_state.trades[new_id] = {
                        "ticker": ticker,
                        "date": pd.Timestamp.now().strftime("%d/%m %H:%M"),
                        "price": in_price,
                        "qty": in_qty,
                        "status": "פתוח",
                        "pnl": 0.0
                    }
                    st.success("הטרייד נשמר!")
                    st.rerun()

            st.markdown("---")
            
            # הצגת הטריידים
            if not st.session_state.trades:
                st.info("אין טריידים פתוחים כרגע.")
            else:
                # המרת המילון לרשימה כדי לעבור עליה
                all_trades = list(st.session_state.trades.items())
                
                for t_id, t_data in all_trades:
                    # מסגרת לכל טרייד
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([1.5, 1.5, 1.5, 1, 0.5])
                        
                        # פרטי טרייד
                        col1.write(f"**{t_data['ticker']}**")
                        col1.caption(t_data['date'])
                        
                        col2.write(f"כניסה: ${t_data['price']}")
                        col2.write(f"כמות: {t_data['qty']}")
                        
                        # סטטוס ופעולות
                        if t_data['status'] == "פתוח":
                            col3.markdown("🟢 **פתוח**")
                            # פעולת מכירה
                            exit_val = col4.number_input("מחיר יציאה", value=float(last_price), key=f"ex_{t_id}", label_visibility="collapsed")
                            if col4.button("מכור", key=f"btn_sell_{t_id}"):
                                # חישוב: רווח גולמי פחות 12 דולר עמלה
                                raw_pnl = (exit_val - t_data['price']) * t_data['qty']
                                net_pnl = raw_pnl - 12
                                
                                st.session_state.trades[t_id]['status'] = "סגור"
                                st.session_state.trades[t_id]['pnl'] = net_pnl
                                st.rerun()
                        else:
                            # אם סגור
                            pnl = t_data['pnl']
                            color_pnl = "green" if pnl > 0 else "red"
                            col3.markdown("🔴 **סגור**")
                            col3.markdown(f"רווח נקי: <span style='color:{color_pnl}'>${pnl:.2f}</span>", unsafe_allow_html=True)

                        # מחיקה
                        if col5.button("🗑️", key=f"del_{t_id}"):
                            del st.session_state.trades[t_id]
                            st.rerun()
                        
                        st.divider()

    elif ticker:
        st.error("לא נמצאו נתונים. נסה סימול אחר.")
