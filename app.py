import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import yfinance as yf
import os
import requests

# ==========================================
# 1. 網頁設定與字型下載
# ==========================================
st.set_page_config(page_title="台灣權值股分析系統", layout="wide")

# 下載中文字型函式 (為了讓圖表顯示繁體中文)
def download_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/notosanstc/NotoSansTC-Regular.ttf"
    font_path = "NotoSansTC-Regular.ttf"
    # 如果檔案不存在，才下載
    if not os.path.exists(font_path):
        with st.spinner("正在下載中文字型 (NotoSansTC)..."):
            try:
                response = requests.get(font_url)
                with open(font_path, "wb") as f:
                    f.write(response.content)
            except:
                st.warning("字型下載失敗，圖表中文可能會變亂碼。")
    return font_path

# 設定 Matplotlib 字型
font_path = download_font()
if os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
else:
    font_prop = None # 如果下載失敗，就用預設字型

# ==========================================
# 2. 資料載入與處理邏輯 (包含模擬缺失值)
# ==========================================
@st.cache_data # 使用快取，避免每次操作網頁都重新下載資料
def load_and_process_data():
    # 定義股票清單
    tickers = {
        "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科",
        "2308.TW": "台達電", "2382.TW": "廣達", "2881.TW": "富邦金",
        "2882.TW": "國泰金", "2412.TW": "中華電", "2303.TW": "聯電",
        "2891.TW": "中信金"
    }
    
    # 1. 下載資料 (原始資料)
    data = yf.download(list(tickers.keys()), start="2023-01-01", auto_adjust=False)['Adj Close']
    data.rename(columns=tickers, inplace=True)
    
    # 備份一份原始資料 (這通常是完美的，全為 0)
    df_original = data.copy()
    missing_orig = df_original.isnull().sum().to_frame("缺失筆數").T

    # 2. 人工模擬缺失值 (弄髒資料)
    # 為了展示清洗功能，我們故意把一些數據刪掉
    df_dirty = data.copy()
    if not df_dirty.empty:
        df_dirty.iloc[0:5, df_dirty.columns.get_loc("台積電")] = np.nan # 刪台積電 5 天
        df_dirty.iloc[10:13, df_dirty.columns.get_loc("鴻海")] = np.nan # 刪鴻海 3 天
        df_dirty.iloc[20, df_dirty.columns.get_loc("聯發科")] = np.nan  # 刪聯發科 1 天
    
    # 計算髒資料的缺失數
    missing_dirty = df_dirty.isnull().sum().to_frame("缺失筆數").T

    # 3. 執行資料修復 (清洗資料)
    # 使用 ffill (前值填補) 和 bfill (後值填補)
    df_clean = df_dirty.ffill().bfill()
    missing_clean = df_clean.isnull().sum().to_frame("缺失筆數").T
    
    return tickers, df_original, missing_orig, df_dirty, missing_dirty, df_clean, missing_clean

# 執行載入函式
try:
    tickers_map, df_orig, miss_orig, df_dirty, miss_dirty, df_final, miss_final = load_and_process_data()
except Exception as e:
    st.error(f"資料載入失敗: {e}")
    st.stop()

# ==========================================
# 3. 網頁介面設計 (UI)
# ==========================================
st.title("📈 台灣前十大權值股 - 分析與資料清洗展示")

# --- 第一區塊：資料清洗三部曲 (你要求的重點) ---
st.header("1. 資料清洗三部曲 (模擬展示)")
st.markdown("這裡展示從 **原始資料** $\\rightarrow$ **模擬缺失** $\\rightarrow$ **修復完成** 的完整過程。")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("步驟 1：檢查原始資料")
    st.write("這是從 Yahoo 財經抓下來的原始狀態，通常非常完整。")
    st.dataframe(miss_orig) # 顯示全 0 的表格

with col2:
    st.warning("步驟 2：模擬資料缺失")
    st.write("我們人工刪除了部分數據 (台積電、鴻海、聯發科)。")
    # 將缺失值大於 0 的地方標示為紅色
    st.dataframe(miss_dirty.style.highlight_max(axis=1, color='pink'))

with col3:
    st.success("步驟 3：資料修復完成")
    st.write("使用 Pandas 的 `ffill()` 修補後，資料恢復完整。")
    st.dataframe(miss_final) # 顯示變回 0 的表格

st.markdown("---")

