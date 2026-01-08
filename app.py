# -*- coding: utf-8 -*-
"""
Streamlit – "התיק החכם" - ניתוח מניות וניהול תיק בעברית
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
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        background-size: cover;
        background-attachment: fixed;
    }
    .main .block-container {
        background-color: rgba(255,255,255,0.95);
        padding: 2rem;
        border-radius: 15px;
        margin-top: 1rem;
        direction: rtl;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1 {
        color: #3498db;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 16px;
        font-weight: 600;
    }
    div.stButton > button {
        width: 100%;
        background: linear-gradient(45deg, #3498db 0%, #2ecc71 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background: linear-gradient(45deg, #2980b9 0%, #27ae60 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
    }
    .stTextInput input {
        text-align: center;
        border-radius: 8px;
        border: 2px solid #3498db;
        padding: 10px;
        font-size: 1rem;
    }
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 2px solid #3498db;
    }
    .stMetric {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #3498db;
        margin-bottom: 10px;
    }
    .info-box {
        background-color: #e8f4fd;
        border: 1px solid #b6e0fe;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
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
    .stock-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 3px 10px rgba(0,0,0,0.08);
        border: 1px solid #eaeaea;
    }
    .company-info {
        background: #f8fafc;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        border-right: 5px solid #3498db;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# 2️⃣ פונקציות ליבה
# ----------------------------------------------------------------------

# ---------- פונקציות לטעינת נתונים ----------
@st.cache_data(ttl=3600)
def load_stock_data(ticker):
    """
    טוען נתוני מניות מ-yfinance
    """
    try:
        df = yf.download(
            ticker, 
            period="1y", 
            auto_adjust=True, 
            progress=False,
            timeout=10
        )
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        if df.empty or len(df) < 5:
            return None, None, ticker
        
        info = {}
        full_name = ticker
        
        try:
            t_obj = yf.Ticker(ticker)
            info = t_obj.info
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
    df_calc = df.copy()
    
    if isinstance(df_calc.columns, pd.MultiIndex):
        df_calc.columns = df_calc.columns.get_level_values(0)
    df_calc = df_calc.loc[:, ~df_calc.columns.duplicated()]
    
    if 'Close' not in df_calc.columns:
        return df_calc, []
    
    if "קצר" in ma_type:
        periods = [9, 20, 50]
    else:
        periods = [100, 150, 200]
    
    for p in periods:
        df_calc[f'SMA_{p}'] = df_calc['Close'].rolling(window=p, min_periods=1).mean()
    
    # חישוב RSI
    delta = df_calc['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14, min_periods=1).mean()
    avg_loss = loss.rolling(window=14, min_periods=1).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df_calc['RSI'] = 100 - (100 / (1 + rs))
    df_calc['RSI'] = df_calc['RSI'].clip(0, 100).fillna(50)
    
    # חישוב MACD
    ema12 = df_calc['Close'].ewm(span=12, adjust=False, min_periods=1).mean()
    ema26 = df_calc['Close'].ewm(span=26, adjust=False, min_periods=1).mean()
    df_calc['MACD'] = ema12 - ema26
    df_calc['MACD_Signal'] = df_calc['MACD'].ewm(span=9, adjust=False, min_periods=1).mean()
    
    # חישוב Bollinger Bands
    df_calc['BB_Mid'] = df_calc['Close'].rolling(window=20, min_periods=1).mean()
    df_calc['BB_Std'] = df_calc['Close'].rolling(window=20, min_periods=1).std()
    df_calc['BB_Upper'] = df_calc['BB_Mid'] + (2 * df_calc['BB_Std'])
    df_calc['BB_Lower'] = df_calc['BB_Mid'] - (2 * df_calc['BB_Std'])
    
    return df_calc, periods

def calculate_final_score(row, periods):
    """
    מחשב ציון טכני כולל
    """
    score = 50
    
    try:
        if 'RSI' in row and not pd.isna(row['RSI']):
            if row['RSI'] < 30:
                score += 15
            elif row['RSI'] > 70:
                score -= 15
        
        if 'MACD' in row and 'MACD_Signal' in row:
            if not pd.isna(row['MACD']) and not pd.isna(row['MACD_Signal']):
                if row['MACD'] > row['MACD_Signal']:
                    score += 15
                else:
                    score -= 15
        
        if periods:
            long_ma = periods[-1]
            sma_key = f'SMA_{long_ma}'
            if sma_key in row and 'Close' in row:
                if not pd.isna(row[sma_key]) and not pd.isna(row['Close']):
                    if row['Close'] > row[sma_key]:
                        score += 10
                    else:
                        score -= 10
        
        if 'Close' in row and 'BB_Upper' in row and 'BB_Lower' in row:
            if not pd.isna(row['Close']) and not pd.isna(row['BB_Upper']) and not pd.isna(row['BB_Lower']):
                if row['Close'] < row['BB_Lower']:
                    score += 5
                elif row['Close'] > row['BB_Upper']:
                    score -= 5
        
    except (KeyError, TypeError):
        pass
    
    score = max(0, min(100, score))
    
    if score >= 80:
        return score, "קנייה חזקה 🚀", "#27ae60"
    elif score >= 60:
        return score, "קנייה ✅", "#2ecc71"
    elif score <= 20:
        return score, "מכירה חזקה 📉", "#e74c3c"
    elif score <= 40:
        return score, "מכירה 🔻", "#e67e22"
    else:
        return score, "נייטרלי ✋", "#95a5a6"

def get_smart_analysis(df, periods):
    """
    מחזיר רשימה של פרשנויות טכניות חכמות
    """
    analysis = []
    
    if df.empty:
        return ["אין מספיק נתונים לניתוח"]
    
    last = df.iloc[-1]
    
    if 'RSI' in last and not pd.isna(last['RSI']):
        rsi_val = last['RSI']
        if rsi_val > 70:
            analysis.append(f"🔴 **מדד חוזק יחסי ({rsi_val:.1f}):** קניית יתר. המחיר גבוה מדי וייתכן תיקון.")
        elif rsi_val < 30:
            analysis.append(f"🟢 **מדד חוזק יחסי ({rsi_val:.1f}):** מכירת יתר. הזדמנות לכניסה.")
    
    if 'MACD' in last and 'MACD_Signal' in last:
        if not pd.isna(last['MACD']) and not pd.isna(last['MACD_Signal']):
            if last['MACD'] > last['MACD_Signal']:
                analysis.append("🚀 **מדד התבדלות ממוצעים נעים:** מומנטום חיובי - מגמת עלייה.")
            else:
                analysis.append("📉 **מדד התבדלות ממוצעים נעים:** מומנטום שלילי - מגמת ירידה.")
    
    if periods:
        long_ma = periods[-1]
        sma_key = f'SMA_{long_ma}'
        if sma_key in last and 'Close' in last:
            if not pd.isna(last[sma_key]) and not pd.isna(last['Close']):
                if last['Close'] > last[sma_key]:
                    analysis.append(f"📈 **מגמה ארוכה ({long_ma} ימים):** המחיר מעל הממוצע - עלייה.")
                else:
                    analysis.append(f"📊 **מגמה ארוכה ({long_ma} ימים):** המחיר מתחת לממוצע - ירידה.")
    
    if 'Close' in last and 'BB_Upper' in last and 'BB_Lower' in last:
        if not pd.isna(last['Close']) and not pd.isna(last['BB_Upper']) and not pd.isna(last['BB_Lower']):
            if last['Close'] > last['BB_Upper']:
                analysis.append("⚠️ **רצועות בולינגר:** המחיר חורג מהרצועה העליונה - קניית יתר.")
            elif last['Close'] < last['BB_Lower']:
                analysis.append("💎 **רצועות בולינגר:** המחיר חורג מהרצועה התחתונה - הזדמנות קנייה.")
    
    if not analysis:
        analysis.append("ℹ️ **מידע כללי:** אין איתותים טכניים ברורים. המשך מעקב.")
    
    return analysis

# ---------- פונקציות ניתוח פונדמנטלי ----------
def translate_field(field_name):
    """
    מתרגם שדות מאנגלית לעברית
    """
    translations = {
        'longName': 'שם החברה',
        'industry': 'תחום עיסוק',
        'sector': 'סקטור',
        'exchange': 'בורסה',
        'country': 'מדינה',
        'currency': 'מטבע',
        'website': 'אתר אינטרנט',
        'marketCap': 'שווי שוק',
        'forwardPE': 'מכפיל רווח צפוי',
        'trailingPE': 'מכפיל רווח',
        'dividendYield': 'תשואת דיבידנד',
        'profitMargins': 'שולי רווח',
        'revenueGrowth': 'צמיחת הכנסות',
        'currentPrice': 'מחיר נוכחי',
        'targetMeanPrice': 'מחיר יעד ממוצע',
        'recommendationKey': 'המלצת אנליסטים',
        'fiftyTwoWeekHigh': 'שיא 52 שבועות',
        'fiftyTwoWeekLow': 'שפל 52 שבועות',
        'volume': 'נפח מסחר',
        'averageVolume': 'נפח ממוצע',
        'beta': 'בטא (תנודתיות)',
        'debtToEquity': 'יחס חוב להון'
    }
    return translations.get(field_name, field_name)

def analyze_fundamentals(info):
    """
    מנתח נתונים פונדמנטליים של מניה
    """
    insights = []
    
    if not info:
        return ["אין נתונים פונדמנטליים זמינים למניה זו."]
    
    try:
        pe = info.get('forwardPE', info.get('trailingPE', None))
        if pe:
            if pe < 15:
                insights.append(f"✅ **מכפיל רווח ({pe:.1f}):** המניה זולה יחסית לרווחיה.")
            elif pe > 40:
                insights.append(f"⚠️ **מכפיל רווח ({pe:.1f}):** המניה יקרה - מצפים לצמיחה גבוהה.")
            else:
                insights.append(f"ℹ️ **מכפיל רווח ({pe:.1f}):** תמחור סביר.")
        
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
        
        margins = info.get('profitMargins', 0)
        if margins:
            if margins > 0.2:
                insights.append(f"💎 **רווחיות:** החברה רווחית מאוד ({margins*100:.1f}%).")
            elif margins > 0.1:
                insights.append(f"👍 **רווחיות:** החברה רווחית ({margins*100:.1f}%).")
            elif margins < 0:
                insights.append(f"⚠️ **סיכון:** החברה מפסידה כסף.")
        
        dividend_yield = info.get('dividendYield', 0)
        if dividend_yield and dividend_yield > 0:
            insights.append(f"💰 **דיבידנד:** תשואת דיבידנד של {dividend_yield*100:.2f}%.")
        
        revenue_growth = info.get('revenueGrowth', None)
        if revenue_growth:
            if revenue_growth > 0.2:
                insights.append(f"📈 **צמיחה:** צמיחת הכנסות גבוהה ({revenue_growth*100:.1f}%).")
            elif revenue_growth < 0:
                insights.append(f"📉 **צמיחה:** ירידה בהכנסות ({revenue_growth*100:.1f}%).")
    
    except Exception as e:
        insights.append(f"⚠️ **שגיאה בניתוח פונדמנטלי:** {str(e)}")
    
    if not insights:
        insights.append("ℹ️ **מידע פונדמנטלי:** אין מספיק נתונים לניתוח מעמיק.")
    
    return insights

# ---------- פונקציות יצוא ----------
def to_excel(df):
    """
    ממיר DataFrame לקובץ Excel
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Portfolio')
    buffer.seek(0)
    return buffer

