import twstock
import yfinance as yf
import pandas as pd
import datetime
import time

# --- 1. 獲取股票代碼清單 ---
def get_all_tickers():
    # 重新整理 twstock 代碼清單
    codes = twstock.codes
    valid_tickers = []
    
    for code in codes:
        stock_info = codes[code]
        # 只抓股票 (type='股票') 且代號長度為 4
        if stock_info.type == '股票' and len(code) == 4:
            valid_tickers.append(f"{code}.TW")
            
    return valid_tickers

# --- 2. 核心掃描函數 ---
def scan_market():
    tickers = get_all_tickers()
    breakout_list = []
    
    # ⭐ 設定台灣時間 (用於判斷今日是否開盤)
    tz = datetime.timezone(datetime.timedelta(hours=8))
    taiwan_now = datetime.datetime.now(tz)
    today_str = taiwan_now.strftime('%Y-%m-%d')
    
    # 設定抓取資料的日期範圍 (抓過去 3 個月，確保 MA20 算得出來)
    start_date = (taiwan_now - datetime.timedelta(days=100)).strftime('%Y-%m-%d')
    
    print(f"🚀 開始掃描全市場 {len(tickers)} 檔股票...")
    print(f"📅 台灣今天日期: {today_str}")
    print(f"⏰ 執行時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 統計用
    count_success = 0
    count_fail = 0
    wrong_date_count = 0 # 用於假日偵測
    
    for i, code in enumerate(tickers):
        try:
            # ⭐⭐⭐ 關鍵修正：改用 yf.download ⭐⭐⭐
            # yf.download 比 yf.Ticker 更穩定，遇到無效股票會直接回傳空值，不會崩潰
            df = yf.download(
                code, 
                start=start_date, 
                end=None, # None 代表抓到最新
                progress=False, # 關閉進度條，讓 Log 更乾淨
                multi_level_index=False # 確保欄位是單層的 (Open, Close...)
            )
            
            # --- 檢查資料是否空值 (解決 1240.TW, 1259.TW 等下市股票報錯問題) ---
            if df.empty:
                # 默默跳過無效股票，不印錯誤訊息干擾 Log
                count_fail += 1
                continue

            # 資料不足 20 天無法算 MA20，跳過
            if len(df) < 20: 
                count_fail += 1
                continue

            # 取得最新一筆資料
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            # 取得資料日期
            last_candle_date = today.name.strftime('%Y-%m-%d')

            # --- 假日/沒開盤偵測 (防止報舊牌) ---
            if last_candle_date != today_str:
                wrong_date_count += 1
                # 如果連續 10 檔股票的日期都不是今天，代表今天可能是假日
                if wrong_date_count > 10:
                    print(f"😴 偵測到今日({today_str})似乎是假日或未開盤 (資料停在 {last_candle_date})，停止掃描。")
                    break # 強制中止
                continue # 跳過本檔
            
            wrong_date_count = 0 # 只要有抓到一檔今天的資料，重置計數器

            # --- 3. 計算均線 ---
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA10'] = df['Close'].rolling(window=10).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            # --- 4. 判斷篩選條件 ---
            
            # 條件 A: 成交量 > 1000 張 (1,000,000 股)
            # 使用 .iloc[-1] 取值確保拿到的是數值
            vol = float(today['Volume'])
            cond_volume = vol > 1000000 
            
            # 取得數值 (使用 float 強制轉換，避免型別問題)
            close_now = float(today['Close'])
            close_prev = float(yesterday['Close'])
            ma5_now = float(df['MA5'].iloc[-1])
            ma5_prev = float(df['MA5'].iloc[-2])
            ma10_now = float(df['MA10'].iloc[-1])
            ma10_prev = float(df['MA10'].iloc[-2])
            ma20_now = float(df['MA20'].iloc[-1])

            # 條件 B1: 剛站上 MA5 (且在 MA10, MA20 之上)
            is_c1 = (close_now > ma5_now) & \
                    (close_prev < ma5_prev) & \
                    (close_now > ma10_now) & \
                    (close_now > ma20_now) & \
                    cond_volume
            
            # 條件 B2: 剛站上 MA10 (且在 MA5, MA20 之上)
            is_c2 = (close_now > ma10_now) & \
                    (close_prev < ma10_prev) & \
                    (close_now > ma5_now) & \
                    (close_now > ma20_now) & \
                    cond_volume

            if is_c1 or is_c2:
                # 建立觸發條件文字
                trigger_text = []
                if is_c1: trigger_text.append("①站上MA5")
                if is_c2: trigger_text.append("②站上MA10")
                final_trigger = " & ".join(trigger_text)
                
                # 計算乖離率
                bias = round(((close_now - ma20_now) / ma20_now) * 100, 2)
                
                # 取得中文名稱
                stock_id = code.replace(".TW", "")
                stock_name = stock_id
                if stock_id in twstock.codes:
                    stock_name = twstock.codes[stock_id].name

                print(f"🔥 發現 [{last_candle_date}]: {stock_id} {stock_name} -> {final_trigger}")
                
                breakout_list.append({
                    "資料日期": last_candle_date,
                    "代號": stock_id,
                    "名稱": stock_name,
                    "觸發條件": final_trigger,
                    "收盤價": round(close_now, 2),
                    "MA5": round(ma5_now, 2),
                    "MA10": round(ma10_now, 2),
                    "MA20": round(ma20_now, 2),
                    "乖離率(%)": bias,
                    "成交量(張)": int(vol/1000)
                })
                count_success += 1
            
        except Exception as e:
            # 這裡捕捉意外錯誤，確保迴圈不中斷
            # print(f"Error scanning {code}: {e}") 
            count_fail += 1
            continue
        
        # --- 關鍵修正：休息時間 ---
        # 1.2秒是比較安全的設定，避免被 Yahoo 封鎖
        time.sleep(1.2) 
        
        # 進度顯示
        if (i + 1) % 100 == 0:
            print(f"--- 進度: 已掃描 {i + 1} / {len(tickers)} 檔 (目前發現 {len(breakout_list)} 檔) ---")

    # --- 5. 存檔 ---
    df_result = pd.DataFrame(breakout_list)
    
    if not df_result.empty:
        # 排序：優先顯示乖離率小的 (剛起漲)
        df_result = df_result.sort_values(by="乖離率(%)", ascending=True)
        # 調整欄位順序
        df_result = df_result[["資料日期", "代號", "名稱", "觸發條件", "收盤價", "MA5", "MA10", "MA20", "乖離率(%)", "成交量(張)"]]
    else:
        # 建立空表
        df_result = pd.DataFrame(columns=["資料日期", "代號", "名稱", "觸發條件", "收盤價", "MA5", "MA10", "MA20", "乖離率(%)", "成交量(張)"])
    
    df_result.to_csv("result.csv", index=False, encoding="utf-8-sig")
    print(f"🏁 掃描結束。總掃描: {len(tickers)} | 符合條件: {len(df_result)} | 無效/失敗: {count_fail}")

if __name__ == "__main__":
    scan_market()
