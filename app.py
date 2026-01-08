# -*- coding: utf-8 -*-
"""
התיק החכם - גרסת PRO עם AI ופיצ'רים מתקדמים
"""

import uuid
import io
import json
import requests
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# ----------------------------------------------------------------------
# 1️⃣ הגדרות מתקדמות
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="התיק החכם PRO",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS מתקדם עם אנימציות
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700&display=swap');

* {
    font-family: 'Heebo', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    animation: gradientBG 15s ease infinite;
    background-size: 400% 400%;
}

@keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.main .block-container {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 2rem;
    margin-top: 1.5rem;
    direction: rtl;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    animation: fadeIn 0.8s ease-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* כרטיסים עם hover effects */
.stock-card {
    background: white;
    border-radius: 15px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
    border: 1px solid #eaeaea;
    transition: all 0.3s ease;
}

.stock-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 30px rgba(0,0,0,0.15);
}

/* כפתורים עם גרדיאנט */
.stButton > button {
    background: linear-gradient(45deg, #667eea, #764ba2);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 24px;
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.3s ease;
    width: 100%;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

/* אינדיקטורים עם icons */
.indicator-box {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 10px;
    text-align: center;
    border-left: 5px solid #667eea;
}

/* מדד פחד - צבעים דינמיים */
.fear-greed {
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
    font-weight: bold;
    text-align: center;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.8; }
    100% { opacity: 1; }
}

/* טאבים מעוצבים */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: #f8f9fa;
    padding: 10px;
    border-radius: 12px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 12px 24px;
    font-weight: 600;
    background: white;
    border: 2px solid transparent;
    transition: all 0.3s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    border-color: #667eea;
    background: #f0f2ff;
}

/* נורות יפניות בגרף */
.candle-up {
    fill: #26a69a;
    stroke: #26a69a;
}

.candle-down {
    fill: #ef5350;
    stroke: #ef5350;
}

/* אנימציות להתראות */
.alert-pulse {
    animation: alertPulse 1.5s infinite;
}

@keyframes alertPulse {
    0% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(255, 193, 7, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0); }
}

/* כוכבים לגיימיפיקציה */
.star-rating {
    color: #FFD700;
    font-size: 1.2rem;
    margin: 5px 0;
}

/* טרופי ללוח מובילים */
.trophy {
    color: #FFD700;
    font-size: 1.5rem;
    animation: bounce 2s infinite;
}

@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-5px); }
}

