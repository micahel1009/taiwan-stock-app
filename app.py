import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import yfinance as yf
import os

# ==========================================
# 1. 網頁與字型設定 (本地讀取版)
# ==========================================
st.set_page_config(page_title="台灣權值股分析", layout="wide")

# 設定中文字型
font_path = "TaipeiSansTCBeta-Regular.ttf"
my_font = None

if os.path.exists(font_path):
    my_font = fm.FontProperties(fname=font_path)
    # 設定全域字型 (備用)
    plt.rcParams['font.family'] = my_font.get_name()
else:
    st.warning("⚠️ 找不到字型檔！請確認 GitHub 上有 TaipeiSansTCBeta-Regular.ttf")

# ==========================================
# 2. 資料載入
# ==========================================
@st.cache_data
def load_data():
    tickers = {
        "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科",
        "2308.TW": "台達電", "2382.TW": "廣達", "2881.TW": "富邦金",
        "2882.TW": "國泰金", "2412.TW": "中華電", "2303.TW": "聯電",
        "2891.TW": "中信金"
    }
    
    try:
        data = yf.download(list(tickers.keys()), start="2023-01-01", auto_adjust=False)['Adj Close']
        if data.empty: raise ValueError("No data")
        data.rename(columns=tickers, inplace=True)
    except:
        return None, None, None, None

    # 1. 原始資料
    df_orig = data.copy()
    
    # 2. 模擬髒資料
    df_dirty = data.copy()
    try:
        df_dirty.iloc[0:5, 0] = np.nan # 第一支股票缺5筆
        df_dirty.iloc[10:13, 1] = np.nan # 第二支股票缺3筆
        df_dirty.iloc[20, 2] = np.nan # 第三支股票缺1筆
    except: pass
        
    # 3. 修復後資料
    df_clean = df_dirty.ffill().bfill()
    
    return tickers, df_orig, df_dirty, df_clean

# 執行載入
tickers_map, df_orig, df_dirty, df_final = load_data()

if df_final is None:
    st.error("❌ 資料下載失敗，請重新整理網頁。")
    st.stop()

# ==========================================
# 3. 介面顯示 - 第一部分：資料清洗
# ==========================================
st.title("📈 台灣前十大權值股分析系統")

st.header("1. 資料清洗演示 (Data Cleaning)")
c1, c2, c3 = st.columns(3)
with c1:
    st.info("步驟 1：原始資料")
    st.dataframe(df_orig.isnull().sum().to_frame("缺失數").T)
with c2:
    st.warning("步驟 2：模擬缺失 (紅色)")
    st.dataframe(df_dirty.isnull().sum().to_frame("缺失數").T.style.highlight_max(axis=1, color='pink'))
with c3:
    st.success("步驟 3：修復完成")
    st.dataframe(df_final.isnull().sum().to_frame("缺失數").T)

st.markdown("---")

# ==========================================
# 4. 介面顯示 - 第二部分：統計與風險 (這部分是加回來的！)
# ==========================================
st.header("2. 統計數據與風險分析")

# 計算指標
returns = df_final.pct_change()
summary_df = pd.DataFrame({
    '平均報酬率(年)': returns.mean() * 252,
    '風險波動率(年)': returns.std() * np.sqrt(252)
})

col_stats_1, col_stats_2 = st.columns([1, 1.5]) # 左窄右寬

with col_stats_1:
    st.subheader("📊 股價統計摘要")
    st.dataframe(df_final.describe())
    st.subheader("⚖️ 風險報酬數值")
    st.dataframe(summary_df.style.format("{:.4f}").background_gradient(cmap="Blues"))

with col_stats_2:
    st.subheader("風險 vs 報酬 散佈圖")
    fig_risk, ax_risk = plt.subplots(figsize=(10, 6))
    
    x = summary_df['風險波動率(年)']
    y = summary_df['平均報酬率(年)']
    
    ax_risk.scatter(x, y, color='red', s=100, alpha=0.7)
    
    # 標示文字
    for i, txt in enumerate(summary_df.index):
        label_font = my_font if my_font else None
        ax_risk.text(x.iloc[i]+0.002, y.iloc[i], txt, fontproperties=label_font, fontsize=12)
    
    # 設定標籤字型
    if my_font:
        ax_risk.set_xlabel("風險 (波動率)", fontproperties=my_font)
        ax_risk.set_ylabel("年化報酬率", fontproperties=my_font)
        ax_risk.set_title("風險 vs 報酬 (越左上越好)", fontproperties=my_font, fontsize=15)
    
    ax_risk.grid(True, alpha=0.3)
    st.pyplot(fig_risk)

st.markdown("---")

# ==========================================
# 5. 介面顯示 - 第三部分：互動儀表板
# ==========================================
st.header("3. 視覺化儀表板 (Dashboard)")
tab1, tab2 = st.tabs(["📈 股價走勢", "🏆 報酬率排行"])

with tab1:
    st.subheader("股價走勢")
    selected_stock = st.selectbox("選擇股票:", ["全部比較 (歸一化)"] + list(tickers_map.values()))
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    if selected_stock == "全部比較 (歸一化)":
        for col in df_final.columns:
            ax.plot(df_final[col] / df_final[col].iloc[0], label=col, alpha=0.8)
        ylabel_text = "倍數"
    else:
        ax.plot(df_final[selected_stock], label=selected_stock, color='blue')
        # 加均線
        ma20 = df_final[selected_stock].rolling(20).mean()
        ax.plot(ma20, label='月線 (20MA)', color='orange', linestyle='--')
        ylabel_text = "價格"

    if my_font:
        ax.set_title(f"{selected_stock} 走勢圖", fontproperties=my_font, fontsize=15)
        ax.set_ylabel(ylabel_text, fontproperties=my_font)
        ax.legend(prop=my_font)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(my_font)
    else:
        ax.legend()
        
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

with tab2:
    st.subheader("報酬率排行")
    ret = (df_final.iloc[-1] / df_final.iloc[0] - 1) * 100
    ret = ret.sort_values(ascending=False)
    
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    colors = ['red' if v > 0 else 'green' for v in ret.values]
    ax2.bar(ret.index, ret.values, color=colors)
    
    if my_font:
        ax2.set_title("近一年報酬率排行 (%)", fontproperties=my_font, fontsize=15)
        ax2.set_xticklabels(ret.index, fontproperties=my_font, fontsize=12)
        ax2.set_ylabel("報酬率 %", fontproperties=my_font)
        
    st.pyplot(fig2)
