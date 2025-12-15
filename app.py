import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import yfinance as yf
import os
import requests

# ==========================================
# 1. 網頁設定
# ==========================================
st.set_page_config(page_title="台灣權值股分析系統", layout="wide")

# ==========================================
# 2. 字型處理 (包含防崩潰機制)
# ==========================================
def get_chinese_font():
    # 字型檔案設定
    font_name = "NotoSansTC-Regular.ttf"
    font_url = "https://github.com/google/fonts/raw/main/ofl/notosanstc/NotoSansTC-Regular.ttf"
    
    # 1. 如果檔案存在，但小於 1MB (代表下載失敗或壞檔)，先刪除它
    if os.path.exists(font_name):
        if os.path.getsize(font_name) < 1000000: # 小於 1MB
            try:
                os.remove(font_name)
                print("已刪除損壞的字型檔")
            except:
                pass

    # 2. 如果檔案不存在，嘗試下載
    if not os.path.exists(font_name):
        with st.spinner("正在下載中文字型 (首次執行需約 10 秒)..."):
            try:
                response = requests.get(font_url, timeout=10)
                if response.status_code == 200:
                    with open(font_name, "wb") as f:
                        f.write(response.content)
                else:
                    return None # 下載失敗
            except:
                return None # 網路錯誤

    # 3. 再次檢查檔案大小，確認是否下載成功
    if os.path.exists(font_name) and os.path.getsize(font_name) > 1000000:
        return fm.FontProperties(fname=font_name)
    else:
        return None # 檔案還是有問題，放棄使用中文

# 取得字型物件 (如果失敗會是 None)
font_prop = get_chinese_font()

# 設定全域字型 (如果 font_prop 有效)
if font_prop:
    plt.rcParams['font.family'] = font_prop.get_name()

# ==========================================
# 3. 資料載入與處理邏輯
# ==========================================
@st.cache_data
def load_and_process_data():
    tickers = {
        "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科",
        "2308.TW": "台達電", "2382.TW": "廣達", "2881.TW": "富邦金",
        "2882.TW": "國泰金", "2412.TW": "中華電", "2303.TW": "聯電",
        "2891.TW": "中信金"
    }
    
    # 下載資料
    data = yf.download(list(tickers.keys()), start="2023-01-01", auto_adjust=False)['Adj Close']
    data.rename(columns=tickers, inplace=True)
    
    df_original = data.copy()
    missing_orig = df_original.isnull().sum().to_frame("缺失筆數").T

    # 模擬缺失
    df_dirty = data.copy()
    if not df_dirty.empty:
        try:
            df_dirty.iloc[0:5, df_dirty.columns.get_loc("台積電")] = np.nan
            df_dirty.iloc[10:13, df_dirty.columns.get_loc("鴻海")] = np.nan
            df_dirty.iloc[20, df_dirty.columns.get_loc("聯發科")] = np.nan
        except:
            pass # 防止索引錯誤
    
    missing_dirty = df_dirty.isnull().sum().to_frame("缺失筆數").T

    # 修復
    df_clean = df_dirty.ffill().bfill()
    missing_clean = df_clean.isnull().sum().to_frame("缺失筆數").T
    
    return tickers, df_original, missing_orig, df_dirty, missing_dirty, df_clean, missing_clean

try:
    tickers_map, df_orig, miss_orig, df_dirty, miss_dirty, df_final, miss_final = load_and_process_data()
except Exception as e:
    st.error(f"資料載入失敗: {e}")
    st.stop()

# ==========================================
# 4. 網頁介面設計
# ==========================================
st.title("📈 台灣前十大權值股 - 分析與資料清洗展示")

# 顯示警告：如果字型下載失敗
if font_prop is None:
    st.warning("⚠️ 注意：中文字型下載失敗，圖表將顯示英文或方框，但程式不會崩潰。")

st.header("1. 資料清洗三部曲 (模擬展示)")
col1, col2, col3 = st.columns(3)
with col1:
    st.info("步驟 1：原始資料")
    st.dataframe(miss_orig)
with col2:
    st.warning("步驟 2：模擬缺失")
    st.dataframe(miss_dirty.style.highlight_max(axis=1, color='pink'))
with col3:
    st.success("步驟 3：修復完成")
    st.dataframe(miss_final)

st.markdown("---")

