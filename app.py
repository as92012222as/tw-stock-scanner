import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="台股 MA20 突破偵測器", layout="wide")
st.title("📈 台股 MA20 強勢突破選股 (每日自動更新)")

csv_file = 'result.csv'

# 檢查檔案是否存在
if os.path.exists(csv_file):
    # 讀取 CSV
    df = pd.read_csv(csv_file)
    
    st.info(f"資料來源: GitHub Actions 自動掃描 | 總筆數: {len(df)}")
    
    if not df.empty:
        # 顯示表格
        st.dataframe(
            df.style.highlight_max(axis=0, color='lightgreen', subset=['乖離率(%)']),
            use_container_width=True
        )
    else:
        st.warning("今日掃描無符合條件股票。")
else:
    st.error("尚未產生掃描結果，請等待下午自動排程執行，或手動觸發 Action。")

# 增加一個手動重新整理按鈕
if st.button("重新整理"):
    st.rerun()
