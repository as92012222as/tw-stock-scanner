import twstock
import yfinance as yf
import pandas as pd
import datetime
import time

# --- 獲取股票代碼清單 ---
def get_all_tickers():
    listed = twstock.codes.keys()
    
    # 篩選條件：長度為 4 的代號 (排除權證等)
    # 為避免 GitHub Actions 超時，我們跑前 300 檔熱門股做測試
    valid_tickers = [f"{code}.TW" for code in listed if len(code) == 4]
    
    # 如果要跑全市場，請將 [:300] 刪除
    # return [f"{code}.TW" for code in listed if len(code) == 4]
    
    return valid_tickers

# --- 核心掃描函數 ---
def scan_market():
    tickers = get_all_tickers()
    breakout_list = []
    
    print(f"開始掃描 {len(tickers)} 檔股票...")
    
    for i, code in enumerate(tickers):
        try:
            # 抓取最近 3 個月資料 (確保有足夠資料計算 MA20)
            stock = yf.Ticker(code)
            df = stock.history(period="3mo")
            
            if len(df) < 20: continue

            # --- 1. 計算所有需要的均線 ---
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA10'] = df['Close'].rolling(window=10).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            # --- 2. 判斷多重條件 ---
            
            # 輔助濾網：成交量 > 1000 張
            cond_volume = today['Volume'] > 1000000 
            
            # A. 條件一：站上MA5，且已在MA10及MA20之上 (短線轉強，中長線確立)
            is_c1 = (today['Close'] > today['MA5']) & \
                    (yesterday['Close'] < yesterday['MA5']) & \
                    (today['Close'] > today['MA10']) & \
                    (today['Close'] > today['MA20']) & \
                    cond_volume
            
            # B. 條件二：站上MA10，且已在MA5及MA20之上 (中線轉強，短線及長線確立)
            is_c2 = (today['Close'] > today['MA10']) & \
                    (yesterday['Close'] < yesterday['MA10']) & \
                    (today['Close'] > today['MA5']) & \
                    (today['Close'] > today['MA20']) & \
                    cond_volume

            if is_c1 or is_c2:
                # 建立觸發條件文字
                trigger_text = ""
                if is_c1:
                    trigger_text += "①站上MA5 (短線發動)"
                if is_c2:
                    if is_c1: trigger_text += " & "
                    trigger_text += "②站上MA10 (中線轉強)"
                
                # 計算乖離率
                bias = round(((today['Close'] - today['MA20']) / today['MA20']) * 100, 2)
                
                # 取得中文名稱
                stock_id = code.replace(".TW", "")
                stock_name = stock_id
                if stock_id in twstock.codes:
                    stock_name = twstock.codes[stock_id].name

                print(f"🔥 發現: {stock_id} {stock_name}，條件: {trigger_text}")
                
                breakout_list.append({
                    "代號": stock_id,
                    "名稱": stock_name,
                    "收盤價": round(today['Close'], 2),
                    "MA5": round(today['MA5'], 2),
                    "MA10": round(today['MA10'], 2),
                    "MA20": round(today['MA20'], 2),
                    "乖離率(%)": bias,
                    "成交量(張)": int(today['Volume']/1000),
                    "觸發條件": trigger_text
                })
            
            # 避免請求太快被擋，每 10 檔休息一下
            if i % 10 == 0:
                time.sleep(1)
                
        except Exception as e:
            # print(f"Error scanning {code}: {e}")
            continue
            
    # 存檔
    df_result = pd.DataFrame(breakout_list)
    
    # 確保欄位順序並存檔
    if not df_result.empty:
        df_result = df_result[["代號", "名稱", "觸發條件", "收盤價", "MA5", "MA10", "MA20", "乖離率(%)", "成交量(張)"]]
    else:
        df_result = pd.DataFrame(columns=["代號", "名稱", "觸發條件", "收盤價", "MA5", "MA10", "MA20", "乖離率(%)", "成交量(張)"])
        
    df_result.to_csv("result.csv", index=False, encoding="utf-8-sig")
    print(f"掃描結束，共發現 {len(df_result)} 檔，已存檔。")

if __name__ == "__main__":
    scan_market()




