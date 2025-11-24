import twstock
import yfinance as yf
import pandas as pd
import datetime
import time

# --- 1. 獲取股票代碼清單 ---
def get_all_tickers():
    # 這裡的邏輯是正確的，確保抓取所有上市櫃股票
    codes = twstock.codes
    valid_tickers = []
    
    for code in codes:
        stock_info = codes[code]
        if stock_info.type == '股票' and len(code) == 4:
            valid_tickers.append(f"{code}.TW")
            
    return valid_tickers

# --- 2. 核心掃描函數 ---
def scan_market():
    tickers = get_all_tickers()
    breakout_list = []
    
    # 設定台灣時間
    tz = datetime.timezone(datetime.timedelta(hours=8))
    taiwan_now = datetime.datetime.now(tz)
    today_str = taiwan_now.strftime('%Y-%m-%d')
    
    print(f"🚀 開始掃描全市場 {len(tickers)} 檔股票... 台灣今天日期: {today_str}")

    count_fail = 0
    wrong_date_count = 0
    
    for i, code in enumerate(tickers):
        try:
            # ⭐ 關鍵修正：回歸最簡單的 yfinance 呼叫，移除 session
            stock = yf.Ticker(code) 
            df = stock.history(period="3mo", auto_adjust=True, prepost=False)
            
            # --- 檢查資料是否空值或不足 ---
            if df.empty or len(df) < 20: 
                # 這裡可能包含已下市或資料不足20天的股票
                count_fail += 1
                continue

            # --- 假日/沒開盤偵測 (防止報舊牌) ---
            last_candle_date = df.index[-1].strftime('%Y-%m-%d')
            
            if last_candle_date != today_str:
                wrong_date_count += 1
                if wrong_date_count > 10:
                    print(f"😴 偵測到今日({today_str})似乎是假日或未開盤 (資料停在 {last_candle_date})，停止掃描。")
                    break 
                continue 
            
            wrong_date_count = 0 

            # --- 3. 均線計算與判斷 (邏輯正確) ---
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
            # print(f"Error: {code} - {e}") # 這裡印出來會知道詳細錯誤，但會佔用log空間
            count_fail += 1
            continue
        
        # ⭐ 關鍵修正：延遲時間拉長到 1.5 秒
        time.sleep(1.5) 
        
        if (i + 1) % 100 == 0:
            print(f"--- 進度: 已掃描 {i + 1} / {len(tickers)} 檔 (目前發現 {len(breakout_list)} 檔) ---")

    # --- 4. 存檔 ---
    df_result = pd.DataFrame(breakout_list)
    
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
