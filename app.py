import streamlit as st
import pandas as pd
import os
import datetime
import plotly.express as px

# --- 1. 頁面全域設定 ---
st.set_page_config(
    page_title="台股強勢突破偵測儀",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# --- 2. 自定義 CSS 樣式 (美化介面) ---
st.markdown("""
    <style>
    /* 調整主要標題字體與間距 */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #555;
        margin-bottom: 2rem;
    }
    /* 指標卡片樣式 */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: bold;
        color: #e63946; /* 台股紅 */
    }
    /* 表格樣式優化 */
    div[data-testid="stDataFrame"] {
        border: 1px solid #f0f2f6;
        border-radius: 10px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 輔助函式 ---
def load_data(filepath):
    """讀取並預處理資料"""
    if not os.path.exists(filepath):
        return None, None
    
    try:
        df = pd.read_csv(filepath)
        # 取得最後修改時間
        mod_timestamp = os.path.getmtime(filepath)
        mod_time = datetime.datetime.fromtimestamp(mod_timestamp).strftime('%Y-%m-%d %H:%M')
        
        # 確保代號是字串 (補零，例如 0050) - 視 CSV 格式而定，這裡假設 CSV 可能是 int
        if '代號' in df.columns:
            df['代號'] = df['代號'].astype(str).str.zfill(4) # 假設是純數字代號
        
        # 產生 Yahoo 股市連結
        if '代號' in df.columns:
            df['連結'] = df['代號'].apply(lambda x: f"https://tw.stock.yahoo.com/quote/{x}")
            
        return df, mod_time
    except Exception as e:
        st.error(f"讀取資料失敗: {e}")
        return None, None

def render_dashboard(df):
    """繪製儀表板統計區"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 今日符合檔數", f"{len(df)} 檔")
    with col2:
        if '成交量(張)' in df.columns:
            top_vol_stock = df.loc[df['成交量(張)'].idxmax()]
            st.metric("🔥 成交量王", f"{top_vol_stock['名稱']}", f"{int(top_vol_stock['成交量(張)']):,} 張")
    with col3:
        if '乖離率(%)' in df.columns:
            avg_bias = df['乖離率(%)'].mean()
            st.metric("📈 平均乖離率", f"{avg_bias:.2f} %")
    with col4:
        # 顯示最多股票符合的策略
        if '觸發條件' in df.columns:
            top_strategy = df['觸發條件'].mode()[0]
            st.metric("🚀 主流訊號", top_strategy)

# --- 4. 主程式邏輯 ---
def main():
    # 檔案路徑
    csv_file = 'result.csv'

    # 側邊欄：控制與資訊
    with st.sidebar:
        st.title("⚙️ 控制面板")
        st.markdown("---")
        
        # 重新整理按鈕
        if st.button("🔄 重新掃描 / 讀取", use_container_width=True):
            st.rerun()
            
        st.markdown("### 關於策略")
        st.info(
            """
            **多重均線共振突破**
            \n偵測股價同時站上 MA5, MA10, MA20 
            且均線呈現多頭排列之強勢股。
            """
        )
        st.caption("資料來源: GitHub Actions 自動運算")

    # 讀取資料
    df, mod_time = load_data(csv_file)

    # 頁面標題
    st.markdown('<div class="main-title">📈 台股強勢突破選股雷達</div>', unsafe_allow_html=True)
    if mod_time:
        st.markdown(f'<div class="sub-title">最後更新時間：{mod_time}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="sub-title">等待資料生成中...</div>', unsafe_allow_html=True)

    # 內容呈現
    if df is not None and not df.empty:
        
        # 1. 儀表板區域
        render_dashboard(df)
        st.markdown("---")

        # 2. 進階篩選區 (兩欄配置)
        col_filter_1, col_filter_2 = st.columns([1, 2])
        
        with col_filter_1:
            # 策略篩選
            all_strategies = ['全部顯示'] + sorted(df['觸發條件'].astype(str).unique().tolist())
            selected_strategy = st.selectbox("📌 選擇觸發訊號", all_strategies)
        
        with col_filter_2:
            # 關鍵字搜尋
            search_term = st.text_input("🔍 搜尋代號或名稱", placeholder="輸入 2330 或 台積電...")

        # 執行篩選邏輯
        filtered_df = df.copy()
        if selected_strategy != '全部顯示':
            filtered_df = filtered_df[filtered_df['觸發條件'] == selected_strategy]
        
        if search_term:
            filtered_df = filtered_df[
                filtered_df['代號'].str.contains(search_term) | 
                filtered_df['名稱'].str.contains(search_term)
            ]

        # 3. 圖表分析 (如果有資料)
        if not filtered_df.empty:
            tab1, tab2 = st.tabs(["📋 詳細清單", "📊 訊號分佈分析"])

            with tab1:
                # 準備 Column Config
                max_vol = int(df['成交量(張)'].max()) if '成交量(張)' in df.columns else 10000
                
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    hide_index=True,
                    column_order=[
                        "代號", "名稱", "收盤價", "乖離率(%)", "成交量(張)", 
                        "觸發條件", "連結", "MA5", "MA10", "MA20", "資料日期"
                    ],
                    column_config={
                        "連結": st.column_config.LinkColumn(
                            "K線圖", 
                            display_text="Yahoo股市",
                            help="點擊前往 Yahoo 股市查看詳情"
                        ),
                        "代號": st.column_config.TextColumn("代號"),
                        "名稱": st.column_config.TextColumn("名稱", width="small"),
                        "收盤價": st.column_config.NumberColumn(
                            "收盤價", format="$%.2f", width="small"
                        ),
                        "乖離率(%)": st.column_config.NumberColumn(
                            "乖離率(%)", 
                            format="%.2f %%",
                            help="正乖離過大需注意修正風險"
                        ),
                        "成交量(張)": st.column_config.ProgressColumn(
                            "成交量",
                            format="%d 張",
                            min_value=0,
                            max_value=max_vol,
                        ),
                        "觸發條件": st.column_config.TextColumn("🚀 訊號類型"),
                    }
                )
            
            with tab2:
                # 使用 Plotly 畫出策略分佈
                if '觸發條件' in filtered_df.columns:
                    counts = filtered_df['觸發條件'].value_counts().reset_index()
                    counts.columns = ['策略', '數量']
                    
                    fig = px.bar(
                        counts, x='策略', y='數量', 
                        text='數量', 
                        title="各策略觸發股數統計",
                        color='數量',
                        color_continuous_scale='Reds'
                    )
                    fig.update_layout(xaxis_title="", yaxis_title="檔數")
                    st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("⚠️ 篩選後無符合條件的股票。")

    else:
        # 空資料狀態 (Empty State)
        st.container()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("https://cdn-icons-png.flaticon.com/512/6133/6133066.png", width=150)
            st.info("目前沒有資料，或資料庫為空。")
            st.markdown("""
                **可能原因：**
                1. 今日盤勢尚未結束，或 Actions 尚未執行。
                2. 今日無股票符合「均線突破」條件。
                3. `result.csv` 檔案不存在。
            """)
            if st.button("嘗試手動重新讀取"):
                st.rerun()

if __name__ == "__main__":
    main()
