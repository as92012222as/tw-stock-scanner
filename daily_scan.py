import twstock
import yfinance as yf
import pandas as pd
import datetime
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- 🎯 1. 全域連線設定 (新增 Retry 機制) ---
# 設定重試策略：總共重試 3 次，針對 429, 500, 502, 503, 504 錯誤碼
retry_strategy = Retry(
    total=3,
    backoff_factor=1, # 每次重試間隔會依序拉長 (1s, 2s, 4s...)
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
# 將重試策略應用到連線
adapter = HTTPAdapter(max_retries=retry_strategy)
http_session = requests.Session()
http_session.mount("https://", adapter)
http_session.mount("http://", adapter)

# --- 2. 獲取股票代碼清單 ---
def get_all_tickers():
    codes = twstock.codes
    valid_tickers = []
    
    for code in codes:
        stock_info = codes[code]
        if stock_info.type == '股票' and len(code) == 4:
            valid_tickers.append(f"{code}.TW")
            
    return valid_tickers

# --- 3. 核心掃描函數 ---
def scan_market():
    tickers = get_all_tickers()
    breakout_list = []
    
    # 設定台灣時間 (GitHub 主機是 UTC，所以要 +8)
    tz = datetime.timezone(datetime.timedelta(hours=8))
    taiwan_now = datetime.datetime.now(tz)
    today_str = taiwan_now.strftime('%Y-%m-%d')
    
    print(f"🚀 開始掃描全市場 {len(tickers)} 檔股票... 台灣今天日期: {today_str}")

    count_fail = 0
    wrong_date_count = 0
    
    for i, code in enumerate(tickers):
        try:
            # ⭐ 核心修正：將 Session 傳給 yfinance
            stock = yf.Ticker(code, session=http_session) 
            df = stock.history(period="3mo", auto_adjust=True, prepost=False)
            
            if df.empty or len(df) < 20: 
                count_fail += 1
                continue

            # --- 假日/沒開盤偵測 ---
            last_candle_date = df.index[-1].strftime('%Y-%m-%d')
            
            if last_candle_date != today_str:
                wrong_date_count += 1
                if wrong_date_count > 10:
                    print(f"😴 偵測到今日({today_str})似乎是假日或未開盤 (資料停在 {last_candle_date})，停止掃描。")
                    break 
                continue 
            
            wrong_date_count = 0 

            # --- 4. 計算與判斷 (邏輯保持不變) ---
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA10'] = df['Close'].rolling(window=10).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            # 輔助濾網：成交量 > 1000 張 (1000,000 股)
            cond_volume = today['Volume'] > 1000000 
            
            # A. 條件一：站上MA5
            is_c1 = (today['Close'] > today['MA5']) & \
                    (yesterday['Close'] < yesterday['MA5']) & \
                    (today['Close'] > today['MA10']) & \
                    (today['Close'] > today['MA20']) & \
                    cond_volume
            
            # B. 條件二：站上MA10
            is_c2 = (today['Close'] > today['MA10']) & \
                    (yesterday['Close'] < yesterday['MA10']) & \
                    (today['Close'] > today['MA5']) & \
                    (today['Close'] > today['MA20']) & \
                    cond_volume

            if is_c1 or is_c2:
                # 建立觸發條件文字
                trigger_text = []
                if is_c1: trigger_text.append("①站上MA5")
                if is_c2: trigger_text.append("②站上MA10")
                final_trigger = " & ".join(trigger_text)
                
                # 計算乖離率
                bias = round(((today['Close'] - today['MA20']) / today['MA20']) * 100, 2)
                
                # 取得中文名稱
                stock_id = code.replace(".TW", "")
                stock_name = twstock.codes.get(stock_id, {'name': stock_id})['name']

                print(f"🔥 發現 [{last_candle_date}]: {stock_id} {stock_name} -> {final_trigger}")
                
                breakout_list.append({
                    "資料日期": last_candle_date,
                    "代號": stock_id,
                    "名稱": stock_name,
                    "觸發條件": final_trigger,
                    "收盤價": round(today['Close'], 2),
                    "MA5": round(today['MA5'], 2),
                    "MA10": round(today['MA10'], 2),
                    "MA20": round(today['MA20'], 2),
                    "乖離率(%)": bias,
                    "成交量(張)": int(today['Volume']/1000)
                })
            
        except Exception as e:
            # print(f"Error: {code} - {e}")
            count_fail += 1
            continue
        
        # 關鍵修正：連線重試已經處理了大部分問題，這裡只需要基本的延遲
        time.sleep(0.5) # 由於有 Retry 機制，延遲可以稍微調降
        
        if (i + 1) % 100 == 0:
            print(f"--- 進度: 已掃描 {i + 1} / {len(tickers)} 檔 (目前發現 {len(breakout_list)} 檔) ---")

    # --- 5. 存檔 ---
    df_result = pd.DataFrame(breakout_list)
    
    # 確保欄位順序並存檔 (略過細節)
    if not df_result.empty:
        df_result = df_result.sort_values(by="乖離率(%)", ascending=True)
        cols = ["資料日期", "代號", "名稱", "觸發條件", "收盤價", "MA5", "MA10", "MA20", "乖離率(%)", "成交量(張)"]
        df_result = df_result[cols]
    else:
        cols = ["資料日期", "代號", "名稱", "觸發條件", "收盤價", "MA5", "MA10", "MA20", "乖離率(%)", "成交量(張)"]
        df_result = pd.DataFrame(columns=cols)

    df_result.to_csv("result.csv", index=False, encoding="utf-8-sig")
    print(f"🏁 掃描結束。總掃描: {len(tickers)} | 符合條件: {len(df_result)} | 失敗/跳過: {count_fail}")

if __name__ == "__main__":
    scan_market()
