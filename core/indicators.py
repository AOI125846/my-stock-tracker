import pandas as pd

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def macd(series):
    exp1 = series.ewm(span=12, adjust=False).mean()
    exp2 = series.ewm(span=26, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line, signal_line

def get_detailed_signal(row):
    explanations = []
    score = 0
    
    # ניתוח RSI
    if row['RSI'] > 70:
        explanations.append("מכירת יתר (RSI גבוה) - המניה עשויה להיות יקרה מדי")
        score -= 1
    elif row['RSI'] < 30:
        explanations.append("קניית יתר (RSI נמוך) - הזדמנות פוטנציאלית לתיקון מעלה")
        score += 1
        
    # ניתוח MACD
    if row['MACD'] > row['MACD_Signal']:
        explanations.append("קו MACD חצה מעל קו הסיגנל - מומנטום חיובי")
        score += 1
    else:
        explanations.append("קו MACD חצה מתחת לקו הסיגנל - מומנטום שלילי")
        score -= 1
        
    summary = "קנייה" if score > 0 else "מכירה" if score < 0 else "המתנה"
    return summary, explanations
