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

# ✨ 自定義大標題函數 (用於章節 1, 2, 3...)
def section_header(text):
    st.markdown(f"<h2 style='color: {SPOTIFY_GREEN}; font-size: 32px; font-weight: 900; margin-top: 30px;'>{text}</h2>", unsafe_allow_html=True)

# ✨ 強化版圖表標題樣式 (對應您的截圖需求)
def chart_title_style(fig, title_text):
    fig.update_layout(
        title=dict(
            text=f"<b>{title_text}</b>",
            font=dict(color=SPOTIFY_GREEN, size=28, family="Arial Black"),
            x=0, y=0.95
        ),
        font=dict(family="Arial Black", color="black"),
        margin=dict(t=80, b=50),
        template="simple_white"
    )
    # 強制座標軸文字變黑加粗
    fig.update_xaxes(tickfont=dict(family="Arial Black", size=12, color="black"), title_font=dict(size=14))
    fig.update_yaxes(tickfont=dict(family="Arial Black", size=12, color="black"), title_font=dict(size=14))
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

    # 數值與日期處理
    cols = ['Popularity', 'danceability', 'energy', 'tempo', 'duration_ms', 'Artist_followers']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
    df['Year'] = df['Release_date'].dt.year
    df['duration_min'] = df['duration_ms'] / 60000
    df = df.dropna(subset=['Year', 'Popularity', 'Genre', 'Artist'])
    
    # 清理流派 NA
    junk = ['N-A', 'N-a', 'Nan', 'Unknown', 'N/A']
    df = df[~df['Genre'].astype(str).str.title().isin(junk)]
    df['Genre'] = df['Genre'].astype(str).str.title()

    # 🔥 修復 Explicit 空白圖表的關鍵清洗
    if 'Explicit' in df.columns:
        df['Exp_Str'] = df['Explicit'].astype(str).str.lower().str.strip()
        mapping = {
            'true': 'Explicit 🔞', '1': 'Explicit 🔞', '1.0': 'Explicit 🔞',
            'false': 'Clean 🟢', '0': 'Clean 🟢', '0.0': 'Clean 🟢'
        }
        df['Explicit_Label'] = df['Exp_Str'].map(mapping).fillna('Unknown')

    return df

df = load_data()
if df is None:
    st.error("❌ 資料讀取失敗")
    st.stop()

# --- 4. 側邊欄 ---
with st.sidebar:
    st.title("🎧 Settings")
    year_range = st.slider("📅 Year Range", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
    df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    top_n = st.slider("🏆 Top Genres", 3, 10, 5)

# --- 5. 主頁面 ---
st.title("🎵 Spotify Producer Dashboard")

tab1, tab2, tab3 = st.tabs(["📈 Strategy", "🎛️ Audio Lab", "🌍 Global"])

with tab1:
    # 1. 市場趨勢
    section_header("1. Market Trend Evolution")
    yearly = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
    fig1 = px.line(yearly, x='Year', y='Popularity', markers=True, height=500)
    fig1.update_traces(line=dict(color=SPOTIFY_BLACK, width=4), marker=dict(size=10, color=SPOTIFY_GREEN))
    fig1 = chart_title_style(fig1, "Yearly Popularity Evolution")
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")

    # 2. 發行策略
    section_header("2. Single vs. Album Strategy")
    top_genres = df_filtered['Genre'].value_counts().head(top_n).index
    df_strat = df_filtered[df_filtered['Genre'].isin(top_genres)]
    fig2 = px.box(df_strat, x='Album/Single', y='Popularity', color='Album/Single',
                 facet_col='Genre', facet_col_wrap=5, height=700,
                 color_discrete_map={'single': SPOTIFY_GREEN, 'album': "#B3B3B3"})
    fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>", font=dict(size=16)))
    fig2 = chart_title_style(fig2, f"Format Performance (Top {top_n} Genres)")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # 3. Explicit (已修復空白問題)
    section_header("3. Content Strategy (Explicit)")
    df_exp = df_filtered[df_filtered['Genre'].isin(top_genres)]
    df_exp = df_exp[df_exp['Explicit_Label'] != 'Unknown']
    if not df_exp.empty:
        avg_exp = df_exp.groupby(['Genre', 'Explicit_Label'])['Popularity'].mean().reset_index()
        fig3 = px.bar(avg_exp, x='Genre', y='Popularity', color='Explicit_Label', barmode='group',
                     color_discrete_map={'Explicit 🔞': SPOTIFY_BLACK, 'Clean 🟢': SPOTIFY_GREEN}, height=500)
        fig3 = chart_title_style(fig3, "Explicit vs. Clean Content Performance")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("此年份區間無 Explicit 資料")

    st.markdown("---")

    # 4. 巨星效應 (相關係數標籤移動至此)
    section_header("4. The Superstar Effect")
    art_stats = df_filtered.groupby('Artist').agg({'Artist_followers': 'mean', 'Popularity': 'max', 'Title': 'count'}).reset_index()
    art_stats = art_stats[art_stats['Title'] > 2]
    
    if len(art_stats) > 1:
        corr = art_stats['Artist_followers'].corr(art_stats['Popularity'])
        
        # 🔥 這裡處理您的需求：將相關係數移出圖表，用 Metric 卡片顯示
        st.metric(label="📊 Artist Followers vs. Peak Popularity Correlation", value=f"{corr:.2f}")
        
        fig4 = px.scatter(art_stats, x='Artist_followers', y='Popularity', hover_name='Artist', 
                         log_x=True, trendline="ols", trendline_color_override=SPOTIFY_BLACK, height=600)
        fig4.update_traces(marker=dict(size=8, color=SPOTIFY_GREEN, line=dict(width=1, color='black')))
        fig4 = chart_title_style(fig4, "Do More Followers Mean Higher Peaks?")
        st.plotly_chart(fig4, use_container_width=True)

with tab2:
    # 5. 黑馬雷達
    section_header("5. Talent Scouting: Dark Horse Radar 🦄")
    dark = df_filtered[(df_filtered['Artist_followers'] < 50000) & (df_filtered['Popularity'] > 75)].copy()
    if not dark.empty:
        fig5 = px.scatter(dark, x='energy', y='danceability', size='Popularity', color='Popularity',
                         hover_name='Title', color_continuous_scale=['#A0E0A0', SPOTIFY_GREEN], height=700)
        fig5.add_vline(x=0.5, line_dash="dash", line_color="grey")
        fig5.add_hline(y=0.5, line_dash="dash", line_color="grey")
        fig5 = chart_title_style(fig5, "High-Stream Songs by Low-Follower Artists")
        st.plotly_chart(fig5, use_container_width=True)

with tab3:
    # 6. 全球地圖
    section_header("🌍 Global Market Reach")
    geo = df_filtered.groupby('Country')['Popularity'].mean().reset_index()
    fig6 = px.choropleth(geo, locations="Country", locationmode='country names', color="Popularity",
                        color_continuous_scale=['#F5F5F5', SPOTIFY_GREEN], height=700)
    fig6 = chart_title_style(fig6, "Average Popularity by Market")
    st.plotly_chart(fig6, use_container_width=True)
