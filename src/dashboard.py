"""
This module centralizes Streamlit UI components and themes.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime

def inject_custom_css():
    """Injects custom CSS to beautify the Streamlit app layout."""
    st.markdown("""
        <style>
        /* Main title styling */
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
        /* Metric card styling */
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem;
            font-weight: bold;
            color: #e63946; /* TW Stock Red */
        }
        /* Table styling */
        div[data-testid="stDataFrame"] {
            border: 1px solid #f0f2f6;
            border-radius: 10px;
            padding: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

def load_data(filepath: str):
    """
    Reads and preprocesses the CSV data file for the dashboard.
    Returns:
        tuple (DataFrame, Formatted Modified Time String)
    """
    if not os.path.exists(filepath):
        return None, None
    
    try:
        df = pd.read_csv(filepath)
        mod_timestamp = os.path.getmtime(filepath)
        mod_time = datetime.datetime.fromtimestamp(mod_timestamp).strftime('%Y-%m-%d %H:%M')
        
        # Ensure '代號' is a string with leading zeros if necessary
        if '代號' in df.columns:
            df['代號'] = df['代號'].astype(str).str.zfill(4)
        
        # Generator for Yahoo stock link
        if '代號' in df.columns:
            df['連結'] = df['代號'].apply(lambda x: f"https://tw.stock.yahoo.com/quote/{x}")
            
        return df, mod_time
    except Exception as e:
        st.error(f"讀取資料失敗 (Failed reading data): {e}")
        return None, None

def render_metrics_dashboard(df: pd.DataFrame):
    """
    Renders top KPI metrics (e.g., total count, top volume).
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 今日符合檔數", f"{len(df)} 檔")
        
    with col2:
        if '成交量(張)' in df.columns and not df.empty:
            top_vol_stock = df.loc[df['成交量(張)'].idxmax()]
            st.metric("🔥 成交量王", f"{top_vol_stock['名稱']}", f"{int(top_vol_stock['成交量(張)']):,} 張")
        else:
            st.metric("🔥 成交量王", "-", "0 張")
            
    with col3:
        if '乖離率(%)' in df.columns and not df.empty:
            avg_bias = df['乖離率(%)'].mean()
            st.metric("📈 平均乖離率", f"{avg_bias:.2f} %")
        else:
            st.metric("📈 平均乖離率", "-")
            
    with col4:
        if '觸發條件' in df.columns and not df.empty:
            top_strategy = df['觸發條件'].mode()[0]
            st.metric("🚀 主流訊號", top_strategy)
        else:
            st.metric("🚀 主流訊號", "-")

def render_strategy_chart(df: pd.DataFrame):
    """
    Renders the bar chart for strategy distribution using Plotly.
    """
    if '觸發條件' in df.columns and not df.empty:
        counts = df['觸發條件'].value_counts().reset_index()
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
