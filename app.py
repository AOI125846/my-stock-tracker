# -*- coding: utf-8 -*-
"""
Streamlit – “התיק החכם” (גרסה משופרת)
"""

import uuid
import io
from datetime import datetime

import pandas as pd
import numpy as np
import requests
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------------------------
# 1️⃣ הגדרות כלליות של העמוד
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="התיק החכם",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS מותאם – רקע, כיווניות, גודל כפתורים
st.markdown(
    """
    <style>
    /* רקע */
    [data-testid="stAppViewContainer"] {
        background-image: url("https://images.unsplash.com/photo-1521737604893-d14cc237f11d");
        background-size: cover;
        background-attachment: fixed;
    }
    /* קונטיינר מרכזי – רקע חצי שקוף, ריווח ו‑RTL */
    .main .block-container {
        background-color: rgba(255,255,255,0.93);
        padding: 2rem;
        border-radius: 20px;
        margin-top: 2rem;
        direction: rtl;
    }
    /* כפתורים במצב רוחב מלא */
    div.stButton > button { width: 100%; }
    /* קלטים – יישור מרכזי */
    .stTextInput input { text-align: center; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# 2️⃣ כלי עזר – Caching
# ----------------------------------------------------------------------
@st.cache_data(ttl=60 * 10)  # 10 דקות – ניתן לשנות
def fetch_stock_data(symbol: str) -> tuple[pd.DataFrame, dict]:
    """
    טוען את ה‑historical data ואת המידע הפונדמנטלי של המניה.
    משתמש ב‑requests Session עם Header כדי למנוע חסימות.
    """
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (Streamlit)"})

        ticker_obj = yf.Ticker(symbol, session=session)

        # היסטוריית מחיר – 1 שנה
        df = ticker_obj.history(period="1y")
        if df.empty:  # fallback אם ה‑history נכשל
            df = yf.download(symbol, period="1y", progress=False)

        info = ticker_obj.info  # dict עם מידע פונדמנטלי
        return df, info
    except Exception as exc:
        st.exception(exc)
        return None, None


# ----------------------------------------------------------------------
# 3️⃣ ניהול Session State – יומן פוזיציות ו‑Portfolio
# ----------------------------------------------------------------------
if "trades" not in st.session_state:
    st.session_state.trades = {}          # {uuid: {...}}
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(
        columns=["Ticker", "EntryPrice", "Shares", "Date"]
    )  # טבלה נוחה ל‑DataFrame


def add_trade(ticker: str, price: float, shares: int = 1):
    """מוסיף רשומה ליומן הפוזיציות."""
    trade_id = uuid.uuid4().hex[:8]
    st.session_state.trades[trade_id] = {
        "Ticker": ticker,
        "Price": round(price, 2),
        "Shares": shares,
        "Date": datetime.now().strftime("%Y-%m-%d"),
    }

    # עדכון Portfolio DataFrame
    new_row = {
        "Ticker": ticker,
        "EntryPrice": round(price, 2),
        "Shares": shares,
        "Date": datetime.now(),
    }
    st.session_state.portfolio = pd.concat(
        [st.session_state.portfolio, pd.DataFrame([new_row])],
        ignore_index=True,
    )


def delete_trade(trade_id: str):
    """מוחק פוזיציה משני האובייקטים."""
    if trade_id in st.session_state.trades:
        del st.session_state.trades[trade_id]

    # מחיקת השורה מה‑Portfolio לפי מזהה ייחודי (Ticker + Date)
    # נניח שכל פוזיציה נרשמה פעם אחת – נשתמש ב‑index האחרון של אותו Ticker
    ticker = st.session_state.trades.get(trade_id, {}).get("Ticker")
    if ticker:
        mask = st.session_state.portfolio["Ticker"] == ticker
        st.session_state.portfolio = st.session_state.portfolio[~mask]


# ----------------------------------------------------------------------
# 4️⃣ UI – כותרת ראשית והזנת סימול
# ----------------------------------------------------------------------
st.title("📈 התיק החכם")
st.caption("כלים לניתוח, מעקב ו‑journalling של מניות – בעברית, עם UI רספונסיבי")

col_left, col_center, col_right = st.columns([1, 2, 1])
with col_center:
    ticker_input = st.text_input(
        "הזן סימול מנייה (למשל TSLA)", value="AAPL", help="הסימול חייב להיות באנגלית"
    ).upper().strip()

# ----------------------------------------------------------------------
# 5️⃣ קבלת נתונים – עם הודעות משוב למשתמש
# ----------------------------------------------------------------------
if ticker_input:
    with st.spinner(f"מוריד נתונים עבור {ticker_input}..."):
        df_price, stock_info = fetch_stock_data(ticker_input)

    if df_price is None or df_price.empty:
        st.error(
            f"❌ לא נמצאו נתונים עבור `{ticker_input}`. "
            "ודא שהסימול כתוב באנגלית וללא רווחים."
        )
        st.stop()

    # כותרת משנה דינאמית
    st.subheader(f"🔎 ניתוח מניית **{ticker_input}**")

    # ------------------------------------------------------------------
    # 6️⃣ טאבים – גרף, מידע, יומן אישי
    # ------------------------------------------------------------------
    tab_chart, tab_info, tab_journal = st.tabs(
        ["📊 גרף טכני", "🏢 אודות", "📓 יומן אישי"]
    )

    # --------------------------------------------------------------
    # 6.1️⃣ טאב גרף – Plotly + TradingView fallback
    # --------------------------------------------------------------
    with tab_chart:
        # גרף קו סגור + נפח (volume) באמצעות Plotly
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df_price.index,
                y=df_price["Close"],
                name="מחיר סגור",
                mode="lines",
                line=dict(color="#0066CC"),
            )
        )
        fig.add_trace(
            go.Bar(
                x=df_price.index,
                y=df_price["Volume"],
                name="נפח",
                marker_color="#A0C3D2",
                opacity=0.4,
                yaxis="y2",
            )
        )
        fig.update_layout(
            height=500,
            xaxis_title="תאריך",
            yaxis_title="מחיר (USD)",
            yaxis2=dict(
                title="נפח", overlaying="y", side="right", showgrid=False
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="ggplot2",
        )
        st.plotly_chart(fig, use_container_width=True)

        # fallback – TradingView widget (רק אם רוצים)
        with st.expander("תצוגת TradingView (קוד משולב)"):
            tv_html = f"""
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
            new TradingView.widget({{
                "width": "100%",
                "height": 500,
                "symbol": "{ticker_input}",
                "interval": "D",
                "timezone": "Etc/UTC",
                "theme": "light",
                "style": "1",
                "locale": "he_IL",
                "toolbar_bg": "#f1f3f6",
                "hide_side_toolbar": false,
                "allow_symbol_change": true,
                "container_id": "tradingview_{ticker_input}"
            }});
            </script>
            <div id="tradingview_{ticker_input}"></div>
            """
            components.html(tv_html, height=520)

    # --------------------------------------------------------------
    # 6.2️⃣ טאב מידע – פרטי חברה + טבלאות
    # --------------------------------------------------------------
    with tab_info:
        if stock_info:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**שם החברה:** {stock_info.get('longName', ticker_input)}")
                st.markdown(f"**ענף:** {stock_info.get('industry', 'לא ידוע')}")
                st.markdown(f"**שוק:** {stock_info.get('exchange', 'לא ידוע')}")
                st.markdown(f"**מטבע:** {stock_info.get('currency', 'USD')}")
                st.markdown("---")
                st.markdown(stock_info.get("longBusinessSummary", "אין תיאור זמין."))
            with col2:
                st.metric(
                    label="מחיר נוכחי",
                    value=f"${df_price['Close'].iloc[-1]:.2f}",
                )
                st.metric(
                    label="שינוי 1‑יום",
                    value=f"{df_price['Close'].pct_change().iloc[-1]*100:+.2f} %",
                )
                st.metric(
                    label="שינוי 1‑שנה",
                    value=f"{(df_price['Close'].iloc[-1] / df_price['Close'].iloc[0] - 1)*100:+.2f} %",
                )
        else:
            st.warning("לא הצלחנו לקבל מידע פונדמנטלי, אך הגרף זמין.")

    # --------------------------------------------------------------
    # 6.3️⃣ טאב יומן אישי – ניהול פוזיציות + הורדת CSV
    # --------------------------------------------------------------
    with tab_journal:
        st.markdown("### 🛎️ ניהול פוזיציות")
        col_price, col_shares = st.columns(2)

        with col_price:
            price_to_save = st.number_input(
                "מחיר קנייה (USD)", min_value=0.0, value=round(df_price["Close"].iloc[-1], 2)
            )
        with col_shares:
            shares_to_save = st.number_input(
                "כמות מניות", min_value=1, step=1, value=1
            )

        if st.button(f"הוסף פוזיציה של {ticker_input}"):
            add_trade(ticker_input, price_to_save, shares_to_save)
            st.success("✅ הפוזיציה נשמרה!")

        # הצגת רשימת הפוזיציות
        if st.session_state.trades:
            st.markdown("#### 📋 הפוזיציות שלי")
            for uid, trade in list(st.session_state.trades.items()):
                c1, c2, c3 = st.columns([4, 2, 1])
                with c1:
                    st.info(
                        f"**{trade['Ticker']}** – מחיר: ${trade['Price']:.2f} – "
                        f"מספר מניות: {trade['Shares']} – תאריך: {trade['Date']}"
                    )
                with c2:
                    # אפשרות לערוך מחיר/כמות (מופעל רק כשלחצים על “ערוך”)
                    if st.button("✏️ ערוך", key=f"edit_{uid}"):
                        new_price = st.number_input(
                            f"מחיר חדש ({trade['Ticker']})",
                            min_value=0.0,
                            value=trade["Price"],
                            key=f"newprice_{uid}",
                        )
                        new_shares = st.number_input(
                            f"כמות חדשה ({trade['Ticker']})",
                            min_value=1,
                            step=1,
                            value=trade["Shares"],
                            key=f"newshares_{uid}",
                        )
                        # עדכון הפוזיציה
                        st.session_state.trades[uid]["Price"] = round(new_price, 2)
                        st.session_state.trades[uid]["Shares"] = new_shares
                        st.success("✅ הפוזיציה עודכנה")
                        st.rerun()
                with c3:
                    if st.button("🗑️ מחק", key=f"del_{uid}"):
                        delete_trade(uid)
                        st.success("✅ הפוזיציה נמחקה")
                        st.rerun()
        else:
            st.info("עדיין לא הוספת פוזיציות. השתמש בלחצן “הוסף פוזיציה”.")
        st.markdown("---")
        # כפתור הורדת CSV של כל הפוזיציות
        if st.session_state.trades:
            csv_buffer = io.StringIO()
            pd.DataFrame.from_dict(st.session_state.trades, orient="index").to_csv(
                csv_buffer, index=False
            )
            csv_bytes = csv_buffer.getvalue().encode()
            st.download_button(
                label="📥 הורד יומן בפורמט CSV",
                data=csv_bytes,
                file_name=f"journal_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )

# ----------------------------------------------------------------------
# 7️⃣ תצוגת פורטפוליו (בצד שמאל/ימין – תלוי ברוחב המסך)
# ----------------------------------------------------------------------
if st.session_state.portfolio.shape[0] > 0:
    st.markdown("---")
    st.subheader("💼 סיכום פורטפוליו")
    # חיבור מחירי סגירה עדכניים
    latest_prices = {}
    for ticker in st.session_state.portfolio["Ticker"].unique():
        df_tmp, _ = fetch_stock_data(ticker)
        if df_tmp is not None and not df_tmp.empty:
            latest_prices[ticker] = df_tmp["Close"].iloc[-1]

    df_port = st.session_state.portfolio.copy()
    df_port["CurrentPrice"] = df_port["Ticker"].map(latest_prices)
    df_port["CurrentValue"] = df_port["CurrentPrice"] * df_port["Shares"]
    df_port["Invested"] = df_port["EntryPrice"] * df_port["Shares"]
    df_port["P&L ($)"] = df_port["CurrentValue"] - df_port["Invested"]
    df_port["P&L (%)"] = (df_port["P&L ($)"] / df_port["Invested"]) * 100

    # טבלה אינטרקטיבית
    st.dataframe(
        df_port[
            [
                "Ticker",
                "EntryPrice",
                "Shares",
                "Invested",
                "CurrentPrice",
                "CurrentValue",
                "P&L ($)",
                "P&L (%)",
            ]
        ].style.format(
            {
                "EntryPrice": "${:,.2f}",
                "Invested": "${:,.2f}",
                "CurrentPrice": "${:,.2f}",
                "CurrentValue": "${:,.2f}",
                "P&L ($)": "${:+,.2f}",
                "P&L (%)": "{:+.2f} %",
            }
        )
    )

    # מדדים מצטברים
    total_invested = df_port["Invested"].sum()
    total_current = df_port["CurrentValue"].sum()
    total_pl = total_current - total_invested
    total_pl_pct = (total_pl / total_invested) * 100 if total_invested else 0

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("הון מושקע", f"${total_invested:,.2f}")
    col_b.metric("שווי נוכחי", f"${total_current:,.2f}")
    col_c.metric("רווח/הפסד", f"${total_pl:,.2f} ({total_pl_pct:+.2f} %)")

    # גרף פיזור – השקעה לפי מניה
    fig_port = px.pie(
        df_port,
        values="Invested",
        names="Ticker",
        title="חלוקת הון לפי מניות",
        hole=0.4,
    )
    st.plotly_chart(fig_port, use_container_width=True)

# ----------------------------------------------------------------------
# 8️⃣ Footer – קישורים ושימושים
# ----------------------------------------------------------------------
st.markdown(
    """
    <hr>
    <div style="text-align:center; font-size:0.9rem;">
        © 2026 – <b>התיק החכם</b> | 
        <a href="https://github.com/your-repo" target="_blank">קוד מקור ב‑GitHub</a> |
        <a href="https://www.yfinance.com" target="_blank">yFinance</a>
    </div>
    """,
    unsafe_allow_html=True,
)
