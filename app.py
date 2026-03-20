import streamlit as st
import pandas as pd

from config import RESULT_CSV_FILE
from src.dashboard import inject_custom_css, load_data, render_metrics_dashboard, render_strategy_chart

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="台股強勢突破偵測儀",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# --- 2. Inject CSS ---
inject_custom_css()

# --- 3. Main Streamlit Controller ---
def main():
    # Sidebar: Control Panel
    with st.sidebar:
        st.title("⚙️ 控制面板 (Control Panel)")
        st.markdown("---")
        
        # Refresh Button
        if st.button("🔄 重新掃描 / 讀取 (Refresh)", use_container_width=True):
            st.rerun()
            
        st.markdown("### 關於策略 (Strategy Logic)")
        st.info(
            """
            **多重均線共振突破**
            \n偵測股價同時站上 MA5, MA10, MA20 
            且均線呈現多頭排列之強勢股。
            """
        )
        st.caption("資料來源: GitHub Actions 自動運算")

    # Load Data via src.dashboard helper function
    df, mod_time = load_data(RESULT_CSV_FILE)

    # Page Header
    st.markdown('<div class="main-title">📈 台股強勢突破選股雷達</div>', unsafe_allow_html=True)
    if mod_time:
        st.markdown(f'<div class="sub-title">最後更新時間 (Last Updated)：{mod_time}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="sub-title">等待資料生成中... (Awaiting Data...)</div>', unsafe_allow_html=True)

    # Render Content
    if df is not None and not df.empty:
        
        # 1. Dashboard Metrics
        render_metrics_dashboard(df)
        st.markdown("---")

        # 2. Filters
        col_filter_1, col_filter_2 = st.columns([1, 2])
        
        with col_filter_1:
            all_strategies = ['全部顯示'] + sorted(df['觸發條件'].astype(str).unique().tolist())
            selected_strategy = st.selectbox("📌 選擇觸發訊號 (Symbol Filter)", all_strategies)
        
        with col_filter_2:
            search_term = st.text_input("🔍 搜尋代號或名稱 (Search Component)", placeholder="輸入 2330 或 台積電...")

        # Filtering Logic
        filtered_df = df.copy()
        if selected_strategy != '全部顯示':
            filtered_df = filtered_df[filtered_df['觸發條件'] == selected_strategy]
