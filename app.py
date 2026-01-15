import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import statsmodels.api as sm

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="Spotify Producer Dashboard",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 視覺風格定義 (Spotify Theme) ---
SPOTIFY_GREEN = "#1DB954"
SPOTIFY_BLACK = "#191414"
SPOTIFY_GREY = "#B3B3B3"
SPOTIFY_DARK_GREY = "#535353"
SPOTIFY_WHITE = "#FFFFFF"

# ✨ 自定義標題函數：讓綠色標題更大一點點
def section_title(text):
    st.markdown(f"<h3 style='color: {SPOTIFY_GREEN}; font-size: 28px; font-weight: bold; margin-bottom: 20px;'>{text}</h3>", unsafe_allow_html=True)

# --- 3. 資料讀取與清洗 (快取加速) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Final database.csv.gz', compression='gzip', low_memory=False)
    except FileNotFoundError:
        try:
            df = pd.read_csv('Final database.zip', compression='zip', low_memory=False)
        except:
            return None

    numeric_cols = ['Popularity', 'danceability', 'energy', 'loudness', 'speechiness', 
                    'acoustics', 'instrumentalness', 'liveliness', 'valence', 'tempo', 
                    'duration_ms', 'Artist_followers']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
    df['Year'] = df['Release_date'].dt.year
    df['duration_min'] = df['duration_ms'] / 60000 
    
    df = df.dropna(subset=['Release_date', 'Popularity', 'Genre', 'tempo', 'Artist'])
    df = df[(df['Popularity'] >= 0) & (df['Popularity'] <= 100)]
    
    df['Genre'] = df['Genre'].astype(str).str.title()
    df['Genre'] = df['Genre'].replace({'K-Pop': 'K-Pop', 'K-pop': 'K-Pop'})
    
    if 'Explicit' in df.columns:
        # 修正：處理有些資料已經是字串 "True" 的情況
        df['Explicit_Label'] = df['Explicit'].astype(str).map({'True': 'Explicit 🔞', 'False': 'Clean 🟢', 'true': 'Explicit 🔞', 'false': 'Clean 🟢'})

    return df

df = load_data()

if df is None:
    st.error("❌ 找不到資料檔！請確認 GitHub 上有檔案")
    st.stop()

# --- 4. 側邊欄 ---
with st.sidebar:
    st.title("🎧 Settings")
    min_year = int(df['Year'].min())
    max_year = int(df['Year'].max())
    year_range = st.slider("📅 Year Range", min_year, max_year, (2010, 2024))
    df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    
    st.markdown("---")
    top_n = st.slider("🏆 Top Genres Count", 3, 10, 5)
    st.info(f"Analyzing {len(df_filtered):,} songs")

# --- 5. 主頁面內容 ---
st.title("🎵 Spotify Producer Analytics")
st.markdown(f"### Market Insights ({year_range[0]} - {year_range[1]})")

tab1, tab2, tab3 = st.tabs(["📈 Market Strategy", "🎛️ Audio Lab", "🌍 Global Map"])

