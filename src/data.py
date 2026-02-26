"""
This module handles all data fetching logic, interacting with twstock and yfinance.
"""

import twstock
import yfinance as yf
import pandas as pd
from typing import List, Optional

def get_all_tickers() -> List[str]:
    """
    Fetches all valid stock tickers from twstock.
    Returns a list of tickers formatted for Yahoo Finance (e.g., '2330.TW').
    """
    codes = twstock.codes
    valid_tickers = []
    
    for code, stock_info in codes.items():
        # Only fetch '股票' (stocks) and length of 4
        if stock_info.type == '股票' and len(code) == 4:
            valid_tickers.append(f"{code}.TW")
            
    return valid_tickers

def fetch_stock_data(code: str, start_date: str) -> Optional[pd.DataFrame]:
    """
    Fetches historical stock data from Yahoo Finance.
    
    Args:
        code: The stock code (e.g., '2330.TW').
        start_date: Start date for fetching data ('YYYY-MM-DD').
        
    Returns:
        pd.DataFrame containing historical data, or None if failed/empty.
    """
    try:
        # yf.download is more stable than yf.Ticker
        df = yf.download(
            code, 
            start=start_date, 
            end=None, 
            progress=False, 
            multi_level_index=False 
        )
        
        if df.empty:
            return None
        
        return df
    
    except Exception:
        # Ignore errors for delisted or invalid stocks to keep logs clean
        return None

def get_stock_name(code: str) -> str:
    """
    Gets the Chinese name of the stock from twstock.
    """
    stock_id = code.replace(".TW", "")
    if stock_id in twstock.codes:
        return twstock.codes[stock_id].name
    return stock_id