st.header("2. 統計數據分析")
returns = df_final.pct_change()
summary_df = pd.DataFrame({
    '平均報酬率 (年化)': returns.mean() * 252,
    '風險波動率 (年化)': returns.std() * np.sqrt(252)
})

c1, c2 = st.columns(2)
with c1:
    st.subheader("📊 股價統計摘要")
    st.dataframe(df_final.describe())
with c2:
    st.subheader("⚖️ 風險 vs 報酬表")
    st.dataframe(summary_df.style.format("{:.4f}").background_gradient(cmap="Blues"))

st.markdown("---")

st.header("3. 視覺化儀表板")
tab_trend, tab_risk, tab_rank = st.tabs(["📈 股價走勢圖", "⚖️ 風險報酬分析", "🏆 報酬率排行"])

with tab_trend:
    st.subheader("股價走勢")
    options = ["全部比較 (歸一化)"] + list(tickers_map.values())
    selected_view = st.selectbox("選擇股票:", options)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    if selected_view == "全部比較 (歸一化)":
        for col in df_final.columns:
            normalized = df_final[col] / df_final[col].iloc[0]
            # 安全繪圖：如果沒有字型，就不傳入 fontproperties
            if font_prop:
                ax.plot(normalized, label=col, alpha=0.7)
            else:
                ax.plot(normalized, label=col, alpha=0.7)
        
        ylabel_text = "累計報酬倍數" if font_prop else "Cumulative Return"
        if font_prop:
            ax.set_ylabel(ylabel_text, fontproperties=font_prop)
        else:
            ax.set_ylabel(ylabel_text)
            
    else:
        ax.plot(df_final[selected_view], label=selected_view, color='blue')
        ma20 = df_final[selected_view].rolling(20).mean()
        ax.plot(ma20, label='20MA', color='orange', linestyle='--')
        
        ylabel_text = "股價 (TWD)" if font_prop else "Price (TWD)"
        if font_prop:
            ax.set_ylabel(ylabel_text, fontproperties=font_prop)
        else:
            ax.set_ylabel(ylabel_text)
    
    # 統一設定標題與圖例 (防崩潰)
    title_text = f"{selected_view} 走勢圖" if font_prop else f"{selected_view} Trend"
    
    if font_prop:
        ax.legend(prop=font_prop)
        ax.set_title(title_text, fontproperties=font_prop, fontsize=14)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(font_prop)
    else:
        ax.legend()
        ax.set_title(title_text)
        
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

with tab_risk:
    st.subheader("風險 vs 報酬")
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    x = summary_df['風險波動率 (年化)']
    y = summary_df['平均報酬率 (年化)']
    
    ax2.scatter(x, y, color='red', s=100, alpha=0.7)
    
    for i, txt in enumerate(summary_df.index):
        if font_prop:
            ax2.text(x.iloc[i]+0.002, y.iloc[i], txt, fontproperties=font_prop, fontsize=12)
        else:
            ax2.text(x.iloc[i]+0.002, y.iloc[i], txt)
            
    xlabel_text = "風險 (波動率)" if font_prop else "Risk (Volatility)"
    ylabel_text = "年化報酬率" if font_prop else "Annual Return"
    
    if font_prop:
        ax2.set_xlabel(xlabel_text, fontproperties=font_prop)
        ax2.set_ylabel(ylabel_text, fontproperties=font_prop)
        for label in ax2.get_xticklabels() + ax2.get_yticklabels():
            label.set_fontproperties(font_prop)
    else:
        ax2.set_xlabel(xlabel_text)
        ax2.set_ylabel(ylabel_text)
        
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2)

with tab_rank:
    st.subheader("報酬率排行")
    total_return = (df_final.iloc[-1] / df_final.iloc[0] - 1) * 100
    total_return = total_return.sort_values(ascending=False)
    
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    colors = ['red' if v > 0 else 'green' for v in total_return.values]
    ax3.bar(total_return.index, total_return.values, color=colors)
    
    ylabel_text = "報酬率 %" if font_prop else "Return %"
    if font_prop:
        ax3.set_ylabel(ylabel_text, fontproperties=font_prop)
        ax3.set_xticklabels(total_return.index, fontproperties=font_prop, fontsize=12)
        for label in ax3.get_yticklabels():
            label.set_fontproperties(font_prop)
    else:
        ax3.set_ylabel(ylabel_text)
        ax3.set_xticklabels(total_return.index, fontsize=12)
        
    ax3.grid(axis='y', linestyle='--', alpha=0.5)
    st.pyplot(fig3)
