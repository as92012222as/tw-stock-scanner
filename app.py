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

