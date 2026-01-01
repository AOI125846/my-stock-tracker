import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime, date
import logging
import subprocess
from typing import Optional

# Logging בסיסי
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# גרסא / מזהה שינויים (אם הריפו מקומי)
def get_git_info():
    try:
        commit = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .decode()
            .strip()
        )
        branch = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .decode()
            .strip()
        )
        return branch, commit
    except Exception:
        return None, None


# --- הגדרות מערכת ועיצוב ---
st.set_page_config(page_title="Pro Trader AI", layout="wide")

# הזרקת CSS (כולל מתג מצב חשוך)
st.markdown(
    """
    <style>
    /* כיוון ימין לשמאל */
    .stApp {
        direction: rtl;
        text-align: right;
    }

    /* כרטיסיות מידע - רקע נעים */
    div[data-testid="stMetricValue"] {
        color: #0078ff;
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

    /* מצב חשוך פשוט - מחליף צבע טקסט רק */
    body.dark-mode {
        background-color: #0b1220;
        color: #e8eef8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- קבועים ושימושיות ---
JOURNAL_FILE = "trading_journal.csv"
ALLOWED_RANGES = ["1m", "5m", "15m", "1h", "4h", "1d"]


# --- פונקציות ליבה ---
def load_journal() -> pd.DataFrame:
    if not os.path.exists(JOURNAL_FILE):
        df = pd.DataFrame(
            columns=[
                "תאריך",
                "סימול",
                "פעולה",
                "מחיר ($)",
                "כמות",
                "רווח ($)",
                "רווח (₪)",
            ]
        )
        df.to_csv(JOURNAL_FILE, index=False, encoding="utf-8-sig")
        return df
    try:
        return pd.read_csv(JOURNAL_FILE, encoding="utf-8-sig")
    except Exception as e:
        logger.warning("אין אפשרות לקרוא את יומן המסחר: %s", e)
        return pd.DataFrame(
            columns=[
                "תאריך",
                "סימול",
                "פעולה",
                "מחיר ($)",
                "כמות",
                "רווח ($)",
                "רווח (₪)",
            ]
        )


def save_trade(trade_date, symbol, action, price, qty, profit_usd=0, profit_ils=0):
    # המרת תאריך לפורמט ISO
    if isinstance(trade_date, (pd.Timestamp, datetime, date)):
        trade_date_str = trade_date.isoformat()
    else:
        trade_date_str = str(trade_date)

    new_row = pd.DataFrame(
        [
            {
                "תאריך": trade_date_str,
                "סימול": symbol,
                "פעולה": action,
                "מחיר ($)": round(float(price), 2),
                "כמות": int(qty),
                "רווח ($)": round(float(profit_usd), 2) if profit_usd else 0.0,
                "רווח (₪)": round(float(profit_ils), 2) if profit_ils else 0.0,
            }
        ]
    )
    df = load_journal()
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(JOURNAL_FILE, index=False, encoding="utf-8-sig")


@st.cache_data(ttl=3600)
def get_usd_rate() -> float:
    try:
        rate = yf.Ticker("ILS=X").history(period="1d")["Close"].iloc[-1]
        return float(rate)
    except Exception as e:
        logger.warning("אי אפשר לקבל שער דולר מ‑yfinance: %s — שימוש בערך ברירת מחדל", e)
        return 3.65


@st.cache_data(ttl=300)
def get_data(symbol: str):
    """
    מחזיר (df, company_name, ticker_obj) — תמיד שלושה ערכים.
    אם יש כשל, מחזיר (None, None, None).
    """
    try:
        ticker_obj = yf.Ticker(symbol)
        df = ticker_obj.history(period="2y", auto_adjust=False)

        if df is None or df.empty:
            return None, None, None

        # שמירה על עותק לפני שינוי
        df = df.copy()

        # פרטי חברה (שם מלא) — guarded access
        try:
            info = ticker_obj.info or {}
            company_name = info.get("longName") or info.get("shortName") or symbol
        except Exception:
            company_name = symbol

        # חישוב אינדיקטורים עם min_periods כדי למנוע NaN מיותר
        df["SMA50"] = df["Close"].rolling(window=50, min_periods=1).mean()
        df["SMA200"] = df["Close"].rolling(window=200, min_periods=1).mean()

        # RSI - חישוב יציב שמטפל בחלוקת אפס
        delta = df["Close"].diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)
        avg_gain = gains.rolling(window=14, min_periods=14).mean()
        avg_loss = losses.rolling(window=14, min_periods=14).mean()
        rs = avg_gain / avg_loss.replace({0: pd.NA})
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.fillna(50)  # ברירת מחדל ניטרלית כאשר אין מספיק נתונים
        df["RSI"] = rsi

        # MACD
        df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
        df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = df["EMA12"] - df["EMA26"]
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

        return df, company_name, ticker_obj
    except Exception as e:
        logger.exception("שגיאה בטעינת נתוני מניה %s: %s", symbol, e)
        return None, None, None


def analyze_indicators(df: pd.DataFrame) -> dict:
    """
    מקבל DataFrame עם עמודות Close, SMA50, SMA200, RSI, MACD, Signal
    ומחזיר dict עם ניתוח טכני כולל ציון כללי והמלצה (קנה/מכור/המתן)
    + רשימת נקודות הסבר לשימוש הסוחר.
    """
    closes = df["Close"].dropna().tolist()
    res = {"notes": []}
    score = 50

    # SMA קיצור
    sma10 = df["Close"].rolling(window=10, min_periods=1).mean().iloc[-1]
    sma50 = df.get("SMA50", pd.Series()).iloc[-1] if "SMA50" in df.columns else None
    sma200 = df.get("SMA200", pd.Series()).iloc[-1] if "SMA200" in df.columns else None

    if sma50 is not None and sma200 is not None:
        if sma10 > sma50 > sma200:
            score += 15
            res["notes"].append(
                "SMA קצר עולה מעל SMA50 ו‑SMA200 — מגמה חיובית ברורה לטווח הארוך והבינוני."
            )
        elif sma10 > sma50:
            score += 5
            res["notes"].append("SMA קצר מעל SMA50 — מומנטום חיובי לטווח הקצר.")
        elif sma10 < sma50:
            score -= 8
            res["notes"].append("SMA קצר מתחת ל‑SMA50 — לחץ מכירה לטווח הקצר.")

    # RSI
    rsi = df["RSI"].iloc[-1] if "RSI" in df.columns else None
    if rsi is not None:
        if rsi > 70:
            score -= 10
            res["notes"].append(
                f"RSI גבוה ({rsi:.1f}) — סיכון קניית יתר; שקול הקטנת חשיפה או צמצום חשיפה."
            )
        elif rsi < 30:
            score += 10
            res["notes"].append(
                f"RSI נמוך ({rsi:.1f}) — ייתכן הזדמנות קניה במחיר דישדוש/תיקון."
            )
        else:
            res["notes"].append(f"RSI נייטרלי ({rsi:.1f}).")

    # MACD חישוב וסימן
    macd_val = df["MACD"].iloc[-1] if "MACD" in df.columns else None
    signal_val = df["Signal"].iloc[-1] if "Signal" in df.columns else None
    prev_macd = df["MACD"].iloc[-2] if len(df) >= 2 and "MACD" in df.columns else None
    prev_signal = df["Signal"].iloc[-2] if len(df) >= 2 and "Signal" in df.columns else None

    if macd_val is not None and signal_val is not None:
        if prev_macd is not None and prev_signal is not None:
            if macd_val > signal_val and prev_macd <= prev_signal:
                score += 8
                res["notes"].append(
                    "חציית MACD למעלה — אות שוורי שמצביע על התחזקות מומנטום."
                )
            elif macd_val < signal_val and prev_macd >= prev_signal:
                score -= 8
                res["notes"].append(
                    "חציית MACD למטה — אות דובי שעשוי להצביע על ירידה במומנטום."
                )
            else:
                if macd_val > signal_val:
                    res["notes"].append("MACD מעל הסיגנל — מומנטום חיובי.")
                else:
                    res["notes"].append("MACD מתחת הסיגנל — מומנטום שלילי.")

    # upcoming events (נסיון לקרוא דוחות קרובים)
    upcoming = []
    try:
        # yfinance יכול להכיל calendar או actions/earnings
        ticker = yf.Ticker(df.attrs.get("symbol", ""))
        cal = getattr(ticker, "calendar", None)
        if isinstance(cal, pd.DataFrame) and not cal.empty:
            # דוגמה: 'Earnings Date' יכול להופיע
            upcoming = [{"type": k, "value": str(v[0])} for k, v in cal.items()]
    except Exception:
        upcoming = []

    # סיכום והמלצה
    score = max(0, min(100, int(score)))
    recommendation = "המתן"
    if score >= 65:
        recommendation = "קנה"
    elif score <= 35:
        recommendation = "מכור"

    res.update(
        {
            "score": score,
            "recommendation": recommendation,
            "sma10": float(sma10) if sma10 is not None else None,
            "sma50": float(sma50) if sma50 is not None else None,
            "sma200": float(sma200) if sma200 is not None else None,
            "rsi": float(rsi) if rsi is not None else None,
            "macd": float(macd_val) if macd_val is not None else None,
            "signal": float(signal_val) if signal_val is not None else None,
            "upcoming_reports": upcoming,
        }
    )
    return res


# --- ממשק משתמש ---
st.title("📊 מערכת מסחר חכמה — Pro Trader AI")

branch, commit = get_git_info()
if branch and commit:
    st.caption(f"גרסה: {branch}@{commit}")

# עליון — חיפוש, טווח ומצב חשוך
usd_val = get_usd_rate()
c1, c2, c3 = st.columns([3, 1, 1])

with c1:
    symbol_input = st.text_input("הכנס סימול (למשל TSLA, NVDA):", "SPY").upper()

with c2:
    st.metric("שער הדולר", f"₪{usd_val:.2f}")

with c3:
    # מתג מצב חשוך - משנה CSS class בעמוד (פשוט ויעיל)
    dark = st.checkbox("מצב חשוך", value=False)
    if dark:
        st.markdown("<script>document.body.classList.add('dark-mode')</script>", unsafe_allow_html=True)
    else:
        st.markdown("<script>document.body.classList.remove('dark-mode')</script>", unsafe_allow_html=True)

# טווח נתונים לבחירה (מוגבל)
range_col1, range_col2 = st.columns([1, 4])
with range_col1:
    range_select = st.selectbox("טווח נתונים", ALLOWED_RANGES, index=ALLOWED_RANGES.index("1d"))

# טעינת נתונים
df, company_name, ticker_obj = get_data(symbol_input)

# שמירת סימבול ב‑attrs כדי שנוכל לקרוא בעל הוא analyze_indicators
if df is not None:
    df.attrs["symbol"] = symbol_input

if df is not None:
    # הצגת שם המניה ומחיר נוכחי
    try:
        last_price = float(df["Close"].iloc[-1])
        prev_price = float(df["Close"].iloc[-2])
        change = (last_price - prev_price) / prev_price * 100
    except Exception:
        last_price = float(df["Close"].iloc[-1])
        change = 0.0

    st.markdown(f"### {company_name} ({symbol_input})")
    st.metric("מחיר אחרון", f"${last_price:.2f}", f"{change:.2f}%")

    # לשוניות ראשיות
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📈 גרף טכני", "🧠 ניתוח חכם", "📰 חדשות", "📓 יומן מסחר", "ℹ️ שינויים / גרסה"]
    )

    # --- לשונית 1: גרף ---
    with tab1:
        st.caption(
            "רזולוציות נתונים קבועות — אין אפשרות לשנות באופן חופשי את רזולוציית הנרות. ניתן לעשות זום וגרירה במסגרת הנתונים המוצגים."
        )
        # אם רוצים להציג רק טווח מסוים מה‑df בהתאם ל‑range_select — אפשר לממש כאן פילטר
        # כרגע מציגים את כל הנתונים שהתקבלו (2y) אך המשתמש שולט בטווח באמצעות select אם נחבר API אחר בעתיד
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05
        )

        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="מחיר",
            ),
            row=1,
            col=1,
        )

        # ממוצעים
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["SMA50"], line=dict(color="orange", width=1.5), name="SMA 50"
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["SMA200"], line=dict(color="blue", width=1.5), name="SMA 200"
            ),
            row=1,
            col=1,
        )

        # ווליום
        fig.add_trace(
            go.Bar(
                x=df.index, y=df["Volume"], marker_color="rgba(200,200,200,0.5)", name="Volume"
            ),
            row=2,
            col=1,
        )

        fig.update_layout(
            height=650,
            template="plotly_white" if not dark else "plotly_dark",
            xaxis_rangeslider_visible=False,
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- לשונית 2: ניתוח חכם ---
    with tab2:
        st.subheader("פרשנות אינדיקטורים אוטומטית")
        analysis = analyze_indicators(df)
        st.markdown(f"**ציון כללי:** {analysis['score']} — *{analysis['recommendation']}*")
        st.write("**הסברים ופרשנות:**")
        for n in analysis["notes"]:
            st.write("- " + n)

        st.markdown("#### פרטי אינדיקטורים")
        st.table(
            {
                "מדד": ["SMA10", "SMA50", "SMA200", "RSI", "MACD", "Signal"],
                "ערך": [
                    f"{analysis.get('sma10', '-'):.2f}" if analysis.get("sma10") is not None else "-",
                    f"{analysis.get('sma50', '-'):.2f}" if analysis.get("sma50") is not None else "-",
                    f"{analysis.get('sma200', '-'):.2f}" if analysis.get("sma200") is not None else "-",
                    f"{analysis.get('rsi', '-'):.2f}" if analysis.get("rsi") is not None else "-",
                    f"{analysis.get('macd', '-'):.4f}" if analysis.get("macd") is not None else "-",
                    f"{analysis.get('signal', '-'):.4f}" if analysis.get("signal") is not None else "-",
                ],
            }
        )

        st.markdown("**דו\"חות/אירועים קרובים (אם ידועים):**")
        if analysis.get("upcoming_reports"):
            for e in analysis["upcoming_reports"]:
                st.write(f"- {e}")
        else:
            # נסיון לטעון אירועי רווחים מתוך yfinance
            try:
                cal = getattr(ticker_obj, "calendar", None)
                if isinstance(cal, pd.DataFrame) and not cal.empty:
                    st.write(cal)
                else:
                    st.write("לא נמצאו דוחות קרובים במערכת.")
            except Exception:
                st.write("לא ניתן לאחזר מידע על דוחות.")

    # --- לשונית 3: חדשות ---
    with tab3:
        st.subheader(f"חדשות אחרונות על {symbol_input}")
        try:
            news = getattr(ticker_obj, "news", None)
            if news:
                for item in news[:6]:
                    title = item.get("title") or item.get("summary") or "כתבה"
                    publisher = item.get("publisher") or item.get("source") or "Unknown"
                    link = item.get("link") or item.get("url")
                    with st.expander(f"📰 {title}"):
                        st.write(f"פורסם על ידי: {publisher}")
                        if link:
                            st.markdown(f"[למעבר לכתבה המלאה לחץ כאן]({link})")
                        try:
                            thumb = item.get("thumbnail") or {}
                            url = None
                            if isinstance(thumb, dict):
                                if "resolutions" in thumb and isinstance(thumb["resolutions"], list) and thumb["resolutions"]:
                                    url = thumb["resolutions"][0].get("url")
                                elif "url" in thumb:
                                    url = thumb["url"]
                            if url:
                                st.image(url, width=200)
                        except Exception:
                            logger.debug("לא הוצגה תמונה עבור כתבה")
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
        trade_date = c_act4.date_input("תאריך", value=date.today())

        if st.button("רשום ביומן"):
            p_usd = 0.0
            p_ils = 0.0
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
            try:
                total_profit = journal_df[journal_df["פעולה"] == "מכירה"]["רווח (₪)"].sum()
                st.metric("סה\"כ נפח מכירות (₪)", f"₪{total_profit:,.2f}")
            except Exception:
                st.write("שגיאה בסיכום היומן.")
        else:
            st.info("היומן ריק.")

    # --- לשונית 5: שינויים / גרסה ---
    with tab5:
        st.subheader("מזהה גרסה ושינויים אחרונים")
        if branch and commit:
            st.write(f"ענף: `{branch}` — commit: `{commit}`")
        else:
            st.write("אין מידע git זמין בסביבה זו.")
        # נסיון לקרוא CHANGELOG.md אם קיים
        try:
            if os.path.exists("CHANGELOG.md"):
                with open("CHANGELOG.md", "r", encoding="utf-8") as f:
                    changelog = f.read()
                # הצג רק הקטע הראשון
                st.markdown("#### CHANGELOG (חלקי)")
                st.code("\n".join(changelog.splitlines()[:30]), language="markdown")
            else:
                st.write("אין CHANGELOG במאגר.")
        except Exception:
            logger.debug("לא ניתן לקרוא CHANGELOG.md")

else:
    st.info("אנא הזן סימול מניה תקין (למשל GOOG, AMZN, TEVA) והמתין לטעינה...")
