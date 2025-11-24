import streamlit as st
import pandas as pd
import os
import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="台股均線突破偵測", layout="wide", page_icon="📈")

# --- 標題區 ---
st.title("📈 台股強勢突破選股 (MA5/MA10/MA20)")
st.caption("資料來源: GitHub Actions 自動掃描 | 策略: 多重均線共振突破")

csv_file = 'result.csv'

# 手動重新整理按鈕
if st.button("🔄 重新讀取資料"):
    st.rerun()

# --- 核心邏輯 ---
if os.path.exists(csv_file):
    try:
        # 讀取 CSV
        df = pd.read_csv(csv_file)
        
        # 取得檔案最後修改時間
        mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(csv_file)).strftime('%Y-%m-%d %H:%M')
        
        if not df.empty:
            # --- 側邊欄：資料統計與篩選 ---
            st.sidebar.header("🔍 篩選與統計")
            st.sidebar.write(f"最後更新: {mod_time}")
            st.sidebar.metric("今日符合檔數", f"{len(df)} 檔")
            
            # 1. 策略篩選器
            if '觸發條件' in df.columns:
                all_strategies = ['全部顯示'] + sorted(df['觸發條件'].astype(str).unique().tolist())
                selected_strategy = st.sidebar.selectbox("選擇觸發策略", all_strategies)
                
                if selected_strategy != '全部顯示':
                    df = df[df['觸發條件'] == selected_strategy]
            
            # 2. 顯示主表格
            st.subheader(f"📋 篩選結果 ({len(df)} 筆)")
            
            # 【關鍵修正】計算最大成交量，並強制轉為一般 int，避免 JSON 錯誤
            max_vol = 10000
            if '成交量(張)' in df.columns and not df.empty:
                max_vol = int(df['成交量(張)'].max()) # <--- 這裡加了 int()
            
            # 設定表格顯示格式
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "資料日期": st.column_config.TextColumn("📅 日期"),
                    "代號": st.column_config.TextColumn("代號", help="股票代碼"),
                    "名稱": st.column_config.TextColumn("名稱"),
                    "觸發條件": st.column_config.TextColumn("🚀 觸發訊號", width="medium"),
                    "收盤價": st.column_config.NumberColumn("收盤價", format="$%.2f"),
                    "MA5": st.column_config.NumberColumn("MA5", format="%.2f"),
                    "MA10": st.column_config.NumberColumn("MA10", format="%.2f"),
                    "MA20": st.column_config.NumberColumn("MA20", format="%.2f"),
                    "乖離率(%)": st.column_config.NumberColumn(
                        "乖離率(%)", 
                        format="%.2f %%",
                        help="距離 MA20 的幅度"
                    ),
                    "成交量(張)": st.column_config.ProgressColumn(
                        "成交量 (張)",
                        format="%d",
                        min_value=0,
                        max_value=max_vol, # 使用修正後的變數
                    ),
                }
            )
            
        else:
            st.warning("📭 今日掃描無符合條件股票 (資料檔為空)。")
            st.write(f"最後更新時間: {mod_time}")
            
    except Exception as e:
        st.error(f"❌ 讀取資料發生錯誤: {e}")
        # st.code(str(e)) 
else:
    st.info("⏳ 尚未產生掃描結果。")
    st.write("請等待下午自動排程執行 (約 14:30)，或前往 GitHub Actions 手動觸發。")
