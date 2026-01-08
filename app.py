import streamlit as st
import pandas as pd
import yfinance as yf
import io
import streamlit.components.v1 as components
from core.indicators import calculate_all_indicators, get_smart_analysis, calculate_final_score, analyze_fundamentals
import uuid

# --- הגדרות דף ---
st.set_page_config(page_title="התיק החכם", layout="wide")

# --- עיצוב CSS לרקע ולנראות ---
st.markdown("""
    <style>
    /* רקע לכל האפליקציה */
    [data-testid="stAppViewContainer"] {
        background-image: url("https://images.unsplash.com/photo-1642543492481-44e81e3914a7?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* רקע חצי שקוף לאזור התוכן כדי שהטקסט יהיה קריא */
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background-color: rgba(0,0,0,0);
    }
    
    .main .block-container {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-top: 2rem;
        max-width: 1000px;
    }

    /* יישור לימין */
    .stTextInput > label { direction: rtl; text-align: right; font-weight: bold; }
    .stTextInput input { direction: ltr; text-align: center; }
    h1, h2, h3, p, div { direction: rtl; text-align: right; }
    
    /* הסתרת אייקון מסך מלא של הגרף שלא יפריע */
    iframe { display: block; margin: 0 auto; }
    </style>
""", unsafe_allow_html=True)

# --- פונקציות עזר ---

# פונקציה אמינה יותר למשיכת נתונים
def get_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        # משיכת היסטוריה של שנתיים
        df = stock.history(period="2y")
        
        if df.empty:
            return None, None, None
            
        info = stock.info
        name = info.get('longName', ticker_symbol)
        return df, info, name
    except:
        return None, None, None

def to_excel(trades_dict):
    if not trades_dict: return None
    data_list = []
    for t in trades_dict.values():
        data_list.append(t)
    df = pd.DataFrame(data_list)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def render_tradingview_widget(symbol):
    # וידג'ט נקי ללא התקנות חיצוניות
    html_code = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
      "width": "100%", "height": 500, "symbol": "{symbol}",
      "interval": "D", "timezone": "Etc/UTC", "theme": "light",
      "style": "1", "locale": "en", "toolbar_bg": "#f1f3f6",
      "enable_publishing": false, "allow_symbol_change": true,
      "container_id": "tradingview_chart"
      }}
      );
      </script>
    </div>
    """
    components.html(html_code, height=500)

# --- אתחול זיכרון (Session) ---
if 'trades' not in st.session_state:
    st.session_state.trades = {}

# --- גוף האתר ---

st.title("📈 התיק החכם")
st.markdown("### מערכת מקצועית לניתוח ומעקב אחר מניות")

# שורת חיפוש מעוצבת וקטנה יותר
col_spacer1, col_input, col_spacer2 = st.columns([1, 2, 1])
with col_input:
    # ברירת מחדל AAPL במקום MARA
    ticker_input = st.text_input("הזן סימול מניה (לדוגמא AAPL):", "AAPL").upper()

if ticker_input:
    # שימוש בפונקציה החדשה והאמינה
    df, info, full_name = get_data(ticker_input)
    
    if df is not None:
        st.markdown("---")
        st.header(f"{full_name} ({ticker_input})")
        
        # טאבים
        tab1, tab2, tab3, tab4 = st.tabs(["📊 גרף חי", "🧠 ניתוח חכם", "🏢 נתוני חברה", "📓 יומן אישי"])
        
        with tab1:
            render_tradingview_widget(ticker_input)
            
        with tab2:
            try:
                # חישוב אינדיקטורים
                # וודא שפונקציות העזר ב-core/indicators.py קיימות ומותאמות
                # כאן נשתמש בחישוב בסיסי אם אין קובץ חיצוני, או נקרא לפונקציה שלך
                df_calc, periods = calculate_all_indicators(df, "סווינג") 
                last_row = df_calc.iloc[-1]
                score, txt, color = calculate_final_score(last_row, periods)
                
                st.markdown(f"""
                <div style="background-color:{color}; padding:15px; border-radius:10px; color:white; text-align:center; margin-bottom:20px;">
                    <h2 style="margin:0;">ציון טכני: {score}</h2>
                    <h3 style="margin:0;">{txt}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                analysis = get_smart_analysis(df_calc, periods)
                for item in analysis:
                    st.info(item)
            except Exception as e:
                st.warning("לא ניתן היה לחשב ניתוח טכני מלא עקב חוסר בנתונים היסטוריים מספקים.")
        
        with tab3:
            if info:
                # נתונים פונדמנטליים בסיסיים
                c1, c2, c3 = st.columns(3)
                c1.metric("שווי שוק", f"${info.get('marketCap', 0):,}")
                c2.metric("מכפיל רווח (PE)", info.get('trailingPE', 'N/A'))
                c3.metric("שינוי 52 שבועות", f"{info.get('52WeekChange', 0)*100:.1f}%")
                
                st.write(f"**תחום עיסוק:** {info.get('sector', 'לא ידוע')} | {info.get('industry', '')}")
                st.write(f"**תיאור:** {info.get('longBusinessSummary', 'אין תיאור זמין.')[:400]}...")
        
        with tab4:
            # אזור הוספת טרייד
            with st.expander("➕ הוסף עסקה ליומן", expanded=False):
                col_p, col_q, col_btn = st.columns([2, 2, 1])
                price_in = col_p.number_input("מחיר קנייה ($)", value=float(df['Close'].iloc[-1]))
                qty_in = col_q.number_input("כמות מניות", min_value=1, value=10)
                
                if col_btn.button("שמור ביומן"):
                    t_id = str(uuid.uuid4())
                    st.session_state.trades[t_id] = {
                        "Date": str(pd.Timestamp.now().date()),
                        "Ticker": ticker_input,
                        "Price": price_in,
                        "Quantity": qty_in,
                        "Status": "פתוח"
                    }
                    st.rerun()

            # כפתור הורדה לאקסל
            if st.session_state.trades:
                excel_data = to_excel(st.session_state.trades)
                st.download_button("📥 הורד יומן לאקסל", excel_data, "my_trades.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                st.markdown("### העסקאות שלי")
                for tid, t in list(st.session_state.trades.items()):
                    with st.container():
                        cc1, cc2, cc3 = st.columns([3, 1, 0.5])
                        cc1.write(f"**{t['Ticker']}** | {t['Date']} | כמות: {t['Quantity']} | מחיר: ${t['Price']}")
                        cc2.caption(t['Status'])
                        if cc3.button("🗑️", key=tid):
                            del st.session_state.trades[tid]
                            st.rerun()
                    st.divider()
            else:
                st.info("היומן שלך ריק כרגע. הוסף עסקה ראשונה!")
            
    else:
        st.error(f"לא הצלחנו למצוא נתונים עבור '{ticker_input}'. נסה לבדוק את האיות.")
