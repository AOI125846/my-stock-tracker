import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime, date
import logging

# Logging בסיסי
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def save_trade(trade_date, symbol, action, price, qty, profit_usd=0, profit_ils=0):
    # המרה של תאריך למחרוזת אם צריך
    if isinstance(trade_date, (pd.Timestamp, datetime, date)):
        trade_date_str = trade_date.isoformat()
    else:
        trade_date_str = str(trade_date)

    new_row = pd.DataFrame([{
        "תאריך": trade_date_str,
        "סימול": symbol,
        "פעולה": action,
        "מחיר ($)": round(float(price), 2),
        "כמות": int(qty),
        "רווח ($)": round(float(profit_usd), 2) if profit_usd else 0,
        "רווח (₪)": round(float(profit_ils), 2) if profit_ils else 0
    }])
    df = load_journal()
    df = pd.concat([df, new_row], ignore_index=True)
    # כתיבה אטומית בסיסית (overwrite)
    df.to_csv(JOURNAL_FILE, index=False, encoding='utf-8-sig')

# 2. שער דולר
@st.cache_data(ttl=3600)
def get_usd_rate():
    try:
        rate = yf.Ticker("ILS=X").history(period="1d")['Close'].iloc[-1]
        return float(rate)
    except Exception as e:
        logger.warning("אי אפשר לקבל שער דולר מ‑yfinance: %s — שימוש בערך ברירת מחדל", e)
        return 3.65

# 3. ניתוח נתונים
@st.cache_data(ttl=300)
def get_data(symbol):
    """
    מחזיר (df, company_name, ticker_obj) — תמיד שלושה ערכים.
    אם המניה לא נמצאה או יש שגיאה מחזיר (None, None, None).
    """
    try:
        ticker_obj = yf.Ticker(symbol)
        # בקשה תקופתית ממולצת; אם תרצה ארגומנט להגדיר את התקופה אפשר להרחיב.
        df = ticker_obj.history(period="2y", auto_adjust=False)

        if df is None or df.empty:
            return None, None, None

        # פרטי חברה (שם מלא) — guarded access
        company_name = None
        try:
            info = ticker_obj.info or {}
            company_name = info.get('longName') or info.get('shortName') or symbol
        except Exception:
            # yfinance יכול לזרוק פה; נזרום הלאה עם סימול
            company_name = symbol

        # חישוב אינדיקטורים
        df = df.copy()  # בטיחות לשינויים
        df['SMA50'] = df['Close'].rolling(window=50, min_periods=1).mean()
        df['SMA200'] = df['Close'].rolling(window=200, min_periods=1).mean()

        # RSI - חישוב יציב שמטפל בחלוקת אפס
        delta = df['Close'].diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)
        avg_gain = gains.rolling(window=14, min_periods=14).mean()
        avg_loss = losses.rolling(window=14, min_periods=14).mean()
        # הימנעות מחלוקה באפס
        rs = avg_gain / avg_loss.replace({0: pd.NA})
        rsi = 100 - (100 / (1 + rs))
        # במקום NaN נוכל למלא ערכים קיצוניים בהתאם
        rsi = rsi.fillna(50)  # אם אין מספיק נתונים, נניח ניטרלי
        df['RSI'] = rsi

        # MACD
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        return df, company_name, ticker_obj
    except Exception as e:
        logger.exception("שגיאה בטעינת נתוני מניה %s: %s", symbol, e)
        return None, None, None

# --- ממשק משתמש ---

st.title("📊 מערכת מסחר חכמה")

# סרגל עליון - חיפוש ומדדים
usd_val = get_usd_rate()
c1, c2 = st.columns([3, 1])

with c1:
    symbol_input = st.text_input("הכנס סימול (למשל TSLA, NVDA):", "SPY").upper()

with c2:
    st.metric("שער הדולר", f"₪{usd_val:.2f}")

# טעינת נתונים
df, name, ticker_obj = get_data(symbol_input)

