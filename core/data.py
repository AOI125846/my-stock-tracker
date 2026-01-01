import yfinance as yf

def load_stock_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end, progress=False)
    return df
