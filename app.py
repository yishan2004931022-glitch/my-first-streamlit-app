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

# --- 2. 視覺風格定義 ---
SPOTIFY_GREEN = "#1DB954"
SPOTIFY_BLACK = "#191414"
SPOTIFY_GREY = "#B3B3B3"

# ✨ 強化版大標題函數：保證綠色、加大、加粗
def big_green_header(text):
    st.markdown(f"""
        <h2 style='color: {SPOTIFY_GREEN}; font-size: 32px; font-weight: 800; border-left: 8px solid {SPOTIFY_GREEN}; padding-left: 15px; margin-top: 40px; margin-bottom: 20px;'>
        {text}
        </h2>
        """, unsafe_allow_html=True)

# --- 3. 資料讀取與清洗 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Final database.csv.gz', compression='gzip', low_memory=False)
    except:
        try:
            df = pd.read_csv('Final database.zip', compression='zip', low_memory=False)
        except:
            return None

    # 數值轉換
    numeric_cols = ['Popularity', 'danceability', 'energy', 'tempo', 'duration_ms', 'Artist_followers', 'loudness', 'valence']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 日期處理
    df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
    df['Year'] = df['Release_date'].dt.year
    df['duration_min'] = df['duration_ms'] / 60000 
    
    # 基礎清洗
    df = df.dropna(subset=['Year', 'Popularity', 'Genre', 'Artist'])
    df = df[(df['Popularity'] >= 0) & (df['Popularity'] <= 100)]
    
    df['Genre'] = df['Genre'].astype(str).str.title()
    
    # Explicit 修復 (確保多種格式都能對應)
    if 'Explicit' in df.columns:
        df['Exp_Str'] = df['Explicit'].astype(str).str.lower()
        mapping = {'true': 'Explicit 🔞', 'false': 'Clean 🟢', '1': 'Explicit 🔞', '0': 'Clean 🟢', '1.0': 'Explicit 🔞', '0.0': 'Clean 🟢'}
        df['Explicit_Label'] = df['Exp_Str'].map(mapping).fillna('Unknown')

    return df

df = load_data()

if df is None:
    st.error("❌ 無法讀取資料，請確認 GitHub 檔案路徑")
    st.stop()