if df is not None:
    # הצגת שם המניה ומחיר נוכחי
    try:
        last_price = float(df['Close'].iloc[-1])
        prev_price = float(df['Close'].iloc[-2])
        change = (last_price - prev_price) / prev_price * 100
    except Exception:
        last_price = float(df['Close'].iloc[-1])
        change = 0.0

    st.markdown(f"### {name} ({symbol_input})")
    st.metric("מחיר אחרון", f"${last_price:.2f}", f"{change:.2f}%")

    # לשוניות ראשיות
    tab1, tab2, tab3, tab4 = st.tabs(["📈 גרף טכני", "🧠 ניתוח חכם", "📰 חדשות", "📓 יומן מסחר"])

    # --- לשונית 1: גרף ---
    with tab1:
        st.caption("זום וגרירה זמינים אך רזולוציות נתונים קבועות — אין אפשרות לשנות רזולוציית נרות חופשית.")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)

        # נרות
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="מחיר"), row=1, col=1)

        # ממוצעים
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=1.5), name="SMA 50"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='blue', width=1.5), name="SMA 200"), row=1, col=1)

        # ווליום
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='rgba(200,200,200,0.5)', name="Volume"), row=2, col=1)

        fig.update_layout(height=600, template="plotly_white", xaxis_rangeslider_visible=False, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    # --- לשונית 2: ניתוח חכם (הבקשה שלך) ---
    with tab2:
        st.subheader("פרשנות אינדיקטורים אוטומטית")

        curr_rsi = float(df['RSI'].iloc[-1]) if 'RSI' in df.columns else None
        curr_macd = float(df['MACD'].iloc[-1]) if 'MACD' in df.columns else None
        curr_signal = float(df['Signal'].iloc[-1]) if 'Signal' in df.columns else None
        prev_macd = float(df['MACD'].iloc[-2]) if len(df) >= 2 else None
        prev_signal = float(df['Signal'].iloc[-2]) if len(df) >= 2 else None

        col_a, col_b = st.columns(2)

        with col_a:
            if curr_rsi is not None:
                st.info(f"RSI נוכחי: {curr_rsi:.1f}")
                if curr_rsi > 70:
                    st.error("⚠️ **אזהרת קניית יתר (Overbought):** המניה התחממה מדי. סטטיסטית, ייתכן תיקון למטה בקרוב. שקול מימוש רווחים או הקטנת חשיפה בהתאם לאסטרטגיה.")
                elif curr_rsi < 30:
                    st.success("💎 **הזדמנות מכירת יתר (Oversold):** המניה ירדה חזק. ייתכן שהמוכרים התעייפו וצפוי תיקון למעלה. שקול כניסה חלקית עם ניהול סיכון.")
                else:
                    st.write("✅ **RSI ניטרלי:** המניה מתנהגת בצורה מאוזנת. אין איתות קיצון.")
            else:
                st.write("RSI לא מחושב עבור התקופה הנוכחית.")

        with col_b:
            if curr_macd is not None and curr_signal is not None and prev_macd is not None and prev_signal is not None:
                st.info(f"MACD: {curr_macd:.4f} | Signal: {curr_signal:.4f}")
                # זיהוי חצייה (Crossover)
                if curr_macd > curr_signal and prev_macd <= prev_signal:
                    st.success("🚀 **איתות שוורי (Bullish Cross):** קו ה‑MACD חצה את הסיגנל כלפי מעלה — איתות כניסה/לונג חזק יחסית.")
                elif curr_macd < curr_signal and prev_macd >= prev_signal:
                    st.error("🔻 **איתות דובי (Bearish Cross):** קו ה‑MACD חצה את הסיגנל כלפי מטה — יתכן סימן לירידה במומנטום.")
                elif curr_macd > curr_signal:
                    st.write("📈 **מגמה חיובית:** המומנטום חיובי (MACD מעל הסיגנל).")
                else:
                    st.write("📉 **מגמה שלילית:** המומנטום שלילי (MACD מתחת לסיגנל).")
            else:
                st.write("MACD/SIGNAL לא מספיקים לחישוב איתותים אמינים.")

        st.divider()
        st.markdown("#### המלצת מגמה (Micha Stocks Logic)")
        p_now = last_price
        sma50 = float(df['SMA50'].iloc[-1]) if 'SMA50' in df.columns else None
        sma200 = float(df['SMA200'].iloc[-1]) if 'SMA200' in df.columns else None

        if sma50 is not None and sma200 is not None and p_now > sma50 > sma200:
            st.success("🔥 **מגמת עלייה חזקה:** המחיר מעל ממוצע 50, וממוצע 50 מעל 200. שוק שוורי מובהק.")
        elif sma50 is not None and p_now < sma50:
            st.warning("⚠️ **זהירות:** המחיר ירד מתחת לממוצע 50. המומנטום לטווח הקצר נשבר.")
        else:
            st.info("🟡 **דשדוש/אי ודאות:** אין כיוון ברור בין הממוצעים.")

    # --- לשונית 3: חדשות ---
    with tab3:
        st.subheader(f"חדשות אחרונות על {symbol_input}")
        try:
            news = getattr(ticker_obj, "news", None)
            if news:
                for item in news[:5]:  # הצג 5 כתבות אחרונות
                    title = item.get('title') or item.get('summary') or 'כתבה'
                    publisher = item.get('publisher') or item.get('source') or 'Unknown'
                    link = item.get('link') or item.get('url')
                    with st.expander(f"📰 {title}"):
                        st.write(f"פורסם על ידי: {publisher}")
                        if link:
                            st.markdown(f"[למעבר לכתבה המלאה לחץ כאן]({link})")
                        # תמונה אם קיימת
                        try:
                            thumb = item.get('thumbnail') or {}
                            # yfinance structure משתנה — נחפש מיקום אפשרי לתמונה
                            if isinstance(thumb, dict):
                                # מקרים שונים — ננסה למצוא URL
                                url = None
                                if 'resolutions' in thumb and isinstance(thumb['resolutions'], list) and thumb['resolutions']:
                                    url = thumb['resolutions'][0].get('url')
                                elif 'url' in thumb:
                                    url = thumb['url']
                                if url:
                                    st.image(url, width=200)
                        except Exception:
                            logger.debug("לא ניתן להציג תמונה עבור כתבה")
            else:
                st.write("לא נמצאו חדשות עדכניות כרגע.")
        except Exception:
            logger.exception("שגיאה בטעינת חדשות")
            st.write("לא ניתן לטעון חדשות למניה זו.")

    # --- לשונית 4: יומן מסחר ---
    with tab4:
        st.subheader("תיעוד עסקאות")

        c_act1, c_act2, c_act3, c_act4 = st.columns(4)
        action = c_act1.selectbox("פעולה", ["קנייה", "מכירה"])
        trade_price = float(c_act2.number_input("מחיר ($)", value=last_price))
        trade_qty = int(c_act3.number_input("כמות", min_value=1, value=1))
        trade_date = c_act4.date_input("תאריך")

        if st.button("רשום ביומן"):
            p_usd = 0.0
            p_ils = 0.0
            # אם זו מכירה, ננסה לחשב רווח (פשוט לצורך הדוגמה)
            if action == "מכירה":
                p_usd = trade_price * trade_qty
                p_ils = p_usd * usd_val

            save_trade(trade_date, symbol_input, action, trade_price, trade_qty, p_usd, p_ils)
            st.success("נרשם בהצלחה!")
            st.experimental_rerun()

        st.divider()
        journal_df = load_journal()
        if not journal_df.empty:
            st.dataframe(journal_df, use_container_width=True)

            # סיכום רווחים ממכירות
            try:
                total_profit = journal_df[journal_df['פעולה'] == 'מכירה']['רווח (₪)'].sum()
                st.metric("סה\"כ נפח מכירות (₪)", f"₪{total_profit:,.2f}")
            except Exception:
                st.write("שגיאה בסיכום היומן.")
        else:
            st.info("היומן ריק.")

else:
    st.info("אנא הזן סימול מניה תקין (למשל GOOG, AMZN, TEVA) והמתן לטעינה...")
