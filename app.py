# -*- coding: utf-8 -*-
"""
התיק החכם - גרסה מתקדמת עם UI משופר
"""

import uuid
import io
import requests
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# ----------------------------------------------------------------------
# 1️⃣ הגדרות וסטייל
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="התיק החכם",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS מעודכן עם רקע בהיר יותר
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    background-size: cover;
}

.main .block-container {
    background-color: white;
    padding: 2rem;
    border-radius: 15px;
    margin-top: 1rem;
    direction: rtl;
    box-shadow: 0 5px 20px rgba(0,0,0,0.05);
    border: 1px solid #e0e0e0;
}

h1, h2, h3, h4 {
    color: #2c3e50;
    font-family: 'Segoe UI', 'Heebo', sans-serif;
    font-weight: 600;
}

.stButton > button {
    width: 100%;
    background: linear-gradient(45deg, #2196F3 0%, #21CBF3 100%);
    color: white;
    border: none;
    padding: 0.75rem;
    border-radius: 10px;
    font-weight: bold;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(33, 150, 243, 0.3);
}

.stTextInput input {
    text-align: center;
    border-radius: 10px;
    border: 2px solid #2196F3;
    padding: 10px;
}

/* כרטיסים */
.stock-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    border: 1px solid #e0e0e0;
}

/* אינדיקטורים */
.indicator-positive {
    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    border-left: 5px solid #28a745;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
}

.indicator-negative {
    background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
    border-left: 5px solid #dc3545;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
}

