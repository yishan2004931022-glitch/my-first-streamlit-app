import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio

# --- 1. 頁面基礎設定 (必須是第一行執行代碼) ---
st.set_page_config(
    page_title="Spotify Strategy Dashboard",
    page_icon="🎵",
    layout="wide"
)

# --- 2. 視覺風格定義 (Spotify Theme) ---
SPOTIFY_GREEN = "#1DB954"
SPOTIFY_BLACK = "#191414"
SPOTIFY_GREY = "#B3B3B3"
SPOTIFY_LIGHT_BG = "#FFFFFF"

# --- 3. 資料讀取與清洗函數 (使用 Cache 加速) ---
@st.cache_data
def load_and_clean_data():
    # 讀取 CSV (請確保檔案在同一目錄)
    try:
        df = pd.read_csv('spotify_data.parquet')
    except FileNotFoundError:
        return None

    # 1.1 強制轉換數值欄位
    numeric_cols = ['Popularity', 'danceability', 'energy', 'loudness', 'speechiness', 
                    'acoustics', 'instrumentalness', 'liveliness', 'valence', 'tempo', 
                    'duration_ms', 'Artist_followers']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 1.2 日期與時間維度
    df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
    df['Year'] = df['Release_date'].dt.year
    df = df.dropna(subset=['Release_date', 'Popularity', 'energy', 'Genre', 'Title'])
    df['duration_min'] = df['duration_ms'] / 60000 # 修正單位轉換 (ms -> min 應該除以 60000)

    # 1.3 進階清洗 (Q1 專用邏輯)
    # A. 剔除髒數據 (Popularity 0-100)
    df_clean = df[(df['Popularity'] >= 0) & (df['Popularity'] <= 100)].copy()

    # B. 只保留 Single 和 Album
    df_clean = df_clean[df_clean['Album/Single'].isin(['single', 'album'])]

    # C. 排除垃圾流派
    mask_junk = df_clean['Genre'].isin(['n-a', 'unknown', 'world-music']) 
    df_clean = df_clean[~mask_junk]

    # D. 流派名稱首字大寫
    df_clean['Genre'] = df_clean['Genre'].astype(str).str.title()
    # 修正 K-Pop 寫法
    df_clean['Genre'] = df_clean['Genre'].replace({'K-Pop': 'K-Pop', 'K-pop': 'K-Pop'})

    return df_clean

# --- 4. 執行資料讀取 ---
df_clean = load_and_clean_data()

if df_clean is None:
    st.error("❌ 找不到 'Final database.csv'。請將 CSV 檔案放入與 app.py 相同的資料夾中。")
    st.stop()

# --- 5. 側邊欄 (Sidebar) ---
with st.sidebar:
    st.title("🎧 Settings")
    st.markdown("Customize your view")
    
    # 讓使用者可以決定看「前幾名」的流派 (預設 4)
    top_n = st.slider("Select Top N Genres", min_value=2, max_value=8, value=4)
    
    st.markdown("---")
    st.markdown("Data Source: Spotify Dataset")

# --- 6. 主圖表邏輯 (Q1) ---
st.title("🎵 Release Strategy Analysis")
st.markdown("### Single vs. Album Performance by Genre")

# Step E: 根據側邊欄選擇的前 N 大流派進行篩選
target_genres = df_clean['Genre'].value_counts().head(top_n).index
df_segment = df_clean[df_clean['Genre'].isin(target_genres)]

# 計算平均值 (用於檢查或未來擴充)
means = df_segment.groupby(['Genre', 'Album/Single'])['Popularity'].mean().reset_index()

# 繪圖
fig1 = px.box(df_segment, 
              x='Album/Single', 
              y='Popularity', 
              color='Album/Single', 
              facet_col='Genre', 
              facet_col_wrap=top_n if top_n <= 4 else 4, # 自動調整排版
              title=f'Release Strategy: Top {top_n} Genres Comparison',
              color_discrete_map={'single': SPOTIFY_GREEN, 'album': SPOTIFY_GREY},
              category_orders={'Album/Single': ['single', 'album']},
              height=600)

# Layout Optimization (複製您的優化邏輯)
fig1.update_traces(boxmean=True)
fig1.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1])) # Clean labels

fig1.update_layout(
    title=dict(
        font=dict(color=SPOTIFY_GREEN, size=22, family="Arial Black")
    ),
    xaxis_title="", 
    yaxis_title="Popularity Score",
    template="simple_white",
    margin=dict(t=80),
    showlegend=True,
    legend_title_text="Format"
)

# Capitalize Legend Names
fig1.for_each_trace(lambda t: t.update(name=t.name.capitalize()))

# --- 7. 顯示圖表 ---
st.plotly_chart(fig1, use_container_width=True)

# (選用) 顯示數據統計摘要
with st.expander("📊 View Detailed Statistics"):
    st.dataframe(means.style.format({"Popularity": "{:.2f}"}))


