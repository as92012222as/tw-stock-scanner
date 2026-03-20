import streamlit as st
import pandas as pd
import yfinance as yf  # 用於抓取新聞
from config import RESULT_CSV_FILE
from src.dashboard import inject_custom_css, load_data, render_metrics_dashboard, render_strategy_chart

# --- 新增功能函式：抓取股票新聞與簡單分析 ---
def render_news_section(symbol, name):
    st.subheader(f"🔍 {name} ({symbol}) 近期動態分析")
    
    try:
        # 確保代號是字串
        str_symbol = str(symbol)
        
        # 1. 先嘗試以上市 (.TW) 搜尋
        yf_symbol = f"{str_symbol}.TW"
        ticker = yf.Ticker(yf_symbol)
        news = ticker.news
        
        # 2. 如果沒抓到新聞，可能是上櫃股票，改用 (.TWO) 再次嘗試
        if not news:
            yf_symbol = f"{str_symbol}.TWO"
            ticker = yf.Ticker(yf_symbol)
            news = ticker.news
        
        # 如果還是沒有新聞，就提早結束
        if not news:
            st.info("目前暫無相關新聞。")
            return

        col1, col2 = st.columns(2)
        
        with col1:
            st.success("🟢 潛在利多 (Positive / News)")
            # 示範顯示前 3 則新聞，並使用 .get() 避免欄位遺失報錯
            for n in news[:3]:
                title = n.get('title', '無標題新聞')
                link = n.get('link', '#')
                publisher = n.get('publisher', '未知來源')
                st.markdown(f"**[{title}]({link})**")
                st.caption(f"來源: {publisher}")

        with col2:
            st.error("🔴 風險注意 (Risks / Negative)")
            st.warning("提醒：請留意近期成交量變化與乖離率過高修正風險。")
            st.write("- 市場情緒波動風險")
            st.write("- 產業景氣循環壓力")

    except Exception as e:
        st.error(f"無法取得新聞資訊: {e}")

# --- 2. Main Streamlit Controller ---
def main():
    # ... (前面的 Sidebar 與數據載入保持不變，為保持簡潔先省略) ...
    # 假設這裡已經執行了 df, mod_time = load_data(RESULT_CSV_FILE)
    
    # 為了測試方便，我們加上這行避免 DataFrame 不存在時報錯
    if 'df' not in locals() or df is None:
        st.warning("請確保已經正確載入資料 (df)。")
        return

    # (中略：標題與指標渲染)
    # render_metrics_dashboard(df) # 假設這行存在
    st.markdown("---")

    if not df.empty:
        # --- 優化區：新增選股後的詳細分析 ---
        st.markdown("### 🎯 個股深度診斷")
        
        # 將 DataFrame 中的代號統一轉為字串，避免格式比對錯誤
        df['代號'] = df['代號'].astype(str)
        
        selected_stock = st.selectbox(
            "選擇一支股票查看利多利空分析：",
            options=df['代號'].tolist(),
            format_func=lambda x: f"{x} {df[df['代號']==x]['名稱'].values[0]}"
        )
        
        if selected_stock:
            stock_name = df[df['代號']==selected_stock]['名稱'].values[0]
            render_news_section(selected_stock, stock_name)
        
        st.markdown("---")

        # --- 以下為你原本的 Filters 與 Tab 邏輯 ---
        # ... 繼續接上你後續的程式碼 ...

if __name__ == "__main__":
    main()
