# -*- coding: utf-8 -*-
"""
התיק החכם - גרסה בסיסית ויציבה
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
# 1️⃣ הגדרות בסיסיות
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="התיק החכם",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS בסיסי
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-size: cover;
}

.main .block-container {
    background-color: rgba(255,255,255,0.98);
    padding: 2rem;
    border-radius: 20px;
    margin-top: 1rem;
    direction: rtl;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

h1, h2, h3, h4 {
    color: #2c3e50;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.stButton > button {
    width: 100%;
    background: linear-gradient(45deg, #3498db 0%, #2ecc71 100%);
    color: white;
    border: none;
    padding: 0.75rem;
    border-radius: 10px;
    font-weight: bold;
}

.stTextInput input {
    text-align: center;
    border-radius: 10px;
    border: 2px solid #3498db;
}

.stock-card {
    background: white;
    border-radius: 15px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
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
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# 2️⃣ פונקציות ליבה
# ----------------------------------------------------------------------

@st.cache_data(ttl=3600)
def load_stock_data(ticker):
    """טוען נתוני מניות מ-yfinance"""
    try:
        df = yf.download(ticker, period="6mo", progress=False, auto_adjust=True)
        
        # המרת MultiIndex לעמודות רגילות
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
        except:
            pass
        
        return df, info, full_name
        
    except Exception as e:
        st.error(f"❌ שגיאה בטעינת נתונים: {str(e)}")
        return None, None, ticker

def calculate_basic_indicators(df):
    """מחשב אינדיקטורים טכניים בסיסיים"""
    try:
        df_calc = df.copy()
        
        # וידוא שיש עמודות נדרשות
        if 'Close' not in df_calc.columns:
            if 'Adj Close' in df_calc.columns:
                df_calc['Close'] = df_calc['Adj Close']
            else:
                return df
        
        # ממוצעים נעים
        df_calc['SMA_20'] = df_calc['Close'].rolling(20, min_periods=1).mean()
        df_calc['SMA_50'] = df_calc['Close'].rolling(50, min_periods=1).mean()
        
        # RSI
        delta = df_calc['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(14, min_periods=1).mean()
        avg_loss = loss.rolling(14, min_periods=1).mean()
        
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df_calc['RSI'] = 100 - (100 / (1 + rs))
        df_calc['RSI'] = df_calc['RSI'].fillna(50)
        
        # Bollinger Bands
        df_calc['BB_Middle'] = df_calc['Close'].rolling(20, min_periods=1).mean()
        bb_std = df_calc['Close'].rolling(20, min_periods=1).std().fillna(0)
        df_calc['BB_Upper'] = df_calc['BB_Middle'] + (bb_std * 2)
        df_calc['BB_Lower'] = df_calc['BB_Middle'] - (bb_std * 2)
        
        return df_calc
        
    except Exception as e:
        st.error(f"❌ שגיאה בחישוב אינדיקטורים: {str(e)}")
        return df

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

def get_usd_ils_rate():
    """מביא שער דולר/שקל"""
    try:
        ticker = yf.Ticker("USDILS=X")
        hist = ticker.history(period="1d")
        if not hist.empty:
            rate = hist['Close'].iloc[-1]
            change = hist['Close'].iloc[-1] - hist['Open'].iloc[-1]
            change_pct = (change / hist['Open'].iloc[-1]) * 100
            return round(rate, 3), round(change, 3), round(change_pct, 2)
    except:
        pass
    
    return 3.65, -0.02, -0.54

def analyze_fundamentals(info):
    """מנתח נתונים פונדמנטליים"""
    insights = []
    
    if not info:
        return ["אין נתונים פונדמנטליים זמינים"]
    
    try:
        pe = info.get('forwardPE', info.get('trailingPE', None))
        if pe:
            if pe < 15:
                insights.append(f"✅ **מכפיל רווח ({pe:.1f}):** המניה זולה יחסית")
            elif pe > 40:
                insights.append(f"⚠️ **מכפיל רווח ({pe:.1f}):** המניה יקרה")
        
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        target_price = info.get('targetMeanPrice', info.get('targetMedianPrice', 0))
        
        if current_price and target_price and current_price > 0:
            upside = ((target_price - current_price) / current_price) * 100
            if upside > 15:
                insights.append(f"🎯 **תחזית אנליסטים:** צופים עלייה של {upside:.1f}%")
        
        margins = info.get('profitMargins', 0)
        if margins:
            if margins > 0.2:
                insights.append(f"💎 **רווחיות:** החברה רווחית מאוד")
            elif margins < 0:
                insights.append(f"⚠️ **סיכון:** החברה מפסידה כסף")
    
    except:
        pass
    
    if not insights:
        insights.append("ℹ️ אין מספיק נתונים לניתוח מעמיק")
    
    return insights

def to_excel(df):
    """ממיר DataFrame לקובץ Excel"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Portfolio')
    buffer.seek(0)
    return buffer

