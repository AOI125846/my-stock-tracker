import streamlit as st
import pandas as pd
import io
from streamlit_tradingview_chart import streamlit_tradingview_chart as st_tv
from core.data import load_stock_data
from core.indicators import calculate_all_indicators, get_smart_analysis, calculate_final_score, analyze_fundamentals
import uuid

# הגדרות דף ועיצוב
st.set_page_config(page_title="מערכת מסחר מקצועית", layout="wide")

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
        </style>
        """,
        unsafe_allow_html=True
    )

add_bg_and_style()

# פונקציה לייצוא לאקסל
def to_excel(trades_dict):
    if not trades_dict:
        return None
    df_export = pd.DataFrame.from_dict(trades_dict, orient='index')
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Trades')
    return output.getvalue()

if 'trades' not in st.session_state:
    st.session_state.trades = {}

st.title("📊 מערכת Micha Stocks - פרימיום")

col_search = st.columns([1, 2, 1])[1]
with col_search:
    ticker_input = st.text_input("הזן סימול מניה (למשל MARA)", value="").upper()

if ticker_input:
    df, info, full_name = load_stock_data(ticker_input)
    
    if df is not None and not df.empty:
        st.markdown("---")
        ma_option = st.radio("בחר טווח ניתוח:", ["טווח קצר (סווינג)", "טווח ארוך (השקעה)"], horizontal=True)
        
        df, periods = calculate_all_indicators(df, ma_option)
        last_row = df.iloc[-1]
        score, rec_text, color = calculate_final_score(last_row, periods)
        
        st.markdown(f"<div style='background:{color}; padding:15px; border-radius:15px; text-align:center; color:white;'>"
                    f"<h2>{full_name} | ציון: {score}/100 - {rec_text}</h2></div>", unsafe_allow_html=True)

        tab_chart, tab_tech, tab_fund, tab_journal = st.tabs(["📈 גרף TradingView", "🧠 ניתוח טכני", "🏢 פונדמנטלי", "📓 יומן טריידים"])

        with tab_chart:
            st.subheader("גרף ניתוח טכני אינטראקטיבי")
            st_tv(symbol=ticker_input, height=500)

        with tab_tech:
            st.subheader("תובנות טכניות")
            for msg in get_smart_analysis(df, periods):
                st.info(msg)

        with tab_fund:
            st.subheader("ניתוח פונדמנטלי")
            for insight in analyze_fundamentals(info):
                st.success(insight)

        with tab_journal:
            st.subheader("ניהול תיק עסקאות")
            
            # כפתור ייצוא לאקסל
            if st.session_state.trades:
                excel_data = to_excel(st.session_state.trades)
                st.download_button(
                    label="📥 ייצא יומן טריידים לאקסל",
                    data=excel_data,
                    file_name=f"trading_journal_{ticker_input}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with st.expander("➕ הוסף טרייד חדש"):
                c1, c2 = st.columns(2)
                p_in = c1.number_input("מחיר כניסה", value=float(last_row['Close']))
                q_in = c2.number_input("כמות", value=1, min_value=1)
                if st.button("שמור"):
                    tid = str(uuid.uuid4())
                    st.session_state.trades[tid] = {
                        "Ticker": ticker_input, 
                        "Entry_Price": p_in, 
                        "Quantity": q_in, 
                        "Status": "פתוח", 
                        "PnL": 0.0
                    }
                    st.rerun()

            st.divider()
            for tid, t in list(st.session_state.trades.items()):
                with st.container():
                    r1, r2, r3, r4, r5 = st.columns([1, 2, 1, 1, 0.5])
                    r1.write(f"**{t['Ticker']}**")
                    r2.write(f"מחיר: {t['Entry_Price']} | כמות: {t['Quantity']}")
                    
                    if t['Status'] == "פתוח":
                        exit_p = r3.number_input("יציאה", key=f"ex_{tid}", label_visibility="collapsed", value=float(last_row['Close']))
                        if r4.button("מכור", key=f"s_{tid}"):
                            st.session_state.trades[tid]['Status'] = "סגור"
                            st.session_state.trades[tid]['PnL'] = (exit_p - t['Entry_Price']) * t['Quantity'] - 12
                            st.rerun()
                    else:
                        r3.write(f"רווח: ${t['PnL']:.2f}")
                        r4.write("✅ סגור")
                    
                    if r5.button("🗑️", key=f"del_{tid}"):
                        del st.session_state.trades[tid]
                        st.rerun()
