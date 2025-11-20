import twstock
import yfinance as yf
import pandas as pd
import datetime
import time

def get_all_tickers():
    # 取得上市 + 上櫃股票代號
    twstock.auth() # 讓 twstock 更新最新的代號列表
    listed = twstock.codes.keys()
    # 為了示範穩定性，這裡我們先抓前 500 檔熱門股，避免一次跑 1800 檔超時
    # 如果你想跑全台股，可以把 [:500] 拿掉，但 GitHub Action 免費版有執行時間限制
    return [f"{code}.TW" for code in listed if len(code) == 4][:500]

def scan_market():
    tickers = get_all_tickers()
    breakout_list = []
    
    print(f"開始掃描 {len(tickers)} 檔股票...")
    
    # 批量處理或迴圈處理
    for code in tickers:
        try:
            # 只抓最近 40 天數據，減少流量
            stock = yf.Ticker(code)
            df = stock.history(period="2mo")
            
            if len(df) < 20: continue

            # 計算 MA20
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            # 策略：剛剛站上 MA20
            if (today['Close'] > today['MA20']) and \
               (yesterday['Close'] < yesterday['MA20']) and \
               (today['Volume'] > 500000): # 成交量 > 500張 (yfinance 單位是股)
                
                bias = round(((today['Close'] - today['MA20']) / today['MA20']) * 100, 2)
                breakout_list.append({
                    "代號": code.replace(".TW", ""),
                    "收盤價": round(today['Close'], 2),
                    "MA20": round(today['MA20'], 2),
                    "乖離率(%)": bias,
                    "成交量": int(today['Volume']/1000)
                })
                print(f"發現: {code}")
                
        except Exception as e:
            continue
            
    # 存成 CSV
    df_result = pd.DataFrame(breakout_list)
    # 加入更新時間標記
    update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 儲存檔案
    df_result.to_csv("result.csv", index=False, encoding="utf-8-sig")
    print(f"掃描完成，共 {len(df_result)} 檔，已存檔。")

if __name__ == "__main__":
    scan_market()
