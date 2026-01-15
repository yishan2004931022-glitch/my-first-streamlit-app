import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="Spotify Dashboard 2026",
    page_icon="🎧",
    layout="wide"
)

# --- 2. 視覺函數 ---
SPOTIFY_GREEN = "#1DB954"

def section_header(text):
    st.markdown(f"<div style='border-left: 10px solid {SPOTIFY_GREEN}; padding-left: 20px; margin-top: 40px;'><h2 style='font-family: Arial Black;'>{text}</h2></div>", unsafe_allow_html=True)

def apply_style(fig, title):
    fig.update_layout(
        template="simple_white",
        title=dict(text=f"<b>{title}</b>", font=dict(color=SPOTIFY_GREEN, size=24), x=0, y=0.95),
        margin=dict(t=100, b=50)
    )
    return fig

# --- 3. 資料讀取 (防當機版) ---
@st.cache_data
def load_data():
    # 診斷檔案
    all_files = os.listdir('.')
    target = None
    if 'Final database.csv.gz' in all_files: target = 'Final database.csv.gz'
    elif 'Final database.zip' in all_files: target = 'Final database.zip'
    
    if not target:
        st.error(f"File Not Found! Available: {all_files}")
        return None

    try:
        df = pd.read_csv(target, low_memory=False) # 預設會自動處理 gz/zip
        # 基本欄位轉換
        for col in ['Popularity', 'danceability', 'energy', 'tempo', 'duration_ms', 'Artist_followers']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
        df['Year'] = df['Release_date'].dt.year
        df['duration_min'] = df['duration_ms'] / 60000
        df = df.dropna(subset=['Year', 'Popularity', 'Genre'])
        
        # Explicit 標籤處理
        if 'Explicit' in df.columns:
            df['Explicit_Label'] = df['Explicit'].astype(str).map({'True': 'Explicit 🔞', 'False': 'Clean 🟢', 'true': 'Explicit 🔞', 'false': 'Clean 🟢'})
        
        return df
    except Exception as e:
        st.error(f"Loading Error: {e}")
        return None

# --- 4. 主程式 ---
df = load_data()

if df is not None:
    # 側邊欄
    with st.sidebar:
        st.title("Settings")
        yr = st.slider("Year", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
        search = st.text_input("Search Artist", "")
        top_n = st.slider("Genres", 3, 15, 5)
        
        df_filtered = df[(df['Year'] >= yr[0]) & (df['Year'] <= yr[1])]
        if search:
            df_filtered = df_filtered[df_filtered['Artist'].str.contains(search, case=False, na=False)]
        
        csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Download CSV", csv, "spotify.csv", "text/csv")

    # 主頁面
    st.title("🎵 Spotify Intelligence")
    
    # KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tracks", len(df_filtered))
    c2.metric("Avg Pop", f"{df_filtered['Popularity'].mean():.1f}")
    c3.metric("Tempo", f"{df_filtered['tempo'].mean():.0f} BPM")
    c4.metric("Superstars", len(df_filtered[df_filtered['Artist_followers']>1000000]['Artist'].unique()))

    t1, t2, t3 = st.tabs(["Strategy", "AI Lab", "Global"])

    with t1:
        # 1. 趨勢
        section_header("1. Market Evolution")
        y_avg = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
        fig1 = apply_style(px.line(y_avg, x='Year', y='Popularity', markers=True), "Global Popularity Trend")
        st.plotly_chart(fig1, width='stretch')

        # 2. 發行策略 (箱型圖)
        section_header("2. Boxplot Analysis")
        top_g = df_filtered['Genre'].value_counts().head(top_n).index
        df_sub = df_filtered[df_filtered['Genre'].isin(top_g)]
        fig2 = apply_style(px.box(df_sub, x='Album/Single', y='Popularity', color='Album/Single', facet_col='Genre', facet_col_wrap=4), "Strategy by Genre")
        st.plotly_chart(fig2, width='stretch')

        # 3. 巨星效應 (OLS 趨勢線)
        section_header("3. Superstar Correlation")
        art = df_filtered.groupby('Artist').agg({'Artist_followers':'mean', 'Popularity':'max'}).reset_index()
        if len(art) > 5:
            fig3 = apply_style(px.scatter(art, x='Artist_followers', y='Popularity', log_x=True, trendline="ols"), "Followers vs. Peaks")
            st.plotly_chart(fig3, width='stretch')

    with t2:
        # 4. AI 預測
        section_header("4. AI Potential Predictor")
        ca1, ca2 = st.columns([1, 2])
        with ca1:
            d = st.slider("Dance", 0.0, 1.0, 0.6); e = st.slider("Energy", 0.0, 1.0, 0.7)
            st.metric("Hit Score", f"{(d*40 + e*60):.1f}")
        with ca2:
            radar = go.Figure(data=go.Scatterpolar(r=[d, e, 0.5, d], theta=['Dance','Energy','Loud','Dance'], fill='toself'))
            st.plotly_chart(radar, width='stretch')

        # 5. BPM 分析 (Jupyter 紮實版)
        section_header("5. Tempo Sweet Spot")
        fig5 = apply_style(px.histogram(df_filtered, x='tempo', nbins=50, text_auto='.2s'), "BPM Distribution")
        fig5.update_traces(xbins=dict(size=5), textposition='outside')
        st.plotly_chart(fig5, width='stretch')

        # 6. 相關矩陣
        section_header("6. Audio Feature Matrix")
        corr = df_filtered[['Popularity','danceability','energy','tempo']].corr()
        fig6 = apply_style(px.imshow(corr, text_auto='.2f'), "Correlation Matrix")
        st.plotly_chart(fig6, width='stretch')

    with t3:
        # 7. 地圖
        section_header("7. Global Heatmap")
        geo = df_filtered.groupby('Country')['Popularity'].mean().reset_index()
        fig7 = apply_style(px.choropleth(geo, locations="Country", locationmode='country names', color="Popularity"), "Market Reach")
        st.plotly_chart(fig7, width='stretch')
