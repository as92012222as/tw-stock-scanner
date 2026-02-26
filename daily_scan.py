import time
import datetime
import pandas as pd

from config import TZ_TAIWAN, DATA_LOOKBACK_DAYS, HOLIDAY_DETECT_THRESHOLD, RESULT_CSV_FILE
from src.data import get_all_tickers, fetch_stock_data, get_stock_name
from src.strategy import calculate_indicators, analyze_breakout

def scan_market():
    """
    Main controller for scanning all valid markers, computing breakout indicators, and saving results.
    """
    tickers = get_all_tickers()
    breakout_list = []
    
    taiwan_now = datetime.datetime.now(TZ_TAIWAN)
    today_str = taiwan_now.strftime('%Y-%m-%d')
    start_date = (taiwan_now - datetime.timedelta(days=DATA_LOOKBACK_DAYS)).strftime('%Y-%m-%d')
    
    print(f"🚀 開始掃描全市場 {len(tickers)} 檔股票... (Starting sweep of {len(tickers)} stocks...)")
    print(f"📅 台灣今天日期 (Taiwan Date): {today_str}")
    print(f"⏰ 執行時間 (Execution Time): {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    count_success = 0
    count_fail = 0
    wrong_date_count = 0 
    
    for i, code in enumerate(tickers):
        # 1. Fetching Data
        df = fetch_stock_data(code, start_date)
        
        if df is None:
            count_fail += 1
            continue

        # 2. Extract Basic Data
        today = df.iloc[-1]
        last_candle_date = today.name.strftime('%Y-%m-%d')

        # 3. Handle Holiday / Invalid Open Checking
        if last_candle_date != today_str:
            wrong_date_count += 1
            if wrong_date_count > HOLIDAY_DETECT_THRESHOLD:
                print(f"😴 偵測到今日({today_str})似乎是假日或未開盤 (資料停在 {last_candle_date})，停止掃描。(Holiday Detected. Exiting.)")
                break
            continue
            
        wrong_date_count = 0 

        # 4. Calculate Indicators and Identify Breakout
        df = calculate_indicators(df)
        stock_id = code.replace(".TW", "")
        stock_name = get_stock_name(code)
        
        result = analyze_breakout(df, stock_id, stock_name, today_str)

        if result:
            trigger_text = result["觸發條件"]
            print(f"🔥 發現 [{last_candle_date}]: {stock_id} {stock_name} -> {trigger_text}")
            breakout_list.append(result)
            count_success += 1
        
        # 5. Delay to avoid API bans
        time.sleep(1.2)
        
        # Periodic Progress Update
        if (i + 1) % 100 == 0:
            print(f"--- 進度 (Progress): 已掃描 {i + 1} / {len(tickers)} 檔 (目前發現 {len(breakout_list)} 檔) ---")

    # 6. Save State
    df_result = pd.DataFrame(breakout_list)
    
    if not df_result.empty:
        # Sort by bias ratio
        df_result = df_result.sort_values(by="乖離率(%)", ascending=True)
        # Reorder columns
        columns_order = ["資料日期", "代號", "名稱", "觸發條件", "收盤價", "MA5", "MA10", "MA20", "乖離率(%)", "成交量(張)"]
        df_result = df_result[columns_order]
    else:
        # Empty placeholder structure
        df_result = pd.DataFrame(columns=["資料日期", "代號", "名稱", "觸發條件", "收盤價", "MA5", "MA10", "MA20", "乖離率(%)", "成交量(張)"])
    
    df_result.to_csv(RESULT_CSV_FILE, index=False, encoding="utf-8-sig")
    print(f"🏁 掃描結束。總掃描 (Total Scanned): {len(tickers)} | 符合條件 (Matches): {len(df_result)} | 無效/失敗 (Failed/Invalid): {count_fail}")

if __name__ == "__main__":
    scan_market()
