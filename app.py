import streamlit as st
import pandas as pd
import io
from streamlit_tradingview_chart import streamlit_tradingview_chart as st_tv
from core.data import load_stock_data
from core.indicators import calculate_all_indicators, get_smart_analysis, calculate_final_score, analyze_fundamentals
import uuid

# הגדרות דף ועיצוב
st.set_page_config(page_title="מערכת מסחר Micha Stocks", layout="wide")

def add_bg_and_style():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.9)), 
                        url("https://images.unsplash.com/photo-1611974717482-589252c8465f?q=80&w=2070");
            background-size: cover;
        }
        .main { direction: rtl; text-align: right; }
        /* מניעת קפיצות של אלמנטים */
        .block-container { padding-top: 2rem; }
        </style>
        """,
        unsafe_allow_html=True
    )

add_bg_and_style()

# פונקציה לייצוא לאקסל
def to_excel(trades_dict):
    if not trades_dict:
        return None
    # המרה למבנה טבלאי נקי לייצוא
    export_list = []
    for tid, data in trades_dict.items():
        export_list.append(data)
    df_export = pd.DataFrame(export_list)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Trades')
    return output.getvalue()

# אתחול ה-Session State בצורה בטוחה
if 'trades' not in st.session_state:
    st.session_state.trades = {}

st.title("📊 מערכת Micha Stocks - פרימיום")

# תיבת חיפוש מרכזית
col_search = st.columns([1, 2, 1])[1]
with col_search:
    ticker_input = st.text_input("הזן סימול מניה (למשל MARA)", value="", key="main_ticker").upper()

if ticker_input:
    df, info, full_name = load_stock_data(ticker_input)
    
    if df is not None and not df.empty:
        st.markdown("---")
        
        # בחירת טווח ניתוח
        ma_option = st.radio("בחר טווח ניתוח:", ["טווח קצר (סווינג)", "טווח ארוך (השקעה)"], horizontal=True)
        
        # חישובים
        df, periods = calculate_all_indicators(df, ma_option)
        last_row = df.iloc[-1]
        score, rec_text, color = calculate_final_score(last_row, periods)
        
        # תצוגת ציון מרכזית
        st.markdown(f"""
            <div style='background:{color}; padding:15px; border-radius:15px; text-align:center; color:white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h2 style='margin:0;'>{full_name} ({ticker_input})</h2>
                <h3 style='margin:0;'>ציון: {score}/100 - {rec_text}</h3>
            </div>
        """, unsafe_allow_html=True)

        # טאבים לממשק
        tab_chart, tab_tech, tab_fund, tab_journal = st.tabs(["📈 גרף מתקדם", "🧠 ניתוח טכני", "🏢 פונדמנטלי", "📓 יומן טריידים"])

        with tab_chart:
            # שימוש ב-container כדי למנוע את שגיאת ה-removeChild
            chart_container = st.container()
            with chart_container:
                st.subheader("TradingView Real-time Chart")
                try:
                    st_tv(symbol=ticker_input, height=550)
                except:
                    st.error("טעינת הגרף נכשלה. נסה לרענן את הדף.")

        with tab_tech:
            st.subheader("תובנות אלגוריתמיות")
            analysis = get_smart_analysis(df, periods)
            for msg in analysis:
                st.info(msg)

        with tab_fund:
            st.subheader("נתונים פיננסיים")
            insights = analyze_fundamentals(info)
            for insight in insights:
                st.success(insight)

        with tab_journal:
            st.subheader("ניהול עסקאות")
            
            # כפתור ייצוא
            if st.session_state.trades:
                excel_data = to_excel(st.session_state.trades)
                if excel_data:
                    st.download_button(
                        label="📥 הורד יומן טריידים (Excel)",
                        data=excel_data,
                        file_name=f"trades_{ticker_input}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            # הוספת טרייד
            with st.expander("➕ רשום טרייד חדש"):
                c1, c2 = st.columns(2)
                p_in = c1.number_input("מחיר כניסה", value=float(last_row['Close']), key="p_in")
                q_in = c2.number_input("כמות", value=1, min_value=1, key="q_in")
                if st.button("שמור במערכת"):
                    tid = str(uuid.uuid4())
                    st.session_state.trades[tid] = {
                        "Ticker": ticker_input, 
                        "Price": p_in, 
                        "Qty": q_in, 
                        "Status": "פתוח", 
                        "PnL": 0.0
                    }
                    st.rerun()

            st.markdown("---")
            # הצגת טריידים קיימים
            for tid, t in list(st.session_state.trades.items()):
                with st.container():
                    r1, r2, r3, r4, r5 = st.columns([1, 2, 1, 1, 0.5])
                    r1.write(f"**{t['Ticker']}**")
                    r2.write(f"מחיר: {t['Price']} | כמות: {t['Qty']}")
                    
                    if t['Status'] == "פתוח":
                        exit_p = r3.number_input("מחיר מכירה", key=f"ex_{tid}", label_visibility="collapsed", value=float(last_row['Close']))
                        if r4.button("בצע מכירה", key=f"btn_s_{tid}"):
                            st.session_state.trades[tid]['Status'] = "סגור"
                            st.session_state.trades[tid]['PnL'] = (exit_p - t['Price']) * t['Qty'] - 12
                            st.rerun()
                    else:
                        color_pnl = "green" if t['PnL'] > 0 else "red"
                        r3.markdown(f"רווח: <span style='color:{color_pnl}'>${t['PnL']:.2f}</span>", unsafe_allow_html=True)
                        r4.write("✅ עסקה סגורה")
                    
                    if r5.button("🗑️", key=f"btn_d_{tid}"):
                        del st.session_state.trades[tid]
                        st.rerun()
                st.divider()
    else:
        st.warning(f"לא הצלחנו למצוא נתונים עבור {ticker_input}. וודא שהסימול נכון (למשל TSLA).")
