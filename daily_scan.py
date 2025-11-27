import twstock
import yfinance as yf
import pandas as pd
import datetime
import time

# --- 1. 獲取股票代碼清單 ---
def get_all_tickers():
    # 重新整理 twstock 代碼清單
    # twstock.codes 包含上市櫃，我們只抓股票 (type='股票') 且代號長度為 4
    codes = twstock.codes
    valid_tickers = []
    
    for code in codes:
        stock_info = codes[code]
        if stock_info.type == '股票' and len(code) == 4:
            valid_tickers.append(f"{code}.TW")
            
    # 為了測試，您可以先只跑前 500 檔，確認有資料後再拿掉 [:500]
    # return valid_tickers[:500] 
    return valid_tickers

# --- 2. 核心掃描函數 ---
def scan_market():
    tickers = get_all_tickers()
    breakout_list = []
    
    print(f"🚀 開始掃描全市場 {len(tickers)} 檔股票...")
    print(f"⏰ 執行時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 統計用
    count_success = 0
    count_fail = 0
    
    for i, code in enumerate(tickers):
        try:
            stock = yf.Ticker(code)
            # 抓取最近 3 個月資料
            df = stock.history(period="3mo")
            
            # --- 除錯：如果前 5 檔抓不到資料，印出原因 ---
            if df.empty:
                if i < 5: print(f"⚠️ {code}: 抓取失敗 (資料為空)，可能被 API 限制")
                count_fail += 1
                continue

            if len(df) < 20: 
                count_fail += 1
                continue

            # --- 3. 計算均線 ---
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA10'] = df['Close'].rolling(window=10).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            # 取得最新一筆資料
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            # 取得資料日期 (重要！用來確認是否抓到今天的)
            data_date = today.name.strftime('%Y-%m-%d')

            # --- 4. 判斷篩選條件 ---
            
            # 條件 A: 成交量 > 500 張 (500,000 股)
            # 注意：Yahoo 有時成交量會有誤差，設 300 張 (300,000) 比較保險，您原本設 500 張也可以
            cond_volume = today['Volume'] > 300000 
            
            # 條件 B1: 剛站上 MA5 (且在 MA10, MA20 之上)
            is_c1 = (today['Close'] > today['MA5']) & \
                    (yesterday['Close'] < yesterday['MA5']) & \
                    (today['Close'] > today['MA10']) & \
                    (today['Close'] > today['MA20']) & \
                    cond_volume
            
            # 條件 B2: 剛站上 MA10 (且在 MA5, MA20 之上)
            is_c2 = (today['Close'] > today['MA10']) & \
                    (yesterday['Close'] < yesterday['MA10']) & \
                    (today['Close'] > today['MA5']) & \
                    (today['Close'] > today['MA20']) & \
                    cond_volume

            if is_c1 or is_c2:
                trigger_text = []
                if is_c1: trigger_text.append("①站上MA5")
                if is_c2: trigger_text.append("②站上MA10")
                
                final_trigger = " & ".join(trigger_text)
                
                # 計算乖離率
                bias = round(((today['Close'] - today['MA20']) / today['MA20']) * 100, 2)
                
                # 取得中文名稱
                stock_id = code.replace(".TW", "")
                stock_name = stock_id
                if stock_id in twstock.codes:
                    stock_name = twstock.codes[stock_id].name

                print(f"🔥 發現 [{data_date}]: {stock_id} {stock_name} -> {final_trigger}")
                
                breakout_list.append({
                    "資料日期": data_date,  # 新增日期欄位
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
                count_success += 1
            
        except Exception as e:
            # print(f"Error: {code} - {e}")
            count_fail += 1
            continue
        
        # --- 關鍵修正：每一檔都休息，避免被 Yahoo 封鎖 ---
        # 掃全市場時，建議設 0.5 ~ 1 秒
        time.sleep(0.8) 
        
        # 進度條
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
        # 建立空表，防止網頁報錯
        df_result = pd.DataFrame(columns=["資料日期", "代號", "名稱", "觸發條件", "收盤價", "MA5", "MA10", "MA20", "乖離率(%)", "成交量(張)"])
    
    df_result.to_csv("result.csv", index=False, encoding="utf-8-sig")
    print(f"🏁 掃描結束。總掃描: {len(tickers)} | 符合條件: {len(df_result)} | 失敗/跳過: {count_fail}")

if __name__ == "__main__":
    scan_market()
