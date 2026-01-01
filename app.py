import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import date, datetime
import io
import subprocess
import logging

# ================== בסיס ==================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JOURNAL_FILE = "trading_journal.csv"

# ================== Git Info ==================
def get_git_info():
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
        return branch, commit
    except Exception:
        return None, None

# ================== UI ==================
st.set_page_config(page_title="Pro Trader AI", layout="wide")

st.markdown("""
<style>
.stApp { direction: rtl; text-align: right; background-color: #f7f9fc; }
h1, h2, h3 { color: #0b3c5d; }
div[data-testid="stMetricValue"] { color: #0078ff; font-weight: bold; }
.stTabs [data-baseweb="tab"] {
    background-color: #e9eef5;
    border-radius: 8px;
    font-weight: 600;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #0078ff;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ================== Journal ==================
def load_journal():
    if not os.path.exists(JOURNAL_FILE):
        df = pd.DataFrame(columns=["תאריך", "סימול", "פעולה", "מחיר ($)", "כמות", "רווח ($)", "רווח (₪)"])
        df.to_csv(JOURNAL_FILE, index=False, encoding="utf-8-sig")
        return df
    return pd.read_csv(JOURNAL_FILE, encoding="utf-8-sig")

def save_trade(d, symbol, action, price, qty, usd_rate):
    profit_usd = price * qty if action == "מכירה" else 0
    profit_ils = profit_usd * usd_rate
    df = load_journal()
    df = pd.concat([df, pd.DataFrame([{
        "תאריך": d.isoformat(),
        "סימול": symbol,
        "פעולה": action,
        "מחיר ($)": round(price,2),
        "כמות": qty,
        "רווח ($)": round(profit_usd,2),
        "רווח (₪)": round(profit_ils,2),
    }])], ignore_index=True)
    df.to_csv(JOURNAL_FILE, index=False, encoding="utf-8-sig")

# ================== Data ==================
@st.cache_data(ttl=600)
def get_usd_rate():
    try:
        return float(yf.Ticker("ILS=X").history(period="1d")["Close"].iloc[-1])
    except:
        return 3.65

@st.cache_data(ttl=300)
def get_data(symbol):
    try:
        df = yf.Ticker(symbol).history(period="2y")
        if df.empty:
            return None
        df["SMA10"] = df["Close"].rolling(10).mean()
        df["SMA50"] = df["Close"].rolling(50).mean()
        df["SMA200"] = df["Close"].rolling(200).mean()

        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        rs = gain.rolling(14).mean() / loss.rolling(14).mean()
        df["RSI"] = 100 - (100 / (1 + rs))

        df["EMA12"] = df["Close"].ewm(span=12).mean()
        df["EMA26"] = df["Close"].ewm(span=26).mean()
        df["MACD"] = df["EMA12"] - df["EMA26"]
        df["Signal"] = df["MACD"].ewm(span=9).mean()
        return df
    except:
        return None

# ================== Analysis ==================
def analyze(df):
    score = 50
    notes = []
    last = df.iloc[-1]

    if last["SMA10"] > last["SMA50"] > last["SMA200"]:
        score += 15
        notes.append("מגמה חיובית ברורה (SMA10 > SMA50 > SMA200)")
    elif last["SMA10"] < last["SMA50"]:
        score -= 10
        notes.append("לחץ מכירה בטווח הקצר")

    if last["RSI"] > 70:
        score -= 10
        notes.append("RSI גבוה – קניית יתר")
    elif last["RSI"] < 30:
        score += 10
        notes.append("RSI נמוך – מכירת יתר")

    if last["MACD"] > last["Signal"]:
        score += 5
        notes.append("MACD מעל הסיגנל")

    score = max(0, min(100, score))
    rec = "קנה" if score >= 65 else "מכור" if score <= 35 else "המתן"

    return score, rec, notes

# ================== App ==================
def main():
    st.title("📊 Pro Trader AI")

    branch, commit = get_git_info()
    if branch:
        st.caption(f"גרסה: {branch}@{commit}")

    usd_rate = get_usd_rate()
    col1, col2 = st.columns([3,1])
    with col1:
        symbol = st.text_input("סימול מניה", "SPY").upper()
    with col2:
        st.metric("דולר", f"₪{usd_rate:.2f}")

    df = get_data(symbol)

    if df is None:
        st.info("אנא הזן סימול תקין")
        return

    last = df["Close"].iloc[-1]
    change = (last - df["Close"].iloc[-2]) / df["Close"].iloc[-2] * 100

    st.metric("מחיר אחרון", f"${last:.2f}", f"{change:.2f}%")

    tab1, tab2, tab3 = st.tabs(["📈 גרף", "🧠 ניתוח", "📓 יומן מסחר"])

    with tab1:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7,0.3])
        fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"]))
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="SMA 50"))
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"], name="SMA 200"))
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"]), row=2, col=1)
        fig.update_layout(height=650, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        score, rec, notes = analyze(df)
        st.subheader(f"המלצה: {rec} (ציון {score})")
        for n in notes:
            st.write("•", n)

    with tab3:
        c1, c2, c3 = st.columns(3)
        action = c1.selectbox("פעולה", ["קנייה","מכירה"])
        price = c2.number_input("מחיר", value=float(last))
        qty = c3.number_input("כמות", min_value=1, value=1)

        if st.button("רשום"):
            save_trade(date.today(), symbol, action, price, qty, usd_rate)
            st.success("נשמר")
            st.rerun()

        j = load_journal()
        st.dataframe(j, use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            j.to_excel(writer, index=False)
        st.download_button("📥 הורדת Excel", output.getvalue(), "trading_journal.xlsx")

if __name__ == "__main__":
    main()
