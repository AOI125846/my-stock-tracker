import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime, date
import logging
import traceback
import subprocess
import io  # חדש: עבור ייצוא האקסל בזיכרון
from typing import Optional

# Logging בסיסי
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_git_info():
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
        return branch, commit
    except Exception:
        return None, None

# --- הגדרות UI ועיצוב ---
st.set_page_config(page_title="Pro Trader AI", layout="wide")

st.markdown(
    """
    <style>
    .stApp { direction: rtl; text-align: right; }
    div[data-testid="stMetricValue"] { color: #0078ff; font-weight: bold; }
    div[data-testid="stMetricLabel"] { width: 100%; text-align: right; direction: rtl; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f0f2f6; border-radius: 5px; color: #31333F; font-weight: 600; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #0078ff; color: white; }
    .block-container { padding-top: 2rem; }
    body.dark-mode { background-color: #0b1220; color: #e8eef8; }
    </style>
    """,
    unsafe_allow_html=True,
)

JOURNAL_FILE = "trading_journal.csv"
ALLOWED_RANGES = ["1m", "5m", "15m", "1h", "4h", "1d"]

# --- פונקציות ליבה ---

def load_journal() -> pd.DataFrame:
    if not os.path.exists(JOURNAL_FILE):
        df = pd.DataFrame(columns=["תאריך", "סימול", "פעולה", "מחיר ($)", "כמות", "רווח ($)", "רווח (₪)"])
        df.to_csv(JOURNAL_FILE, index=False, encoding="utf-8-sig")
        return df
    try:
        return pd.read_csv(JOURNAL_FILE, encoding="utf-8-sig")
    except Exception as e:
        logger.warning("אין אפשרות לקרוא את יומן המסחר: %s", e)
        return pd.DataFrame(columns=["תאריך", "סימול", "פעולה", "מחיר ($)", "כמות", "רווח ($)", "רווח (₪)"])

def save_trade(trade_date, symbol, action, price, qty, profit_usd=0, profit_ils=0):
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
        "רווח ($)": round(float(profit_usd), 2),
        "רווח (₪)": round(float(profit_ils), 2),
    }])
    df = load_journal()
    df = pd.concat([df, new_row], ignore_index=True)
    try:
        df.to_csv(JOURNAL_FILE, index=False, encoding="utf-8-sig")
    except Exception as e:
        logger.exception("שגיאה בכתיבת יומן המסחר")

@st.cache_data(ttl=3600)
def get_usd_rate() -> float:
    try:
        rate = yf.Ticker("ILS=X").history(period="1d")["Close"].iloc[-1]
        return float(rate)
    except Exception:
        return 3.65

@st.cache_data(ttl=300)
def get_data(symbol: str):
    try:
        ticker_obj = yf.Ticker(symbol)
        df = ticker_obj.history(period="2y", auto_adjust=False)
        if df is None or df.empty: return None, None
        df = df.copy()
        try:
            info = ticker_obj.info or {}
            company_name = info.get("longName") or info.get("shortName") or symbol
        except: company_name = symbol

        df["SMA50"] = df["Close"].rolling(window=50, min_periods=1).mean()
        df["SMA200"] = df["Close"].rolling(window=200, min_periods=1).mean()
        delta = df["Close"].diff()
        rs = delta.clip(lower=0).rolling(14).mean() / -delta.clip(upper=0).rolling(14).mean().replace({0: pd.NA})
        df["RSI"] = 100 - (100 / (1 + rs.fillna(0)))
        df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
        df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = df["EMA12"] - df["EMA26"]
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        return df, company_name
    except Exception:
        return None, None

def analyze_indicators(df: pd.DataFrame) -> dict:
    try:
        res = {"notes": []}
        score = 50
        last = df.iloc[-1]
        
        if last["SMA50"] > last["SMA200"]:
            score += 10
            res["notes"].append("מגמה שורית: ממוצע 50 מעל ממוצע 200.")
        
        rsi = last["RSI"]
        if rsi > 70:
            score -= 10
            res["notes"].append(f"קניית יתר (RSI: {rsi:.1f}).")
        elif rsi < 30:
            score += 10
            res["notes"].append(f"מכירת יתר (RSI: {rsi:.1f}).")
        
        score = max(0, min(100, int(score)))
        recommendation = "קנה" if score >= 65 else "מכור" if score <= 35 else "המתן"
        res.update({"score": score, "recommendation": recommendation, "rsi": rsi, "macd": last["MACD"]})
        return res
    except:
        return {"score": 50, "recommendation": "המתן", "notes": ["שגיאה בניתוח"]}

def main():
    st.title("📊 מערכת מסחר חכמה — Pro Trader AI")
    
    branch, commit = get_git_info()
    if branch and commit: st.caption(f"גרסה: {branch}@{commit}")

    usd_val = get_usd_rate()
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1: symbol_input = st.text_input("הכנס סימול (למשל TSLA, NVDA):", "SPY").upper()
    with c2: st.metric("שער הדולר", f"₪{usd_val:.2f}")
    with c3: dark = st.checkbox("מצב חשוך", value=False)

    df, company_name = get_data(symbol_input)

    if df is not None:
        df.attrs["symbol"] = symbol_input
        last_price = float(df["Close"].iloc[-1])
        st.markdown(f"### {company_name} ({symbol_input})")
        st.metric("מחיר אחרון", f"${last_price:.2f}")

        tab1, tab2, tab3, tab4 = st.tabs(["📈 גרף טכני", "🧠 ניתוח חכם", "📰 חדשות", "📓 יומן מסחר ואקסל"])

        with tab1:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="מחיר"), row=1, col=1)
            fig.update_layout(height=600, template="plotly_white", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            analysis = analyze_indicators(df)
            st.write(f"**המלצה:** {analysis['recommendation']} (ציון: {analysis['score']})")
            for n in analysis["notes"]: st.write("- " + n)

        with tab3:
            st.write("חדשות יופיעו כאן...")

        with tab4:
            st.subheader("ניהול עסקאות וייצוא")
            c_a1, c_a2, c_a3 = st.columns(3)
            action = c_a1.selectbox("פעולה", ["קנייה", "מכירה"])
            t_price = c_a2.number_input("מחיר ($)", value=last_price)
            t_qty = c_a3.number_input("כמות", min_value=1, value=1)
            
            if st.button("רשום ביומן"):
                save_trade(date.today(), symbol_input, action, t_price, t_qty)
                st.success("נרשם!")
                st.rerun()

            st.divider()
            j_df = load_journal()
            if not j_df.empty:
                st.dataframe(j_df, use_container_width=True)
                
                # יצירת קובץ אקסל להורדה
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    j_df.to_excel(writer, index=False, sheet_name='Trades')
                
                st.download_button(
                    label="📥 הורד יומן מסחר כ-Excel",
                    data=output.getvalue(),
                    file_name=f"trading_journal_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("היומן ריק.")

    else:
        st.info("אנא הזן סימול תקין.")

if __name__ == "__main__":
    main()
