import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.data import load_stock_data
from core.indicators import calculate_indicators, generate_explanations
from utils.export import to_excel

# === הגדרות עמוד ועיצוב ===
st.set_page_config(page_title="מערכת מסחר מקצועית", layout="wide", page_icon="📈")

# הזרקת CSS ליישור לימין (RTL) ועיצוב נקי
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    .stTextInput > div > div > input { text-align: right; direction: ltr; } /* קלט באנגלית */
    h1, h2, h3, p, div { text-align: right; }
    .metric-card { background-color: #f8f9fa; border: 1px solid #ddd; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# אתחול Session State לניהול טריידים
if 'trades' not in st.session_state:
    st.session_state.trades = []
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# === כותרת וחיפוש מרכזי ===
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📈 מערכת ניתוח שוק - PRO</h1>", unsafe_allow_html=True)

# שימוש ב-Form כדי ש-Enter יעבוד
with st.form(key='search_form'):
    col1, col2 = st.columns([4, 1])
    with col1:
        ticker_input = st.text_input("הקלד סימול מניה ולחץ Enter (לדוגמה: NVDA, TSLA)", 
                                     placeholder="הקלד כאן...").upper()
    with col2:
        # כפתור מוסתר ויזואלית שעדיין קיים ללוגיקה, אבל Enter עושה את העבודה
        submit_button = st.form_submit_button(label='חפש מניה 🔎')

# בחירת ממוצעים - מופיעה תמיד
ma_type = st.radio("בחר סוג ניתוח:", 
                   ["טווח קצר (סווינג מהיר)", "טווח ארוך (השקעה/מגמה)"], 
                   horizontal=True)

# === לוגיקה ראשית ===
if submit_button or ticker_input:
    with st.spinner('מושך נתונים מהבורסה...'):
        df, full_name, next_earnings, levels = load_stock_data(ticker_input)

    if df is not None and not df.empty:
        st.session_state.data_loaded = True
        
        # חישוב אינדיקטורים
        df, periods = calculate_indicators(df, ma_type)
        
        # אזור מידע ראשי
        st.markdown(f"""
        <div style="background-color: #e8f4f8; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="margin:0; color: #2980b9;">{full_name} ({ticker_input})</h2>
            <p style="margin:0; font-size: 18px;">📅 דוחות כספיים קרובים: <b>{next_earnings}</b></p>
            <p style="margin:0; font-size: 24px; font-weight: bold;">מחיר אחרון: ${df['Close'].iloc[-1]:.2f}</p>
        </div>
        """, unsafe_allow_html=True)

        # === טאבים ===
        tab1, tab2, tab3 = st.tabs(["📊 ניתוח וגרף", "🧠 פרשנות חכמה", "📒 יומן טריידים"])

        # טאב 1: גרף
        with tab1:
            fig = go.Figure()
            # נרות
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='מחיר'))
            # ממוצעים נעים
            colors = ['orange', 'blue', 'purple']
            for i, p in enumerate(periods):
                fig.add_trace(go.Scatter(x=df.index, y=df[f'SMA_{p}'], name=f'ממוצע {p}', line=dict(color=colors[i], width=1.5)))
            
            fig.update_layout(height=600, xaxis_rangeslider_visible=False, template="plotly_white", title="גרף מחיר וממוצעים")
            st.plotly_chart(fig, use_container_width=True)

        # טאב 2: פרשנות
        with tab2:
            st.subheader("מה אומרים המספרים?")
            explanations = generate_explanations(df, periods, levels)
            
            for exp in explanations:
                if "---" in exp:
                    st.markdown("---")
                else:
                    st.info(exp)

        # טאב 3: יומן טריידים
        with tab3:
            st.subheader("ניהול מעקב אישי")
            
            with st.form("trade_form"):
                c1, c2, c3 = st.columns(3)
                t_action = c1.selectbox("פעולה", ["קנייה", "מכירה בחסר (Short)"])
                t_price = c2.number_input("מחיר כניסה", value=float(df['Close'].iloc[-1]))
                t_qty = c3.number_input("כמות מניות", min_value=1, value=10)
                t_notes = st.text_area("הערות לטרייד (למה נכנסתי?)")
                
                add_trade = st.form_submit_button("שמור טרייד ליומן 💾")
                
                if add_trade:
                    trade_record = {
                        "תאריך": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                        "מניה": ticker_input,
                        "פעולה": t_action,
                        "מחיר": t_price,
                        "כמות": t_qty,
                        "סה״כ ($)": t_price * t_qty,
                        "הערות": t_notes
                    }
                    st.session_state.trades.append(trade_record)
                    st.success("הטרייד נשמר בהצלחה!")

            if len(st.session_state.trades) > 0:
                st.write("### היסטוריית טריידים (סשן נוכחי)")
                trades_df = pd.DataFrame(st.session_state.trades)
                st.dataframe(trades_df, use_container_width=True)
                
                # כפתור הורדה
                excel_data = to_excel(trades_df)
                st.download_button("📥 הורד יומן לאקסל", data=excel_data, file_name="my_trades.xlsx")
            else:
                st.info("עדיין לא הזנת טריידים במערכת.")

    elif ticker_input: 
        st.error("לא נמצאו נתונים. בדוק את הסימול.")
