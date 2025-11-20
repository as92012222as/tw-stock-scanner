import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 網頁設定 ---
st.set_page_config(page_title="台股 MA20 突破偵測器", layout="wide")
st.title("📈 台股 MA20 強勢突破選股")
st.write(f"更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# --- 側邊欄：設定參數 ---
st.sidebar.header("篩選設定")
target_market = st.sidebar.selectbox("選擇掃描範圍", ["台灣50成分股", "中型100 (示範)"])
min_volume = st.sidebar.number_input("最低成交量 (張)", value=1000)

# --- 1. 定義股票清單 (這裡為了示範速度，先用 0050 成分股) ---
# 實務上你可以匯入完整的台股代號清單
tw50_tickers = [
    "2330.TW", "2317.TW", "2454.TW", "2308.TW", "2303.TW", "2881.TW", "2412.TW", 
    "2882.TW", "3008.TW", "2886.TW", "3013.TW", "6290.TW" # 這裡放入你關注的股票代號
]

# --- 2. 核心邏輯函數 ---
@st.cache_data(ttl=3600) # 設定快取，避免重複抓取浪費時間
def get_breakout_stocks(tickers):
    breakout_list = []
    progress_bar = st.progress(0)
    
    for i, code in enumerate(tickers):
        try:
            # 抓取過去 40 天資料以計算 MA
            stock = yf.Ticker(code)
            df = stock.history(period="2mo") 
            
            if len(df) < 20: continue

            # 計算 MA20
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            # 取得今天與昨天的資料
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            # 判斷邏輯：
            # 1. 今天收盤 > 今天 MA20
            # 2. 昨天收盤 < 昨天 MA20
            # 3. 成交量濾網 (簡單過濾)
            cond1 = today['Close'] > today['MA20']
            cond2 = yesterday['Close'] < yesterday['MA20']
            cond3 = today['Volume'] > (min_volume * 1000) # yfinance volume 是股數

            if cond1 and cond2 and cond3:
                # 乖離率
                bias = round(((today['Close'] - today['MA20']) / today['MA20']) * 100, 2)
                
                breakout_list.append({
                    "代號": code.replace(".TW", ""),
                    "收盤價": round(today['Close'], 2),
                    "MA20": round(today['MA20'], 2),
                    "乖離率(%)": bias,
                    "成交量": int(today['Volume']/1000)
                })
        except Exception as e:
            pass
        
        # 更新進度條
        progress_bar.progress((i + 1) / len(tickers))
            
    return pd.DataFrame(breakout_list)

# --- 3. 執行篩選並顯示 ---
if st.button("開始掃描"):
    with st.spinner('正在掃描市場，請稍候... (約需 30-60 秒)'):
        result_df = get_breakout_stocks(tw50_tickers)
    
    if not result_df.empty:
        st.success(f"掃描完成！共發現 {len(result_df)} 檔符合條件")
        
        # 顯示互動式表格 (可以排序)
        st.dataframe(
            result_df.style.highlight_max(axis=0, color='lightgreen', subset=['乖離率(%)']),
            use_container_width=True
        )
        
        # 簡單視覺化
        st.bar_chart(result_df, x="代號", y="乖離率(%)")
        
    else:
        st.warning("今日無符合條件的股票，或是成交量不足。")