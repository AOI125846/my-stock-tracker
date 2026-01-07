import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.data import load_stock_data
from core.indicators import calculate_all_indicators, get_smart_analysis, calculate_final_score, analyze_fundamentals
import uuid

st.set_page_config(page_title="מערכת מסחר ישראל", layout="wide")
st.markdown("""<style>.main { direction: rtl; text-align: right; }</style>""", unsafe_allow_html=True)

# אתחול יומן טריידים
if 'trades' not in st.session_state:
    st.session_state.trades = {}

st.title("🦅 מערכת הניתוח המקצועית")

# --- שלב 1: חיפוש מניה ---
col_search_1, col_search_2, col_search_3 = st.columns([1, 2, 1])
with col_search_2:
    ticker = st.text_input("הזן סימול מניה (למשל GOOGL)", value="").upper()

# --- בדיקה אם הוזן סימול ---
if ticker:
    # טעינת נתונים
    df, info, full_name = load_stock_data(ticker)
    
    # --- בדיקה אם הנתונים תקינים ---
    if df is None or df.empty:
        st.error(f"❌ לא נמצאו נתונים עבור הסימול '{ticker}'. אנא בדוק את האיות או נסה סימול אחר.")
    else:
        # --- שלב 2: הגדרות ניתוח (מופיע רק אחרי טעינה תקינה) ---
        st.markdown("---")
        c_opt1, c_opt2 = st.columns([1, 3])
        with c_opt1:
            ma_option = st.radio("בחר סוג ניתוח:", ["טווח קצר (סווינג)", "טווח ארוך (השקעה)"], horizontal=False)
        
        # חישובים טכניים
        df, periods = calculate_all_indicators(df, ma_option)
        last_row = df.iloc[-1]
        
        # חישוב ציון
        score, rec_text, color = calculate_final_score(last_row, periods)
        
        # כותרת ראשית עם שם החברה והמחיר
        st.markdown(f"<h2 style='text-align:center;'>{full_name} ({ticker}) - ${last_row['Close']:.2f}</h2>", unsafe_allow_html=True)
        
        # תצוגת הציון
        st.markdown(f"""
        <div style="background-color:{color}; padding:15px; border-radius:10px; text-align:center; color:white; margin-bottom:20px;">
            <h3 style="margin:0;">{rec_text} (ציון: {score})</h3>
        </div>
        """, unsafe_allow_html=True)

        # --- יצירת הטאבים (כולל הטאב החדש) ---
        tab_chart, tab_tech, tab_fund, tab_journal = st.tabs(["📈 גרף נקי", "🧠 ניתוח טכני", "🏢 ניתוח פנדמנטלי", "📓 יומן טריידים"])

        # 1. טאב גרף
        with tab_chart:
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="מחיר")])
            colors = ['#FFA500', '#0000FF', '#800080']
            for i, p in enumerate(periods):
                fig.add_trace(go.Scatter(x=df.index, y=df[f'SMA_{p}'], name=f'ממוצע {p}', line=dict(color=colors[i], width=1.5)))
            fig.update_layout(height=600, template="plotly_white", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        

        # 2. טאב טכני
        with tab_tech:
            st.subheader("פרשנות האינדיקטורים הטכניים")
            tech_analysis = get_smart_analysis(df, periods)
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                for item in tech_analysis:
                    st.info(item)
            with col_t2:
                st.write("כאן מוצג ניתוח המבוסס על תבניות המחיר (RSI, MACD, בולינגר). השתמש בזה לתזמון הכניסה והיציאה.")

        # 3. טאב פנדמנטלי (חדש!)
        with tab_fund:
            st.subheader("📊 ניתוח דוחות ונתונים פיננסיים")
            if info:
                fund_insights = analyze_fundamentals(info)
                
                # הצגת נתוני מפתח בקוביות
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("שווי שוק", f"${info.get('marketCap', 0)/1e9:.1f}B")
                m2.metric("מכפיל רווח (PE)", f"{info.get('forwardPE', 'N/A')}")
                m3.metric("תשואת דיבידנד", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "0%")
                m4.metric("מחיר יעד (אנליסטים)", f"${info.get('targetMeanPrice', 'N/A')}")
                
                st.markdown("---")
                st.markdown("### 💡 מה זה אומר עבורך?")
                if not fund_insights:
                    st.warning("אין מספיק נתונים פונדמנטליים לניתוח אוטומטי.")
                else:
                    for insight in fund_insights:
                        st.success(insight)
                    
                st.markdown("""
                > **הסבר לסוחר:** הניתוח הפנדמנטלי בודק את ה"בריאות" של העסק עצמו, ולא רק את הגרף. 
                > אם החברה רווחית והמכפיל נמוך - היא עשויה להיות השקעה טובה לטווח ארוך, גם אם הגרף יורד כרגע.
                """)
            else:
                st.warning("לא התקבל מידע פונדמנטלי מהשרת.")

        # 4. טאב יומן טריידים
        with tab_journal:
            st.subheader("ניהול תיק מסחר")
            with st.expander("➕ הוסף פוזיציה חדשה"):
                c1, c2 = st.columns(2)
                p_in = c1.number_input("מחיר", value=float(last_row['Close']))
                q_in = c2.number_input("כמות", value=10)
                if st.button("שמור"):
                    st.session_state.trades[str(uuid.uuid4())] = {
                        "ticker": ticker, "date": pd.Timestamp.now().strftime("%d/%m"), 
                        "price": p_in, "qty": q_in, "status": "פתוח", "pnl": 0
                    }
                    st.rerun()
            
            # רשימת טריידים
            if st.session_state.trades:
                for t_id, t in list(st.session_state.trades.items()):
                    with st.container():
                        cc1, cc2, cc3, cc4 = st.columns([2, 2, 1, 1])
                        cc1.write(f"**{t['ticker']}** ({t['date']})")
                        cc2.write(f"קנייה: ${t['price']} (כמות: {t['qty']})")
                        if t['status'] == "פתוח":
                            exit_p = cc3.number_input("יציאה", key=f"x{t_id}", label_visibility="collapsed")
                            if cc4.button("מכור", key=f"s{t_id}"):
                                st.session_state.trades[t_id]['status'] = "סגור"
                                st.session_state.trades[t_id]['pnl'] = (exit_p - t['price']) * t['qty'] - 12
                                st.rerun()
                        else:
                            color = "green" if t['pnl'] > 0 else "red"
                            cc3.markdown(f"רווח: <b style='color:{color}'>${t['pnl']:.2f}</b>", unsafe_allow_html=True)
                            if cc4.button("מחק", key=f"d{t_id}"):
                                del st.session_state.trades[t_id]
                                st.rerun()
                        st.divider()

# סרגל צד לאיפוס
with st.sidebar:
    if st.button("אפס מערכת"):
        st.session_state.clear()
        st.rerun()