.indicator-neutral {
    background: linear-gradient(135deg, #e2e3e5 0%, #d6d8db 100%);
    border-left: 5px solid #6c757d;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
}

/* סקטורים */
.sector-up {
    color: #28a745;
    font-weight: bold;
}

.sector-down {
    color: #dc3545;
    font-weight: bold;
}

/* טבלאות */
.stDataFrame {
    border-radius: 10px;
    overflow: hidden;
}

/* טאבים */
.stTabs [data-baseweb="tab-list"] {
    gap: 5px;
    background: #f8f9fa;
    padding: 10px;
    border-radius: 12px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 12px 24px;
    font-weight: 600;
    background: white;
    border: 2px solid #e0e0e0;
    transition: all 0.3s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    border-color: #2196F3;
    background: #e3f2fd;
}

/* מידע חברה */
.company-logo {
    width: 60px;
    height: 60px;
    border-radius: 10px;
    object-fit: cover;
    border: 2px solid #e0e0e0;
    padding: 5px;
    background: white;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# 2️⃣ פונקציות ליבה
# ----------------------------------------------------------------------

@st.cache_data(ttl=3600)
def load_stock_data(ticker):
    """טוען נתוני מניות"""
    try:
        df = yf.download(ticker, period="6mo", progress=False, auto_adjust=True)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        if df.empty:
            return None, None, ticker
        
        info = {}
        full_name = ticker
        
        try:
            t_obj = yf.Ticker(ticker)
            info = t_obj.info
            full_name = info.get('longName', info.get('shortName', ticker))
        except:
            pass
        
        return df, info, full_name
        
    except Exception as e:
        return None, None, ticker

def calculate_advanced_indicators(df):
    """מחשב את כל האינדיקטורים הטכניים"""
    df_calc = df.copy()
    
    if 'Close' not in df_calc.columns:
        if 'Adj Close' in df_calc.columns:
            df_calc['Close'] = df_calc['Adj Close']
        else:
            return df_calc
    
    # ===== ממוצעים נעים =====
    df_calc['SMA_10'] = df_calc['Close'].rolling(10, min_periods=1).mean()
    df_calc['SMA_20'] = df_calc['Close'].rolling(20, min_periods=1).mean()
    df_calc['SMA_50'] = df_calc['Close'].rolling(50, min_periods=1).mean()
    df_calc['SMA_200'] = df_calc['Close'].rolling(200, min_periods=1).mean()
    
    # ===== EMA =====
    df_calc['EMA_12'] = df_calc['Close'].ewm(span=12, min_periods=1).mean()
    df_calc['EMA_26'] = df_calc['Close'].ewm(span=26, min_periods=1).mean()
    
    # ===== MACD =====
    df_calc['MACD'] = df_calc['EMA_12'] - df_calc['EMA_26']
    df_calc['MACD_Signal'] = df_calc['MACD'].ewm(span=9, min_periods=1).mean()
    df_calc['MACD_Histogram'] = df_calc['MACD'] - df_calc['MACD_Signal']
    
    # ===== RSI =====
    delta = df_calc['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(14, min_periods=1).mean()
    avg_loss = loss.rolling(14, min_periods=1).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df_calc['RSI'] = 100 - (100 / (1 + rs))
    df_calc['RSI'] = df_calc['RSI'].fillna(50)
    
    # ===== Bollinger Bands =====
    df_calc['BB_Middle'] = df_calc['Close'].rolling(20, min_periods=1).mean()
    bb_std = df_calc['Close'].rolling(20, min_periods=1).std().fillna(0)
    df_calc['BB_Upper'] = df_calc['BB_Middle'] + (bb_std * 2)
    df_calc['BB_Lower'] = df_calc['BB_Middle'] - (bb_std * 2)
    df_calc['BB_Width'] = (df_calc['BB_Upper'] - df_calc['BB_Lower']) / df_calc['BB_Middle']
    
    # ===== Stochastic =====
    low_14 = df_calc['Low'].rolling(14, min_periods=1).min()
    high_14 = df_calc['High'].rolling(14, min_periods=1).max()
    df_calc['%K'] = 100 * ((df_calc['Close'] - low_14) / (high_14 - low_14).replace(0, np.nan))
    df_calc['%D'] = df_calc['%K'].rolling(3, min_periods=1).mean()
    
    # ===== ATR (Average True Range) =====
    high_low = df_calc['High'] - df_calc['Low']
    high_close = np.abs(df_calc['High'] - df_calc['Close'].shift())
    low_close = np.abs(df_calc['Low'] - df_calc['Close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df_calc['ATR'] = true_range.rolling(14, min_periods=1).mean()
    
    # ===== Volume Indicators =====
    df_calc['Volume_SMA'] = df_calc['Volume'].rolling(20, min_periods=1).mean()
    df_calc['Volume_Ratio'] = df_calc['Volume'] / df_calc['Volume_SMA'].replace(0, np.nan)
    df_calc['Volume_Ratio'] = df_calc['Volume_Ratio'].fillna(1)
    
    # ===== Momentum Indicators =====
    df_calc['Momentum'] = df_calc['Close'] - df_calc['Close'].shift(10)
    df_calc['ROC'] = ((df_calc['Close'] - df_calc['Close'].shift(10)) / df_calc['Close'].shift(10)) * 100
    
    # ===== Support & Resistance =====
    df_calc['Resistance_20'] = df_calc['High'].rolling(20, min_periods=1).max()
    df_calc['Support_20'] = df_calc['Low'].rolling(20, min_periods=1).min()
    
    return df_calc

def get_market_sentiment():
    """מביא נתוני שוק כלליים"""
    sentiment_data = {}
    
    # שער דולר/שקל
    try:
        usd_ticker = yf.Ticker("USDILS=X")
        usd_hist = usd_ticker.history(period="1d")
        if not usd_hist.empty:
            usd_rate = usd_hist['Close'].iloc[-1]
            usd_change = ((usd_hist['Close'].iloc[-1] - usd_hist['Open'].iloc[-1]) / usd_hist['Open'].iloc[-1]) * 100
            sentiment_data['usd_ils'] = {
                'rate': round(usd_rate, 3),
                'change': round(usd_change, 2)
            }
    except:
        sentiment_data['usd_ils'] = {'rate': 3.65, 'change': -0.5}
    
    # מדדי שוק (סימולציה)
    sectors = {
        'טכנולוגיה': {'change': 1.2, 'trend': 'up'},
        'פיננסים': {'change': -0.8, 'trend': 'down'},
        'בריאות': {'change': 0.5, 'trend': 'up'},
        'אנרגיה': {'change': -1.5, 'trend': 'down'},
        'צריכה': {'change': 0.3, 'trend': 'up'},
        'תעשייה': {'change': -0.2, 'trend': 'down'}
    }
    sentiment_data['sectors'] = sectors
    
    # מדד פחד (סימולציה)
    fear_levels = ['פחד קיצוני', 'פחד', 'ניטרלי', 'תאוות בצע', 'תאוות בצע קיצונית']
    import random
    fear_value = random.randint(30, 70)
    
    if fear_value < 25:
        classification = fear_levels[0]
    elif fear_value < 40:
        classification = fear_levels[1]
    elif fear_value < 60:
        classification = fear_levels[2]
    elif fear_value < 75:
        classification = fear_levels[3]
    else:
        classification = fear_levels[4]
    
    sentiment_data['fear_greed'] = {
        'value': fear_value,
        'classification': classification
    }
    
    return sentiment_data

def get_trading_recommendations(df, indicators):
    """מספק המלצות מסחר מפורטות לפי אינדיקטורים"""
    recommendations = []
    last = df.iloc[-1]
    
    # ===== RSI המלצות =====
    if 'RSI' in last:
        rsi = last['RSI']
        if rsi > 70:
            recommendations.append({
                'indicator': 'RSI',
                'value': f"{rsi:.1f}",
                'action': 'מכירה',
                'reason': 'קניית יתר - RSI מעל 70',
                'confidence': 'גבוהה',
                'details': 'המניה בקניית יתר. שקול מכירה חלקית או הגנה עם Stop-Loss'
            })
        elif rsi < 30:
            recommendations.append({
                'indicator': 'RSI',
                'value': f"{rsi:.1f}",
                'action': 'קנייה',
                'reason': 'מכירת יתר - RSI מתחת 30',
                'confidence': 'גבוהה',
                'details': 'המניה במכירת יתר. הזדמנות לכניסה עם Stop-Loss מתחת לתמיכה'
            })
        else:
            recommendations.append({
                'indicator': 'RSI',
                'value': f"{rsi:.1f}",
                'action': 'המתנה',
                'reason': 'RSI בטווח ניטרלי',
                'confidence': 'נמוכה',
                'details': 'אין איתות ברור. המתין לאיתות חדש'
            })
    
    # ===== MACD המלצות =====
    if 'MACD' in last and 'MACD_Signal' in last:
        if last['MACD'] > last['MACD_Signal']:
            recommendations.append({
                'indicator': 'MACD',
                'value': f"{last['MACD']:.4f} > {last['MACD_Signal']:.4f}",
                'action': 'קנייה',
                'reason': 'MACD מעל קו הסיגנל',
                'confidence': 'בינונית',
                'details': 'מומנטום חיובי. ניתן להיכנס עם Stop-Loss מתחת ל-SMA 20'
            })
        else:
            recommendations.append({
                'indicator': 'MACD',
                'value': f"{last['MACD']:.4f} < {last['MACD_Signal']:.4f}",
                'action': 'מכירה',
                'reason': 'MACD מתחת לקו הסיגנל',
                'confidence': 'בינונית',
                'details': 'מומנטום שלילי. שקול מכירה או Short'
            })
    
    # ===== Bollinger Bands המלצות =====
    if 'Close' in last and 'BB_Upper' in last and 'BB_Lower' in last:
        if last['Close'] > last['BB_Upper']:
            recommendations.append({
                'indicator': 'Bollinger Bands',
                'value': 'מחיר מעל הרצועה העליונה',
                'action': 'מכירה',
                'reason': 'מחיר חורג מהרצועה העליונה',
                'confidence': 'גבוהה',
                'details': 'יתר קנייה. צפוי תיקון. מכור או Short עם Stop-Loss מעל השיא'
            })
        elif last['Close'] < last['BB_Lower']:
            recommendations.append({
                'indicator': 'Bollinger Bands',
                'value': 'מחיר מתחת לרצועה התחתונה',
                'action': 'קנייה',
                'reason': 'מחיר חורג מהרצועה התחתונה',
                'confidence': 'גבוהה',
                'details': 'הזדמנות קנייה. היכנס עם Stop-Loss מתחת לשפל'
            })
    
    # ===== ממוצעים נעים המלצות =====
    if 'SMA_20' in last and 'SMA_50' in last and 'SMA_200' in last:
        # Golden Cross / Death Cross
        if last['SMA_20'] > last['SMA_50'] > last['SMA_200']:
            recommendations.append({
                'indicator': 'ממוצעים נעים',
                'value': '20 > 50 > 200',
                'action': 'קנייה',
                'reason': 'ממוצעים מסודרים לעלייה (Golden Cross)',
                'confidence': 'גבוהה',
                'details': 'מגמה עולה חזקה. קנה במשיכות למטה'
            })
        elif last['SMA_20'] < last['SMA_50'] < last['SMA_200']:
            recommendations.append({
                'indicator': 'ממוצעים נעים',
                'value': '20 < 50 < 200',
                'action': 'מכירה',
                'reason': 'ממוצעים מסודרים לירידה (Death Cross)',
                'confidence': 'גבוהה',
                'details': 'מגמה יורדת חזקה. מכור בגואים'
            })
    
    # ===== Stochastic המלצות =====
    if '%K' in last and '%D' in last:
        if last['%K'] > 80 and last['%D'] > 80:
            recommendations.append({
                'indicator': 'Stochastic',
                'value': f"%K={last['%K']:.1f}, %D={last['%D']:.1f}",
                'action': 'מכירה',
                'reason': 'Stochastic בקניית יתר',
                'confidence': 'בינונית',
                'details': 'שקול מכירה חלקית או הגנה'
            })
        elif last['%K'] < 20 and last['%D'] < 20:
            recommendations.append({
                'indicator': 'Stochastic',
                'value': f"%K={last['%K']:.1f}, %D={last['%D']:.1f}",
                'action': 'קנייה',
                'reason': 'Stochastic במכירת יתר',
                'confidence': 'בינונית',
                'details': 'הזדמנות קנייה. היכנס בהדרגה'
            })
    
    # ===== ATR המלצות =====
    if 'ATR' in last:
        atr_percent = (last['ATR'] / last['Close']) * 100
        if atr_percent > 3:
            recommendations.append({
                'indicator': 'ATR',
                'value': f"{atr_percent:.1f}%",
                'action': 'זהירות',
                'reason': 'תנודתיות גבוהה',
                'confidence': 'בינונית',
                'details': 'תנודתיות גבוהה - הגדר Stop-Loss רחב יותר'
            })
    
    return recommendations

def get_company_logo_url(ticker):
    """מביא URL ללוגו החברה"""
    # מאגר לוגואים ידועים
    logo_urls = {
        'AAPL': 'https://logo.clearbit.com/apple.com',
        'TSLA': 'https://logo.clearbit.com/tesla.com',
        'GOOGL': 'https://logo.clearbit.com/google.com',
        'MSFT': 'https://logo.clearbit.com/microsoft.com',
        'AMZN': 'https://logo.clearbit.com/amazon.com',
        'META': 'https://logo.clearbit.com/meta.com',
        'NVDA': 'https://logo.clearbit.com/nvidia.com',
        'NFLX': 'https://logo.clearbit.com/netflix.com',
    }
    
    return logo_urls.get(ticker, 'https://cdn-icons-png.flaticon.com/512/3124/3124975.png')

# ----------------------------------------------------------------------
# 3️⃣ Session State
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
# 4️⃣ כותרת וחיפוש
# ----------------------------------------------------------------------

# כותרת
col_title1, col_title2, col_title3 = st.columns([1, 3, 1])
with col_title2:
    st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📈 התיק החכם</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #7f8c8d;'>ניתוח מניות מתקדם עם המלצות מסחר</h3>", unsafe_allow_html=True)

# חיפוש
st.markdown("---")
col_search1, col_search2, col_search3 = st.columns([1, 3, 1])
with col_search2:
    ticker_input = st.text_input(
        "**🔍 הזן סימול מנייה:**",
        value="AAPL",
        placeholder="לדוגמה: AAPL, TSLA, GOOGL",
        help="יש להזין סימול מנייה באנגלית"
    ).upper().strip()

# מניות מובילות
st.markdown("### 📋 מניות מובילות")
popular_stocks = ["AAPL", "TSLA", "GOOGL", "MSFT", "AMZN", "META", "NVDA", "NFLX"]
cols = st.columns(len(popular_stocks))

for idx, stock in enumerate(popular_stocks):
    with cols[idx]:
        if st.button(stock, key=f"btn_{stock}", use_container_width=True):
            ticker_input = stock
            st.rerun()

# ----------------------------------------------------------------------
# 5️⃣ טעינת נתונים
# ----------------------------------------------------------------------
if ticker_input:
    with st.spinner(f"טוען נתונים עבור {ticker_input}..."):
        df_price, stock_info, full_name = load_stock_data(ticker_input)
    
    if df_price is None or df_price.empty:
        st.error(f"❌ לא נמצאו נתונים עבור {ticker_input}")
        st.stop()
    
    # טעינת אינדיקטורים
    df_with_indicators = calculate_advanced_indicators(df_price)
    
    # נתוני שוק
    market_data = get_market_sentiment()
    
    # המלצות מסחר
    trading_recommendations = get_trading_recommendations(df_with_indicators, df_with_indicators.columns)
    
    # לוגו החברה
    logo_url = get_company_logo_url(ticker_input)
    
    # שם החברה
    company_name = full_name if full_name != ticker_input else ticker_input
    
    # תצוגת כותרת עם לוגו
    col_logo, col_name = st.columns([1, 4])
    with col_logo:
        st.image(logo_url, width=80, caption=ticker_input)
    with col_name:
        st.markdown(f"<h2 style='margin-top: 20px;'>{company_name}</h2>", unsafe_allow_html=True)
    
    # טאבים ראשיים
    tab_names = ["📊 גרף נרות", "📈 ניתוח טכני", "🏢 נתונים פונדמנטליים", "💼 ניהול פוזיציות", "🌐 מצב השוק"]
    tabs = st.tabs(tab_names)
    
    # ==============================================================
    # טאב 1: גרף נרות יפניים
    # ==============================================================
    with tabs[0]:
        st.markdown("### 🕯️ גרף נרות יפניים")
        
        # בחירת תקופה
        period = st.selectbox(
            "בחר תקופה",
            ["1 חודש", "3 חודשים", "6 חודשים", "שנה", "2 שנים"],
            index=2
        )
        
        period_map = {
            "1 חודש": "1mo",
            "3 חודשים": "3mo",
            "6 חודשים": "6mo",
            "שנה": "1y",
            "2 שנים": "2y"
        }
        
        # טעינת נתונים לפי התקופה
        period_df = yf.download(ticker_input, period=period_map[period], progress=False, auto_adjust=True)
        if isinstance(period_df.columns, pd.MultiIndex):
            period_df.columns = period_df.columns.get_level_values(0)
        
        # יצירת גרף נרות
        fig_candles = go.Figure(data=[go.Candlestick(
            x=period_df.index,
            open=period_df['Open'],
            high=period_df['High'],
            low=period_df['Low'],
            close=period_df['Close'],
            name='מחיר'
        )])
        
        # הוספת ממוצעים נעים
        period_df['SMA_20'] = period_df['Close'].rolling(20, min_periods=1).mean()
        period_df['SMA_50'] = period_df['Close'].rolling(50, min_periods=1).mean()
        
        fig_candles.add_trace(go.Scatter(
            x=period_df.index,
            y=period_df['SMA_20'],
            name="ממוצע 20 ימים",
            line=dict(color='orange', width=1)
        ))
        
        fig_candles.add_trace(go.Scatter(
            x=period_df.index,
            y=period_df['SMA_50'],
            name="ממוצע 50 ימים",
            line=dict(color='purple', width=1)
        ))
        
        fig_candles.update_layout(
            title=f"גרף נרות - {period}",
            xaxis_title="תאריך",
            yaxis_title="מחיר (USD)",
            template="plotly_white",
            height=600,
            xaxis_rangeslider_visible=True
        )
        
        st.plotly_chart(fig_candles, use_container_width=True)
        
        # סטטיסטיקות מהירות
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        
        with col_stats1:
            current_price = df_with_indicators['Close'].iloc[-1]
            st.metric("מחיר נוכחי", f"${current_price:.2f}")
        
        with col_stats2:
            daily_change = ((df_with_indicators['Close'].iloc[-1] - df_with_indicators['Close'].iloc[-2]) / 
                          df_with_indicators['Close'].iloc[-2]) * 100 if len(df_with_indicators) > 1 else 0
            st.metric("שינוי יומי", f"{daily_change:+.2f}%")
        
        with col_stats3:
            monthly_change = ((df_with_indicators['Close'].iloc[-1] - df_with_indicators['Close'].iloc[0]) / 
                            df_with_indicators['Close'].iloc[0]) * 100
            st.metric("שינוי חודשי", f"{monthly_change:+.2f}%")
        
        with col_stats4:
            volume = df_with_indicators['Volume'].iloc[-1]
            st.metric("נפח מסחר", f"{volume:,.0f}")
    
    # ==============================================================
    # טאב 2: ניתוח טכני
    # ==============================================================
    with tabs[1]:
        st.markdown("### 📈 ניתוח טכני מפורט")
        
        # טבלת אינדיקטורים
        st.markdown("#### 📊 ערכי אינדיקטורים נוכחיים")
        
        # עמודות לתצוגה
        col_indic1, col_indic2, col_indic3, col_indic4 = st.columns(4)
        
        last_row = df_with_indicators.iloc[-1]
        
        with col_indic1:
            st.markdown("**מחירים וממוצעים**")
            st.metric("מחיר", f"${last_row['Close']:.2f}")
            st.metric("SMA 20", f"${last_row.get('SMA_20', 0):.2f}")
            st.metric("SMA 50", f"${last_row.get('SMA_50', 0):.2f}")
            st.metric("SMA 200", f"${last_row.get('SMA_200', 0):.2f}")
        
        with col_indic2:
            st.markdown("**אוסצילטורים**")
            st.metric("RSI", f"{last_row.get('RSI', 50):.1f}")
            st.metric("%K", f"{last_row.get('%K', 50):.1f}")
            st.metric("%D", f"{last_row.get('%D', 50):.1f}")
            st.metric("MACD", f"{last_row.get('MACD', 0):.4f}")
        
        with col_indic3:
            st.markdown("**בולינגר באנדס**")
            st.metric("מחיר", f"${last_row['Close']:.2f}")
            st.metric("רצועה עליונה", f"${last_row.get('BB_Upper', 0):.2f}")
            st.metric("אמצע", f"${last_row.get('BB_Middle', 0):.2f}")
            st.metric("רצועה תחתונה", f"${last_row.get('BB_Lower', 0):.2f}")
        
        with col_indic4:
            st.markdown("**מדדים נוספים**")
            st.metric("ATR", f"{last_row.get('ATR', 0):.2f}")
            st.metric("נפח יחסי", f"{last_row.get('Volume_Ratio', 1):.2f}x")
            st.metric("מומנטום", f"{last_row.get('Momentum', 0):.2f}")
            st.metric("ROC", f"{last_row.get('ROC', 0):.1f}%")
        
        # המלצות מסחר
        st.markdown("---")
        st.markdown("### 🎯 המלצות מסחר")
        
        if trading_recommendations:
            for rec in trading_recommendations:
                if rec['action'] == 'קנייה':
                    css_class = "indicator-positive"
                elif rec['action'] == 'מכירה':
                    css_class = "indicator-negative"
                else:
                    css_class = "indicator-neutral"
                
                st.markdown(f"""
                <div class="{css_class}">
                    <h4>{rec['indicator']}: {rec['action']} ({rec['confidence']} בטחון)</h4>
                    <p><strong>ערך:</strong> {rec['value']}</p>
                    <p><strong>סיבה:</strong> {rec['reason']}</p>
                    <p><strong>הוראות:</strong> {rec['details']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("אין המלצות מסחר זמינות כרגע")
        
        # סיכום טכני
        st.markdown("---")
        st.markdown("### 📝 סיכום טכני")
        
        # חישוב ציון טכני
        technical_score = 50
        
        if 'RSI' in last_row:
            if last_row['RSI'] > 70:
                technical_score -= 20
            elif last_row['RSI'] < 30:
                technical_score += 20
        
        if 'MACD' in last_row and 'MACD_Signal' in last_row:
            if last_row['MACD'] > last_row['MACD_Signal']:
                technical_score += 15
            else:
                technical_score -= 15
        
        if 'SMA_20' in last_row and 'SMA_50' in last_row:
            if last_row['Close'] > last_row['SMA_20'] > last_row['SMA_50']:
                technical_score += 20
            elif last_row['Close'] < last_row['SMA_20'] < last_row['SMA_50']:
                technical_score -= 20
        
        technical_score = max(0, min(100, technical_score))
        
        col_summary1, col_summary2 = st.columns([2, 1])
        
        with col_summary1:
            st.markdown(f"**ציון טכני:** {technical_score}/100")
            st.progress(technical_score / 100)
            
            if technical_score >= 70:
                st.success("📈 **מצב טכני חיובי** - נטייה לקנייה")
            elif technical_score <= 30:
                st.error("📉 **מצב טכני שלילי** - נטייה למכירה")
            else:
                st.info("⚖️ **מצב טכני ניטרלי** - אין נטייה ברורה")
        
        with col_summary2:
            st.markdown("**איתותים פעילים:**")
            active_signals = sum(1 for rec in trading_recommendations if rec['confidence'] in ['גבוהה', 'בינונית'])
            st.metric("איתותים", active_signals)
    
    # ==============================================================
    # טאב 3: נתונים פונדמנטליים
    # ==============================================================
    with tabs[2]:
        st.markdown("### 🏢 נתונים פונדמנטליים")
        
        if stock_info:
            # מידע בסיסי
            col_fund1, col_fund2 = st.columns([2, 1])
            
            with col_fund1:
                st.markdown("#### פרטי החברה")
                
                # תרגום שדות
                translations = {
                    'longName': 'שם החברה',
                    'industry': 'תחום עיסוק',
                    'sector': 'סקטור',
                    'exchange': 'בורסה',
                    'country': 'מדינה',
                    'currency': 'מטבע',
                    'website': 'אתר אינטרנט',
                    'fullTimeEmployees': 'מספר עובדים',
                    'city': 'עיר',
                    'state': 'מדינה',
                    'zip': 'מיקוד',
                    'phone': 'טלפון'
                }
                
                for eng_key, heb_key in translations.items():
                    if eng_key in stock_info and stock_info[eng_key]:
                        st.markdown(f"**{heb_key}:** {stock_info[eng_key]}")
                
                # פעולות החברה (תרגום)
                st.markdown("---")
                st.markdown("#### פעולות ומעשי החברה")
                
                business_summary = stock_info.get('longBusinessSummary', 'אין תיאור זמין')
                st.markdown(f"**תיאור פעילות:**")
                st.write(business_summary)
            
            with col_fund2:
                st.markdown("#### מדדים פיננסיים")
                
                financial_metrics = {
                    'marketCap': ('שווי שוק', 'מטבע'),
                    'forwardPE': ('מכפיל רווח צפוי', 'מספר'),
                    'trailingPE': ('מכפיל רווח', 'מספר'),
                    'priceToBook': ('מחיר לערך ספר', 'מספר'),
                    'dividendYield': ('תשואת דיבידנד', 'אחוז'),
                    'profitMargins': ('שולי רווח', 'אחוז'),
                    'revenueGrowth': ('צמיחת הכנסות', 'אחוז'),
                    'earningsGrowth': ('צמיחת רווחים', 'אחוז'),
                    'debtToEquity': ('יחס חוב להון', 'מספר'),
                    'currentRatio': ('יחס שוטף', 'מספר'),
                    'returnOnAssets': ('תשואה על נכסים', 'אחוז'),
                    'returnOnEquity': ('תשואה על הון', 'אחוז')
                }
                
                for key, (heb_name, format_type) in financial_metrics.items():
                    if key in stock_info and stock_info[key] is not None:
                        value = stock_info[key]
                        
                        if format_type == 'מטבע':
                            if value >= 1e12:
                                display_value = f"${value/1e12:.2f}T"
                            elif value >= 1e9:
                                display_value = f"${value/1e9:.2f}B"
                            elif value >= 1e6:
                                display_value = f"${value/1e6:.2f}M"
                            else:
                                display_value = f"${value:,.0f}"
                        elif format_type == 'אחוז':
                            display_value = f"{value*100:.2f}%"
                        else:
                            display_value = f"{value:.2f}"
                        
                        st.metric(heb_name, display_value)
            
            # ניתוח פונדמנטלי
            st.markdown("---")
            st.markdown("#### 📊 ניתוח פונדמנטלי")
            
            fundamental_insights = []
            
            # מכפיל רווח
            pe = stock_info.get('forwardPE', stock_info.get('trailingPE'))
            if pe:
                if pe < 15:
                    fundamental_insights.append("✅ **מכפיל רווח נמוך** - המניה זולה יחסית לרווחיה")
                elif pe > 40:
                    fundamental_insights.append("⚠️ **מכפיל רווח גבוה** - המניה יקרה, מצפים לצמיחה גבוהה")
            
            # רווחיות
            margins = stock_info.get('profitMargins')
            if margins:
                if margins > 0.2:
                    fundamental_insights.append("💎 **רווחיות גבוהה** - החברה רווחית מאוד")
                elif margins < 0:
                    fundamental_insights.append("🔻 **הפסד תפעולי** - החברה מפסידה כסף")
            
            # צמיחה
            revenue_growth = stock_info.get('revenueGrowth')
            if revenue_growth:
                if revenue_growth > 0.2:
                    fundamental_insights.append("📈 **צמיחה גבוהה** - הכנסות גדלות במהירות")
                elif revenue_growth < 0:
                    fundamental_insights.append("📉 **צמיחה שלילית** - הכנסות בירידה")
            
            # דיבידנד
            dividend_yield = stock_info.get('dividendYield')
            if dividend_yield and dividend_yield > 0:
                fundamental_insights.append(f"💰 **דיבידנד** - תשואה של {dividend_yield*100:.2f}%")
            
            # חוב
            debt_ratio = stock_info.get('debtToEquity')
            if debt_ratio:
                if debt_ratio > 2:
                    fundamental_insights.append("🏦 **חוב גבוה** - יחס חוב להון מעל 2")
                elif debt_ratio < 0.5:
                    fundamental_insights.append("💪 **חוב נמוך** - מבנה הון שמרני")
            
            for insight in fundamental_insights:
                st.markdown(f"- {insight}")
        
        else:
            st.warning("אין נתונים פונדמנטליים זמינים")
    
    # ==============================================================
    # טאב 4: ניהול פוזיציות
    # ==============================================================
    with tabs[3]:
        st.markdown("### 💼 ניהול פוזיציות")
        
        # הוספת פוזיציה
        st.markdown("#### 🛒 הוספת פוזיציה חדשה")
        
        col_add1, col_add2, col_add3 = st.columns([2, 2, 1])
        
        with col_add1:
            current_price = df_with_indicators['Close'].iloc[-1]
            price_input = st.number_input(
                "מחיר קנייה (USD)",
                min_value=0.0,
                value=round(current_price, 2),
                step=0.01,
                key="price_input"
            )
        
        with col_add2:
            shares_input = st.number_input(
                "מספר מניות",
                min_value=1,
                step=1,
                value=100,
                key="shares_input"
            )
        
        with col_add3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"➕ הוסף {ticker_input}", use_container_width=True, key="add_position"):
                if price_input > 0 and shares_input > 0:
                    add_trade(ticker_input, price_input, shares_input)
                    st.success("✅ פוזיציה נוספה בהצלחה!")
                    st.rerun()
        
        st.info(f"💡 מחיר נוכחי: **${current_price:.2f}** | שווי מוצע: **${current_price * shares_input:,.2f}**")
        
        # פוזיציות קיימות
        st.markdown("---")
        st.markdown("#### 📋 פוזיציות שלי")
        
        if not st.session_state.trades:
            st.info("📝 עדיין אין לך פוזיציות. הוסף פוזיציה ראשונה למעלה.")
        else:
            # יצירת DataFrame עם חישוב רווח והפסד
            trades_list = []
            
            for trade_id, trade in st.session_state.trades.items():
                try:
                    # טעינת מחיר נוכחי
                    df_tmp, _, _ = load_stock_data(trade['Ticker'])
                    if df_tmp is not None and not df_tmp.empty:
                        current_price_tmp = df_tmp['Close'].iloc[-1]
                        current_value = current_price_tmp * trade['Shares']
                        invested = trade['Price'] * trade['Shares']
                        pnl = current_value - invested
                        pnl_pct = (pnl / invested) * 100 if invested > 0 else 0
                        
                        trades_list.append({
                            'סימול': trade['Ticker'],
                            'מחיר קנייה': trade['Price'],
                            'מניות': trade['Shares'],
                            'הושקע': invested,
                            'מחיר נוכחי': current_price_tmp,
                            'שווי נוכחי': current_value,
                            'רווח/הפסד': pnl,
                            'אחוז': pnl_pct,
                            'תאריך': trade['Date'],
                            'מזהה': trade_id
                        })
                except:
                    continue
            
            if trades_list:
                trades_df = pd.DataFrame(trades_list)
                
                # תצוגה מעוצבת
                st.dataframe(
                    trades_df.style.format({
                        'מחיר קנייה': '${:,.2f}',
                        'הושקע': '${:,.2f}',
                        'מחיר נוכחי': '${:,.2f}',
                        'שווי נוכחי': '${:,.2f}',
                        'רווח/הפסד': '${:+,.2f}',
                        'אחוז': '{:+.2f}%'
                    }).apply(
                        lambda x: ['background-color: #d4edda' if isinstance(v, (int, float)) and v > 0 
                                  else 'background-color: #f8d7da' if isinstance(v, (int, float)) and v < 0 
                                  else '' for v in x],
                        subset=['רווח/הפסד', 'אחוז']
                    ),
                    use_container_width=True,
                    height=300,
                    hide_index=True
                )
                
                # סיכום תיק
                st.markdown("---")
                st.markdown("#### 📊 סיכום תיק")
                
                total_invested = trades_df['הושקע'].sum()
                total_current = trades_df['שווי נוכחי'].sum()
                total_pnl = total_current - total_invested
                total_pnl_pct = (total_pnl / total_invested) * 100 if total_invested > 0 else 0
                
                col_sum1, col_sum2, col_sum3 = st.columns(3)
                
                with col_sum1:
                    st.metric("הון מושקע", f"${total_invested:,.2f}")
                
                with col_sum2:
                    st.metric("שווי נוכחי", f"${total_current:,.2f}")
                
                with col_sum3:
                    st.metric("רווח/הפסד", f"${total_pnl:+,.2f}", f"{total_pnl_pct:+.2f}%")
                
                # כפתורי פעולה
                st.markdown("---")
                col_actions1, col_actions2, col_actions3 = st.columns(3)
                
                with col_actions1:
                    if st.button("🗑️ מחק פוזיציה אחרונה", use_container_width=True):
                        last_trade_id = list(st.session_state.trades.keys())[-1]
                        delete_trade(last_trade_id)
                        st.success("✅ הפוזיציה נמחקה!")
                        st.rerun()
                
                with col_actions2:
                    if st.session_state.trades:
                        csv_buffer = io.StringIO()
                        pd.DataFrame.from_dict(st.session_state.trades, orient='index').to_csv(csv_buffer, index=False)
                        st.download_button(
                            label="📥 הורד CSV",
                            data=csv_buffer.getvalue(),
                            file_name=f"פוזיציות_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                
                with col_actions3:
                    if st.session_state.trades:
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            pd.DataFrame.from_dict(st.session_state.trades, orient='index').to_excel(writer, index=False)
                        excel_buffer.seek(0)
                        
                        st.download_button(
                            label="📊 הורד Excel",
                            data=excel_buffer,
                            file_name=f"פוזיציות_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
    
    # ==============================================================
    # טאב 5: מצב השוק
    # ==============================================================
    with tabs[4]:
        st.markdown("### 🌐 מצב השוק")
        
        # מדד פחד ותאוות בצע
        st.markdown("#### 📊 מדד פחד ותאוות בצע")
        
        fear_value = market_data['fear_greed']['value']
        fear_class = market_data['fear_greed']['classification']
        
        # צבע לפי ערך
        if fear_value < 25:
            fear_color = "#3498db"
            fear_emoji = "😨"
        elif fear_value < 40:
            fear_color = "#2980b9"
            fear_emoji = "😟"
        elif fear_value < 60:
            fear_color = "#7f8c8d"
            fear_emoji = "😐"
        elif fear_value < 75:
            fear_color = "#e67e22"
            fear_emoji = "😊"
        else:
            fear_color = "#e74c3c"
            fear_emoji = "😍"
        
        col_fear1, col_fear2 = st.columns([1, 2])
        
        with col_fear1:
            st.markdown(f"""
            <div style="background-color: {fear_color}; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                <h1>{fear_value}</h1>
                <p>{fear_emoji} {fear_class}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_fear2:
            st.markdown("**הסבר:**")
            if fear_value < 40:
                st.info("שוק בפחד - הזדמנויות קנייה")
            elif fear_value > 60:
                st.warning("שוק בתאוות בצע - זהירות מקנייה")
            else:
                st.success("שוק ניטרלי - המשך מסחר רגיל")
        
        # שער דולר/שקל
        st.markdown("---")
        st.markdown("#### 💱 שער מטבעות")
        
        usd_data = market_data['usd_ils']
        col_usd1, col_usd2 = st.columns(2)
        
        with col_usd1:
            st.metric("דולר/שקל", f"{usd_data['rate']} ₪", f"{usd_data['change']:+.2f}%")
        
        with col_usd2:
            # ניתן להוסיף מטבעות נוספים כאן
            st.metric("אירו/שקל", "3.92 ₪", "-0.25%")
        
        # סקטורים
        st.markdown("---")
        st.markdown("#### 📈 סקטורים היום")
        
        sectors = market_data['sectors']
        
        for sector_name, sector_data in sectors.items():
            col_sector1, col_sector2 = st.columns([2, 1])
            
            with col_sector1:
                st.markdown(f"**{sector_name}**")
            
            with col_sector2:
                change = sector_data['change']
                if sector_data['trend'] == 'up':
                    st.markdown(f"<span class='sector-up'>📈 {change:+.1f}%</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span class='sector-down'>📉 {change:+.1f}%</span>", unsafe_allow_html=True)
        
        # תובנות שוק
        st.markdown("---")
        st.markdown("#### 💡 תובנות שוק")
        
        market_insights = [
            "📊 **טכנולוגיה בעלייה** - סקטור הטכנולוגיה מוביל את השוק היום",
            "💼 **פיננסים בירידה** - בנקים וממוסדות פיננסיים במגמת ירידה",
            "⚡ **אנרגיה חלשה** - מחירי הנפט משפיעים לרעה על הסקטור",
            "🛒 **צריכה יציבה** - סקטור הצריכה מראה יציבות יחסית"
        ]
        
        for insight in market_insights:
            st.markdown(f"- {insight}")

# ----------------------------------------------------------------------
# 6️⃣ Footer
# ----------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px;">
        <p style="color: #7f8c8d;">📈 <strong>התיק החכם</strong> - כלים מתקדמים לניתוח מניות וניהול תיק</p>
        <p style="font-size: 0.8rem; color: #bdc3c7;">
            ⚠️ הערה: האפליקציה נועדה לסיוע בלבד. יש לבצע מחקר עצמאי לפני כל החלטת השקעה.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
