"""
This module contains the logic for calculating indicators and determining buy/breakout signals.
"""
import pandas as pd
from typing import Dict, Any, Optional

from config import MA_SHORT, MA_MID, MA_LONG, MIN_VOLUME_THRESHOLD

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates moving averages for the given DataFrame.
    """
    df['MA5'] = df['Close'].rolling(window=MA_SHORT).mean()
    df['MA10'] = df['Close'].rolling(window=MA_MID).mean()
    df['MA20'] = df['Close'].rolling(window=MA_LONG).mean()
    return df

def analyze_breakout(df: pd.DataFrame, stock_id: str, stock_name: str, today_str: str) -> Optional[Dict[str, Any]]:
    """
    Analyzes the DataFrame to check if the stock meets the breakout criteria.
    
    Args:
        df: The stock data DataFrame (must contain indicators).
        stock_id: The ID of the stock.
        stock_name: The name of the stock.
        today_str: Today's date string.
        
    Returns:
        A dictionary containing the breakout result if conditions are met, otherwise None.
    """
    # Ensure enough data points for MA20
    if len(df) < MA_LONG:
        return None

    # Get the latest and previous day data
    today = df.iloc[-1]
    yesterday = df.iloc[-2]
    
    # Check if the data is up-to-date (holiday detection handled by the main loop)
    # Get last candle's date (assuming DateTimeIndex)
    last_candle_date = today.name.strftime('%Y-%m-%d')
    # Use pandas native attribute parsing for speed, and to avoid multi-index tuple issues
    
    try:
        vol = float(today['Volume'])
        close_now = float(today['Close'])
        close_prev = float(yesterday['Close'])
        ma5_now = float(df['MA5'].iloc[-1])
        ma5_prev = float(df['MA5'].iloc[-2])
        ma10_now = float(df['MA10'].iloc[-1])
        ma10_prev = float(df['MA10'].iloc[-2])
        ma20_now = float(df['MA20'].iloc[-1])
    except Exception:
        # Avoid crashing if column format deviates (e.g. index/multi-level issue)
        return None

    # Condition: Volume greater than threshold
    cond_volume = vol > MIN_VOLUME_THRESHOLD

    # Strategy 1: Cross above MA5 horizontally (and price > MA10, MA20)
    is_c1 = (close_now > ma5_now) and \
            (close_prev < ma5_prev) and \
            (close_now > ma10_now) and \
            (close_now > ma20_now) and \
            cond_volume

    # Strategy 2: Cross above MA10 horizontally (and price > MA5, MA20)
    is_c2 = (close_now > ma10_now) and \
            (close_prev < ma10_prev) and \
            (close_now > ma5_now) and \
            (close_now > ma20_now) and \
            cond_volume

    if is_c1 or is_c2:
        trigger_text = []
        if is_c1: trigger_text.append(f"①站上MA{MA_SHORT}")
        if is_c2: trigger_text.append(f"②站上MA{MA_MID}")
        final_trigger = " & ".join(trigger_text)
        
        # Calculate Bias Ratio against MA_LONG
        # Avoid division by zero
        bias_denom = ma20_now if ma20_now > 0 else 1
        bias = round(((close_now - ma20_now) / bias_denom) * 100, 2)
        
        return {
            "資料日期": last_candle_date,
            "代號": stock_id,
            "名稱": stock_name,
            "觸發條件": final_trigger,
            "收盤價": round(close_now, 2),
            "MA5": round(ma5_now, 2),
            "MA10": round(ma10_now, 2),
            "MA20": round(ma20_now, 2),
            "乖離率(%)": bias,
            "成交量(張)": int(vol / 1000)
        }
        
    return None
