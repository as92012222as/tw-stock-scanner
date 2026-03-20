import streamlit as st
import pandas as pd
import yfinance as yf  # 新增：用於抓取新聞
from config import RESULT_CSV_FILE
from src.dashboard import inject_custom_css, load_data, render_metrics_dashboard, render_strategy_chart

# --- 新增功能函式：抓取股票新聞與簡單分析 ---
def render_news_section(symbol, name):
    st.subheader(f"🔍 {name} ({symbol}) 近期動態分析")
    
    try:
        # 轉換成 Yahoo Finance 格式 (例如 2330.TW)
        yf_symbol = f"{symbol}.TW"
        ticker = yf.Ticker(yf_symbol)
        news = ticker.news
        
        if not news:
            st.info("目前暫無相關新聞。")
            return

        col1, col2 = st.columns(2)
        
        with col1:
            st.success("🟢 潛在利多 (Positive / News)")
            # 這裡示範顯示前 3 則新聞
            for n in news[:3]:
                st.markdown(f"**[{n['title']}]({n['link']})**")
                st.caption(f"來源: {n['publisher']}")

        with col2:
            st.error("🔴 風險注意 (Risks / Negative)")
            st.warning("提醒：請留意近期成交量變化與乖離率過高修正風險。")
            # 實務上這裡可以串接 LLM 分析新聞標題後的摘要
            st.write("- 市場情緒波動風險")
            st.write("- 產業景氣循環壓力")

    except Exception as e:
        st.error(f"無法取得新聞資訊: {e}")

# --- 2. Main Streamlit Controller ---
def main():
    # ... (前面的 Sidebar 與數據載入保持不變) ...
    df, mod_time = load_data(RESULT_CSV_FILE)

    # (中略：標題與指標渲染)
    render_metrics_dashboard(df)
    st.markdown("---")

    if df is not None and not df.empty:
        # --- 優化區：新增選股後的詳細分析 ---
        st.markdown("### 🎯 個股深度診斷")
        selected_stock = st.selectbox(
            "選擇一支股票查看利多利空分析：",
            options=df['代號'].tolist(),
            format_func=lambda x: f"{x} {df[df['代號']==x]['名稱'].values[0]}"
        )
        
        if selected_stock:
            stock_name = df[df['代號']==selected_stock]['名稱'].values[0]
            render_news_section(selected_stock, stock_name)
        
        st.markdown("---")

        # --- 2. Filters ---
        col_filter_1, col_filter_2 = st.columns([1, 2])
        # ... (後續原有的 Table 和 Chart 邏輯) ...
        
        # (原有的 tab1, tab2 邏輯內容...)
        with tab1:
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
            # ... (原本的 column_config) ...

if __name__ == "__main__":
    main()