/* גרפים עם אפקט זכוכית */
.glass-effect {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

/* AI chatbot */
.chat-bubble {
    background: #f0f2ff;
    border-radius: 20px;
    padding: 15px;
    margin: 10px;
    max-width: 80%;
    position: relative;
}

.chat-bubble::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 20px;
    width: 0;
    height: 0;
    border: 10px solid transparent;
    border-top-color: #f0f2ff;
    border-bottom: 0;
    margin-bottom: -10px;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# 2️⃣ פונקציות מתקדמות - AI והפתעות
# ----------------------------------------------------------------------

# ---------- מדד פחד (Fear & Greed Index) ----------
def get_fear_greed_index():
    """שולף מדד פחד ותאוות בצע מהאינטרנט"""
    try:
        # מקור: Alternative.me (אמיתי)
        url = "https://api.alternative.me/fng/"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            value = int(data['data'][0]['value'])
            classification = data['data'][0]['value_classification']
            
            # תרגום לעברית
            hebrew_classification = {
                'Extreme Fear': 'פחד קיצוני',
                'Fear': 'פחד',
                'Neutral': 'ניטרלי',
                'Greed': 'תאוות בצע',
                'Extreme Greed': 'תאוות בצע קיצונית'
            }.get(classification, classification)
            
            return value, hebrew_classification
    except:
        # במקרה של שגיאה, נשתמש בערכים סימולציה
        import random
        value = random.randint(25, 75)
        levels = ['פחד קיצוני', 'פחד', 'ניטרלי', 'תאוות בצע', 'תאוות בצע קיצונית']
        if value < 25:
            classification = levels[0]
        elif value < 40:
            classification = levels[1]
        elif value < 60:
            classification = levels[2]
        elif value < 75:
            classification = levels[3]
        else:
            classification = levels[4]
        
        return value, classification

# ---------- שער דולר/שקל בזמן אמת ----------
def get_usd_ils_rate():
    """מביא שער דולר/שקל מעודכן"""
    try:
        # שימוש ב-yfinance עבור USD/ILS
        ticker = yf.Ticker("USDILS=X")
        hist = ticker.history(period="1d")
        if not hist.empty:
            rate = hist['Close'].iloc[-1]
            change = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
            change_pct = (change / hist['Open'].iloc[-1]) * 100
            return round(rate, 3), round(change, 3), round(change_pct, 2)
    except:
        pass
    
    # גיבוי - נתונים סטטיים
    return 3.65, -0.02, -0.54

# ---------- התראות דיווחים קרובים ----------
def get_upcoming_events(ticker):
    """מביא אירועים קרובים של החברה"""
    events = []
    try:
        stock = yf.Ticker(ticker)
        # בדיקת דיבידנדים קרובים
        dividends = stock.dividends
        if len(dividends) > 0:
            next_div = dividends.index[-1]
            if next_div.date() >= datetime.now().date():
                events.append({
                    'type': 'דיבידנד',
                    'date': next_div.date(),
                    'amount': dividends.iloc[-1]
                })
        
        # בדיקת דוחות כספיים (הנחה על בסיס רבעונים)
        today = datetime.now().date()
        next_quarter = today + timedelta(days=45)
        events.append({
            'type': 'דוח רבעוני משוער',
            'date': next_quarter,
            'amount': None
        })
        
    except:
        pass
    
    return events

# ---------- AI - זיהוי תבניות ----------
def detect_chart_patterns(df):
    """מזהה תבניות טכניות בגרף"""
    patterns = []
    
    if len(df) < 50:
        return patterns
    
    # חישוב נדרשים
    df['High_20'] = df['High'].rolling(window=20).max()
    df['Low_20'] = df['Low'].rolling(window=20).min()
    df['Close_MA_20'] = df['Close'].rolling(window=20).mean()
    df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()
    
    # זיהוי תבניות בסיסיות
    recent = df.iloc[-20:]
    
    # 1. תבנית ראש וכתפיים
    if len(df) > 100:
        middle = len(df) // 2
        left_shoulder = df.iloc[middle-30:middle-10]['High'].max()
        head = df.iloc[middle-10:middle+10]['High'].max()
        right_shoulder = df.iloc[middle+10:middle+30]['High'].max()
        
        if head > left_shoulder and head > right_shoulder:
            if abs(left_shoulder - right_shoulder) / head < 0.05:
                patterns.append({
                    'name': 'ראש וכתפיים',
                    'confidence': 75,
                    'signal': 'מכירה'
                })
    
    # 2. תבנית דגל
    if len(df) > 40:
        first_half = df.iloc[-40:-20]
        second_half = df.iloc[-20:]
        
        if first_half['Close'].std() > second_half['Close'].std() * 2:
            patterns.append({
                'name': 'דגל',
                'confidence': 70,
                'signal': 'המשך מגמה'
            })
    
    # 3. תבנית Double Top/Bottom
    if len(df) > 60:
        peak1 = df.iloc[-60:-40]['High'].max()
        peak2 = df.iloc[-20:]['High'].max()
        valley = df.iloc[-40:-20]['Low'].min()
        
        if abs(peak1 - peak2) / peak1 < 0.03:
            patterns.append({
                'name': 'Double Top',
                'confidence': 80,
                'signal': 'מכירה'
            })
    
    # 4. תבנית חדירה של ממוצעים
    if 'SMA_50' in df.columns and 'SMA_200' in df.columns:
        last_close = df['Close'].iloc[-1]
        sma50 = df['SMA_50'].iloc[-1]
        sma200 = df['SMA_200'].iloc[-1]
        
        if last_close > sma50 > sma200:
            patterns.append({
                'name': 'ממוצעים זהביים',
                'confidence': 85,
                'signal': 'קנייה'
            })
    
    # 5. Volume spike
    last_volume = df['Volume'].iloc[-1]
    avg_volume = df['Volume'].iloc[-20:].mean()
    
    if last_volume > avg_volume * 2:
        patterns.append({
            'name': 'נפח חריג',
            'confidence': 90,
            'signal': 'שינוי מגמה'
        })
    
    return patterns

# ---------- AI - המלצות ML בסיסיות ----------
def generate_ai_recommendation(df, info, patterns):
    """מייצר המלצת AI בסיסית"""
    
    recommendations = []
    
    if df.empty:
        return ["אין מספיק נתונים להמלצה"]
    
    # ניתוח טכני
    last_close = df['Close'].iloc[-1]
    sma_20 = df['Close'].rolling(20).mean().iloc[-1]
    sma_50 = df['Close'].rolling(50).mean().iloc[-1]
    
    # ניתוח מגמה
    if last_close > sma_20 > sma_50:
        recommendations.append("📈 **מגמה עולה חזקה** - כל הממוצעים מסודרים לעלייה")
    elif last_close < sma_20 < sma_50:
        recommendations.append("📉 **מגמה יורדת חזקה** - כל הממוצעים מסודרים לירידה")
    
    # ניתוח תבניות
    if patterns:
        for pattern in patterns[:2]:  # לוקח רק 2 תבניות מובילות
            rec = f"🎯 **תבנית {pattern['name']}** (בטחון {pattern['confidence']}%) - איתור ל{pattern['signal']}"
            recommendations.append(rec)
    
    # ניתוח RSI
    if 'RSI' in df.columns:
        rsi = df['RSI'].iloc[-1]
        if rsi < 30:
            recommendations.append(f"🟢 **RSI ({rsi:.1f})** - מכירת יתר, הזדמנות קנייה")
        elif rsi > 70:
            recommendations.append(f"🔴 **RSI ({rsi:.1f})** - קניית יתר, שקול מכירה")
    
    # ניתוח תנודתיות
    volatility = df['Close'].pct_change().std() * np.sqrt(252) * 100
    if volatility > 40:
        recommendations.append(f"⚡ **תנודתיות גבוהה** ({volatility:.1f}%) - השקעה מסוכנת")
    elif volatility < 15:
        recommendations.append(f"🛡️ **תנודתיות נמוכה** ({volatility:.1f}%) - השקעה שמרנית")
    
    # אם אין המלצות, נוסיף המלצה כללית
    if not recommendations:
        price_change = ((last_close - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
        if price_change > 20:
            recommendations.append("📊 **ביצועים מעולים** בשנה האחרונה - המשך מעקב")
        elif price_change < -10:
            recommendations.append("⚠️ **ביצועים חלשים** בשנה האחרונה - היזהר")
        else:
            recommendations.append("⚖️ **ביצועים סבירים** - אין איתותים קיצוניים")
    
    return recommendations[:5]  # מחזיר עד 5 המלצות

# ---------- ניוז פיד בעברית ----------
def get_hebrew_news(ticker, company_name):
    """מביא חדשות בעברית על החברה (סימולציה)"""
    news_items = []
    
    # בניתוק אמיתי, היינו מחברים ל-API של חדשות
    # כרגע נשתמש בדוגמאות
    
    sample_news = [
        {
            'title': f'דוח רבעוני מצפוי ל-{company_name}',
            'summary': 'אנליסטים מעריכים כי החברה תדווח על צמיחה בהכנסות',
            'date': 'היום',
            'sentiment': 'חיובי'
        },
        {
            'title': f'השקעה חדשה של {company_name} בטכנולוגיה',
            'summary': 'החברה מכריזה על רכישה בתחום הבינה המלאכותית',
            'date': 'אתמול',
            'sentiment': 'חיובי'
        },
        {
            'title': f'תחרות גוברת עבור {company_name}',
            'summary': 'מתחרים חדשים נכנסים לשוק ומאיימים על נתח השוק',
            'date': 'לפני 3 ימים',
            'sentiment': 'שלילי'
        }
    ]
    
    return sample_news

# ---------- גיימיפיקציה - מערכת תגים ----------
def calculate_user_score(trades, analysis_count):
    """מחשב ניקוד משתמש לתגים"""
    score = 0
    
    # ניקוד על פוזיציות
    score += len(trades) * 10
    
    # ניקוד על ניתוחים
    score += analysis_count * 5
    
    # תגים לפי ניקוד
    badges = []
    
    if score >= 100:
        badges.append(('🏆', 'סוחר מומחה', 'gold'))
    if score >= 50:
        badges.append(('⭐', 'סוחר בינוני', 'silver'))
    if len(trades) >= 5:
        badges.append(('📊', 'מנתח פעיל', 'bronze'))
    if analysis_count >= 10:
        badges.append(('🔍', 'חוקר שוק', 'blue'))
    
    return score, badges

# ---------- השוואת מניות ----------
def compare_stocks(tickers):
    """משווה בין מספר מניות"""
    comparison_data = []
    
    for ticker in tickers[:4]:  # מוגבל ל-4 מניות להשוואה
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            info = stock.info
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                month_change = ((current_price - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                
                comparison_data.append({
                    'Ticker': ticker,
                    'Name': info.get('longName', ticker),
                    'Price': current_price,
                    'Change_1M': month_change,
                    'Volume': hist['Volume'].mean(),
                    'Market_Cap': info.get('marketCap', 0)
                })
        except:
            continue
    
    return pd.DataFrame(comparison_data)

# ----------------------------------------------------------------------
# 3️⃣ הגדרות Session State מתקדמות
# ----------------------------------------------------------------------
if "user_score" not in st.session_state:
    st.session_state.user_score = 0
    st.session_state.badges = []
    st.session_state.analysis_count = 0
    st.session_state.comparison_stocks = ["AAPL", "GOOGL", "MSFT"]

if "trades" not in st.session_state:
    st.session_state.trades = {}
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(
        columns=["Ticker", "EntryPrice", "Shares", "Date", "TradeID"]
    )

# ----------------------------------------------------------------------
# 4️⃣ פונקציות אינדיקטורים מתקדמות
# ----------------------------------------------------------------------
def calculate_advanced_indicators(df):
    """מחשב אינדיקטורים טכניים מתקדמים"""
    df_calc = df.copy()
    
    # ממוצעים נעים בסיסיים
    df_calc['SMA_20'] = df_calc['Close'].rolling(20).mean()
    df_calc['SMA_50'] = df_calc['Close'].rolling(50).mean()
    df_calc['SMA_200'] = df_calc['Close'].rolling(200).mean()
    
    # EMA
    df_calc['EMA_12'] = df_calc['Close'].ewm(span=12).mean()
    df_calc['EMA_26'] = df_calc['Close'].ewm(span=26).mean()
    
    # MACD
    df_calc['MACD'] = df_calc['EMA_12'] - df_calc['EMA_26']
    df_calc['MACD_Signal'] = df_calc['MACD'].ewm(span=9).mean()
    df_calc['MACD_Histogram'] = df_calc['MACD'] - df_calc['MACD_Signal']
    
    # RSI
    delta = df_calc['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df_calc['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df_calc['BB_Middle'] = df_calc['Close'].rolling(20).mean()
    bb_std = df_calc['Close'].rolling(20).std()
    df_calc['BB_Upper'] = df_calc['BB_Middle'] + (bb_std * 2)
    df_calc['BB_Lower'] = df_calc['BB_Middle'] - (bb_std * 2)
    
    # Stochastic
    low_14 = df_calc['Low'].rolling(14).min()
    high_14 = df_calc['High'].rolling(14).max()
    df_calc['%K'] = 100 * ((df_calc['Close'] - low_14) / (high_14 - low_14))
    df_calc['%D'] = df_calc['%K'].rolling(3).mean()
    
    # Average True Range (ATR)
    high_low = df_calc['High'] - df_calc['Low']
    high_close = np.abs(df_calc['High'] - df_calc['Close'].shift())
    low_close = np.abs(df_calc['Low'] - df_calc['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df_calc['ATR'] = true_range.rolling(14).mean()
    
    # Volume indicators
    df_calc['Volume_SMA'] = df_calc['Volume'].rolling(20).mean()
    df_calc['Volume_Ratio'] = df_calc['Volume'] / df_calc['Volume_SMA']
    
    return df_calc

def create_candlestick_chart(df, title="נרות יפניים"):
    """יוצר גרף נרות יפניים"""
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='מחיר'
    )])
    
    fig.update_layout(
        title=title,
        xaxis_title="תאריך",
        yaxis_title="מחיר (USD)",
        template="plotly_white",
        height=500,
        xaxis_rangeslider_visible=True
    )
    
    return fig

# ----------------------------------------------------------------------
# 5️⃣ סיידבר מתקדם
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("<div class='glass-effect'>", unsafe_allow_html=True)
    
    # לוגו וכותרת
    col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
    with col_logo2:
        st.image("https://cdn-icons-png.flaticon.com/512/3124/3124975.png", width=80)
    
    st.markdown("<h2 style='text-align: center;'>התיק החכם PRO</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>גרסה מתקדמת עם AI</p>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # מדד פחד ותאוות בצע
    st.markdown("<div class='stock-card'>", unsafe_allow_html=True)
    st.markdown("### 📊 מדד פחד ותאוות בצע")
    
    fear_value, fear_text = get_fear_greed_index()
    
    # צבע דינמי לפי הערך
    if fear_value < 25:
        color = "#3498db"  # כחול - פחד קיצוני
    elif fear_value < 40:
        color = "#2980b9"  # כחול כהה - פחד
    elif fear_value < 60:
        color = "#7f8c8d"  # אפור - ניטרלי
    elif fear_value < 75:
        color = "#e67e22"  # כתום - תאוות בצע
    else:
        color = "#e74c3c"  # אדום - תאוות בצע קיצונית
    
    st.markdown(f"<div style='background-color: {color}; padding: 15px; border-radius: 10px; color: white; text-align: center;'>", unsafe_allow_html=True)
    st.markdown(f"<h1>{fear_value}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p>{fear_text}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # שער דולר/שקל
    st.markdown("<div class='stock-card'>", unsafe_allow_html=True)
    st.markdown("### 💱 שער דולר/שקל")
    
    usd_rate, usd_change, usd_change_pct = get_usd_ils_rate()
    change_color = "green" if usd_change_pct < 0 else "red"
    
    col_usd1, col_usd2 = st.columns(2)
    with col_usd1:
        st.metric("שער נוכחי", f"{usd_rate} ₪")
    with col_usd2:
        st.metric("שינוי", f"{usd_change_pct}%", delta_color="inverse")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # גיימיפיקציה - תגים של המשתמש
    st.markdown("<div class='stock-card'>", unsafe_allow_html=True)
    st.markdown("### 🏆 הישגים שלך")
    
    # חישוב ניקוד מעודכן
    st.session_state.user_score, st.session_state.badges = calculate_user_score(
        st.session_state.trades, 
        st.session_state.analysis_count
    )
    
    st.markdown(f"**ניקוד:** {st.session_state.user_score} נקודות")
    
    if st.session_state.badges:
        st.markdown("**תגים:**")
        for emoji, name, color in st.session_state.badges:
            st.markdown(f"{emoji} {name}")
    else:
        st.info("עוד לא השגת תגים. הוסף פוזיציות ונתח מניות!")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # השוואת מניות
    st.markdown("<div class='stock-card'>", unsafe_allow_html=True)
    st.markdown("### 📈 השוואת מניות")
    
    comparison_stocks = st.multiselect(
        "בחר מניות להשוואה",
        ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA", "NFLX"],
        default=st.session_state.comparison_stocks,
        key="comparison_select"
    )
    
    if comparison_stocks:
        st.session_state.comparison_stocks = comparison_stocks
        if st.button("השווה מניות", key="compare_btn"):
            st.session_state.analysis_count += 1
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ניקוי נתונים
    if st.button("🧹 נקה כל נתונים", type="secondary", use_container_width=True):
        st.session_state.clear()
        st.success("✅ כל הנתונים נוקו!")
        st.rerun()

# ----------------------------------------------------------------------
# 6️⃣ כותרת ראשית עם אנימציות
# ----------------------------------------------------------------------
col_title1, col_title2, col_title3 = st.columns([1, 3, 1])
with col_title2:
    st.markdown("<h1 style='text-align: center; color: #2c3e50; animation: fadeIn 1s;'>🚀 התיק החכם PRO</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #7f8c8d;'>ניתוח מניות מתקדם עם AI וגיימיפיקציה</h3>", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# 7️⃣ הזנת סימול מנייה
# ----------------------------------------------------------------------
st.markdown("---")

col_search1, col_search2, col_search3 = st.columns([1, 2, 1])
with col_search2:
    ticker_input = st.text_input(
        "**🔍 חפש מניה (הזן סימול באנגלית):**",
        value="AAPL",
        placeholder="לדוגמה: AAPL, TSLA, GOOGL",
        help="יש להזין סימול מנייה באנגלית"
    ).upper().strip()

# הצגת מניות מובילות להקלקה מהירה
st.markdown("### 📋 מניות מובילות")
popular_stocks = ["AAPL", "TSLA", "GOOGL", "MSFT", "AMZN", "META", "NVDA", "NFLX"]
cols = st.columns(len(popular_stocks))

for idx, stock in enumerate(popular_stocks):
    with cols[idx]:
        if st.button(stock, key=f"btn_{stock}", use_container_width=True):
            ticker_input = stock
            st.rerun()

# ----------------------------------------------------------------------
# 8️⃣ טעינת נתונים וניתוח מתקדם
# ----------------------------------------------------------------------
if ticker_input:
    with st.spinner(f"🤖 טוען נתונים מתקדמים עבור {ticker_input}..."):
        # טעינת נתוני מניה
try:
    stock_data = yf.download(ticker_input, period="6mo", progress=False, auto_adjust=True)
    
    # המרת MultiIndex לעמודות רגילות
    if isinstance(stock_data.columns, pd.MultiIndex):
        stock_data.columns = stock_data.columns.get_level_values(0)
    
    # אם עדיין יש בעיה, ננסה להוריד שוב עם הגדרות אחרות
    if stock_data.empty:
        stock_data = yf.download(ticker_input, period="3mo", progress=False, auto_adjust=False)
        
except Exception as e:
    st.error(f"❌ שגיאה בטעינת נתונים: {str(e)}")
    # ניסיון נוסף עם פרמטרים שונים
    try:
        stock_data = yf.download(ticker_input, period="1mo", progress=False)
    except:
        st.error("❌ לא ניתן לטעון נתונים. נסה סימול אחר.")
        st.stop()        
        if stock_data.empty:
            st.error(f"❌ לא נמצאו נתונים עבור {ticker_input}")
            st.stop()
        
        # טעינת מידע על החברה
        try:
            stock_info = yf.Ticker(ticker_input).info
            company_name = stock_info.get('longName', ticker_input)
        except:
            stock_info = {}
            company_name = ticker_input
        
        # חישוב אינדיקטורים מתקדמים
# ---------- פונקציות אינדיקטורים מתקדמות ----------
def calculate_advanced_indicators(df):
    """מחשב אינדיקטורים טכניים מתקדמים"""
    
    # יצירת עותק בטוח של DataFrame
    df_calc = df.copy()
    
    # תיקון קריטי: המרת MultiIndex לעמודות רגילות
    if isinstance(df_calc.columns, pd.MultiIndex):
        # אם יש MultiIndex, ניקח רק את הרמה הראשונה
        df_calc.columns = df_calc.columns.get_level_values(0)
    
    # וידוא שיש לנו את העמודות הנדרשות
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_columns = [col for col in required_columns if col not in df_calc.columns]
    
    if missing_columns:
        st.warning(f"⚠️ חסרות עמודות: {missing_columns}. משתמש בעמודות זמינות.")
        # ננסה למצוא עמודות חלופיות
        for col in missing_columns:
            if col in ['Open', 'High', 'Low', 'Close']:
                # אם חסרה עמודת מחיר, ננסה להשתמש ב'Adj Close' אם קיים
                if 'Adj Close' in df_calc.columns and col == 'Close':
                    df_calc[col] = df_calc['Adj Close']
                else:
                    # אם אין נתון, נשתמש בעמודה הקיימת הראשונה
                    df_calc[col] = df_calc.iloc[:, 0]
            elif col == 'Volume':
                # ל-volume ניתן ערך דיפולטיבי
                df_calc[col] = 1000
    
    # ניקוי עמודות כפולות (במקרה שיש)
    df_calc = df_calc.loc[:, ~df_calc.columns.duplicated()]
    
    # וידוא שיש לנו מספיק נתונים
    if len(df_calc) < 20:
        st.warning("⚠️ אין מספיק נתונים לחישוב אינדיקטורים מתקדמים")
        return df_calc
    
    try:
        # ממוצעים נעים בסיסיים
        df_calc['SMA_20'] = df_calc['Close'].rolling(20, min_periods=1).mean()
        df_calc['SMA_50'] = df_calc['Close'].rolling(50, min_periods=1).mean()
        df_calc['SMA_200'] = df_calc['Close'].rolling(200, min_periods=1).mean()
        
        # EMA
        df_calc['EMA_12'] = df_calc['Close'].ewm(span=12, min_periods=1).mean()
        df_calc['EMA_26'] = df_calc['Close'].ewm(span=26, min_periods=1).mean()
        
        # MACD
        df_calc['MACD'] = df_calc['EMA_12'] - df_calc['EMA_26']
        df_calc['MACD_Signal'] = df_calc['MACD'].ewm(span=9, min_periods=1).mean()
        df_calc['MACD_Histogram'] = df_calc['MACD'] - df_calc['MACD_Signal']
        
        # RSI
        delta = df_calc['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(14, min_periods=1).mean()
        avg_loss = loss.rolling(14, min_periods=1).mean()
        
        # הגנה מפני חלוקה באפס
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df_calc['RSI'] = 100 - (100 / (1 + rs))
        df_calc['RSI'] = df_calc['RSI'].fillna(50)  # ערך ברירת מחדל
        
        # Bollinger Bands - עם הגנות
        df_calc['BB_Middle'] = df_calc['Close'].rolling(20, min_periods=1).mean()
        bb_std = df_calc['Close'].rolling(20, min_periods=1).std()
        
        # החלפת NaN ב-0 ב- bb_std
        bb_std = bb_std.fillna(0)
        
        df_calc['BB_Upper'] = df_calc['BB_Middle'] + (bb_std * 2)
        df_calc['BB_Lower'] = df_calc['BB_Middle'] - (bb_std * 2)
        
        return df_calc
        
    except Exception as e:
        # במקרה של שגיאה, החזר את ה-DataFrame המקורי
        st.error(f"❌ שגיאה בחישוב אינדיקטורים: {str(e)}")
          # החזרת DataFrame המקורי במקרה של שגיאה
        return df_calc        
        # זיהוי תבניות
        patterns = detect_chart_patterns(df_with_indicators)
        
        # התראות דיווחים קרובים
        upcoming_events = get_upcoming_events(ticker_input)
        
        # חדשות בעברית
        hebrew_news = get_hebrew_news(ticker_input, company_name)
        
        # המלצות AI
        ai_recommendations = generate_ai_recommendation(df_with_indicators, stock_info, patterns)
    
    st.session_state.analysis_count += 1
    
    # כותרת עם שם החברה
    st.markdown(f"<h2 style='text-align: center;'>📊 {company_name} ({ticker_input})</h2>", unsafe_allow_html=True)
    
    # התראות דיווחים קרובים
    if upcoming_events:
        st.markdown("<div class='alert-pulse' style='background: #fff3cd; padding: 15px; border-radius: 10px; border: 2px solid #ffc107;'>", unsafe_allow_html=True)
        st.markdown("### ⚠️ התראות דיווחים קרובים")
        for event in upcoming_events:
            event_date = event['date'].strftime('%d/%m/%Y') if isinstance(event['date'], datetime) else event['date']
            st.info(f"**{event['type']}** - תאריך משוער: {event_date}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # טאבים מתקדמים
    tab_names = ["📈 ניתוח טכני", "🕯️ נרות יפניים", "🤖 המלצות AI", "📰 חדשות", "📊 השוואת מניות", "🎮 גיימיפיקציה"]
    tabs = st.tabs(tab_names)
    
    # ==============================================================
    # טאב 1: ניתוח טכני מתקדם
    # ==============================================================
    with tabs[0]:
        # יצירת גרף עם subplots
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.5, 0.2, 0.15, 0.15],
            subplot_titles=("מחיר וממוצעים נעים", "נפח מסחר", "מדד RSI", "מדד MACD")
        )
        
        # גרף מחיר עם ממוצעים
        fig.add_trace(
            go.Scatter(x=df_with_indicators.index, y=df_with_indicators['Close'], name="מחיר", line=dict(color='#3498db')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_with_indicators.index, y=df_with_indicators['SMA_20'], name="ממוצע 20 ימים", line=dict(color='#e74c3c', dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_with_indicators.index, y=df_with_indicators['SMA_50'], name="ממוצע 50 ימים", line=dict(color='#2ecc71', dash='dash')),
            row=1, col=1
        )
        
        # Bollinger Bands
        fig.add_trace(
            go.Scatter(x=df_with_indicators.index, y=df_with_indicators['BB_Upper'], name="בולינגר עליון", line=dict(color='rgba(231, 76, 60, 0.3)'), showlegend=False),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_with_indicators.index, y=df_with_indicators['BB_Lower'], name="בולינגר תחתון", line=dict(color='rgba(231, 76, 60, 0.3)'), fill='tonexty', fillcolor='rgba(231, 76, 60, 0.1)', showlegend=False),
            row=1, col=1
        )
        
        # נפח
        colors = ['red' if row['Open'] > row['Close'] else 'green' for _, row in df_with_indicators.iterrows()]
        fig.add_trace(
            go.Bar(x=df_with_indicators.index, y=df_with_indicators['Volume'], name="נפח", marker_color=colors),
            row=2, col=1
        )
        
        # RSI
        fig.add_trace(
            go.Scatter(x=df_with_indicators.index, y=df_with_indicators['RSI'], name="RSI", line=dict(color='#9b59b6')),
            row=3, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        
        # MACD
        fig.add_trace(
            go.Scatter(x=df_with_indicators.index, y=df_with_indicators['MACD'], name="MACD", line=dict(color='#3498db')),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_with_indicators.index, y=df_with_indicators['MACD_Signal'], name="סיגנל", line=dict(color='#e74c3c')),
            row=4, col=1
        )
        
        # היסטוגרמה
        colors_macd = ['green' if val >= 0 else 'red' for val in df_with_indicators['MACD_Histogram']]
        fig.add_trace(
            go.Bar(x=df_with_indicators.index, y=df_with_indicators['MACD_Histogram'], name="היסטוגרמה", marker_color=colors_macd),
            row=4, col=1
        )
        
        fig.update_layout(height=800, showlegend=True, title_text="ניתוח טכני מתקדם")
        st.plotly_chart(fig, use_container_width=True)
        
        # תצוגת אינדיקטורים מספריים
        st.markdown("### 📊 ערכי אינדיקטורים נוכחיים")
        
        col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
        
        with col_metrics1:
            st.metric("מחיר נוכחי", f"${df_with_indicators['Close'].iloc[-1]:.2f}")
            st.metric("RSI", f"{df_with_indicators['RSI'].iloc[-1]:.1f}")
        
        with col_metrics2:
            st.metric("ממוצע 20 ימים", f"${df_with_indicators['SMA_20'].iloc[-1]:.2f}")
            st.metric("ממוצע 50 ימים", f"${df_with_indicators['SMA_50'].iloc[-1]:.2f}")
        
        with col_metrics3:
            st.metric("בולינגר עליון", f"${df_with_indicators['BB_Upper'].iloc[-1]:.2f}")
            st.metric("בולינגר תחתון", f"${df_with_indicators['BB_Lower'].iloc[-1]:.2f}")
        
        with col_metrics4:
            st.metric("MACD", f"{df_with_indicators['MACD'].iloc[-1]:.4f}")
            st.metric("נפח יחסי", f"{df_with_indicators['Volume_Ratio'].iloc[-1]:.2f}x")
    
    # ==============================================================
    # טאב 2: נרות יפניים
    # ==============================================================
    with tabs[1]:
        st.markdown("### 🕯️ גרף נרות יפניים עם אינדיקטורים")
        
        # בחירת תקופה
        period_options = {
            "1 חודש": "1mo",
            "3 חודשים": "3mo", 
            "6 חודשים": "6mo",
            "שנה": "1y",
            "2 שנים": "2y"
        }
        
        selected_period = st.selectbox("בחר תקופה", list(period_options.keys()), index=2)
        
        # טעינת נתונים לפי התקופה הנבחרת
        if selected_period:
            period_data = yf.download(ticker_input, period=period_options[selected_period], progress=False)
            
            if not period_data.empty:
                # יצירת גרף נרות
                fig_candles = create_candlestick_chart(period_data, f"נרות יפניים - {selected_period}")
                
                # הוספת ממוצעים נעים
                period_data['SMA_20'] = period_data['Close'].rolling(20).mean()
                period_data['SMA_50'] = period_data['Close'].rolling(50).mean()
                
                fig_candles.add_trace(
                    go.Scatter(x=period_data.index, y=period_data['SMA_20'], 
                             name="ממוצע 20 ימים", line=dict(color='orange', width=1))
                )
                fig_candles.add_trace(
                    go.Scatter(x=period_data.index, y=period_data['SMA_50'], 
                             name="ממוצע 50 ימים", line=dict(color='purple', width=1))
                )
                
                st.plotly_chart(fig_candles, use_container_width=True)
                
                # תצוגת תבניות שזוהו
                if patterns:
                    st.markdown("### 🎯 תבניות טכניות שזוהו")
                    pattern_cols = st.columns(min(3, len(patterns)))
                    
                    for idx, pattern in enumerate(patterns):
                        with pattern_cols[idx % len(pattern_cols)]:
                            confidence_color = "green" if pattern['confidence'] > 75 else "orange" if pattern['confidence'] > 60 else "red"
                            signal_color = "green" if pattern['signal'] == 'קנייה' else "red" if pattern['signal'] == 'מכירה' else "blue"
                            
                            st.markdown(f"""
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid {signal_color};">
                                <h4>{pattern['name']}</h4>
                                <p style="color: {confidence_color}; font-weight: bold;">בטחון: {pattern['confidence']}%</p>
                                <p style="color: {signal_color};">איתור: {pattern['signal']}</p>
                            </div>
                            """, unsafe_allow_html=True)
    
    # ==============================================================
    # טאב 3: המלצות AI
    # ==============================================================
    with tabs[2]:
        st.markdown("### 🤖 המלצות בינה מלאכותית")
        
        col_ai1, col_ai2 = st.columns([2, 1])
        
        with col_ai1:
            # תצוגת המלצות AI
            st.markdown("#### 📝 ניתוח AI מתקדם")
            
            for i, recommendation in enumerate(ai_recommendations):
                st.markdown(f"""
                <div class="chat-bubble">
                    <strong>המלצה #{i+1}:</strong><br>
                    {recommendation}
                </div>
                """, unsafe_allow_html=True)
            
            # סיכום AI
            st.markdown("#### 📊 סיכום AI")
            
            # חישוב ציון כולל
            total_score = 0
            max_score = len(ai_recommendations) * 20
            
            # ניתוח רגשי פשוט
            positive_keywords = ['קנייה', 'עלייה', 'מעולה', 'שמרנית', 'סבירים']
            negative_keywords = ['מכירה', 'ירידה', 'מסוכנת', 'חלשים', 'היזהר']
            
            positive_count = sum(1 for rec in ai_recommendations if any(keyword in rec for keyword in positive_keywords))
            negative_count = sum(1 for rec in ai_recommendations if any(keyword in rec for keyword in negative_keywords))
            
            sentiment = "חיובי" if positive_count > negative_count else "שלילי" if negative_count > positive_count else "ניטרלי"
            sentiment_color = "green" if sentiment == "חיובי" else "red" if sentiment == "שלילי" else "gray"
            
            st.metric("📈 רגש כללי", sentiment, delta_color="off")
            st.markdown(f"<p style='color: {sentiment_color}; font-weight: bold;'>{sentiment} - מבוסס על {len(ai_recommendations)} ניתוחים</p>", unsafe_allow_html=True)
        
        with col_ai2:
            # ויזואליזציה של ההמלצות
            st.markdown("#### 📊 התפלגות ההמלצות")
            
            categories = {
                'חיובי': positive_count,
                'שלילי': negative_count,
                'ניטרלי': len(ai_recommendations) - positive_count - negative_count
            }
            
            fig_pie = px.pie(
                values=list(categories.values()),
                names=list(categories.keys()),
                color=list(categories.keys()),
                color_discrete_map={'חיובי': '#2ecc71', 'שלילי': '#e74c3c', 'ניטרלי': '#95a5a6'},
                hole=0.4
            )
            
            fig_pie.update_layout(
                title="חלוקת הרגש בהמלצות",
                height=300,
                showlegend=True
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # כפתור רענון המלצות
            if st.button("🔄 רענן המלצות AI", key="refresh_ai"):
                st.session_state.analysis_count += 1
                st.rerun()
    
    # ==============================================================
    # טאב 4: חדשות
    # ==============================================================
    with tabs[3]:
        st.markdown("### 📰 חדשות פיננסיות בעברית")
        
        # סימולציה של חדשות
        for news in hebrew_news:
            sentiment_color = "green" if news['sentiment'] == 'חיובי' else "red" if news['sentiment'] == 'שלילי' else "blue"
            
            st.markdown(f"""
            <div style="background: white; border-radius: 10px; padding: 15px; margin: 10px 0; border-left: 5px solid {sentiment_color}; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h4>{news['title']}</h4>
                <p style="color: #666;">{news['summary']}</p>
                <div style="display: flex; justify-content: space-between; color: #999; font-size: 0.9rem;">
                    <span>📅 {news['date']}</span>
                    <span>🎭 {news['sentiment']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # מקורות חדשות נוספים
        st.markdown("---")
        st.markdown("### 🔗 מקורות חדשות נוספים")
        
        news_sources = [
            {"name": "גלובס", "url": "https://www.globes.co.il", "category": "כלכלה"},
            {"name": "TheMarker", "url": "https://www.themarker.com", "category": "שווקים"},
            {"name": "כלכליסט", "url": "https://www.calcalist.co.il", "category": "טכנולוגיה"},
            {"name": "ביזפורטל", "url": "https://www.bizportal.co.il", "category": "בורסה"}
        ]
        
        source_cols = st.columns(len(news_sources))
        
        for idx, source in enumerate(news_sources):
            with source_cols[idx]:
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; border: 1px solid #e0e0e0; border-radius: 8px;">
                    <strong>{source['name']}</strong><br>
                    <small>{source['category']}</small>
                </div>
                """, unsafe_allow_html=True)
    
    # ==============================================================
    # טאב 5: השוואת מניות
    # ==============================================================
    with tabs[4]:
        st.markdown("### 📊 השוואה בין מניות")
        
        if st.session_state.comparison_stocks:
            comparison_df = compare_stocks(st.session_state.comparison_stocks)
            
            if not comparison_df.empty:
                # גרף השוואת מחירים
                fig_comparison = px.line(
                    comparison_df, 
                    x='Ticker', 
                    y='Price',
                    color='Ticker',
                    title="השוואת מחירים נוכחיים",
                    labels={'Price': 'מחיר (USD)', 'Ticker': 'סימול מנייה'}
                )
                
                st.plotly_chart(fig_comparison, use_container_width=True)
                
                # גרף שינוי חודשי
                fig_change = px.bar(
                    comparison_df,
                    x='Ticker',
                    y='Change_1M',
                    color='Change_1M',
                    color_continuous_scale=['red', 'white', 'green'],
                    title="שינוי מחיר בחודש האחרון (%)",
                    labels={'Change_1M': 'שינוי (%)', 'Ticker': 'סימול מנייה'}
                )
                
                st.plotly_chart(fig_change, use_container_width=True)
                
                # טבלת השוואה
                st.markdown("#### 📋 נתונים מספריים")
                
                display_df = comparison_df.copy()
                display_df['Price'] = display_df['Price'].apply(lambda x: f"${x:,.2f}")
                display_df['Change_1M'] = display_df['Change_1M'].apply(lambda x: f"{x:+.2f}%")
                display_df['Volume'] = display_df['Volume'].apply(lambda x: f"{x:,.0f}")
                display_df['Market_Cap'] = display_df['Market_Cap'].apply(lambda x: f"${x/1e9:.2f}B" if x > 1e9 else f"${x/1e6:.2f}M")
                
                st.dataframe(
                    display_df,
                    column_config={
                        "Ticker": "סימול",
                        "Name": "שם החברה",
                        "Price": "מחיר",
                        "Change_1M": "שינוי חודשי",
                        "Volume": "נפח ממוצע",
                        "Market_Cap": "שווי שוק"
                    },
                    use_container_width=True
                )
    
    # ==============================================================
    # טאב 6: גיימיפיקציה
    # ==============================================================
    with tabs[5]:
        st.markdown("### 🎮 משחק סימולטור מסחר")
        
        col_game1, col_game2 = st.columns(2)
        
        with col_game1:
            st.markdown("#### 🏆 לוח מובילים")
            
            # סימולציה של לוח מובילים
            leaderboard = [
                {"name": "משה לוי", "score": 250, "badges": 5},
                {"name": "שרה כהן", "score": 180, "badges": 4},
                {"name": "דוד מזרחי", "score": 150, "badges": 3},
                {"name": "אתה", "score": st.session_state.user_score, "badges": len(st.session_state.badges)}
            ]
            
            for i, player in enumerate(leaderboard):
                trophy = "🏆" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "👤"
                st.markdown(f"""
                <div style="background: {'#fff3cd' if player['name'] == 'אתה' else '#f8f9fa'}; 
                            padding: 10px; border-radius: 8px; margin: 5px 0; 
                            border-left: 4px solid {'#ffc107' if player['name'] == 'אתה' else '#6c757d'};">
                    <strong>{trophy} {player['name']}</strong><br>
                    <small>ניקוד: {player['score']} | תגים: {player['badges']}</small>
                </div>
                """, unsafe_allow_html=True)
        
        with col_game2:
            st.markdown("#### 🎯 אתגרים שבועיים")
            
            challenges = [
                {"name": "ניתוח 5 מניות", "progress": min(st.session_state.analysis_count, 5), "target": 5, "reward": 25},
                {"name": "הוסף 3 פוזיציות", "progress": min(len(st.session_state.trades), 3), "target": 3, "reward": 30},
                {"name": "השווה 2 מניות", "progress": 1 if st.session_state.comparison_stocks else 0, "target": 1, "reward": 15},
                {"name": "צפה בגרף נרות", "progress": 1 if 'נרות יפניים' in tab_names else 0, "target": 1, "reward": 10}
            ]
            
            for challenge in challenges:
                progress_pct = (challenge['progress'] / challenge['target']) * 100
                color = "green" if progress_pct == 100 else "blue"
                
                st.markdown(f"**{challenge['name']}**")
                st.progress(progress_pct / 100)
                st.caption(f"{challenge['progress']}/{challenge['target']} - פרס: {challenge['reward']} נקודות")
        
        # משחק ניחוש מחיר
        st.markdown("---")
        st.markdown("#### 🔮 ניחוש מחיר עתידי")
        
        current_price = df_with_indicators['Close'].iloc[-1]
        
        col_guess1, col_guess2, col_guess3 = st.columns(3)
        
        with col_guess1:
            days_ahead = st.slider("ימים קדימה", 1, 30, 7)
        
        with col_guess2:
            guess_price = st.number_input("מה יהיה המחיר?", 
                                         min_value=0.0,
                                         value=current_price * 1.05,
                                         step=0.1)
        
        with col_guess3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🎲 נחש מחיר", use_container_width=True):
                # סימולציה של חיזוי
                predicted_change = np.random.normal(0.001, 0.02) * days_ahead
                predicted_price = current_price * (1 + predicted_change)
                
                accuracy = 100 - abs((guess_price - predicted_price) / predicted_price * 100)
                
                if accuracy > 90:
                    st.success(f"🎯 מצוין! דיוק: {accuracy:.1f}%")
                    st.session_state.user_score += 20
                elif accuracy > 70:
                    st.info(f"👍 לא רע! דיוק: {accuracy:.1f}%")
                    st.session_state.user_score += 10
                else:
                    st.warning(f"📉 נסה שוב! דיוק: {accuracy:.1f}%")
                
                st.metric("מחיר חוזי", f"${predicted_price:.2f}", 
                         f"{predicted_change*100:.2f}%")

# ----------------------------------------------------------------------
# 9️⃣ Footer מתקדם
# ----------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; border-radius: 15px; margin-top: 30px;">
        <h3>🚀 התיק החכם PRO - גרסה מתקדמת</h3>
        <p>פיתוח: צוות AI וטכנולוגיה | גרסה: 2.0.0</p>
        <div style="display: flex; justify-content: center; gap: 20px; margin-top: 15px;">
            <span>🤖 AI מתקדם</span>
            <span>📈 ניתוח בזמן אמת</span>
            <span>🎮 גיימיפיקציה</span>
            <span>🔔 התראות חכמות</span>
        </div>
        <p style="margin-top: 20px; font-size: 0.9rem; opacity: 0.8;">
            ⚠️ הערה: המערכת נועדה לסיוע בלבד ואינה תחליף לייעוץ מקצועי.<br>
            כל החלטת השקעה צריכה להתבסס על מחקר מעמיק.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# תוספת של JavaScript לאנימציות
components.html("""
<script>
// אנימציות נוספות
document.addEventListener('DOMContentLoaded', function() {
    // אנימציה לכרטיסים
    const cards = document.querySelectorAll('.stock-card, .indicator-box');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
    
    // אנימציה לתגים
    const badges = document.querySelectorAll('.trophy');
    badges.forEach(badge => {
        badge.addEventListener('mouseover', function() {
            this.style.transform = 'scale(1.2)';
        });
        badge.addEventListener('mouseout', function() {
            this.style.transform = 'scale(1)';
        });
    });
});
</script>
""", height=0)


