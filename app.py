import streamlit as st
import pandas as pd
import io
import streamlit.components.v1 as components  # רכיב להטמעת HTML
from core.data import load_stock_data
from core.indicators import calculate_all_indicators, get_smart_analysis, calculate_final_score, analyze_fundamentals
import uuid

# הגדרות דף
st.set_page_config(page_title="Micha Stocks", layout="wide")

# עיצוב ורקע
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.9)), 
                    url("https://images.unsplash.com/photo-1611974717482-589252c8465f?q=80&w=2070");
        background-size: cover;
    }
    .main { direction: rtl; text-align: right; }
    /* יישור טקסט בגרף */
    iframe { display: block; margin: 0 auto; }
    </style>
    """, unsafe_allow_html=True)

# אתחול נתונים
if 'trades' not in st.session_state:
    st.session_state.trades = {}

def to_excel(trades_dict):
    if not trades_dict: return None
    # המרת המילון לרשימה שטוחה לאקסל
    data_list = []
    for t in trades_dict.values():
        data_list.append(t)
    df = pd.DataFrame(data_list)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# פונקציה להצגת גרף TradingView מקורי
def render_tradingview_widget(symbol):
    html_code = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
      "width": "100%",
      "height": 500,
      "symbol": "{symbol}",
      "interval": "D",
      "timezone": "Etc/UTC",
      "theme": "light",
      "style": "1",
      "locale": "en",
      "toolbar_bg": "#f1f3f6",
      "enable_publishing": false,
      "allow_symbol_change": true,
      "container_id": "tradingview_chart"
      }}
      );
      </script>
    </div>
    """
    components.html(html_code, height=500)

st.title("📊 מערכת Micha Stocks")

# חיפוש מניה
ticker = st.text_input("הזן סימול מניה (למשל MARA):", "").upper()

if ticker:
    df, info, full_name = load_stock_data(ticker)
    
    if df is not None:
        main_container = st.container()
        with main_container:
            st.header(f"{full_name} ({ticker})")
            
            # טאבים
            t1, t2, t3, t4 = st.tabs(["📈 גרף", "🧠 ניתוח", "🏢 חברה", "📓 יומן"])
            
            with t1:
                # שימוש בפונקציה החדשה שלא דורשת התקנה חיצונית
                render_tradingview_widget(ticker)
            
            with t2:
                df_ind, periods = calculate_all_indicators(df, "סווינג")
                score, txt, col = calculate_final_score(df_ind.iloc[-1], periods)
                
                st.markdown(f"""
                <div style="background-color:{col}; padding:10px; border-radius:10px; color:white; text-align:center;">
                    <h3>ציון טכני: {score}/100 - {txt}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("") # מרווח
                for msg in get_smart_analysis(df_ind, periods):
                    st.info(msg)
            
            with t3:
                for insight in analyze_fundamentals(info):
                    st.success(insight)
            
            with t4:
                # ייצוא לאקסל
                if st.session_state.trades:
                    excel = to_excel(st.session_state.trades)
                    st.download_button("📥 הורד יומן לאקסל", excel, f"{ticker}_journal.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                # הוספת טרייד
                with st.expander("הוסף טרייד"):
                    p = st.number_input("מחיר", value=float(df['Close'].iloc[-1]))
                    if st.button("שמור"):
                        id = str(uuid.uuid4())
                        st.session_state.trades[id] = {"Ticker": ticker, "Price": p, "Status": "Open", "PnL": 0}
                        st.rerun()
                
                st.markdown("---")
                # תצוגה ומחיקה
                if not st.session_state.trades:
                    st.write("אין עסקאות רשומות.")
                
                for tid, t in list(st.session_state.trades.items()):
                    cols = st.columns([3, 1])
                    status_icon = "🟢" if t['Status'] == "Open" else "🔴"
                    cols[0].write(f"{status_icon} **{t['Ticker']}** | מחיר: {t['Price']}")
                    
                    if cols[1].button("🗑️", key=f"del_{tid}"):
                        del st.session_state.trades[tid]
                        st.rerun()
    else:
        st.error("לא נמצאו נתונים. נסה סימול אחר.")
