import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

# --- הגדרות מערכת ועיצוב ---
st.set_page_config(page_title="Pro Trader AI", layout="wide")

# הזרקת CSS לעיצוב נעים יותר (לא שחור מאיים)
st.markdown("""
    <style>
    /* כיוון ימין לשמאל */
    .stApp {
        direction: rtl;
        text-align: right;
    }
    
    /* כרטיסיות מידע - רקע נעים */
    div[data-testid="stMetricValue"] {
        color: #0078ff; /* כחול הייטק */
        font-weight: bold;
    }
    
    /* יישור טקסט בכרטיסיות */
    div[data-testid="stMetricLabel"] {
        width: 100%;
        text-align: right;
        direction: rtl;
    }

    /* עיצוב טאבים */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f0f2f6;
        border-radius: 5px;
        color: #31333F;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #0078ff;
        color: white;
    }
    
    /* הסרת רווחים מיותרים */
    .block-container {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- פונקציות ליבה ---

# 1. יומן מסחר
JOURNAL_FILE = "trading_journal.csv"

def load_journal():
    if not os.path.exists(JOURNAL_FILE):
        df = pd.DataFrame(columns=["תאריך", "סימול", "פעולה", "מחיר ($)", "כמות", "רווח ($)", "רווח (₪)"])
        df.to_csv(JOURNAL_FILE, index=False, encoding='utf-8-sig')
        return df
    return pd.read_csv(JOURNAL_FILE, encoding='utf-8-sig')

def save_trade(date, symbol, action, price, qty, profit_usd=0, profit_ils=0):
    new_row = pd.DataFrame([{
        "תאריך": date,
        "סימול": symbol,
        "פעולה": action,
        "מחיר ($)": round(price, 2),
        "כמות": qty,
        "רווח ($)": round(profit_usd, 2) if profit_usd else 0,
        "רווח (₪)": round(profit_ils, 2) if profit_ils else 0
    }])
    df = load_journal()
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(JOURNAL_FILE, index=False, encoding='utf-8-sig')

# 2. שער דולר
@st.cache_data(ttl=3600)
def get_usd_rate():
    try:
        return yf.Ticker("ILS=X").history(period="1d")['Close'].iloc[-1]
    except:
        return 3.65

# 3. ניתוח נתונים
def get_data(symbol):
    try:
        ticker_obj = yf.Ticker(symbol)
        df = ticker_obj.history(period="2y")
        
        if df.empty: return None, None
        
        # פרטי חברה (שם מלא)
        info = ticker_obj.info
        company_name = info.get('longName', symbol)

        # חישוב אינדיקטורים
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain/loss)))
        
        # MACD
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        return df, company_name, ticker_obj
    except:
        return None, None, None

# --- ממשק משתמש ---

st.title("📊 מערכת מסחר חכמה")

# סרגל עליון - חיפוש ומדדים
usd_val = get_usd_rate()
c1, c2, c3, c4 = st.columns([2, 1, 1, 1])

with c1:
    symbol_input = st.text_input("הכנס סימול (למשל TSLA, NVDA):", "SPY").upper()

with c2:
    st.metric("שער הדולר", f"₪{usd_val:.2f}")

# טעינת נתונים
df, name, ticker_obj = get_data(symbol_input)

if df is not None:
    # הצגת שם המניה ומחיר נוכחי
    last_price = df['Close'].iloc[-1]
    change = (last_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100
    color_delta = "normal" 
    
    st.markdown(f"### {name} ({symbol_input})")
    st.metric("מחיר אחרון", f"${last_price:.2f}", f"{change:.2f}%")

    # לשוניות ראשיות
    tab1, tab2, tab3, tab4 = st.tabs(["📈 גרף טכני", "🧠 ניתוח חכם", "📰 חדשות", "📓 יומן מסחר"])

    # --- לשונית 1: גרף ---
    with tab1:
        st.caption("גלול עם העכבר לזום, גרור כדי לזוז בציר הזמן")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        
        # נרות
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="מחיר"), row=1, col=1)
        
        # ממוצעים
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=1.5), name="SMA 50"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='blue', width=1.5), name="SMA 200"), row=1, col=1)
        
        # ווליום (במקום MACD בגרף הראשי, נשים ווליום שזה סטנדרט)
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='rgba(200,200,200,0.5)', name="Volume"), row=2, col=1)

        fig.update_layout(height=600, template="plotly_white", xaxis_rangeslider_visible=False, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    # --- לשונית 2: ניתוח חכם (הבקשה שלך) ---
    with tab2:
        st.subheader("פרשנות אינדיקטורים אוטומטית")
        
        curr_rsi = df['RSI'].iloc[-1]
        curr_macd = df['MACD'].iloc[-1]
        curr_signal = df['Signal'].iloc[-1]
        prev_macd = df['MACD'].iloc[-2]
        prev_signal = df['Signal'].iloc[-2]

        col_a, col_b = st.columns(2)

        with col_a:
            st.info(f"RSI נוכחי: {curr_rsi:.1f}")
            if curr_rsi > 70:
                st.error("⚠️ **אזהרת קניית יתר (Overbought):** המניה התחממה מדי. סטטיסטית, ייתכן תיקון למטה בקרוב. שקול מימוש רווחים או המתנה.")
            elif curr_rsi < 30:
                st.success("💎 **הזדמנות מכירת יתר (Oversold):** המניה ירדה חזק. ייתכן שהמוכרים התעייפו וצפוי תיקון למעלה. חפש נקודת כניסה.")
            else:
                st.write("✅ **RSI ניטרלי:** המניה מתנהגת בצורה מאוזנת. אין איתות קיצון.")

        with col_b:
            st.info(f"MACD: {curr_macd:.2f} | Signal: {curr_signal:.2f}")
            
            # זיהוי חצייה (Crossover)
            if curr_macd > curr_signal and prev_macd <= prev_signal:
                st.success("🚀 **איתות שוורי (Bullish Cross):** קו ה-MACD בדיוק חצה את הסיגנל כלפי מעלה. זהו איתות חזק לכניסה/לונג.")
            elif curr_macd < curr_signal and prev_macd >= prev_signal:
                st.error("🔻 **איתות דובי (Bearish Cross):** קו ה-MACD חצה את הסיגנל כלפי מטה. המומנטום נחלש, סימן אפשרי לירידות.")
            elif curr_macd > curr_signal:
                st.write("📈 **מגמה חיובית:** המומנטום נשמר חיובי (MACD מעל הסיגנל).")
            else:
                st.write("📉 **מגמה שלילית:** המומנטום נשמר שלילי (MACD מתחת לסיגנל).")

        st.divider()
        st.markdown("#### המלצת מגמה (Micha Stocks Logic)")
        p_now = df['Close'].iloc[-1]
        sma50 = df['SMA50'].iloc[-1]
        sma200 = df['SMA200'].iloc[-1]

        if p_now > sma50 > sma200:
            st.success("🔥 **מגמת עלייה חזקה:** המחיר מעל ממוצע 50, וממוצע 50 מעל 200. שוק שוורי מובהק.")
        elif p_now < sma50:
            st.warning("⚠️ **זהירות:** המחיר ירד מתחת לממוצע 50. המומנטום לטווח הקצר נשבר.")
        else:
            st.info("🟡 **דשדוש/אי ודאות:** אין כיוון ברור בין הממוצעים.")

    # --- לשונית 3: חדשות ---
    with tab3:
        st.subheader(f"חדשות אחרונות על {symbol_input}")
        try:
            news = ticker_obj.news
            if news:
                for item in news[:5]: # הצג 5 כתבות אחרונות
                    with st.expander(f"📰 {item['title']}"):
                        st.write(f"פורסם על ידי: {item.get('publisher', 'Unknown')}")
                        if 'link' in item:
                            st.markdown(f"[למעבר לכתבה המלאה לחץ כאן]({item['link']})")
                        if 'thumbnail' in item and item['thumbnail']:
                            # בדיקה אם יש תמונה ברזולוציה סבירה
                            try:
                                img_url = item['thumbnail']['resolutions'][0]['url']
                                st.image(img_url, width=200)
                            except:
                                pass
            else:
                st.write("לא נמצאו חדשות עדכניות כרגע.")
        except:
            st.write("לא ניתן לטעון חדשות למניה זו.")

    # --- לשונית 4: יומן מסחר ---
    with tab4:
        st.subheader("תיעוד עסקאות")
        
        c_act1, c_act2, c_act3, c_act4, c_act5 = st.columns(5)
        action = c_act1.selectbox("פעולה", ["קנייה", "מכירה"])
        trade_price = c_act2.number_input("מחיר ($)", value=float(last_price))
        trade_qty = c_act3.number_input("כמות", min_value=1, value=1)
        trade_date = c_act4.date_input("תאריך")
        
        if st.button("רשום ביומן"):
            p_usd = 0
            p_ils = 0
            # אם זו מכירה, ננסה לחשב רווח (פשוט לצורך הדוגמה)
            if action == "מכירה":
                # כאן אפשר להוסיף לוגיקה מורכבת יותר, כרגע נשמור את שווי המכירה
                p_usd = trade_price * trade_qty
                p_ils = p_usd * usd_val
            
            save_trade(trade_date, symbol_input, action, trade_price, trade_qty, p_usd, p_ils)
            st.success("נרשם בהצלחה!")
            st.rerun()

        st.divider()
        journal_df = load_journal()
        if not journal_df.empty:
            st.dataframe(journal_df, use_container_width=True)
            
            # סיכום רווחים ממכירות
            total_profit = journal_df[journal_df['פעולה'] == 'מכירה']['רווח (₪)'].sum()
            st.metric("סה\"כ נפח מכירות (₪)", f"₪{total_profit:,.2f}")
        else:
            st.info("היומן ריק.")

else:
    st.info("אנא הזן סימול מניה תקין (למשל GOOG, AMZN, TEVA) והמתן לטעינה...")