# === TAB 1: 市場策略 (全單欄版) ===
with tab1:
    # 1. 市場趨勢
    section_title("1. Market Trend Evolution")
    yearly_trend = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
    fig4 = px.line(yearly_trend, x='Year', y='Popularity', markers=True, height=500)
    fig4.update_traces(line=dict(color=SPOTIFY_BLACK, width=3), marker=dict(size=8, color=SPOTIFY_GREEN))
    fig4.update_layout(template="simple_white")
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")

    # 2. 發行策略
    section_title("2. Single vs. Album Strategy")
    top_genres = df_filtered['Genre'].value_counts().head(top_n).index
    df_strat = df_filtered[(df_filtered['Genre'].isin(top_genres)) & (df_filtered['Album/Single'].isin(['single', 'album']))]
    fig1 = px.box(df_strat, x='Album/Single', y='Popularity', color='Album/Single',
                  facet_col='Genre', facet_col_wrap=3,
                  color_discrete_map={'single': SPOTIFY_GREEN, 'album': SPOTIFY_GREY},
                  height=600)
    fig1.update_traces(boxmean=True)
    fig1.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig1.update_layout(template="simple_white", showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")

    # 3. 歌詞分級
    section_header_text = "3. Content Strategy (Explicit)"
    section_title(section_header_text)
    df_top10 = df_filtered[df_filtered['Genre'].isin(top_genres)].copy()
    if 'Explicit_Label' in df_top10.columns:
        avg_pop_explicit = df_top10.groupby(['Genre', 'Explicit_Label'])['Popularity'].mean().reset_index()
        fig2 = px.bar(avg_pop_explicit, x='Genre', y='Popularity', color='Explicit_Label',
                      barmode='group',
                      color_discrete_map={'Explicit 🔞': SPOTIFY_BLACK, 'Clean 🟢': SPOTIFY_GREEN},
                      height=500)
        fig2.update_layout(template="simple_white", legend_title="")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # 4. 巨星效應
    section_title("4. The Superstar Effect")
    artist_stats = df_filtered.groupby('Artist').agg({'Artist_followers': 'mean', 'Popularity': 'max', 'Title': 'count'}).reset_index()
    artist_stats = artist_stats[artist_stats['Title'] > 2]
    if len(artist_stats) > 1:
        corr_value = artist_stats['Artist_followers'].corr(artist_stats['Popularity'])
        fig8 = px.scatter(artist_stats, x='Artist_followers', y='Popularity', 
                          hover_name='Artist', log_x=True, trendline="ols", 
                          trendline_color_override=SPOTIFY_BLACK, height=600, opacity=0.5)
        fig8.update_traces(marker=dict(size=7, color=SPOTIFY_GREEN, line=dict(width=1, color='white')))
        fig8.add_annotation(xref="paper", yref="paper", x=0.05, y=0.9, text=f"Correlation: {corr_value:.2f}", showarrow=False, font=dict(size=16, color=SPOTIFY_BLACK), bgcolor="white")
        fig8.update_layout(template="simple_white")
        st.plotly_chart(fig8, use_container_width=True)

    st.markdown("---")

    # 5. 黑馬雷達
    section_title("5. Talent Scouting: The Dark Horse Radar 🦄")
    dark_horses = df_filtered[(df_filtered['Artist_followers'] < 50000) & (df_filtered['Popularity'] > 75)].copy()
    if not dark_horses.empty:
        fig9 = px.scatter(dark_horses, x='energy', y='danceability', size='Popularity', color='Popularity', 
                          hover_name='Title', hover_data=['Artist'],
                          color_continuous_scale=['#A0E0A0', SPOTIFY_GREEN], size_max=20, height=700)
        # 加入象限輔助標註
        fig9.add_vline(x=0.5, line_width=1, line_dash="dash", line_color="grey")
        fig9.add_hline(y=0.5, line_width=1, line_dash="dash", line_color="grey")
        fig9.add_annotation(x=0.9, y=0.9, text="🔥 Club", showarrow=False, font=dict(size=14))
        fig9.add_annotation(x=0.1, y=0.9, text="🍷 Groove", showarrow=False, font=dict(size=14))
        fig9.add_annotation(x=0.9, y=0.1, text="⚡ Power", showarrow=False, font=dict(size=14))
        fig9.add_annotation(x=0.1, y=0.1, text="🌙 Ballad", showarrow=False, font=dict(size=14))
        fig9.update_layout(template="simple_white")
        st.plotly_chart(fig9, use_container_width=True)

# === TAB 2: 音樂實驗室 (全單欄版) ===
with tab2:
    # 6. 節奏分析
    section_title("6. Tempo Analysis (BPM)")
    df_bpm = df_filtered.dropna(subset=['tempo']).copy()
    def classify_tempo(bpm):
        if bpm < 100: return 'Slow (<100)'
        elif 100 <= bpm <= 140: return 'Mainstream (100-140)'
        else: return 'Fast (>140)'
    df_bpm['Tempo_Zone'] = df_bpm['tempo'].apply(classify_tempo)
    fig5 = px.histogram(df_bpm, x='tempo', color='Tempo_Zone', 
                        color_discrete_map={'Slow (<100)': '#B3B3B3', 'Mainstream (100-140)': SPOTIFY_GREEN, 'Fast (>140)': '#535353'},
                        text_auto=True, height=500)
    fig5.update_traces(xbins=dict(start=0, end=250, size=5), textposition='outside') 
    fig5.update_layout(template="simple_white", bargap=0.1)
    fig5.add_vline(x=120, line_width=2, line_dash="dash", line_color='#191414')
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown("---")

    # 7. 時長經濟學
    section_title("7. Duration Economics")
    duration_trend = df_filtered.groupby('Year')['duration_min'].mean().reset_index()
    fig7 = px.line(duration_trend, x='Year', y='duration_min', markers=True, height=500)
    fig7.update_traces(line_color="#535353", marker=dict(color=SPOTIFY_GREEN, size=6))
    fig7.update_layout(template="simple_white", yaxis_title="Minutes")
    st.plotly_chart(fig7, use_container_width=True)

    st.markdown("---")

    # 8. 決策矩陣
    section_title("8. Decision Matrix (Feature Correlation)")
    corr_features = ['Popularity', 'danceability', 'energy', 'valence', 'tempo', 'duration_ms', 'loudness']
    valid_corr_cols = [c for c in corr_features if c in df_filtered.columns]
    corr_matrix = df_filtered[valid_corr_cols].corr()
    fig10 = px.imshow(corr_matrix, text_auto='.2f', aspect='auto', color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN], height=600)
    fig10.update_layout(template="simple_white")
    st.plotly_chart(fig10, use_container_width=True)

    st.markdown("---")

    # 9. 能量散佈圖
    section_title("9. Feature Distribution (Energy vs. Danceability)")
    df_sample = df_filtered.sample(n=min(2000, len(df_filtered)), random_state=42)
    fig3 = px.scatter(df_sample, x='energy', y='danceability', color='Popularity',
                      color_continuous_scale=['#F0F0F0', SPOTIFY_GREEN], opacity=0.6, height=600)
    fig3.update_traces(marker=dict(size=8, line=dict(width=1, color='DarkSlateGrey')))
    fig3.update_layout(template="simple_white")
    st.plotly_chart(fig3, use_container_width=True)

# === TAB 3: 全球地圖 ===
with tab3:
    section_title("10. Global Market Reach")
    country_stats = df_filtered.groupby('Country').agg({'Popularity': 'mean', 'Title': 'count'}).reset_index()
    fig_map = px.choropleth(country_stats, locations="Country", locationmode='country names',
                           color="Popularity", color_continuous_scale=['#F5F5F5', SPOTIFY_GREEN, '#106b31'], height=700)
    fig_map.update_layout(geo=dict(showframe=False, projection_type='natural earth'), template="simple_white")
    st.plotly_chart(fig_map, use_container_width=True)
