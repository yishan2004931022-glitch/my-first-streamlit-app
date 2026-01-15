import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="Spotify Producer Dashboard",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 視覺風格與自定義函數 ---
SPOTIFY_GREEN = "#1DB954"
SPOTIFY_BLACK = "#191414"

# ✨ 黑色大章節標題 (1. 2. 3...)
def section_header(text):
    st.markdown(f"""
        <h2 style='color: #333333; font-size: 34px; font-weight: 800; margin-top: 45px; margin-bottom: 5px; font-family: "Arial Black";'>
        {text}
        </h2>
        """, unsafe_allow_html=True)

# ✨ 綠色圖表小副標題樣式 (位於圖表左上角)
def apply_chart_style(fig, title_text):
    fig.update_layout(
        template="simple_white",
        title=dict(
            text=f"<b>{title_text}</b>",
            font=dict(color=SPOTIFY_GREEN, size=22, family="Arial Black"),
            x=0, y=0.98  # 固定在左上角
        ),
        font=dict(family="Arial", size=13, color="black"),
        margin=dict(t=100, b=50, l=50, r=50),
        bargap=0.1 # 柱狀圖間隙
    )
    # 座標軸加深
    fig.update_xaxes(tickfont=dict(color="black", size=12), title_font=dict(color="black", size=14))
    fig.update_yaxes(tickfont=dict(color="black", size=12), title_font=dict(color="black", size=14))
    return fig

# --- 3. 資料讀取與強力清洗 ---
@st.cache_data
def load_data():
    try:
        # 優先讀取壓縮檔
        df = pd.read_csv('Final database.csv.gz', compression='gzip', low_memory=False)
    except:
        try:
            df = pd.read_csv('Final database.zip', compression='zip', low_memory=False)
        except:
            return None

    # 3.1 數值轉換
    numeric_cols = ['Popularity', 'danceability', 'energy', 'tempo', 'duration_ms', 'Artist_followers', 'loudness', 'valence']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 3.2 日期與時間處理
    df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
    df['Year'] = df['Release_date'].dt.year
    df['duration_min'] = df['duration_ms'] / 60000
    
    # 3.3 基礎清洗：移除空值與髒數據
    df = df.dropna(subset=['Year', 'Popularity', 'Genre', 'Artist', 'tempo'])
    df = df[(df['Popularity'] >= 0) & (df['Popularity'] <= 100)]
    
    # 3.4 流派清洗 (移除 N-A, Unknown 等)
    df['Genre'] = df['Genre'].astype(str).str.title()
    junk = ['N-A', 'Nan', 'Unknown', 'N/A', 'N-A']
    df = df[~df['Genre'].isin(junk)]

    # 3.5 Explicit 標籤修復
    if 'Explicit' in df.columns:
        df['Exp_Str'] = df['Explicit'].astype(str).str.lower().str.strip()
        mapping = {
            'true': 'Explicit 🔞', '1': 'Explicit 🔞', '1.0': 'Explicit 🔞',
            'false': 'Clean 🟢', '0': 'Clean 🟢', '0.0': 'Clean 🟢'
        }
        df['Explicit_Label'] = df['Exp_Str'].map(mapping).fillna('Clean 🟢')

    return df

# 執行讀取
df = load_data()

if df is None:
    st.error("❌ 無法載入資料檔，請確認 GitHub 目錄中包含資料檔案。")
    st.stop()

# --- 4. 側邊欄控制 ---
with st.sidebar:
    st.title("🎧 Settings")
    min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
    year_range = st.slider("📅 Year Range", min_year, max_year, (2010, 2024))
    
    # 資料過濾
    df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    
    top_n = st.slider("🏆 Top Genres Count", 3, 15, 5)
    st.markdown("---")
    st.info(f"Analyzing {len(df_filtered):,} tracks")

# --- 5. 主頁面內容 ---
st.title("🎵 Spotify Producer Dashboard")
st.markdown(f"### 📊 Analysis Period: {year_range[0]} - {year_range[1]}")

# 建立分頁
tab1, tab2, tab3 = st.tabs(["📈 Market Strategy", "🎛️ Audio Lab", "🌍 Global Map"])

