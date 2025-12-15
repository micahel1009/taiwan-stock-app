import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import yfinance as yf
import os
import requests

# ==========================================
# 1. 字型設定 (終極手動載入版)
# ==========================================
st.set_page_config(page_title="台灣權值股分析系統", layout="wide")

@st.cache_resource
def get_font():
    font_path = "NotoSansTC-Regular.ttf"
    font_url = "https://github.com/google/fonts/raw/main/ofl/notosanstc/NotoSansTC-Regular.ttf"
    
    # 如果檔案不在，就下載
    if not os.path.exists(font_path):
        with st.spinner("正在下載中文字型檔..."):
            try:
                response = requests.get(font_url)
                with open(font_path, "wb") as f:
                    f.write(response.content)
            except:
                return None
    
    # 直接回傳字型屬性物件
    return fm.FontProperties(fname=font_path)

# 取得字型物件
my_font = get_font()

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
    data = yf.download(list(tickers.keys()), start="2023-01-01", auto_adjust=False)['Adj Close']
    data.rename(columns=tickers, inplace=True)
    
    # 建立三種狀態的資料
    df_orig = data.copy()
    
    df_dirty = data.copy()
    if not df_dirty.empty: # 模擬缺失
        try:
            df_dirty.iloc[0:5, 0] = np.nan
            df_dirty.iloc[10:13, 1] = np.nan
        except: pass
        
    df_clean = df_dirty.ffill().bfill() # 修復
    
    return tickers, df_orig, df_dirty, df_clean

try:
    tickers_map, df_orig, df_dirty, df_final = load_data()
except:
    st.error("資料下載失敗，請重新整理網頁")
    st.stop()

# ==========================================
# 3. 畫面顯示
# ==========================================
st.title("📈 台灣前十大權值股分析")

st.header("1. 資料清洗演示")
c1, c2, c3 = st.columns(3)
c1.dataframe(df_orig.isnull().sum().to_frame("原始缺失").T)
c2.dataframe(df_dirty.isnull().sum().to_frame("模擬缺失").T.style.highlight_max(axis=1, color='pink'))
c3.dataframe(df_final.isnull().sum().to_frame("修復後").T)

st.header("2. 視覺化儀表板")
tab1, tab2 = st.tabs(["股價走勢", "報酬排行"])

with tab1:
    st.subheader("股價走勢")
    stock = st.selectbox("選擇股票", ["全部"] + list(tickers_map.values()))
    
    fig, ax = plt.subplots(figsize=(10, 5))
    if stock == "全部":
        for col in df_final.columns:
            ax.plot(df_final[col]/df_final[col].iloc[0], label=col)
        ylabel = "倍數"
    else:
        ax.plot(df_final[stock], label=stock)
        ylabel = "價格"

    # 【關鍵】這裡手動指定字型，不依賴系統
    if my_font:
        ax.set_title(f"{stock} 走勢圖", fontproperties=my_font, fontsize=15)
        ax.set_ylabel(ylabel, fontproperties=my_font)
        ax.legend(prop=my_font)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(my_font)
    else:
        ax.set_title(f"{stock} Trend")
        ax.legend()
        
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

with tab2:
    st.subheader("報酬率排行")
    ret = (df_final.iloc[-1]/df_final.iloc[0] - 1) * 100
    ret = ret.sort_values(ascending=False)
    
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    colors = ['red' if v > 0 else 'green' for v in ret.values]
    ax2.bar(ret.index, ret.values, color=colors)
    
    if my_font:
        ax2.set_xticklabels(ret.index, fontproperties=my_font, fontsize=12)
        ax2.set_ylabel("報酬率 %", fontproperties=my_font)
        
    st.pyplot(fig2)