# ----------------------------------------------------------------------
# 3️⃣ ניהול Session State
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
# 4️⃣ סיידבר
# ----------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3124/3124975.png", width=100)
    st.title("⚙️ הגדרות")
    
    st.markdown("### 📊 אינדיקטורים")
    show_rsi = st.checkbox("הצג RSI", value=True)
    show_sma = st.checkbox("הצג ממוצעים נעים", value=True)
    
    st.markdown("---")
    
    st.markdown("### 💱 שער דולר/שקל")
    usd_rate, usd_change, usd_change_pct = get_usd_ils_rate()
    st.metric("שער נוכחי", f"{usd_rate} ₪", f"{usd_change_pct:+.2f}%")
    
    st.markdown("---")
    
    if st.button("🧹 נקה נתונים", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("✅ כל הנתונים נוקו!")
        st.rerun()

# ----------------------------------------------------------------------
# 5️⃣ כותרת ראשית
# ----------------------------------------------------------------------
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.image("https://cdn-icons-png.flaticon.com/512/3124/3124975.png", width=80)
    st.title("📈 התיק החכם")
    st.caption("ניתוח מניות וניהול תיק בעברית")

# ----------------------------------------------------------------------
# 6️⃣ חיפוש מניה
# ----------------------------------------------------------------------
st.markdown("---")

col_search1, col_search2, col_search3 = st.columns([1, 2, 1])
with col_search2:
    ticker_input = st.text_input(
        "**🔍 חפש מניה (הזן סימול באנגלית):**",
        value="AAPL",
        placeholder="לדוגמה: AAPL, TSLA, GOOGL"
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
# 7️⃣ טעינת נתונים
# ----------------------------------------------------------------------
if ticker_input:
    with st.spinner(f"טוען נתונים עבור {ticker_input}..."):
        df_price, stock_info, full_name = load_stock_data(ticker_input)
    
    if df_price is None or df_price.empty:
        st.error(f"❌ לא נמצאו נתונים עבור {ticker_input}")
        st.info("נסה אחד מהסימולים: AAPL, TSLA, GOOGL, MSFT")
        st.stop()
    
    company_name = full_name if full_name != ticker_input else ticker_input
    st.markdown(f"<h2 style='text-align: center;'>📊 {company_name} ({ticker_input})</h2>", unsafe_allow_html=True)
    
    # חישוב אינדיקטורים
    df_with_indicators = calculate_basic_indicators(df_price)
    
    # טאבים
    tab_names = ["📈 ניתוח טכני", "🕯️ נרות יפניים", "🏢 נתוני חברה", "💼 ניהול תיק"]
    tabs = st.tabs(tab_names)
    
    # ==============================================================
    # טאב 1: ניתוח טכני
    # ==============================================================
    with tabs[0]:
        # גרף מחיר בסיסי
        fig_price = go.Figure()
        
        fig_price.add_trace(go.Scatter(
            x=df_with_indicators.index,
            y=df_with_indicators['Close'],
            name="מחיר סגור",
            line=dict(color='#3498db', width=2)
        ))
        
        if show_sma:
            fig_price.add_trace(go.Scatter(
                x=df_with_indicators.index,
                y=df_with_indicators['SMA_20'],
                name="ממוצע 20 ימים",
                line=dict(color='#e74c3c', dash='dash')
            ))
            fig_price.add_trace(go.Scatter(
                x=df_with_indicators.index,
                y=df_with_indicators['SMA_50'],
                name="ממוצע 50 ימים",
                line=dict(color='#2ecc71', dash='dash')
            ))
        
        fig_price.update_layout(
            height=500,
            title="גרף מחירים",
            xaxis_title="תאריך",
            yaxis_title="מחיר (USD)",
            template="plotly_white"
        )
        
        st.plotly_chart(fig_price, use_container_width=True)
        
        # אינדיקטורים
        col_ind1, col_ind2, col_ind3 = st.columns(3)
        
        with col_ind1:
            current_price = df_with_indicators['Close'].iloc[-1]
            prev_price = df_with_indicators['Close'].iloc[-2] if len(df_with_indicators) > 1 else current_price
            daily_change = ((current_price - prev_price) / prev_price) * 100
            st.metric("מחיר נוכחי", f"${current_price:.2f}", f"{daily_change:+.2f}%")
        
        with col_ind2:
            if show_rsi and 'RSI' in df_with_indicators.columns:
                rsi_value = df_with_indicators['RSI'].iloc[-1]
                rsi_color = "red" if rsi_value > 70 else "green" if rsi_value < 30 else "blue"
                st.markdown(f"### 📊 RSI")
                st.markdown(f"<h2 style='color: {rsi_color}; text-align: center;'>{rsi_value:.1f}</h2>", unsafe_allow_html=True)
                if rsi_value > 70:
                    st.warning("קניית יתר")
                elif rsi_value < 30:
                    st.success("מכירת יתר")
        
        with col_ind3:
            month_change = ((df_with_indicators['Close'].iloc[-1] - df_with_indicators['Close'].iloc[0]) / df_with_indicators['Close'].iloc[0]) * 100
            st.metric("שינוי חודשי", f"{month_change:+.2f}%")
        
        # גרף נפח
        st.markdown("### 📦 נפח מסחר")
        fig_volume = go.Figure()
        fig_volume.add_trace(go.Bar(
            x=df_price.index,
            y=df_price['Volume'],
            name="נפח",
            marker_color='#3498db'
        ))
        fig_volume.update_layout(height=300, template="plotly_white")
        st.plotly_chart(fig_volume, use_container_width=True)
    
    # ==============================================================
    # טאב 2: נרות יפניים
    # ==============================================================
    with tabs[1]:
        st.markdown("### 🕯️ גרף נרות יפניים")
        
        # יצירת גרף נרות
        fig_candles = create_candlestick_chart(df_price)
        st.plotly_chart(fig_candles, use_container_width=True)
        
        # נתוני מסחר אחרונים
        st.markdown("### 📊 נתוני מסחר אחרונים")
        
        if len(df_price) >= 5:
            recent_data = df_price.tail(5).copy()
            recent_data = recent_data[['Open', 'High', 'Low', 'Close', 'Volume']]
            recent_data.columns = ['פתיחה', 'גבוה', 'נמוך', 'סגירה', 'נפח']
            recent_data.index = recent_data.index.strftime('%d/%m/%Y')
            
            st.dataframe(
                recent_data.style.format({
                    'פתיחה': '${:.2f}',
                    'גבוה': '${:.2f}',
                    'נמוך': '${:.2f}',
                    'סגירה': '${:.2f}',
                    'נפח': '{:,.0f}'
                }),
                use_container_width=True
            )
    
    # ==============================================================
    # טאב 3: נתוני חברה
    # ==============================================================
    with tabs[2]:
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
                    'מטבע': stock_info.get('currency', 'USD')
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
            
            with col_info2:
                st.markdown("### 📊 נתונים פיננסיים")
                
                # מדדים בסיסיים
                metrics_data = {
                    'שווי שוק': stock_info.get('marketCap'),
                    'מכפיל רווח': stock_info.get('forwardPE', stock_info.get('trailingPE')),
                    'תשואת דיבידנד': stock_info.get('dividendYield'),
                    'שולי רווח': stock_info.get('profitMargins')
                }
                
                for key, value in metrics_data.items():
                    if value:
                        if key == 'שווי שוק':
                            if value > 1e12:
                                display_value = f"${value/1e12:.2f}T"
                            elif value > 1e9:
                                display_value = f"${value/1e9:.2f}B"
                            else:
                                display_value = f"${value/1e6:.2f}M"
                        elif key == 'תשואת דיבידנד':
                            display_value = f"{value*100:.2f}%"
                        elif key == 'שולי רווח':
                            display_value = f"{value*100:.1f}%"
                        else:
                            display_value = f"{value:.2f}"
                        
                        st.metric(key, display_value)
            
            # ניתוח פונדמנטלי
            st.markdown("### 🎯 ניתוח פונדמנטלי")
            fundamental_insights = analyze_fundamentals(stock_info)
            for insight in fundamental_insights:
                st.markdown(f"- {insight}")
        
        else:
            st.info("ℹ️ אין מידע נוסף על החברה. נתוני המחיר זמינים בטאבים האחרים.")
    
    # ==============================================================
    # טאב 4: ניהול תיק
    # ==============================================================
    with tabs[3]:
        st.markdown("### 💼 ניהול תיק השקעות")
        
        # הוספת פוזיציה
        st.markdown("#### 🛒 הוספת פוזיציה חדשה")
        
        col_price, col_shares, col_action = st.columns([2, 2, 1])
        
        with col_price:
            current_price = df_with_indicators['Close'].iloc[-1] if len(df_with_indicators) > 0 else 0
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
                    st.success(f"✅ פוזיציה נוספה בהצלחה!")
                    st.rerun()
        
        st.info(f"💡 מחיר נוכחי: **${current_price:.2f}** | שווי פוזיציה: **${current_price * shares_to_save:,.2f}**")
        
        # תצוגת פוזיציות
        st.markdown("---")
        st.markdown("#### 📋 פוזיציות שלי")
        
        if not st.session_state.trades:
            st.info("📝 עדיין אין לך פוזיציות. הוסף פוזיציה ראשונה למעלה.")
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
                        current_price_tmp = df_tmp['Close'].iloc[-1]
                        current_value = current_price_tmp * trade['Shares']
                        profit_loss = current_value - (trade['Price'] * trade['Shares'])
                        profit_loss_pct = (profit_loss / (trade['Price'] * trade['Shares'])) * 100 if (trade['Price'] * trade['Shares']) > 0 else 0
                        
                        current_values.append({
                            'מחיר נוכחי': current_price_tmp,
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
            
            # הצגת הנתונים
            if current_values:
                current_df = pd.DataFrame(current_values)
                display_df = pd.concat([trades_df, current_df], axis=1)
                
                display_df = display_df[['Ticker', 'Price', 'Shares', 'Date', 
                                        'מחיר נוכחי', 'שווי נוכחי', 'רווח/הפסד ($)', 'רווח/הפסד (%)']]
                
                st.dataframe(
                    display_df.style.format({
                        'Price': '${:,.2f}',
                        'מחיר נוכחי': '${:,.2f}',
                        'שווי נוכחי': '${:,.2f}',
                        'רווח/הפסד ($)': '${:+,.2f}',
                        'רווח/הפסד (%)': '{:+.2f}%'
                    }, na_rep="טוען..."),
                    use_container_width=True,
                    height=300
                )
            
            # כפתורי פעולה
            col_actions1, col_actions2, col_actions3 = st.columns(3)
            
            with col_actions1:
                if st.session_state.trades:
                    if st.button("🗑️ מחק אחרונה", use_container_width=True, key="delete_last_button"):
                        last_trade_id = list(st.session_state.trades.keys())[-1]
                        delete_trade(last_trade_id)
                        st.success("✅ הפוזיציה נמחקה!")
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
                        use_container_width=True
                    )
            
            with col_actions3:
                if st.session_state.trades:
                    excel_buffer = to_excel(trades_df)
                    st.download_button(
                        label="📊 הורד Excel",
                        data=excel_buffer,
                        file_name=f"פוזיציות_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

# ----------------------------------------------------------------------
# 8️⃣ Footer
# ----------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px;">
        <h4>💡 התיק החכם</h4>
        <p style="color: #7f8c8d;">כלים לניהול תיק מניות וניתוח טכני בעברית</p>
        <p style="font-size: 0.8rem; color: #bdc3c7;">
            ⚠️ הערה: המערכת נועדה לסיוע בלבד ואינה מהווה ייעוץ השקעות.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
