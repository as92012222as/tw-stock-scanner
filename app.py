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

        

        if search_term:

            filtered_df = filtered_df[

                filtered_df['代號'].str.contains(search_term) | 

                filtered_df['名稱'].str.contains(search_term)

            ]



        # 3. Chart and Lists (If data exists post-filter)

        if not filtered_df.empty:

            tab1, tab2 = st.tabs(["📋 詳細清單 (Details List)", "📊 訊號分佈分析 (Distribution Chart)"])



            with tab1:

                # Setup metrics configs for data grid

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

                            "K線圖", display_text="Yahoo股市", help="點擊前往 Yahoo 股市查看詳情"

                        ),

                        "代號": st.column_config.TextColumn("代號"),

                        "名稱": st.column_config.TextColumn("名稱", width="small"),

                        "收盤價": st.column_config.NumberColumn("收盤價", format="$%.2f", width="small"),

                        "乖離率(%)": st.column_config.NumberColumn("乖離率(%)", format="%.2f %%", help="正乖離過大需注意修正風險"),

                        "成交量(張)": st.column_config.ProgressColumn("成交量", format="%d 張", min_value=0, max_value=max_vol),

                        "觸發條件": st.column_config.TextColumn("🚀 訊號類型"),

                    }

                )