# === TAB 1: 市場策略 (1-5 題) ===
with tab1:
    # Q4. 市場趨勢
    section_header("1. Market Trend Evolution")
    yearly = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
    fig1 = px.line(yearly, x='Year', y='Popularity', markers=True, height=500)
    fig1.update_traces(line=dict(color=SPOTIFY_BLACK, width=3), marker=dict(size=8, color=SPOTIFY_GREEN))
    fig1 = apply_chart_style(fig1, "Yearly Average Popularity Trend")
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")

    # Q1. 發行策略
    section_header("2. Single vs. Album Strategy")
    top_genres_list = df_filtered['Genre'].value_counts().head(top_n).index
    df_strat = df_filtered[df_filtered['Genre'].isin(top_genres_list)]
    fig2 = px.box(df_strat, x='Album/Single', y='Popularity', color='Album/Single',
                 facet_col='Genre', facet_col_wrap=5, height=700,
                 color_discrete_map={'single': SPOTIFY_GREEN, 'album': "#B3B3B3"},
                 category_orders={'Album/Single': ['single', 'album']})
    fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>", font=dict(size=14)))
    fig2 = apply_chart_style(fig2, f"Popularity by Format (Top {top_n} Genres)")
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # Q2. 歌詞分級 (Explicit)
    section_header("3. Content Strategy (Explicit)")
    df_exp = df_filtered[df_filtered['Genre'].isin(top_genres_list)]
    avg_exp = df_exp.groupby(['Genre', 'Explicit_Label'])['Popularity'].mean().reset_index()
    fig3 = px.bar(avg_exp, x='Genre', y='Popularity', color='Explicit_Label', barmode='group',
                 color_discrete_map={'Explicit 🔞': SPOTIFY_BLACK, 'Clean 🟢': SPOTIFY_GREEN}, height=550)
    fig3 = apply_chart_style(fig3, "The Impact of Explicit Content on Popularity")
    fig3.update_layout(legend_title_text="")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # Q8. 巨星效應
    section_header("4. The Superstar Effect")
    art_stats = df_filtered.groupby('Artist').agg({'Artist_followers': 'mean', 'Popularity': 'max', 'Title': 'count'}).reset_index()
    art_stats = art_stats[art_stats['Title'] > 2]
    if len(art_stats) > 1:
        corr_val = art_stats['Artist_followers'].corr(art_stats['Popularity'])
        # 相關係數指標卡片
        st.metric(label="📊 Followers vs. Peak Popularity Correlation", value=f"{corr_val:.2f}")
        
        fig4 = px.scatter(art_stats, x='Artist_followers', y='Popularity', hover_name='Artist', 
                         log_x=True, trendline="ols", trendline_color_override=SPOTIFY_BLACK, height=600)
        fig4.update_traces(marker=dict(size=8, color=SPOTIFY_GREEN, line=dict(width=1, color="black")), opacity=0.6)
        fig4 = apply_chart_style(fig4, "Do More Followers Mean Higher Chart Peaks?")
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")

    # Q9. 黑馬雷達
    section_header("5. Talent Scouting: Dark Horse Radar")
    dark = df_filtered[(df_filtered['Artist_followers'] < 50000) & (df_filtered['Popularity'] > 75)].copy()
    if not dark.empty:
        fig5 = px.scatter(dark, x='energy', y='danceability', size='Popularity', color='Popularity',
                         hover_name='Title', hover_data=['Artist'],
                         color_continuous_scale=['#F0FFF0', SPOTIFY_GREEN], height=750)
        # 加入象限線
        fig5.add_vline(x=0.5, line_dash="dash", line_color="grey")
        fig5.add_hline(y=0.5, line_dash="dash", line_color="grey")
        # 標註象限
        fig5.add_annotation(x=0.9, y=0.9, text="<b>🔥 CLUB</b>", showarrow=False, font=dict(size=16))
        fig5.add_annotation(x=0.1, y=0.9, text="<b>🍷 GROOVE</b>", showarrow=False, font=dict(size=16))
        fig5.add_annotation(x=0.9, y=0.1, text="<b>⚡ POWER</b>", showarrow=False, font=dict(size=16))
        fig5.add_annotation(x=0.1, y=0.1, text="<b>🌙 BALLAD</b>", showarrow=False, font=dict(size=16))
        
        fig5 = apply_chart_style(fig5, "Emerging Artists: High Streams with Low Following")
        st.plotly_chart(fig5, use_container_width=True)