# --- 第二區塊：統計數據與風險分析 ---
st.header("2. 統計數據分析")

# 計算年化報酬與風險
returns = df_final.pct_change()
summary_df = pd.DataFrame({
    '平均報酬率 (年化)': returns.mean() * 252,
    '風險波動率 (年化)': returns.std() * np.sqrt(252)
})

c1, c2 = st.columns(2)

with c1:
    st.subheader("📊 股價統計摘要")
    st.dataframe(df_final.describe()) # 顯示 mean, std, min, max 等統計量

with c2:
    st.subheader("⚖️ 風險 vs 報酬表")
    # 使用漸層色 (Blues) 讓表格看起來更專業
    st.dataframe(summary_df.style.format("{:.4f}").background_gradient(cmap="Blues"))

st.markdown("---")

# --- 第三區塊：互動式視覺化儀表板 ---
st.header("3. 視覺化儀表板")

# 建立分頁籤
tab_trend, tab_risk, tab_rank = st.tabs(["📈 股價走勢圖", "⚖️ 風險報酬分析", "🏆 報酬率排行"])

# 分頁 1: 股價走勢
with tab_trend:
    st.subheader("股價走勢 (歸一化比較)")
    
    # 選擇選單
    options = ["全部比較 (歸一化)"] + list(tickers_map.values())
    selected_view = st.selectbox("請選擇要查看的股票:", options)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    if selected_view == "全部比較 (歸一化)":
        for col in df_final.columns:
            # 歸一化：讓所有股票都從 1.0 開始，方便比較漲幅
            normalized = df_final[col] / df_final[col].iloc[0]
            ax.plot(normalized, label=col, alpha=0.7)
        ax.set_ylabel("累計報酬倍數", fontproperties=font_prop)
    else:
        # 單獨查看某支股票，並加上均線
        ax.plot(df_final[selected_view], label=selected_view, color='blue')
        ma20 = df_final[selected_view].rolling(20).mean()
        ax.plot(ma20, label='月線 (20MA)', color='orange', linestyle='--')
        ax.set_ylabel("股價 (TWD)", fontproperties=font_prop)
    
    # 設定圖表細節
    if font_prop:
        ax.legend(prop=font_prop)
        ax.set_title(f"{selected_view} 走勢圖", fontproperties=font_prop, fontsize=14)
        # 設定座標軸字型
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(font_prop)
    else:
        ax.legend()
        
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

# 分頁 2: 風險報酬散佈圖
with tab_risk:
    st.subheader("風險 vs 報酬 散佈圖")
    st.info("💡 解讀：越往「左上角」代表「低風險、高報酬」，是較佳的投資標的。")
    
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    x = summary_df['風險波動率 (年化)']
    y = summary_df['平均報酬率 (年化)']
    
    ax2.scatter(x, y, color='red', s=100, alpha=0.7)
    
    # 標上股票名稱
    for i, txt in enumerate(summary_df.index):
        if font_prop:
            ax2.text(x.iloc[i]+0.002, y.iloc[i], txt, fontproperties=font_prop, fontsize=12)
        else:
            ax2.text(x.iloc[i]+0.002, y.iloc[i], txt)
            
    ax2.set_xlabel("風險 (波動率)", fontproperties=font_prop)
    ax2.set_ylabel("年化報酬率", fontproperties=font_prop)
    ax2.grid(True, alpha=0.3)
    
    if font_prop:
        for label in ax2.get_xticklabels() + ax2.get_yticklabels():
            label.set_fontproperties(font_prop)
            
    st.pyplot(fig2)

# 分頁 3: 報酬率排行
with tab_rank:
    st.subheader("近一年總報酬率排行")
    # 計算總報酬
    total_return = (df_final.iloc[-1] / df_final.iloc[0] - 1) * 100
    total_return = total_return.sort_values(ascending=False)
    
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    # 漲紅跌綠
    colors = ['red' if v > 0 else 'green' for v in total_return.values]
    ax3.bar(total_return.index, total_return.values, color=colors)
    
    ax3.set_ylabel("報酬率 %", fontproperties=font_prop)
    ax3.grid(axis='y', linestyle='--', alpha=0.5)
    
    if font_prop:
        ax3.set_xticklabels(total_return.index, fontproperties=font_prop, fontsize=12)
        for label in ax3.get_yticklabels():
            label.set_fontproperties(font_prop)
            
    st.pyplot(fig3)