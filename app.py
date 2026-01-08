# -*- coding: utf-8 -*-
"""
Streamlit – "התיק החכם" (גרסה מתוקנת ומשולבת)
"""

import uuid
import io
import sys
from datetime import datetime
import os

import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go

# הוספת נתיבי התיקיות למערכת
sys.path.insert(0, './core')
sys.path.insert(0, './utils')

# ייבוא מודולים מותאמים עם טיפול בשגיאות
try:
    from core.indicators import calculate_all_indicators, calculate_final_score, get_smart_analysis, analyze_fundamentals
    from core.data import load_stock_data
    from utils.export import to_excel
except ImportError as e:
    st.error(f"❌ שגיאה בייבוא מודולים: {e}")
    st.info("""
    **פתרון:**
    1. ודא שקיימות התיקיות הבאות:
       - `core/` עם הקבצים: `indicators.py`, `data.py`
       - `utils/` עם הקובץ: `export.py`
    2. אם התיקיות לא קיימות, צור אותן והעבר את הקבצים המתאימים
    """)
    
    # יצירת מבנה תיקיות אוטומטי (אופציונלי)
    if st.button("📁 צור מבנה תיקיות אוטומטית"):
        os.makedirs("core", exist_ok=True)
        os.makedirs("utils", exist_ok=True)
        st.success("✅ תיקיות נוצרו! אנא העלה את הקבצים המתאימים.")
    st.stop()

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
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# 2️⃣ הגדרות sidebar
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
# 4️⃣ UI – כותרת ראשית
# ----------------------------------------------------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("https://cdn-icons-png.flaticon.com/512/3124/3124975.png", width=80)
    st.title("📈 התיק החכם")
    st.caption("כלים לניתוח, מעקב ו-journaling של מניות – בעברית")

# ----------------------------------------------------------------------
# 5️⃣ הזנת סימול מנייה
# ----------------------------------------------------------------------
col_left, col_center, col_right = st.columns([1, 3, 1])
with col_center:
    ticker_input = st.text_input(
        "הזן סימול מנייה (למשל TSLA, AAPL, GOOGL)",
        value="AAPL",
        help="יש להזין סימול באנגלית. דוגמאות: TSLA, AAPL, MSFT, GOOGL"
    ).upper().strip()

