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

# ✨ 帶有左側綠色裝飾條的大標題 (用於題目編號)
def section_header(text):
    st.markdown(f"""
        <div style='border-left: 10px solid {SPOTIFY_GREEN}; padding-left: 20px; margin-top: 50px; margin-bottom: 10px;'>
            <h2 style='color: #333333; font-size: 34px; font-weight: 800; font-family: "Arial Black"; margin: 0;'>
            {text}
            </h2>
        </div>
        """, unsafe_allow_html=True)

# ✨ 綠色圖表小副標題樣式 (位於圖表左上角)
def apply_chart_style(fig, title_text):
    fig.update_layout(
        template="simple_white",
        title=dict(
            text=f"<b>{title_text}</b>",
            font=dict(color=SPOTIFY_GREEN, size=24, family="Arial Black"),
            x=0, y=0.98
        ),
        font=dict(family="Arial", size=14, color="black"),
        margin=dict(t=100, b=50, l=50, r=50),
        bargap=0.1
    )
    # 座標軸加深
    fig.update_xaxes(tickfont=dict(color="black", size=12), title_font=dict(color="black", size=15, family="Arial Black"))
    fig.update_yaxes(tickfont=dict(color="black", size=12), title_font=dict(color="black", size=15, family="Arial Black"))
    return fig

# --- 3. 資料讀取與強力清洗 ---
@st.cache_data
def load_data():
    try:
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
    
    # 3.3 基礎清洗
    df = df.dropna(subset=['Year', 'Popularity', 'Genre', 'Artist', 'tempo'])
    df = df[(df['Popularity'] >= 0) & (df['Popularity'] <= 100)]
    
    # 3.4 流派清洗 (移除髒數據)
    df['Genre'] = df['Genre'].astype(str).str.title()
    df = df[~df['Genre'].isin(['N-A', 'Nan', 'Unknown', 'N/A'])]

    # 3.5 Explicit 標籤修復
    if 'Explicit' in df.columns:
        df['Exp_Str'] = df['Explicit'].astype(str).str.lower().str.strip()
        mapping = {'true': 'Explicit 🔞', '1': 'Explicit 🔞', 'false': 'Clean 🟢', '0': 'Clean 🟢'}
        df['Explicit_Label'] = df['Exp_Str'].map(mapping).fillna('Clean 🟢')

    return df

df = load_data()

if df is None:
    st.error("❌ 無法載入資料檔，請確認 GitHub 檔案名稱正確。")
    st.stop()

# --- 4. 側邊欄控制 ---
with st.sidebar:
    st.title("🎧 Settings")
    year_range = st.slider("📅 Year Range", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
    df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    top_n = st.slider("🏆 Top Genres Count", 3, 15, 5)
    st.markdown("---")
    st.info(f"Analyzing {len(df_filtered):,} tracks")

# --- 5. 主頁面內容 ---
st.title("🎵 Spotify Intelligence Dashboard")

# 建立三個分頁
tab1, tab2, tab3 = st.tabs(["📈 Market Strategy", "🎛️ Audio Lab", "🌍 Global Map"])

# === TAB 1: 市場策略 (1-5 題) ===
with tab1:
    # 1. 市場趨勢
    section_header("1. Market Trend Evolution")
    yearly = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
    fig1 = px.line(yearly, x='Year', y='Popularity', markers=True, height=500)
    fig1.update_traces(line=dict(color=SPOTIFY_BLACK, width=4), marker=dict(size=10, color=SPOTIFY_GREEN))
    fig1 = apply_chart_style(fig1, "Yearly Average Popularity Trend")
    st.plotly_chart(fig1, width='stretch')

    st.markdown("---")

    # 2. 發行策略 (單曲 vs 專輯)
    section_header("2. Single vs. Album Strategy")
    top_genres_list = df_filtered['Genre'].value_counts().head(top_n).index
    df_strat = df_filtered[df_filtered['Genre'].isin(top_genres_list)]
    fig2 = px.box(df_strat, x='Album/Single', y='Popularity', color='Album/Single',
                 facet_col='Genre', facet_col_wrap=5, height=700,
                 color_discrete_map={'single': SPOTIFY_GREEN, 'album': "#B3B3B3"},
                 category_orders={'Album/Single': ['single', 'album']})
    fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
    fig2 = apply_chart_style(fig2, f"Format Performance by Top {top_n} Genres")
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2, width='stretch')

    st.markdown("---")

    # 3. 內容策略 (Explicit)
    section_header("3. Content Strategy (Explicit Content)")
    df_exp = df_filtered[df_filtered['Genre'].isin(top_genres_list)]
    avg_exp = df_exp.groupby(['Genre', 'Explicit_Label'])['Popularity'].mean().reset_index()
    fig3 = px.bar(avg_exp, x='Genre', y='Popularity', color='Explicit_Label', barmode='group',
                 color_discrete_map={'Explicit 🔞': SPOTIFY_BLACK, 'Clean 🟢': SPOTIFY_GREEN}, height=550)
    fig3 = apply_chart_style(fig3, "Average Popularity: Explicit vs. Clean")
    fig3.update_layout(legend_title_text="")
    st.plotly_chart(fig3, width='stretch')

    st.markdown("---")

    # 4. 巨星效應
    section_header("4. The Superstar Effect")
    art_stats = df_filtered.groupby('Artist').agg({'Artist_followers': 'mean', 'Popularity': 'max', 'Title': 'count'}).reset_index()
    art_stats = art_stats[art_stats['Title'] > 2]
    if len(art_stats) > 1:
        corr_val = art_stats['Artist_followers'].corr(art_stats['Popularity'])
        st.write(f"📊 **Stat Correlation Coefficient:** `{corr_val:.2f}`")
        fig4 = px.scatter(art_stats, x='Artist_followers', y='Popularity', hover_name='Artist', 
                         log_x=True, trendline="ols", trendline_color_override=SPOTIFY_BLACK, height=650)
        fig4.update_traces(marker=dict(size=8, color=SPOTIFY_GREEN, line=dict(width=1, color='black')), opacity=0.6)
        fig4 = apply_chart_style(fig4, "Artist Reach vs. Chart Success")
        st.plotly_chart(fig4, width='stretch')

    st.markdown("---")

    # 5. 黑馬雷達
    section_header("5. Talent Scouting: Dark Horse Radar")
    dark = df_filtered[(df_filtered['Artist_followers'] < 50000) & (df_filtered['Popularity'] > 75)].copy()
    if not dark.empty:
        fig5 = px.scatter(dark, x='energy', y='danceability', size='Popularity', color='Popularity',
                         hover_name='Title', color_continuous_scale=['#F0FFF0', SPOTIFY_GREEN], height=750)
        fig5.add_vline(x=0.5, line_dash="dash", line_color="grey")
        fig5.add_hline(y=0.5, line_dash="dash", line_color="grey")
        fig5 = apply_chart_style(fig5, "High-Impact Tracks from Emerging Artists")
        st.plotly_chart(fig5, width='stretch')

