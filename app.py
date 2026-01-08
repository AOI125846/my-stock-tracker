# -*- coding: utf-8 -*-
"""
Streamlit – "התיק החכם" - גרסה מונוליתית (כל הפונקציות בקובץ אחד)
"""

import uuid
import io
from datetime import datetime

import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf

# ----------------------------------------------------------------------
# 1️⃣ הגדרות כלליות של העמוד
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="התיק החכם",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-size: cover;
        background-attachment: fixed;
    }
    .main .block-container {
        background-color: rgba(255,255,255,0.98);
        padding: 2rem;
        border-radius: 20px;
        margin-top: 2rem;
        direction: rtl;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    div.stButton > button {
        width: 100%;
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 10px;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background: linear-gradient(45deg, #764ba2 0%, #667eea 100%);
    }
    .stTextInput input {
        text-align: center;
        border-radius: 10px;
        border: 2px solid #667eea;
    }
    .stSelectbox > div > div {
        border-radius: 10px;
        border: 2px solid #667eea;
    }
    h1, h2, h3, h4 {
        color: #333;
        text-align: center;
    }
    .stAlert {
        border-radius: 10px;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# 2️⃣ פונקציות ליבה - כל הפונקציות כאן בקובץ אחד
# ----------------------------------------------------------------------

# ---------- פונקציות לטעינת נתונים ----------
@st.cache_data(ttl=3600)
def load_stock_data(ticker):
    """
    טוען נתוני מניות מ-yfinance
    """
    try:
        # שימוש ב-download עם תקופת זמן ארוכה יותר
        df = yf.download(
            ticker, 
            period="2y", 
            auto_adjust=True, 
            progress=False,
            timeout=10
        )
        
        # טיפול ב-MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        if df.empty or len(df) < 5:
            return None, None, ticker
        
        # משיכת מידע נוסף בנפרד
        info = {}
        full_name = ticker
        
        try:
            t_obj = yf.Ticker(ticker)
            info = t_obj.info
            
            # שם מלא של החברה
            full_name = info.get('longName', info.get('shortName', ticker))
            
        except Exception:
            pass
        
        return df, info, full_name
        
    except Exception as e:
        st.error(f"❌ שגיאה בטעינת נתונים עבור {ticker}: {str(e)}")
        return None, None, ticker


# ---------- פונקציות אינדיקטורים טכניים ----------
def calculate_all_indicators(df, ma_type):
    """
    מחשב את כל האינדיקטורים הטכניים
    """
    # יצירת עותק כדי לא לשנות את המקור
    df_calc = df.copy()
    
    # ניקוי עמודות כפולות
    if isinstance(df_calc.columns, pd.MultiIndex):
        df_calc.columns = df_calc.columns.get_level_values(0)
    df_calc = df_calc.loc[:, ~df_calc.columns.duplicated()]
    
    # וידוא שיש עמודת Close
    if 'Close' not in df_calc.columns:
        raise ValueError("DataFrame חייב לכלול עמודת 'Close'")
    
    # בחירת תקופות SMA לפי סוג
    if "קצר" in ma_type:
        periods = [9, 20, 50]
    else:
        periods = [100, 150, 200]
    
    # חישוב Simple Moving Averages
    for p in periods:
        df_calc[f'SMA_{p}'] = df_calc['Close'].rolling(window=p, min_periods=1).mean()
    
    # חישוב RSI (Relative Strength Index)
    delta = df_calc['Close'].diff()
    
    # יצירת סדרות של רווחים והפסדים
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # חישוב ממוצע נע מעריכי
    avg_gain = gain.rolling(window=14, min_periods=1).mean()
    avg_loss = loss.rolling(window=14, min_periods=1).mean()
    
    # חישוב RS ו-RSI (עם הגנה מפני חלוקה באפס)
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df_calc['RSI'] = 100 - (100 / (1 + rs))
    
    # הגבלת ערכי RSI בין 0-100 והחלפת NaN ב-50
    df_calc['RSI'] = df_calc['RSI'].clip(0, 100).fillna(50)
    
    # חישוב MACD (Moving Average Convergence Divergence)
    ema12 = df_calc['Close'].ewm(span=12, adjust=False, min_periods=1).mean()
    ema26 = df_calc['Close'].ewm(span=26, adjust=False, min_periods=1).mean()
    df_calc['MACD'] = ema12 - ema26
    df_calc['MACD_Signal'] = df_calc['MACD'].ewm(span=9, adjust=False, min_periods=1).mean()
    df_calc['MACD_Histogram'] = df_calc['MACD'] - df_calc['MACD_Signal']
    
    # חישוב Bollinger Bands
    df_calc['BB_Mid'] = df_calc['Close'].rolling(window=20, min_periods=1).mean()
    df_calc['BB_Std'] = df_calc['Close'].rolling(window=20, min_periods=1).std()
    df_calc['BB_Upper'] = df_calc['BB_Mid'] + (2 * df_calc['BB_Std'])
    df_calc['BB_Lower'] = df_calc['BB_Mid'] - (2 * df_calc['BB_Std'])
    df_calc['BB_Width'] = (df_calc['BB_Upper'] - df_calc['BB_Lower']) / df_calc['BB_Mid']
    
    # חישוב ממוצעים נעים מעריכיים נוספים
    df_calc['EMA_20'] = df_calc['Close'].ewm(span=20, adjust=False, min_periods=1).mean()
    df_calc['EMA_50'] = df_calc['Close'].ewm(span=50, adjust=False, min_periods=1).mean()
    
    return df_calc, periods


def calculate_final_score(row, periods):
    """
    מחשב ציון טכני כולל
    """
    score = 50  # ציון התחלתי ניטרלי
    
    try:
        # RSI - 30 נקודות
        if 'RSI' in row and not pd.isna(row['RSI']):
            if row['RSI'] < 30:
                score += 15  # מכירת יתר - הזדמנות קנייה
            elif row['RSI'] > 70:
                score -= 15  # קניית יתר - הזדמנות מכירה
        
        # MACD - 30 נקודות
        if 'MACD' in row and 'MACD_Signal' in row:
            if not pd.isna(row['MACD']) and not pd.isna(row['MACD_Signal']):
                if row['MACD'] > row['MACD_Signal']:
                    score += 15  # MACD מעל סיגנל - מגמה חיובית
                else:
                    score -= 15  # MACD מתחת לסיגנל - מגמה שלילית
        
        # מגמה - 20 נקודות (מחיר vs SMA ארוך טווח)
        long_ma = periods[-1]
        sma_key = f'SMA_{long_ma}'
        if sma_key in row and 'Close' in row:
            if not pd.isna(row[sma_key]) and not pd.isna(row['Close']):
                if row['Close'] > row[sma_key]:
                    score += 10  # מחיר מעל SMA - מגמה עולה
                else:
                    score -= 10  # מחיר מתחת ל-SMA - מגמה יורדת
        
        # Bollinger Bands - 10 נקודות
        if 'Close' in row and 'BB_Upper' in row and 'BB_Lower' in row:
            if not pd.isna(row['Close']) and not pd.isna(row['BB_Upper']) and not pd.isna(row['BB_Lower']):
                if row['Close'] < row['BB_Lower']:
                    score += 5  # מחיר מתחת לרצועה תחתונה - הזדמנות קנייה
                elif row['Close'] > row['BB_Upper']:
                    score -= 5  # מחיר מעל רצועה עליונה - יתר קנייה
        
    except (KeyError, TypeError):
        pass
    
    # הגבלת הציון לטווח 0-100
    score = max(0, min(100, score))
    
    # קביעת המלצה וצבע לפי הציון
    if score >= 80:
        return score, "קנייה חזקה 🚀", "green"
    elif score >= 60:
        return score, "קנייה ✅", "#90ee90"
    elif score <= 20:
        return score, "מכירה חזקה 📉", "red"
    elif score <= 40:
        return score, "מכירה 🔻", "orange"
    else:
        return score, "נייטרלי ✋", "gray"


def get_smart_analysis(df, periods):
    """
    מחזיר רשימה של פרשנויות טכניות חכמות
    """
    analysis = []
    
    if df.empty:
        return ["אין מספיק נתונים לניתוח"]
    
    last = df.iloc[-1]
    
    # ניתוח RSI
    if 'RSI' in last and not pd.isna(last['RSI']):
        rsi_val = last['RSI']
        if rsi_val > 70:
            analysis.append(f"🔴 **RSI ({rsi_val:.1f}):** קניית יתר. המחיר 'מתוח' מדי וייתכן תיקון.")
        elif rsi_val < 30:
            analysis.append(f"🟢 **RSI ({rsi_val:.1f}):** מכירת יתר. הזדמנות לכניסה עם פוטנציאל לעלייה.")
        elif 30 <= rsi_val <= 70:
            analysis.append(f"⚪ **RSI ({rsi_val:.1f}):** בטווח נורמלי. אין איתותי קיצון.")
    
    # ניתוח MACD
    if 'MACD' in last and 'MACD_Signal' in last:
        if not pd.isna(last['MACD']) and not pd.isna(last['MACD_Signal']):
            if last['MACD'] > last['MACD_Signal']:
                analysis.append("🚀 **MACD:** מומנטום חיובי ומתחזק - סימן למגמת עלייה.")
            else:
                analysis.append("📉 **MACD:** המומנטום נחלש - סימן למגמת ירידה או התארגנות.")
    
    # ניתוח מגמה לפי SMA
    if periods:
        long_ma = periods[-1]
        sma_key = f'SMA_{long_ma}'
        if sma_key in last and 'Close' in last:
            if not pd.isna(last[sma_key]) and not pd.isna(last['Close']):
                if last['Close'] > last[sma_key]:
                    analysis.append(f"📈 **מגמה ({long_ma} ימים):** המחיר מעל הממוצע - מגמת עלייה.")
                else:
                    analysis.append(f"📊 **מגמה ({long_ma} ימים):** המחיר מתחת לממוצע - מגמת ירידה.")
    
    # ניתוח Bollinger Bands
    if 'Close' in last and 'BB_Upper' in last and 'BB_Lower' in last:
        if not pd.isna(last['Close']) and not pd.isna(last['BB_Upper']) and not pd.isna(last['BB_Lower']):
            if last['Close'] > last['BB_Upper']:
                analysis.append("⚠️ **בולינגר:** המחיר חורג מהרצועה העליונה - יתר קנייה.")
            elif last['Close'] < last['BB_Lower']:
                analysis.append("💎 **בולינגר:** המחיר חורג מהרצועה התחתונה - הזדמנות קנייה.")
    
    # ניתוח נפח
    if 'Volume' in df.columns and len(df) > 1:
        last_volume = df['Volume'].iloc[-1]
        avg_volume = df['Volume'].iloc[-20:].mean() if len(df) >= 20 else df['Volume'].mean()
        if last_volume > avg_volume * 1.5:
            analysis.append("📦 **נפח:** נפח מסחר גבוה מהממוצע - עניין מוגבר במניה.")
        elif last_volume < avg_volume * 0.5:
            analysis.append("📦 **נפח:** נפח מסחר נמוך מהממוצע - מיעוט עניין.")
    
    # אם אין ניתוחים, נוסיף הודעה כללית
    if not analysis:
        analysis.append("ℹ️ **מידע כללי:** אין איתותים טכניים ברורים. המשך מעקב.")
    
    return analysis


def analyze_fundamentals(info):
    """
    מנתח נתונים פונדמנטליים של מניה
    """
    insights = []
    
    if not info:
        return ["אין נתונים פונדמנטליים זמינים למניה זו."]
    
    try:
        # מכפיל רווח (P/E Ratio)
        pe = info.get('forwardPE', info.get('trailingPE', None))
        if pe:
            if pe < 15:
                insights.append(f"✅ **מכפיל רווח ({pe:.1f}):** המניה זולה ביחס לרווחיה.")
            elif pe > 40:
                insights.append(f"⚠️ **מכפיל רווח ({pe:.1f}):** המניה יקרה - צפייה לצמיחה גבוהה.")
            else:
                insights.append(f"ℹ️ **מכפיל רווח ({pe:.1f}):** תמחור סביר ביחס לשוק.")
        
        # יעד אנליסטים
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        target_price = info.get('targetMeanPrice', info.get('targetMedianPrice', 0))
        
        if current_price and target_price and current_price > 0:
            upside = ((target_price - current_price) / current_price) * 100
            if upside > 15:
                insights.append(f"🎯 **תחזית אנליסטים:** צופים עלייה של {upside:.1f}%.")
            elif upside > 0:
                insights.append(f"📊 **תחזית אנליסטים:** צופים עלייה מתונה של {upside:.1f}%.")
            elif upside < -10:
                insights.append(f"🔻 **תחזית אנליסטים:** המחיר גבוה ב-{abs(upside):.1f}% ממחיר היעד.")
        
        # רווחיות
        margins = info.get('profitMargins', 0)
        if margins:
            if margins > 0.2:
                insights.append(f"💎 **רווחיות:** החברה רווחית מאוד ({margins*100:.1f}%).")
            elif margins > 0.1:
                insights.append(f"👍 **רווחיות:** החברה רווחית ({margins*100:.1f}%).")
            elif margins < 0:
                insights.append(f"⚠️ **סיכון:** החברה מפסידה כסף כרגע.")
        
        # דיבידנד
        dividend_yield = info.get('dividendYield', 0)
        if dividend_yield and dividend_yield > 0:
            insights.append(f"💰 **דיבידנד:** תשואת דיבידנד של {dividend_yield*100:.2f}%.")
        
        # צמיחה
        revenue_growth = info.get('revenueGrowth', None)
        if revenue_growth:
            if revenue_growth > 0.2:
                insights.append(f"📈 **צמיחה:** צמיחת הכנסות גבוהה ({revenue_growth*100:.1f}%).")
            elif revenue_growth < 0:
                insights.append(f"📉 **צמיחה:** ירידה בהכנסות ({revenue_growth*100:.1f}%).")
    
    except Exception as e:
        insights.append(f"⚠️ **שגיאה בניתוח פונדמנטלי:** {str(e)}")
    
    # אם אין תובנות, נוסיף הודעה כללית
    if not insights:
        insights.append("ℹ️ **מידע פונדמנטלי:** אין מספיק נתונים לניתוח מעמיק.")
    
    return insights


# ---------- פונקציות יצוא ----------
def to_excel(df):
    """
    ממיר DataFrame לקובץ Excel
    """
    buffer = io.BytesIO()
    
    # יצירת Excel writer
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Portfolio')
    
    buffer.seek(0)
    return buffer


# ----------------------------------------------------------------------
# 3️⃣ הגדרות sidebar
# ----------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3124/3124975.png", width=100)
    st.title("⚙️ הגדרות")
    
    # בחירת סוג ממוצע נע
    ma_type = st.selectbox(
        "סוג ניתוח טכני",
        ["ממוצעים קצרי טווח (9, 20, 50)", "ממוצעים ארוכי טווח (100, 150, 200)"],
        help="בחר את סוגי הממוצעים הנעים שיוצגו בגרף"
    )
    
    # הגדרת נראות אינדיקטורים
    st.markdown("### 📊 אינדיקטורים")
    show_rsi = st.checkbox("הצג RSI", value=True)
    show_macd = st.checkbox("הצג MACD", value=True)
    show_bb = st.checkbox("הצג Bollinger Bands", value=True)
    
    # ערכי ברירת מחדל
    st.markdown("---")
    st.markdown("### 📌 עזרה")
    st.info("""
    **טיפים:**
    1. הזן סימול מנייה באנגלית (AAPL, TSLA, GOOGL)
    2. לחץ 'הוסף פוזיציה' לשמירת עסקאות
    3. הורד דו"ח בפורמט CSV/Excel
    """)
    
    # ניקוי נתונים
    if st.button("🧹 נקה כל הנתונים", type="secondary"):
        st.session_state.clear()
        st.success("✅ כל הנתונים נוקו!")
        st.rerun()

# ----------------------------------------------------------------------
# 4️⃣ ניהול Session State
# ----------------------------------------------------------------------
if "trades" not in st.session_state:
    st.session_state.trades = {}
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(
        columns=["Ticker", "EntryPrice", "Shares", "Date", "TradeID"]
    )

def add_trade(ticker: str, price: float, shares: int = 1):
    """הוספת פוזיציה חדשה"""
    trade_id = uuid.uuid4().hex[:8]
    now = datetime.now()
    
    # שמירה ב-trades dictionary
    st.session_state.trades[trade_id] = {
        "Ticker": ticker,
        "Price": round(price, 2),
        "Shares": shares,
        "Date": now.strftime("%Y-%m-%d %H:%M"),
        "TradeID": trade_id
    }
    
    # עדכון Portfolio DataFrame
    new_row = {
        "Ticker": ticker,
        "EntryPrice": round(price, 2),
        "Shares": shares,
        "Date": now,
        "TradeID": trade_id
    }
    st.session_state.portfolio = pd.concat(
        [st.session_state.portfolio, pd.DataFrame([new_row])],
        ignore_index=True,
    )

def delete_trade(trade_id: str):
    """מחיקת פוזיציה"""
    if trade_id in st.session_state.trades:
        # שמור את הטיקר לפני מחיקה
        ticker = st.session_state.trades[trade_id]["Ticker"]
        del st.session_state.trades[trade_id]
        
        # מחיקת שורה מ-Portfolio
        st.session_state.portfolio = st.session_state.portfolio[
            st.session_state.portfolio["TradeID"] != trade_id
        ]
        return True
    return False

# ----------------------------------------------------------------------
# 5️⃣ UI – כותרת ראשית
# ----------------------------------------------------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("https://cdn-icons-png.flaticon.com/512/3124/3124975.png", width=80)
    st.title("📈 התיק החכם")
    st.caption("כלים לניתוח, מעקב ו-journaling של מניות – בעברית")

# ----------------------------------------------------------------------
# 6️⃣ הזנת סימול מנייה
# ----------------------------------------------------------------------
col_left, col_center, col_right = st.columns([1, 3, 1])
with col_center:
    ticker_input = st.text_input(
        "הזן סימול מנייה (למשל TSLA, AAPL, GOOGL)",
        value="AAPL",
        help="יש להזין סימול באנגלית. דוגמאות: TSLA, AAPL, MSFT, GOOGL"
    ).upper().strip()

# ----------------------------------------------------------------------
# 7️⃣ טעינת נתונים וניתוח
# ----------------------------------------------------------------------
if ticker_input:
    with st.spinner(f"📥 מוריד נתונים עבור {ticker_input}..."):
        df_price, stock_info, full_name = load_stock_data(ticker_input)
    
    if df_price is None or df_price.empty:
        st.error(f"❌ לא נמצאו נתונים עבור **{ticker_input}**. בדוק שהסימול תקין.")
        
        # הצעה לסימולים נפוצים
        st.info("""
        **טיפ:** נסה אחד מהסימולים הבאים:
        - AAPL (אפל)
        - TSLA (טסלה) 
        - GOOGL (גוגל)
        - MSFT (מיקרוסופט)
        - AMZN (אמזון)
        - META (מטא)
        - NVDA (אנווידיה)
        """)
        st.stop()
    
    # כותרת עם שם החברה
    company_name = full_name if full_name != ticker_input else ticker_input
    st.subheader(f"🔍 ניתוח מניית **{company_name}** ({ticker_input})")
    
    # יצירת טאבים
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 ניתוח טכני", "🏢 נתונים פונדמנטליים", "💼 ניהול פורטפוליו", "📓 יומן פוזיציות"]
    )
    
    # --------------------------------------------------------------
    # טאב 1: ניתוח טכני
    # --------------------------------------------------------------
    with tab1:
        # חישוב אינדיקטורים
        try:
            df_with_indicators, periods = calculate_all_indicators(df_price.copy(), ma_type)
        except Exception as e:
            st.error(f"❌ שגיאה בחישוב אינדיקטורים: {e}")
            st.info("נסה להזין סימול מנייה שונה")
            st.stop()
        
        # גרף מחיר עם ממוצעים נעים
        fig_price = go.Figure()
        
        # הוספת קו מחיר
        fig_price.add_trace(go.Scatter(
            x=df_with_indicators.index,
            y=df_with_indicators["Close"],
            name="מחיר סגור",
            mode="lines",
            line=dict(color="#0066CC", width=2)
        ))
        
        # הוספת ממוצעים נעים
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        for idx, period in enumerate(periods):
            fig_price.add_trace(go.Scatter(
                x=df_with_indicators.index,
                y=df_with_indicators[f'SMA_{period}'],
                name=f'SMA {period}',
                mode="lines",
                line=dict(color=colors[idx % len(colors)], width=1.5, dash='dash')
            ))
        
        # Bollinger Bands אם נבחר
        if show_bb and 'BB_Upper' in df_with_indicators.columns:
            fig_price.add_trace(go.Scatter(
                x=df_with_indicators.index,
                y=df_with_indicators['BB_Upper'],
                name='Bollinger Upper',
                line=dict(color='rgba(255, 107, 107, 0.5)', width=1),
                showlegend=False
            ))
            fig_price.add_trace(go.Scatter(
                x=df_with_indicators.index,
                y=df_with_indicators['BB_Lower'],
                name='Bollinger Lower',
                line=dict(color='rgba(255, 107, 107, 0.5)', width=1),
                fill='tonexty',
                fillcolor='rgba(255, 107, 107, 0.1)',
                showlegend=False
            ))
        
        # עדכון עיצוב גרף
        fig_price.update_layout(
            height=500,
            title="גרף מחירים עם ממוצעים נעים",
            xaxis_title="תאריך",
            yaxis_title="מחיר (USD)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_white",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_price, use_container_width=True)
        
        # תצוגת אינדיקטורים נוספים בעמודות
        col_ind1, col_ind2, col_ind3 = st.columns(3)
        
        with col_ind1:
            if show_rsi and 'RSI' in df_with_indicators.columns:
                st.markdown("### 📊 RSI")
                last_rsi = df_with_indicators['RSI'].iloc[-1]
                rsi_color = "red" if last_rsi > 70 else "green" if last_rsi < 30 else "gray"
                st.markdown(f"<h2 style='color: {rsi_color}; text-align: center;'>{last_rsi:.1f}</h2>", unsafe_allow_html=True)
                st.progress(min(max(last_rsi / 100, 0), 1))
                if last_rsi > 70:
                    st.warning("🚨 קניית יתר")
                elif last_rsi < 30:
                    st.success("✅ מכירת יתר - הזדמנות")
                else:
                    st.info("⚖️ בטווח נורמלי")
        
        with col_ind2:
            if show_macd and 'MACD' in df_with_indicators.columns:
                st.markdown("### 📈 MACD")
                last_macd = df_with_indicators['MACD'].iloc[-1]
                last_signal = df_with_indicators['MACD_Signal'].iloc[-1]
                st.metric("MACD", f"{last_macd:.4f}", 
                         f"{(last_macd - last_signal):.4f} מהסיגנל")
                if last_macd > last_signal:
                    st.success("📈 מגמה חיובית")
                else:
                    st.error("📉 מגמה שלילית")
        
        with col_ind3:
            # חישוב ציון טכני
            last_row = df_with_indicators.iloc[-1]
            score, recommendation, color = calculate_final_score(last_row, periods)
            st.markdown("### ⭐ ציון טכני")
            st.markdown(f"<h1 style='color: {color}; text-align: center;'>{score}/100</h1>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='color: {color}; text-align: center;'>{recommendation}</h3>", unsafe_allow_html=True)
        
        # פרשנות חכמה
        st.markdown("### 🧠 פרשנות טכנית")
        analysis = get_smart_analysis(df_with_indicators, periods)
        for item in analysis:
            st.markdown(f"- {item}")
        
        # גרף נפח
        st.markdown("### 📦 נפח מסחר")
        fig_volume = go.Figure()
        fig_volume.add_trace(go.Bar(
            x=df_price.index,
            y=df_price['Volume'],
            name="נפח",
            marker_color='#A0C3D2'
        ))
        fig_volume.update_layout(
            height=300,
            xaxis_title="תאריך",
            yaxis_title="נפח",
            template="plotly_white"
        )
        st.plotly_chart(fig_volume, use_container_width=True)
    
    # --------------------------------------------------------------
    # טאב 2: נתונים פונדמנטליים
    # --------------------------------------------------------------
    with tab2:
        if stock_info:
            col_info1, col_info2 = st.columns([2, 1])
            
            with col_info1:
                st.markdown("### 🏢 פרטי החברה")
                info_data = {
                    "שם החברה": stock_info.get('longName', 'לא זמין'),
                    "ענף": stock_info.get('industry', 'לא זמין'),
                    "סקטור": stock_info.get('sector', 'לא זמין'),
                    "שוק": stock_info.get('exchange', 'לא זמין'),
                    "מדינה": stock_info.get('country', 'לא זמין'),
                    "מטבע": stock_info.get('currency', 'USD'),
                    "אתר": stock_info.get('website', 'לא זמין')
                }
                
                for key, value in info_data.items():
                    st.markdown(f"**{key}:** {value}")
                
                st.markdown("---")
                st.markdown("### 📖 תיאור החברה")
                business_summary = stock_info.get('longBusinessSummary', 'אין תיאור זמין.')
                st.write(business_summary[:500] + "..." if len(business_summary) > 500 else business_summary)
            
            with col_info2:
                st.markdown("### 💰 מדדים פיננסיים")
                
                current_price = df_price['Close'].iloc[-1]
                previous_close = df_price['Close'].iloc[-2] if len(df_price) > 1 else current_price
                daily_change = ((current_price - previous_close) / previous_close) * 100
                
                st.metric("מחיר נוכחי", f"${current_price:.2f}")
                st.metric("שינוי יומי", f"{daily_change:+.2f}%")
                st.metric("מחיר פתיחה", f"${df_price['Open'].iloc[-1]:.2f}")
                st.metric("גבוה יומי", f"${df_price['High'].iloc[-1]:.2f}")
                st.metric("נמוך יומי", f"${df_price['Low'].iloc[-1]:.2f}")
            
            # פרשנות פונדמנטלית
            st.markdown("### 🎯 ניתוח פונדמנטלי")
            fundamental_insights = analyze_fundamentals(stock_info)
            for insight in fundamental_insights:
                st.markdown(f"- {insight}")
        
        else:
            st.warning("⚠️ לא הצלחנו לקבל מידע פונדמנטלי מלא. הגרף הטכני עדיין זמין.")
    
    # --------------------------------------------------------------
    # טאב 3: ניהול פורטפוליו
    # --------------------------------------------------------------
    with tab3:
        st.markdown("### 🛒 הוספת פוזיציה חדשה")
        
        col_price, col_shares, col_action
