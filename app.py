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
# 因為我們已經把字型檔上傳到 GitHub 了，所以它一定會在當前目錄下
font_path = "TaipeiSansTCBeta-Regular.ttf"
my_font = None

if os.path.exists(font_path):
    # 建立字型屬性
    my_font = fm.FontProperties(fname=font_path)
    # 設定 Matplotlib 全局字型 (備用)
    plt.rcParams['font.family'] = my_font.get_name()
else:
    st.warning("⚠️ 找不到字型檔！請確認你有將 .ttf 檔案上傳到 GitHub。")

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
    
    # 下載資料
    try:
        data = yf.download(list(tickers.keys()), start="2023-01-01", auto_adjust=False)['Adj Close']
        # 如果下載回來是空的，拋出錯誤
        if data.empty:
            raise ValueError("No data found")
        data.rename(columns=tickers, inplace=True)
    except Exception as e:
        return None, None, None, None

    # 資料處理
    df_orig = data.copy()
    
    # 模擬缺失
    df_dirty = data.copy()
    try:
        if not df_dirty.empty:
            df_dirty.iloc[0:5, 0] = np.nan
            df_dirty.iloc[10:13, 1] = np.nan
    except:
        pass
        
    # 修復
    df_clean = df_dirty.ffill().bfill()
    
    return tickers, df_orig, df_dirty, df_clean

# 執行載入
tickers_map, df_orig, df_dirty, df_final = load_data()

# 如果資料下載失敗，停止執行並顯示警告
if df_final is None or df_final.empty:
    st.error("❌ 無法從 Yahoo Finance 下載資料，這可能是網路連線問題。請重新整理網頁再試一次。")
    st.stop()

# ==========================================
# 3. 介面顯示
# ==========================================
st.title("📈 台灣前十大權值股分析")

st.header("1. 資料清洗演示")
c1, c2, c3 = st.columns(3)
c1.markdown("**原始缺失值**")
c1.dataframe(df_orig.isnull().sum().to_frame("數量").T)

c2.markdown("**模擬缺失值 (紅色代表有缺)**")
c2.dataframe(df_dirty.isnull().sum().to_frame("數量").T.style.highlight_max(axis=1, color='pink'))

c3.markdown("**修復後狀態**")
c3.dataframe(df_final.isnull().sum().to_frame("數量").T)

st.header("2. 視覺化儀表板")
tab1, tab2 = st.tabs(["股價走勢", "報酬排行"])

with tab1:
    st.subheader("股價走勢")
    selected_stock = st.selectbox("選擇股票", ["全部"] + list(tickers_map.values()))
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    if selected_stock == "全部":
        for col in df_final.columns:
            # 歸一化
            ax.plot(df_final[col] / df_final[col].iloc[0], label=col)
        ylabel_text = "倍數"
    else:
        ax.plot(df_final[selected_stock], label=selected_stock)
        ylabel_text = "價格"

    # 套用中文字型
    if my_font:
        ax.set_title(f"{selected_stock} 走勢圖", fontproperties=my_font, fontsize=15)
        ax.set_ylabel(ylabel_text, fontproperties=my_font)
        ax.legend(prop=my_font)
        # 設定座標軸刻度字型
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
        ax2.set_title("報酬率排行 (%)", fontproperties=my_font, fontsize=15)
        ax2.set_xticklabels(ret.index, fontproperties=my_font, fontsize=12)
        ax2.set_ylabel("報酬率 %", fontproperties=my_font)
        
    st.pyplot(fig2)
