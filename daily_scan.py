import twstock
import yfinance as yf
import pandas as pd
import datetime
import time

def get_all_tickers():
    # 修正：移除錯誤的 auth()，直接讀取 twstock 的內建清單
    # 這裡取得所有上市股票代號
    listed = twstock.codes.keys()
    
    # 過濾出長度為 4 的代號 (排除權證等)，並加上 .TW
    # 為了避免 GitHub Actions 超時，我們先抓前 300 檔熱門股做測試
    # 等測試成功後，你可以把 [:300] 拿掉，改成跑全市場
    valid_tickers = [f"{code}.TW" for code in listed if len(code) == 4 and code[:2] in ['11', '12', '13', '14', '15', '16', '17', '23', '24', '26', '28', '29', '30', '37', '49', '52', '55', '58', '60', '61', '62', '64', '65', '66', '80', '81', '82', '83', '84', '99']]
    
    return valid_tickers[]

def scan_market():
    tickers = get_all_tickers()
    breakout_list = []
    
    print(f"開始掃描 {len(tickers)} 檔股票...")
    
    for i, code in enumerate(tickers):
        try:
            # 抓取最近 60 天資料
            stock = yf.Ticker(code)
            df = stock.history(period="3mo")
            
            if len(df) < 20: continue

            # 計算 MA20 (月線)
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            # 判斷邏輯：
            # 1. 今天收盤價 > 今天 MA20
            # 2. 昨天收盤價 < 昨天 MA20 (剛站上)
            # 3. 成交量 > 1000 張 (1,000,000 股) - 稍微嚴格一點避免冷門股
            
            cond1 = today['Close'] > today['MA20']
            cond2 = yesterday['Close'] < yesterday['MA20']
            cond3 = today['Volume'] > 1000000 

            if cond1 and cond2 and cond3:
                bias = round(((today['Close'] - today['MA20']) / today['MA20']) * 100, 2)
                
                # 取得股票名稱 (twstock 才有中文名)
                stock_id = code.replace(".TW", "")
                stock_name = twstock.codes[stock_id].name if stock_id in twstock.codes else stock_id

                print(f"🔥 發現: {stock_id} {stock_name}")
                
                breakout_list.append({
                    "代號": stock_id,
                    "名稱": stock_name,
                    "收盤價": round(today['Close'], 2),
                    "MA20": round(today['MA20'], 2),
                    "乖離率(%)": bias,
                    "成交量(張)": int(today['Volume']/1000)
                })
            
            # 避免請求太快被擋，每 10 檔休息一下
            if i % 10 == 0:
                time.sleep(1)
                
        except Exception as e:
            # print(f"Error scanning {code}: {e}")
            continue
            
    # 存檔
    df_result = pd.DataFrame(breakout_list)
    update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"掃描結束，共發現 {len(df_result)} 檔。")
    
    # 即使是空的也要存一個檔案，不然網頁讀取代碼會報錯
    if df_result.empty:
        df_result = pd.DataFrame(columns=["代號", "名稱", "收盤價", "MA20", "乖離率(%)", "成交量(張)"])
        
    df_result.to_csv("result.csv", index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    scan_market()

