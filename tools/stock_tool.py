# tools/stock_tool.py
import yfinance as yf
from langchain_core.tools import tool

@tool
def get_stock_price(symbol: str) -> str:
    """
    Get real-time stock price and financial info.
    Use when user asks about stock price, market cap, or company financials.
    
    Args:
        symbol: Stock ticker like AAPL, TSLA, RELIANCE.NS, TCS.NS
    """
    try:
        stock = yf.Ticker(symbol)
        info  = stock.info

        name       = info.get("longName", symbol)
        price      = info.get("currentPrice", info.get("regularMarketPrice", "N/A"))
        change     = info.get("regularMarketChangePercent", 0)
        high       = info.get("dayHigh", "N/A")
        low        = info.get("dayLow", "N/A")
        volume     = info.get("regularMarketVolume", "N/A")
        market_cap = info.get("marketCap", "N/A")
        pe_ratio   = info.get("trailingPE", "N/A")
        revenue    = info.get("totalRevenue", "N/A")

        return (
            f"Stock: {name} ({symbol})\n"
            f"Price      : ${price}\n"
            f"Change     : {round(change, 2)}%\n"
            f"Day High   : ${high}\n"
            f"Day Low    : ${low}\n"
            f"Volume     : {volume}\n"
            f"Market Cap : ${market_cap}\n"
            f"P/E Ratio  : {pe_ratio}\n"
            f"Revenue    : ${revenue}\n"
        )

    except Exception as e:
        return f"Error fetching stock data for {symbol}: {e}"