# === TAB 2: 音樂實驗室 (6-9 題) ===
with tab2:
    # 6. 節奏分析 (BPM) - Jupyter 紮實版
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
    
    fig6.update_traces(xbins=dict(start=0, end=250, size=5), textposition='outside', marker_line_width=1, marker_line_color="white")
    fig6 = apply_chart_style(fig6, "Tempo Distribution: The Mainstream Sweet Spot")
    fig6.add_vline(x=120, line_width=3, line_dash="dash", line_color=SPOTIFY_BLACK, annotation_text="120 BPM")
    st.plotly_chart(fig6, width='stretch')

    st.markdown("---")

    # 7. 歌曲長度趨勢
    section_header("7. Duration Trends")
    dur_trend = df_filtered.groupby('Year')['duration_min'].mean().reset_index()
    fig7 = px.line(dur_trend, x='Year', y='duration_min', markers=True, height=500)
    fig7.update_traces(line_color=SPOTIFY_BLACK, marker=dict(color=SPOTIFY_GREEN, size=8))
    fig7 = apply_chart_style(fig7, "The Streaming Effect: Avg Track Duration")
    st.plotly_chart(fig7, width='stretch')

    st.markdown("---")

    # 8. 決策矩陣 (相關性)
    section_header("8. Audio Feature Correlation Matrix")
    corr_cols = ['Popularity', 'danceability', 'energy', 'valence', 'tempo', 'loudness']
    corr_mat = df_filtered[corr_cols].corr()
    fig8 = px.imshow(corr_mat, text_auto='.2f', aspect='auto',
                    color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN], height=600)
    fig8 = apply_chart_style(fig8, "Which Features Drive Success?")
    st.plotly_chart(fig8, width='stretch')

    st.markdown("---")

    # 9. 能量散佈圖
    section_header("9. Feature Lab: Energy vs. Danceability")
    df_sample = df_filtered.sample(n=min(2000, len(df_filtered)), random_state=42)
    fig9 = px.scatter(df_sample, x='energy', y='danceability', color='Popularity',
                     color_continuous_scale=['#F0F0F0', SPOTIFY_GREEN], opacity=0.6, height=700)
    fig9.update_traces(marker=dict(size=9, line=dict(width=1, color='DarkSlateGrey')))
    fig9 = apply_chart_style(fig9, "Distribution: Energy vs. Danceability")
    st.plotly_chart(fig9, width='stretch')

# === TAB 3: 全球版圖 (第 10 題) ===
with tab3:
    section_header("10. Global Market Reach")
    geo_data = df_filtered.groupby('Country')['Popularity'].mean().reset_index()
    fig10 = px.choropleth(geo_data, locations="Country", locationmode='country names', color="Popularity",
                         color_continuous_scale=['#F5F5F5', SPOTIFY_GREEN, '#106b31'], height=800)
    fig10 = apply_chart_style(fig10, "Average Popularity by Market")
    fig10.update_layout(geo=dict(showframe=False, projection_type='natural earth'))
    st.plotly_chart(fig10, width='stretch')