# ----------------------------------------------------------------------
# 6️⃣ טעינת נתונים וניתוח
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📊 ניתוח טכני", "🏢 נתונים פונדמנטליים", "💼 ניהול פורטפוליו", "📓 יומן פוזיציות", "📈 סיכום תיק"]
    )
    
    # --------------------------------------------------------------
    # טאב 1: ניתוח טכני
    # --------------------------------------------------------------
    with tab1:
        # חישוב אינדיקטורים
        df_with_indicators, periods = calculate_all_indicators(df_price.copy(), ma_type)
        
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
                showlegend=True
            ))
            fig_price.add_trace(go.Scatter(
                x=df_with_indicators.index,
                y=df_with_indicators['BB_Lower'],
                name='Bollinger Lower',
                line=dict(color='rgba(255, 107, 107, 0.5)', width=1),
                fill='tonexty',
                fillcolor='rgba(255, 107, 107, 0.1)',
                showlegend=True
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
                
                metrics = {
                    "מחיר נוכחי": f"${current_price:.2f}",
                    "שינוי יומי": f"{daily_change:+.2f}%",
                    "מחיר פתיחה": f"${df_price['Open'].iloc[-1]:.2f}",
                    "גבוה יומי": f"${df_price['High'].iloc[-1]:.2f}",
                    "נמוך יומי": f"${df_price['Low'].iloc[-1]:.2f}"
                }
                
                for key, value in metrics.items():
                    st.metric(key, value)
                
                st.markdown("---")
                
                # מדדים פונדמנטליים נוספים
                if stock_info:
                    fundamental_metrics = {}
                    
                    if 'forwardPE' in stock_info and stock_info['forwardPE']:
                        fundamental_metrics["P/E Ratio"] = f"{stock_info['forwardPE']:.2f}"
                    
                    if 'marketCap' in stock_info and stock_info['marketCap']:
                        market_cap = stock_info['marketCap']
                        if market_cap > 1e12:
                            fundamental_metrics["Market Cap"] = f"${market_cap/1e12:.2f}T"
                        elif market_cap > 1e9:
                            fundamental_metrics["Market Cap"] = f"${market_cap/1e9:.2f}B"
                        else:
                            fundamental_metrics["Market Cap"] = f"${market_cap/1e6:.2f}M"
                    
                    if 'dividendYield' in stock_info and stock_info['dividendYield']:
                        fundamental_metrics["Dividend Yield"] = f"{stock_info['dividendYield']*100:.2f}%"
                    
                    for key, value in fundamental_metrics.items():
                        st.text(f"{key}: {value}")
            
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
        
        col_price, col_shares, col_action = st.columns([2, 2, 1])
        
        with col_price:
            current_price = df_price['Close'].iloc[-1]
            price_to_save = st.number_input(
                "מחיר קנייה (USD)",
                min_value=0.0,
                value=round(current_price, 2),
                step=0.01,
                key="buy_price"
            )
        
        with col_shares:
            shares_to_save = st.number_input(
                "כמות מניות",
                min_value=1,
                step=1,
                value=100,
                key="shares_amount"
            )
        
        with col_action:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"➕ הוסף {ticker_input}", use_container_width=True):
                add_trade(ticker_input, price_to_save, shares_to_save)
                st.success(f"✅ פוזיציה של {ticker_input} נוספה בהצלחה!")
                st.rerun()
        
        # הצעת מחיר אוטומטית
        st.info(f"💡 מחיר נוכחי: ${current_price:.2f} | שווי פוזיציה מוצע: ${current_price * shares_to_save:.2f}")
    
    # --------------------------------------------------------------
    # טאב 4: יומן פוזיציות
    # --------------------------------------------------------------
    with tab4:
        st.markdown("### 📋 פוזיציות פעילות")
        
        if not st.session_state.trades:
            st.info("📝 עדיין לא הוספת פוזיציות. עבור לטאב 'ניהול פורטפוליו' כדי להוסיף.")
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
                            'Current Price': current_price,
                            'Current Value': current_value,
                            'P&L ($)': profit_loss,
                            'P&L (%)': profit_loss_pct
                        })
                    else:
                        current_values.append({
                            'Current Price': None,
                            'Current Value': None,
                            'P&L ($)': None,
                            'P&L (%)': None
                        })
                except Exception as e:
                    st.warning(f"לא ניתן לטעון נתונים עבור {ticker}: {str(e)}")
                    current_values.append({
                        'Current Price': None,
                        'Current Value': None,
                        'P&L ($)': None,
                        'P&L (%)': None
                    })
            
            # הוספת עמודות חדשות
            if current_values:
                current_df = pd.DataFrame(current_values)
                display_df = pd.concat([trades_df, current_df], axis=1)
                
                # הסדר עמודות
                display_df = display_df[['Ticker', 'Price', 'Shares', 'Date', 
                                        'Current Price', 'Current Value', 'P&L ($)', 'P&L (%)']]
                
                # תצוגת טבלה מעוצבת
                st.dataframe(
                    display_df.style.format({
                        'Price': '${:,.2f}',
                        'Current Price': '${:,.2f}',
                        'Current Value': '${:,.2f}',
                        'P&L ($)': '${:+,.2f}',
                        'P&L (%)': '{:+.2f}%'
                    }, na_rep="N/A").apply(
                        lambda x: ['background-color: #ffcccc' if isinstance(v, (int, float)) and v < 0 
                                  else 'background-color: #ccffcc' if isinstance(v, (int, float)) and v > 0 
                                  else '' for v in x],
                        subset=['P&L ($)', 'P&L (%)']
                    ),
                    use_container_width=True
                )
            
            # כפתורי פעולה
            col_del1, col_del2, col_del3 = st.columns(3)
            
            with col_del1:
                if st.button("🗑️ מחק פוזיציה אחרונה", use_container_width=True):
                    if st.session_state.trades:
                        last_trade_id = list(st.session_state.trades.keys())[-1]
                        delete_trade(last_trade_id)
                        st.success("✅ הפוזיציה האחרונה נמחקה!")
                        st.rerun()
            
            with col_del2:
                if st.session_state.trades:
                    csv_buffer = io.StringIO()
                    trades_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 הורד CSV",
                        data=csv_buffer.getvalue(),
                        file_name=f"trades_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            with col_del3:
                if st.session_state.trades:
                    excel_buffer = to_excel(trades_df)
                    st.download_button(
                        label="📊 הורד Excel",
                        data=excel_buffer,
                        file_name=f"trades_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
    
    # --------------------------------------------------------------
    # טאב 5: סיכום תיק
    # --------------------------------------------------------------
    with tab5:
        if st.session_state.portfolio.shape[0] > 0:
            st.markdown("### 📊 סיכום תיק השקעות")
            
            # חישוב ערכים נוכחיים
            portfolio_summary = []
            total_invested = 0
            total_current = 0
            
            for ticker in st.session_state.portfolio["Ticker"].unique():
                positions = st.session_state.portfolio[st.session_state.portfolio["Ticker"] == ticker]
                invested = (positions["EntryPrice"] * positions["Shares"]).sum()
                
                # קבלת מחיר נוכחי
                try:
                    df_tmp, _, _ = load_stock_data(ticker)
                    if df_tmp is not None and not df_tmp.empty:
                        current_price = df_tmp["Close"].iloc[-1]
                        current_value = current_price * positions["Shares"].sum()
                        
                        portfolio_summary.append({
                            "Ticker": ticker,
                            "Shares": positions["Shares"].sum(),
                            "Avg Entry": positions["EntryPrice"].mean(),
                            "Current Price": current_price,
                            "Invested": invested,
                            "Current Value": current_value,
                            "P&L": current_value - invested,
                            "P&L %": ((current_value - invested) / invested) * 100 if invested > 0 else 0
                        })
                        
                        total_invested += invested
                        total_current += current_value
                except Exception as e:
                    st.warning(f"לא ניתן לטעון מחיר נוכחי עבור {ticker}")
            
            if portfolio_summary:
                summary_df = pd.DataFrame(portfolio_summary)
                
                # הצגת טבלה
                st.dataframe(
                    summary_df.style.format({
                        'Avg Entry': '${:,.2f}',
                        'Current Price': '${:,.2f}',
                        'Invested': '${:,.2f}',
                        'Current Value': '${:,.2f}',
                        'P&L': '${:+,.2f}',
                        'P&L %': '{:+.2f}%'
                    }),
                    use_container_width=True
                )
                
                # מדדים סיכומיים
                total_pl = total_current - total_invested
                total_pl_pct = (total_pl / total_invested) * 100 if total_invested > 0 else 0
                
                col_sum1, col_sum2, col_sum3 = st.columns(3)
                
                with col_sum1:
                    st.metric("💰 הון מושקע", f"${total_invested:,.2f}")
                
                with col_sum2:
                    st.metric("📈 שווי נוכחי", f"${total_current:,.2f}")
                
                with col_sum3:
                    st.metric("🎯 רווח/הפסד", 
                             f"${total_pl:,.2f}",
                             f"{total_pl_pct:+.2f}%")
                
                # גרף עוגה - חלוקת תיק
                if len(summary_df) > 0:
                    st.markdown("### 🥧 חלוקת התיק לפי מניות")
                    fig_pie = px.pie(
                        summary_df,
                        values="Invested",
                        names="Ticker",
                        title="התפלגות השקעות לפי מניות",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                
        else:
            st.info("📭 התיק שלך ריק. הוסף פוזיציות כדי לראות סיכום כאן.")

# ----------------------------------------------------------------------
# 7️⃣ Footer
# ----------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; padding: 20px;">
        <h3>💡 אודות "התיק החכם"</h3>
        <p>מערכת לניהול תיק השקעות וניתוח מניות בעברית</p>
        <p style="font-size: 0.9rem; color: #666;">
            © 2024 התיק החכם | 
            <a href="https://github.com/" target="_blank">קוד פתוח</a> | 
            <a href="#" target="_blank">מדריך שימוש</a> |
            <a href="#" target="_blank">תנאי שימוש</a>
        </p>
        <p style="font-size: 0.8rem; color: #999;">
            ⚠️ הערה: האפליקציה נועדה לסיוע בניתוח בלבד ואינה מהווה ייעוץ השקעות.<br>
            יש לבצע מחקר עצמאי לפני כל החלטת השקעה.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