# === TAB 2: 音樂實驗室 (6-9 題) ===
with tab2:
    # Q5. 節奏分析 (BPM) - Jupyter 紮實版
    section_header("6. Tempo Analysis (BPM)")
    def classify_tempo(bpm):
        if bpm < 100: return 'Slow (<100)'
        elif 100 <= bpm <= 140: return 'Mainstream (100-140)'
        else: return 'Fast (>140)'
    df_filtered['Tempo_Zone'] = df_filtered['tempo'].apply(classify_tempo)
    
    fig6 = px.histogram(df_filtered, x='tempo', color='Tempo_Zone',
                       color_discrete_map={'Slow (<100)': '#B3B3B3', 'Mainstream (100-140)': SPOTIFY_GREEN, 'Fast (>140)': '#535353'},
                       category_orders={'Tempo_Zone': ['Slow (<100)', 'Mainstream (100-140)', 'Fast (>140)']},
                       text_auto='.2s', height=600)
    
    # 🔥 關鍵：讓柱子變粗 (xbins size=5)
    fig6.update_traces(xbins=dict(start=0, end=250, size=5), textposition='outside', marker_line_width=1, marker_line_color="white")
    fig6 = apply_chart_style(fig6, "Tempo Zones: The Dominance of Mainstream")
    fig6.add_vline(x=120, line_width=3, line_dash="dash", line_color=SPOTIFY_BLACK, annotation_text="120 BPM")
    st.plotly_chart(fig6, use_container_width=True)

    st.markdown("---")

    # Q7. 歌曲長度趨勢
    section_header("7. Duration Trends")
    dur_trend = df_filtered.groupby('Year')['duration_min'].mean().reset_index()
    fig7 = px.line(dur_trend, x='Year', y='duration_min', markers=True, height=500)
    fig7.update_traces(line_color=SPOTIFY_BLACK, marker=dict(color=SPOTIFY_GREEN, size=8))
    fig7 = apply_chart_style(fig7, "Are Songs Getting Shorter? (The Streaming Effect)")
    fig7.update_layout(yaxis_title="Minutes")
    st.plotly_chart(fig7, use_container_width=True)

    st.markdown("---")

    # Q10. 決策矩陣 (相關性)
    section_header("8. Audio Feature Correlation Matrix")
    corr_cols = ['Popularity', 'danceability', 'energy', 'valence', 'tempo', 'loudness']
    corr_mat = df_filtered[corr_cols].corr()
    fig8 = px.imshow(corr_mat, text_auto='.2f', aspect='auto',
                    color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN], height=600)
    fig8 = apply_chart_style(fig8, "Which Audio Features Drive Popularity?")
    st.plotly_chart(fig8, use_container_width=True)

    st.markdown("---")

    # Q3. 能量分布散佈圖
    section_header("9. Feature Lab: Energy vs. Danceability")
    df_sample = df_filtered.sample(n=min(2000, len(df_filtered)), random_state=42)
    fig9 = px.scatter(df_sample, x='energy', y='danceability', color='Popularity',
                     color_continuous_scale=['#F0F0F0', SPOTIFY_GREEN], opacity=0.6, height=700)
    fig9.update_traces(marker=dict(size=9, line=dict(width=1, color='DarkSlateGrey')))
    fig9 = apply_chart_style(fig9, "Sample Distribution: Feature Analysis")
    st.plotly_chart(fig9, use_container_width=True)

# === TAB 3: 全球版圖 (10 題) ===
with tab3:
    section_header("10. Global Market Reach")
    geo_data = df_filtered.groupby('Country')['Popularity'].mean().reset_index()
    fig10 = px.choropleth(geo_data, locations="Country", locationmode='country names', color="Popularity",
                         color_continuous_scale=['#F5F5F5', SPOTIFY_GREEN, '#106b31'], height=800)
    fig10 = apply_chart_style(fig10, "Average Popularity by Market")
    fig10.update_layout(geo=dict(showframe=False, projection_type='natural earth'))
    st.plotly_chart(fig10, use_container_width=True)
