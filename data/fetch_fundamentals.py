# data/fetch_fundamentals.py
import yfinance as yf

def get_fundamentals(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    info = stock.info

    # If yfinance can't find the ticker, info will be mostly empty
    if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
        raise ValueError(f"Could not find data for ticker '{ticker}'. Check the symbol and try again.")

    return {
        "longName": info.get("longName"),
        "sector": info.get("sector"),
        "trailingPE": info.get("trailingPE"),
        "marketCap": info.get("marketCap"),
        "revenueGrowth": info.get("revenueGrowth"),
        "profitMargins": info.get("profitMargins"),
        "debtToEquity": info.get("debtToEquity"),
        "freeCashflow": info.get("freeCashflow"),
    }