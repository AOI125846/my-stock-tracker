import streamlit as st
import pandas as pd
import yfinance as yf
import io
import requests
import streamlit.components.v1 as components
from core.indicators import calculate_all_indicators, get_smart_analysis, calculate_final_score, analyze_fundamentals
import uuid

# --- הגדרות דף ---
st.set_page_config(page_title="התיק החכם", layout="wide")

# --- עיצוב CSS ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-image: url("https://images.unsplash.com/photo-1642543492481-44e81e3914a7?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background-color: rgba(0,0,0,0);
    }
    .main .block-container {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        max-width: 1000px;
    }
    .stTextInput > label { direction: rtl; text-align: right; font-weight: bold; }
    h1, h2, h3, p, div { direction: rtl; text-align: right; }
    iframe { display: block; margin: 0 auto; }
    </style>
""", unsafe_allow_html=True)

# --- פונקציות ליבה ---

# פונקציה משופרת לעקיפת חסימות
def get_data_robust(ticker_symbol):
    ticker_symbol = ticker_symbol.strip().upper()
    
    # יצירת סשן שמתחזה לדפדפן כרום רגיל
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })

    try:
        # ניסיון 1: שימוש באובייקט Ticker עם הסשן המיוחד
        stock = yf.Ticker(ticker_symbol, session=session)
        df = stock.history(period="2y")
        
        # אם חזר ריק, ננסה שיטה ישנה (download)
        if df.empty:
            df = yf.download(ticker_symbol, period="2y", progress=False, session=session)
        
        # תיקון מבנה עמודות (MultiIndex) שקורה בגרסאות חדשות
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df.empty or len(df) < 5:
            return None, None, None

        # נסיון למשוך מידע על החברה, עם הגנה מקריסה
        try:
            info = stock.info
            name = info.get('longName', ticker_symbol)
        except:
            info = {}
            name = ticker_symbol

        return df, info, name

    except Exception as e:
        print(f"Error fetching {ticker_symbol}: {e}")
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

if 'trades' not in st.session_state:
    st.session_state.trades = {}

# --- ממשק משתמש ---

st.title("📈 התיק החכם")
st.markdown("### מערכת מקצועית לניתוח ומעקב")

# שורת חיפוש
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    ticker_input = st.text_input("הזן סימול מניה (לדוגמא AAPL, MARA):", "AAPL").upper()

if ticker_input:
    df, info, full_name = get_data_robust(ticker_input)
    
    if df is not None:
        st.markdown("---")
        st.header(f"{full_name} ({ticker_input})")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 גרף חי", "🧠 ניתוח חכם", "🏢 נתוני חברה", "📓 יומן אישי"])
        
        with tab1:
            render_tradingview_widget(ticker_input)
            
        with tab2:
            try:
                # חישוב וניתוח טכני
                df_calc, periods = calculate_all_indicators(df, "סווינג") 
                last_row = df_calc.iloc[-1]
                score, txt, color = calculate_final_score(last_row, periods)
                
                st.markdown(f"""
                <div style="background-color:{color}; padding:15px; border-radius:10px; color:white; text-align:center; margin-bottom:20px;">
                    <h2 style="margin:0;">ציון טכני: {score}</h2>
                    <h3 style="margin:0;">{txt}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                for item in get_smart_analysis(df_calc, periods):
                    st.info(item)
            except Exception as e:
                st.error("לא ניתן לחשב אינדיקטורים טכניים בשל מחסור בנתונים היסטוריים.")
        
        with tab3:
            if info:
                c1, c2, c3 = st.columns(3)
                mkt_cap = info.get('marketCap')
                val_formatted = f"${mkt_cap/1e9:.2f}B" if mkt_cap else "לא זמין"
                
                c1.metric("שווי שוק", val_formatted)
                c2.metric("מחיר נוכחי", f"${info.get('currentPrice', df['Close'].iloc[-1]):.2f}")
                c3.metric("יעד אנליסטים", f"${info.get('targetMeanPrice', 'N/A')}")
                
                st.markdown(f"**תחום:** {info.get('industry', 'כללי')}")
                st.caption(info.get('longBusinessSummary', 'אין תיאור זמין.')[:300] + "...")
            else:
                st.warning("מידע פונדמנטלי חסר, אך הגרף מוצג.")
        
        with tab4:
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

            if st.session_state.trades:
                excel_data = to_excel(st.session_state.trades)
                st.download_button("📥 הורד לאקסל", excel_data, "my_trades.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                for tid, t in list(st.session_state.trades.items()):
                    with st.container():
                        cc1, cc2 = st.columns([4, 1])
                        cc1.info(f"**{t['Ticker']}** | נרכש ב-${t['Price']} | כמות: {t['Quantity']}")
                        if cc2.button("מחק", key=tid):
                            del st.session_state.trades[tid]
                            st.rerun()
            else:
                st.write("אין עסקאות שמורות.")
            
    else:
        st.error(f"❌ שגיאת תקשורת עם השרת עבור '{ticker_input}'. נסה שוב בעוד מספר שניות.")
        