# --- 4. 側邊欄 ---
with st.sidebar:
    st.title("🎧 Settings")
    year_range = st.slider("📅 Year Range", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
    df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    top_n = st.slider("🏆 Top Genres Count", 3, 10, 5)
    st.info(f"Analyzing {len(df_filtered):,} songs")

# --- 5. 主頁面內容 ---
st.title("🎵 Spotify Producer Analytics")
st.markdown(f"### 📈 Period Analyzed: {year_range[0]} - {year_range[1]}")

tab1, tab2, tab3 = st.tabs(["📈 Market Strategy", "🎛️ Audio Lab", "🌍 Global Map"])

# === TAB 1: 市場策略 (1-5 題) ===
with tab1:
    # Q4. 市場趨勢
    big_green_header("1. Market Trend Evolution")
    yearly = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
    fig1 = px.line(yearly, x='Year', y='Popularity', markers=True, height=500)
    fig1.update_traces(line=dict(color=SPOTIFY_BLACK, width=4), marker=dict(size=10, color=SPOTIFY_GREEN))
    fig1.update_layout(template="simple_white", xaxis_title="Year", yaxis_title="Avg Popularity")
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")

    # Q1. 發行策略
    big_green_header("2. Single vs. Album Strategy")
    top_genres_list = df_filtered['Genre'].value_counts().head(top_n).index
    df_strat = df_filtered[df_filtered['Genre'].isin(top_genres_list)]
    fig2 = px.box(df_strat, x='Album/Single', y='Popularity', color='Album/Single',
                 facet_col='Genre', facet_col_wrap=5, height=650,
                 color_discrete_map={'single': SPOTIFY_GREEN, 'album': SPOTIFY_GREY})
    fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>", font=dict(size=16)))
    fig2.update_layout(template="simple_white", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # Q2. 歌詞分級 (Explicit)
    big_green_header("3. Content Strategy (Explicit)")
    df_exp = df_filtered[df_filtered['Genre'].isin(top_genres_list)]
    df_exp = df_exp[df_exp['Explicit_Label'] != 'Unknown']
    if not df_exp.empty:
        avg_exp = df_exp.groupby(['Genre', 'Explicit_Label'])['Popularity'].mean().reset_index()
        fig3 = px.bar(avg_exp, x='Genre', y='Popularity', color='Explicit_Label', barmode='group',
                     color_discrete_map={'Explicit 🔞': SPOTIFY_BLACK, 'Clean 🟢': SPOTIFY_GREEN}, height=500)
        fig3.update_layout(template="simple_white", legend_title="")
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # Q8. 巨星效應
    big_green_header("4. The Superstar Effect")
    art_stats = df_filtered.groupby('Artist').agg({'Artist_followers': 'mean', 'Popularity': 'max', 'Title': 'count'}).reset_index()
    art_stats = art_stats[art_stats['Title'] > 2]
    if len(art_stats) > 1:
        corr_val = art_stats['Artist_followers'].corr(art_stats['Popularity'])
        fig8 = px.scatter(art_stats, x='Artist_followers', y='Popularity', hover_name='Artist', 
                          log_x=True, trendline="ols", trendline_color_override=SPOTIFY_BLACK, height=600, opacity=0.5)
        fig8.update_traces(marker=dict(size=8, color=SPOTIFY_GREEN, line=dict(width=1, color='white')))
        fig8.add_annotation(xref="paper", yref="paper", x=0.05, y=0.9, text=f"Correlation: {corr_val:.2f}", showarrow=False, font=dict(size=18, color=SPOTIFY_BLACK, weight='bold'), bgcolor="white")
        fig8.update_layout(template="simple_white")
        st.plotly_chart(fig8, use_container_width=True)

    st.markdown("---")

    # Q9. 黑馬雷達
    big_green_header("5. Talent Scouting: The Dark Horse Radar 🦄")
    dark = df_filtered[(df_filtered['Artist_followers'] < 50000) & (df_filtered['Popularity'] > 75)].copy()
    if not dark.empty:
        fig9 = px.scatter(dark, x='energy', y='danceability', size='Popularity', color='Popularity', 
                          hover_name='Title', hover_data=['Artist'],
                          color_continuous_scale=['#F0FFF0', SPOTIFY_GREEN], height=750)
        fig9.add_vline(x=0.5, line_dash="dash", line_color="grey")
        fig9.add_hline(y=0.5, line_dash="dash", line_color="grey")
        # 標註象限
        fig9.add_annotation(x=0.9, y=0.9, text="🔥 Club", showarrow=False, font=dict(size=16, weight='bold'))
        fig9.add_annotation(x=0.1, y=0.9, text="🍷 Groove", showarrow=False, font=dict(size=16, weight='bold'))
        fig9.add_annotation(x=0.9, y=0.1, text="⚡ Power", showarrow=False, font=dict(size=16, weight='bold'))
        fig9.add_annotation(x=0.1, y=0.1, text="🌙 Ballad", showarrow=False, font=dict(size=16, weight='bold'))
        fig9.update_layout(template="simple_white")
        st.plotly_chart(fig9, use_container_width=True)

# === TAB 2: 音樂實驗室 (6-9 題) ===
with tab2:
    # 6. 節奏分析
    big_green_header("6. Tempo Analysis (BPM)")
    df_bpm = df_filtered.dropna(subset=['tempo']).copy()
    def classify_tempo(bpm):
        if bpm < 100: return 'Slow (<100)'
        elif 100 <= bpm <= 140: return 'Mainstream (100-140)'
        else: return 'Fast (>140)'
    df_bpm['Tempo_Zone'] = df_bpm['tempo'].apply(classify_tempo)
    fig6 = px.histogram(df_bpm, x='tempo', color='Tempo_Zone', 
                        color_discrete_map={'Slow (<100)': '#B3B3B3', 'Mainstream (100-140)': SPOTIFY_GREEN, 'Fast (>140)': '#535353'},
                        text_auto=True, height=500)
    fig6.update_traces(xbins=dict(start=0, end=250, size=5), textposition='outside') 
    fig6.add_vline(x=120, line_width=2, line_dash="dash", line_color=SPOTIFY_BLACK)
    fig6.update_layout(template="simple_white", bargap=0.1)
    st.plotly_chart(fig6, use_container_width=True)

    st.markdown("---")

    # 7. 時長經濟學
    big_green_header("7. Duration Economics")
    dur_trend = df_filtered.groupby('Year')['duration_min'].mean().reset_index()
    fig7 = px.line(dur_trend, x='Year', y='duration_min', markers=True, height=500)
    fig7.update_traces(line_color="#535353", marker=dict(color=SPOTIFY_GREEN, size=8))
    fig7.update_layout(template="simple_white", yaxis_title="Minutes")
    st.plotly_chart(fig7, use_container_width=True)

    st.markdown("---")

    # 8. 決策矩陣 (相關性)
    big_green_header("8. Audio Feature Correlation Matrix")
    corr_cols = ['Popularity', 'danceability', 'energy', 'valence', 'tempo', 'loudness']
    corr_mat = df_filtered[corr_cols].corr()
    fig10 = px.imshow(corr_mat, text_auto='.2f', aspect='auto', color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN], height=600)
    fig10.update_layout(template="simple_white")
    st.plotly_chart(fig10, use_container_width=True)

    st.markdown("---")

    # 9. 能量分佈
    big_green_header("9. Feature Lab (Energy vs. Danceability)")
    df_sample = df_filtered.sample(n=min(2000, len(df_filtered)), random_state=42)
    fig3 = px.scatter(df_sample, x='energy', y='danceability', color='Popularity',
                      color_continuous_scale=['#F0F0F0', SPOTIFY_GREEN], opacity=0.6, height=650)
    fig3.update_traces(marker=dict(size=9, line=dict(width=1, color='DarkSlateGrey')))
    fig3.update_layout(template="simple_white")
    st.plotly_chart(fig3, use_container_width=True)

# === TAB 3: 全球地圖 ===
with tab3:
    big_green_header("10. Global Market Reach")
    geo_data = df_filtered.groupby('Country')['Popularity'].mean().reset_index()
    fig_map = px.choropleth(geo_data, locations="Country", locationmode='country names',
                           color="Popularity", color_continuous_scale=['#F5F5F5', SPOTIFY_GREEN, '#106b31'], height=800)
    fig_map.update_layout(geo=dict(showframe=False, projection_type='natural earth'), template="simple_white")
    st.plotly_chart(fig_map, use_container_width=True)