# ----------------------------------------------------------------------
# 3️⃣ הגדרות sidebar
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/3124/3124975.png", width=100)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.title("⚙️ הגדרות מערכת")
    
    st.markdown("### 📈 סוג ניתוח")
    ma_type = st.selectbox(
        "בחר סוג ממוצעים נעים",
        ["ממוצעים קצרי טווח (9, 20, 50)", "ממוצעים ארוכי טווח (100, 150, 200)"],
        help="ממוצעים קצרים טובים לסחר יומי, ארוכים טובים להשקעה ארוכה"
    )
    
    st.markdown("### 📊 אינדיקטורים טכניים")
    show_rsi = st.checkbox("הצג מדד חוזק יחסי (RSI)", value=True)
    show_macd = st.checkbox("הצג מדד התבדלות ממוצעים (MACD)", value=True)
    show_bb = st.checkbox("הצג רצועות בולינגר", value=True)
    
    st.markdown("---")
    
    st.markdown("### 🆘 עזרה ומידע")
    with st.expander("📖 מדריך מהיר"):
        st.info("""
        1. **הזן סימול מנייה** בשדה למעלה (לדוגמה: AAPL, TSLA)
        2. **בצע ניתוח** בטאבים השונים
        3. **הוסף פוזיציות** לניהול תיק ההשקעות שלך
        4. **הורד דו"חות** בפורמט CSV או Excel
        """)
    
    if st.button("🧹 נקה נתונים", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
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
    
    st.session_state.trades[trade_id] = {
        "Ticker": ticker,
        "Price": round(price, 2),
        "Shares": shares,
        "Date": now.strftime("%Y-%m-%d %H:%M"),
        "TradeID": trade_id
    }
    
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
        del st.session_state.trades[trade_id]
        st.session_state.portfolio = st.session_state.portfolio[
            st.session_state.portfolio["TradeID"] != trade_id
        ]
        return True
    return False

# ----------------------------------------------------------------------
# 5️⃣ כותרת ראשית
# ----------------------------------------------------------------------
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.markdown("## 📈 **התיק החכם**")
st.markdown("### *ניהול תיק מניות וניתוח טכני בעברית*")
st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# 6️⃣ הזנת סימול מנייה
# ----------------------------------------------------------------------
st.markdown("---")
col_input1, col_input2, col_input3 = st.columns([1, 3, 1])
with col_input2:
    ticker_input = st.text_input(
        "**הזן סימול מנייה (לדוגמה: AAPL, TSLA, GOOGL)**",
        value="AAPL",
        help="יש להזין סימול מנייה באנגלית בלבד"
    ).upper().strip()

# ----------------------------------------------------------------------
# 7️⃣ טעינת נתונים וניתוח
# ----------------------------------------------------------------------
if ticker_input:
    with st.spinner(f"📥 טוען נתונים עבור {ticker_input}..."):
        df_price, stock_info, full_name = load_stock_data(ticker_input)
    
    if df_price is None or df_price.empty:
        st.error(f"❌ לא נמצאו נתונים עבור **{ticker_input}**. בדוק שהסימול תקין.")
        st.info("""
        **טיפ:** נסה אחד מהסימולים הבאים:
        - AAPL (אפל)
        - TSLA (טסלה) 
        - GOOGL (גוגל)
        - MSFT (מיקרוסופט)
        - AMZN (אמזון)
        """)
        st.stop()
    
    company_name = full_name if full_name != ticker_input else ticker_input
    st.markdown(f"<h2 style='text-align: center; color: #2c3e50;'>🔍 ניתוח מניית <b>{company_name}</b> ({ticker_input})</h2>", unsafe_allow_html=True)
    
    # יצירת טאבים
    tab_names = ["📊 ניתוח טכני", "🏢 נתוני חברה", "💼 הוספת פוזיציה", "📓 פוזיציות שלי"]
    tab1, tab2, tab3, tab4 = st.tabs(tab_names)
    
    # ==============================================================
    # טאב 1: ניתוח טכני
    # ==============================================================
    with tab1:
        try:
            df_with_indicators, periods = calculate_all_indicators(df_price.copy(), ma_type)
            
            # גרף מחיר עם ממוצעים נעים
            fig_price = go.Figure()
            
            fig_price.add_trace(go.Scatter(
                x=df_with_indicators.index,
                y=df_with_indicators["Close"],
                name="מחיר סגור",
                mode="lines",
                line=dict(color="#3498db", width=2.5)
            ))
            
            colors = ['#e74c3c', '#2ecc71', '#f39c12']
            for idx, period in enumerate(periods):
                fig_price.add_trace(go.Scatter(
                    x=df_with_indicators.index,
                    y=df_with_indicators[f'SMA_{period}'],
                    name=f'ממוצע נע {period}',
                    mode="lines",
                    line=dict(color=colors[idx % len(colors)], width=1.5, dash='dash')
                ))
            
            if show_bb and 'BB_Upper' in df_with_indicators.columns:
                fig_price.add_trace(go.Scatter(
                    x=df_with_indicators.index,
                    y=df_with_indicators['BB_Upper'],
                    name='רצועה עליונה',
                    line=dict(color='rgba(231, 76, 60, 0.4)', width=1),
                    showlegend=False
                ))
                fig_price.add_trace(go.Scatter(
                    x=df_with_indicators.index,
                    y=df_with_indicators['BB_Lower'],
                    name='רצועה תחתונה',
                    line=dict(color='rgba(231, 76, 60, 0.4)', width=1),
                    fill='tonexty',
                    fillcolor='rgba(231, 76, 60, 0.1)',
                    showlegend=False
                ))
            
            fig_price.update_layout(
                height=500,
                title="גרף מחירים עם אינדיקטורים טכניים",
                xaxis_title="תאריך",
                yaxis_title="מחיר (USD)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                template="plotly_white",
                hovermode='x unified',
                font=dict(family="Arial, sans-serif", size=12)
            )
            
            st.plotly_chart(fig_price, use_container_width=True)
            
            # תצוגת אינדיקטורים
            col_ind1, col_ind2, col_ind3 = st.columns(3)
            
            with col_ind1:
                if show_rsi and 'RSI' in df_with_indicators.columns:
                    st.markdown("### 📊 מדד חוזק יחסי")
                    last_rsi = df_with_indicators['RSI'].iloc[-1]
                    rsi_color = "#e74c3c" if last_rsi > 70 else "#27ae60" if last_rsi < 30 else "#3498db"
                    st.markdown(f"<h1 style='color: {rsi_color}; text-align: center;'>{last_rsi:.1f}</h1>", unsafe_allow_html=True)
                    st.progress(min(max(last_rsi / 100, 0), 1))
                    if last_rsi > 70:
                        st.warning("🚨 קניית יתר - שקול מכירה")
                    elif last_rsi < 30:
                        st.success("✅ מכירת יתר - הזדמנות קנייה")
                    else:
                        st.info("⚖️ בטווח נורמלי")
            
            with col_ind2:
                if show_macd and 'MACD' in df_with_indicators.columns:
                    st.markdown("### 📈 מדד התבדלות ממוצעים")
                    last_macd = df_with_indicators['MACD'].iloc[-1]
                    last_signal = df_with_indicators['MACD_Signal'].iloc[-1]
                    diff = last_macd - last_signal
                    st.metric("ערך נוכחי", f"{last_macd:.4f}", 
                             f"{diff:+.4f} מהסיגנל")
                    if last_macd > last_signal:
                        st.success("📈 מגמה חיובית")
                    else:
                        st.error("📉 מגמה שלילית")
            
            with col_ind3:
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
                marker_color='#3498db',
                opacity=0.7
            ))
            fig_volume.update_layout(
                height=300,
                xaxis_title="תאריך",
                yaxis_title="נפח מסחר",
                template="plotly_white"
            )
            st.plotly_chart(fig_volume, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ שגיאה בניתוח טכני: {str(e)}")
    
    # ==============================================================
    # טאב 2: נתוני חברה
    # ==============================================================
    with tab2:
        if stock_info:
            col_info1, col_info2 = st.columns([2, 1])
            
            with col_info1:
                st.markdown("### 🏢 פרטי החברה")
                
                company_details = {
                    'שם החברה': stock_info.get('longName', 'לא זמין'),
                    'תחום עיסוק': stock_info.get('industry', 'לא זמין'),
                    'סקטור': stock_info.get('sector', 'לא זמין'),
                    'בורסה': stock_info.get('exchange', 'לא זמין'),
                    'מדינה': stock_info.get('country', 'לא זמין'),
                    'מטבע': stock_info.get('currency', 'USD'),
                    'אתר אינטרנט': stock_info.get('website', 'לא זמין')
                }
                
                for key, value in company_details.items():
                    if value != 'לא זמין':
                        st.markdown(f"**{key}:** {value}")
                
                st.markdown("---")
                st.markdown("### 📖 תיאור החברה")
                business_summary = stock_info.get('longBusinessSummary', 'אין תיאור זמין.')
                if business_summary:
                    if len(business_summary) > 500:
                        st.write(business_summary[:500] + "...")
                    else:
                        st.write(business_summary)
                else:
                    st.info("אין תיאור חברה זמין")
            
            with col_info2:
                st.markdown("### 📊 נתונים שוטפים")
                
                current_price = df_price['Close'].iloc[-1] if len(df_price) > 0 else 0
                previous_close = df_price['Close'].iloc[-2] if len(df_price) > 1 else current_price
                daily_change_pct = ((current_price - previous_close) / previous_close * 100) if previous_close > 0 else 0
                
                st.metric("מחיר נוכחי", f"${current_price:.2f}")
                st.metric("שינוי יומי", f"{daily_change_pct:+.2f}%")
                st.metric("מחיר פתיחה", f"${df_price['Open'].iloc[-1]:.2f}" if len(df_price) > 0 else "$0.00")
                st.metric("גבוה יומי", f"${df_price['High'].iloc[-1]:.2f}" if len(df_price) > 0 else "$0.00")
                st.metric("נמוך יומי", f"${df_price['Low'].iloc[-1]:.2f}" if len(df_price) > 0 else "$0.00")
                st.metric("נפח מסחר", f"{df_price['Volume'].iloc[-1]:,}" if len(df_price) > 0 else "0")
            
            # ניתוח פונדמנטלי
            st.markdown("### 🎯 ניתוח פונדמנטלי")
            fundamental_insights = analyze_fundamentals(stock_info)
            for insight in fundamental_insights:
                st.markdown(f"- {insight}")
        
        else:
            st.warning("⚠️ לא הצלחנו לקבל מידע על החברה. נתוני המחיר זמינים בטאב ניתוח טכני.")
    
    # ==============================================================
# טאב 3: הוספת פוזיציה
# ==============================================================
with tab3:
    st.markdown("### 🛒 הוספת פוזיציה חדשה")
    
    col_price, col_shares, col_action = st.columns([2, 2, 1])
    
    with col_price:
        current_price = df_price['Close'].iloc[-1] if len(df_price) > 0 else 0
        price_to_save = st.number_input(
            "מחיר קנייה (USD)",
            min_value=0.0,
            value=round(current_price, 2),
            step=0.01,
            key="buy_price_input"
        )
    
    with col_shares:
        shares_to_save = st.number_input(
            "מספר מניות",
            min_value=1,
            step=1,
            value=100,
            key="shares_input"
        )
    
    with col_action:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button(f"➕ הוסף {ticker_input}", use_container_width=True, key="add_trade_button"):
            if price_to_save > 0 and shares_to_save > 0:
                add_trade(ticker_input, price_to_save, shares_to_save)
                st.success(f"✅ פוזיציה של {ticker_input} נוספה בהצלחה!")
                st.rerun()
            else:
                st.error("❌ אנא הזן ערכים תקינים")
    
    st.markdown("---")
    st.info(f"💡 מחיר נוכחי: **${current_price:.2f}** | שווי פוזיציה מוצע: **${current_price * shares_to_save:,.2f}**")
    
    # תצוגת פוזיציות קיימות של המניה הנוכחית
    current_ticker_trades = {k: v for k, v in st.session_state.trades.items() if v['Ticker'] == ticker_input}
    if current_ticker_trades:
        st.markdown("### 📋 פוזיציות קיימות של מניה זו")
        trades_df = pd.DataFrame.from_dict(current_ticker_trades, orient='index')
        st.dataframe(
            trades_df[['Ticker', 'Price', 'Shares', 'Date']].style.format({
                'Price': '${:,.2f}'
            }),
            use_container_width=True
        )

# ==============================================================
# טאב 4: פוזיציות שלי
# ==============================================================
with tab4:
    st.markdown("### 📓 יומן פוזיציות")
    
    if not st.session_state.trades:
        st.info("📝 עדיין לא הוספת פוזיציות. עבור לטאב 'הוספת פוזיציה' כדי להתחיל.")
    else:
        # יצירת DataFrame מהפוזיציות
        trades_df = pd.DataFrame.from_dict(st.session_state.trades, orient='index')
        
        # חישוב ערכים נוכחיים
        current_values = []
        for _, trade in trades_df.iterrows():
            ticker = trade['Ticker']
            try:
                df_tmp, _, _ = load_stock_data(ticker)
                if df_tmp is not None and not df_tmp.empty:
                    current_price = df_tmp['Close'].iloc[-1]
                    current_value = current_price * trade['Shares']
                    profit_loss = current_value - (trade['Price'] * trade['Shares'])
                    profit_loss_pct = (profit_loss / (trade['Price'] * trade['Shares'])) * 100 if (trade['Price'] * trade['Shares']) > 0 else 0
                    
                    current_values.append({
                        'מחיר נוכחי': current_price,
                        'שווי נוכחי': current_value,
                        'רווח/הפסד ($)': profit_loss,
                        'רווח/הפסד (%)': profit_loss_pct
                    })
                else:
                    current_values.append({
                        'מחיר נוכחי': None,
                        'שווי נוכחי': None,
                        'רווח/הפסד ($)': None,
                        'רווח/הפסד (%)': None
                    })
            except:
                current_values.append({
                    'מחיר נוכחי': None,
                    'שווי נוכחי': None,
                    'רווח/הפסד ($)': None,
                    'רווח/הפסד (%)': None
                })
        
        # הוספת עמודות חדשות
        if current_values:
            current_df = pd.DataFrame(current_values)
            display_df = pd.concat([trades_df, current_df], axis=1)
            
            # הסדר עמודות
            display_df = display_df[['Ticker', 'Price', 'Shares', 'Date', 
                                    'מחיר נוכחי', 'שווי נוכחי', 'רווח/הפסד ($)', 'רווח/הפסד (%)']]
            
            # תצוגת טבלה מעוצבת
            st.dataframe(
                display_df.style.format({
                    'Price': '${:,.2f}',
                    'מחיר נוכחי': '${:,.2f}',
                    'שווי נוכחי': '${:,.2f}',
                    'רווח/הפסד ($)': '${:+,.2f}',
                    'רווח/הפסד (%)': '{:+.2f}%'
                }, na_rep="ממתין...").apply(
                    lambda x: ['background-color: #ffe6e6' if isinstance(v, (int, float)) and v < 0 
                              else 'background-color: #e6ffe6' if isinstance(v, (int, float)) and v > 0 
                              else '' for v in x],
                    subset=['רווח/הפסד ($)', 'רווח/הפסד (%)']
                ),
                use_container_width=True,
                height=400
            )
        
        # כפתורי פעולה
        col_actions1, col_actions2, col_actions3 = st.columns(3)
        
        with col_actions1:
            if st.session_state.trades:
                if st.button("🗑️ מחק פוזיציה אחרונה", use_container_width=True, key="delete_last_button"):
                    last_trade_id = list(st.session_state.trades.keys())[-1]
                    delete_trade(last_trade_id)
                    st.success("✅ הפוזיציה האחרונה נמחקה!")
                    st.rerun()
        
        with col_actions2:
            if st.session_state.trades:
                csv_buffer = io.StringIO()
                trades_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 הורד CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"פוזיציות_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="download_csv_button"
                )
        
        with col_actions3:
            if st.session_state.trades:
                excel_buffer = to_excel(trades_df)
                st.download_button(
                    label="📊 הורד Excel",
                    data=excel_buffer,
                    file_name=f"פוזיציות_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="download_excel_button"
                )

# ----------------------------------------------------------------------
# 8️⃣ Footer
# ----------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; margin-top: 20px;">
        <h4 style="color: #2c3e50;">💡 אודות "התיק החכם"</h4>
        <p style="color: #7f8c8d; margin-bottom: 10px;">מערכת לניהול תיק מניות וניתוח טכני בעברית</p>
        <div style="font-size: 0.9rem; color: #95a5a6;">
            <p>© 2024 התיק החכם | כל הזכויות שמורות</p>
            <p style="font-size: 0.8rem; color: #bdc3c7;">
                ⚠️ הערה: האפליקציה נועדה לסיוע בניתוח בלבד ואינה מהווה ייעוץ השקעות.<br>
                יש לבצע מחקר עצמאי לפני כל החלטת השקעה.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
