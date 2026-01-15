import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="Spotify Intelligence Dashboard",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 視覺風格與自定義函數 ---
SPOTIFY_GREEN = "#1DB954"
SPOTIFY_BLACK = "#191414"

# ✨ 帶有左側綠色裝飾條的大標題 (章節用)
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

    # 數值轉換
    numeric_cols = ['Popularity', 'danceability', 'energy', 'tempo', 'duration_ms', 'Artist_followers', 'loudness', 'valence']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 日期與時間處理
    df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
    df['Year'] = df['Release_date'].dt.year
    df['duration_min'] = df['duration_ms'] / 60000
    
    # 基礎清洗
    df = df.dropna(subset=['Year', 'Popularity', 'Genre', 'Artist', 'tempo'])
    df = df[(df['Popularity'] >= 0) & (df['Popularity'] <= 100)]
    
    # 流派清洗 (移除髒數據)
    df['Genre'] = df['Genre'].astype(str).str.title()
    junk = ['N-A', 'Nan', 'Unknown', 'N/A']
    df = df[~df['Genre'].isin(junk)]

    # Explicit 標籤修復
    if 'Explicit' in df.columns:
        df['Exp_Str'] = df['Explicit'].astype(str).str.lower().str.strip()
        mapping = {'true': 'Explicit 🔞', '1': 'Explicit 🔞', 'false': 'Clean 🟢', '0': 'Clean 🟢'}
        df['Explicit_Label'] = df['Exp_Str'].map(mapping).fillna('Clean 🟢')

    return df

df = load_data()

# --- 4. 側邊欄控制 (含搜尋與下載) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=50)
    st.title("Control Panel")
    
    # 年份篩選
    year_range = st.slider("📅 Year Range", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
    
    # 🔍 新增：藝術家搜尋功能
    search_query = st.text_input("🔍 Search Artist", "")
    
    # 資料過濾
    df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    if search_query:
        df_filtered = df_filtered[df_filtered['Artist'].str.contains(search_query, case=False)]
    
    st.markdown("---")
    top_n = st.slider("🏆 Top Genres Count", 3, 15, 5)
    
    # 📥 新增：CSV 下載按鈕
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Download Analysis Data", data=csv, file_name='spotify_analysis.csv', mime='text/csv')
    
    st.markdown("---")
    st.write("Created by **Selina**")

# --- 5. 主頁面內容 ---
st.title("🎵 Spotify Intelligence Strategy Dashboard")

# 📊 專業 KPI 指標卡
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Total Sample", f"{len(df_filtered):,}")
with col_m2:
    st.metric("Avg Popularity", f"{df_filtered['Popularity'].mean():.1f}")
with col_m3:
    st.metric("Superstar Artists", f"{len(df_filtered[df_filtered['Artist_followers'] > 1000000]['Artist'].unique())}")
with col_m4:
    dominant_genre = df_filtered['Genre'].mode()[0] if not df_filtered.empty else "N/A"
    st.metric("Dominant Genre", dominant_genre)

tab1, tab2, tab3 = st.tabs(["📈 Market Strategy", "🔮 AI Audio Lab", "🌍 Global Map"])

# === TAB 1: 市場策略 (1-4 題) ===
with tab1:
    # 1. 市場趨勢
    section_header("1. Market Trend Evolution")
    yearly = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
    fig1 = px.line(yearly, x='Year', y='Popularity', markers=True, height=500)
    fig1.update_traces(line=dict(color=SPOTIFY_BLACK, width=4), marker=dict(size=10, color=SPOTIFY_GREEN))
    fig1 = apply_chart_style(fig1, "Yearly Average Popularity Evolution")
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")

    # 2. 發行策略
    section_header("2. Single vs. Album Strategy")
    top_genres_list = df_filtered['Genre'].value_counts().head(top_n).index
    df_strat = df_filtered[df_filtered['Genre'].isin(top_genres_list)]
    fig2 = px.box(df_strat, x='Album/Single', y='Popularity', color='Album/Single',
                 facet_col='Genre', facet_col_wrap=5, height=700,
                 color_discrete_map={'single': SPOTIFY_GREEN, 'album': "#B3B3B3"},
                 category_orders={'Album/Single': ['single', 'album']})
    fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
    fig2 = apply_chart_style(fig2, f"Format Performance: Top {top_n} Genres")
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # 3. 巨星效應 (相關係數移出，改用標籤)
    section_header("3. The Superstar Effect")
    art_stats = df_filtered.groupby('Artist').agg({'Artist_followers': 'mean', 'Popularity': 'max', 'Title': 'count'}).reset_index()
    art_stats = art_stats[art_stats['Title'] > 2]
    if len(art_stats) > 1:
        corr_val = art_stats['Artist_followers'].corr(art_stats['Popularity'])
        st.write(f"📊 **Follower-Popularity Correlation Coefficient:** `{corr_val:.2f}`")
        fig4 = px.scatter(art_stats, x='Artist_followers', y='Popularity', hover_name='Artist', 
                         log_x=True, trendline="ols", trendline_color_override=SPOTIFY_BLACK, height=600)
        fig4.update_traces(marker=dict(size=8, color=SPOTIFY_GREEN), opacity=0.6)
        fig4 = apply_chart_style(fig4, "Network Size vs. Peak Popularity")
        st.plotly_chart(fig4, use_container_width=True)

# === TAB 2: 音樂實驗室 & AI (5-9 題) ===
with tab2:
    # 🔮 AI 爆紅預測器
    section_header("4. AI Hit Potential Predictor")
    st.write("調整下方參數，AI 將根據數據趨勢預測該音色組合的 **爆紅指數 (0-100)**。")
    
    col_ai_left, col_ai_right = st.columns([1, 2])
    with col_ai_left:
        in_dance = st.slider("Danceability", 0.0, 1.0, 0.6)
        in_energy = st.slider("Energy", 0.0, 1.0, 0.7)
        in_loud = st.slider("Loudness (dB)", -60, 0, -10)
        in_valence = st.slider("Valence (Happiness)", 0.0, 1.0, 0.5)
        
        # 簡易線性模擬公式
        pred_score = (in_dance * 30) + (in_energy * 25) + ((in_loud+60)/60 * 20) + (in_valence * 10) + 15
        st.metric("Predicted Hit Score", f"{pred_score:.1f} / 100")
    
    with col_ai_right:
        # 特徵雷達圖 (Radar Chart)
        radar_fig = go.Figure(data=go.Scatterpolar(
            r=[in_dance, in_energy, (in_loud+60)/60, in_valence, in_dance],
            theta=['Danceability','Energy','Loudness','Valence','Danceability'],
            fill='toself', fillcolor='rgba(29, 185, 84, 0.4)', line=dict(color=SPOTIFY_GREEN)
        ))
        radar_fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False, height=400)
        st.plotly_chart(radar_fig, use_container_width=True)

    st.markdown("---")

    # 5. BPM 分析 (Jupyter 紮實版)
    section_header("5. Tempo Analysis (BPM)")
    def classify_tempo(bpm):
        if bpm < 100: return 'Slow (<100)'
        elif 100 <= bpm <= 140: return 'Mainstream (100-140)'
        else: return 'Fast (>140)'
    df_filtered['Tempo_Zone'] = df_filtered['tempo'].apply(classify_tempo)
    
    fig5 = px.histogram(df_filtered, x='tempo', color='Tempo_Zone',
                       color_discrete_map={'Slow (<100)': '#B3B3B3', 'Mainstream (100-140)': SPOTIFY_GREEN, 'Fast (>140)': '#535353'},
                       category_orders={'Tempo_Zone': ['Slow (<100)', 'Mainstream (100-140)', 'Fast (>140)']},
                       text_auto='.2s', height=600)
    fig5.update_traces(xbins=dict(start=0, end=250, size=5), textposition='outside', marker_line_width=1, marker_line_color="white")
    fig5 = apply_chart_style(fig5, "Tempo Zones: The Sweet Spot (100-140 BPM)")
    fig5.add_vline(x=120, line_width=3, line_dash="dash", line_color=SPOTIFY_BLACK, annotation_text="Pop Standard (120 BPM)")
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown("---")

    # 6. 決策矩陣 (相關性)
    section_header("6. Audio Feature Correlation Matrix")
    corr_cols = ['Popularity', 'danceability', 'energy', 'valence', 'tempo', 'loudness']
    corr_mat = df_filtered[corr_cols].corr()
    fig6 = px.imshow(corr_mat, text_auto='.2f', aspect='auto',
                    color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN], height=600)
    fig6 = apply_chart_style(fig6, "Which Features Drive Success?")
    st.plotly_chart(fig6, use_container_width=True)

# === TAB 3: 全球版圖 (10 題) ===
with tab3:
    section_header("7. Global Market Reach")
    geo_data = df_filtered.groupby('Country')['Popularity'].mean().reset_index()
    fig10 = px.choropleth(geo_data, locations="Country", locationmode='country names', color="Popularity",
                         color_continuous_scale=['#F5F5F5', SPOTIFY_GREEN, '#106b31'], height=800)
    fig10 = apply_chart_style(fig10, "Average Track Popularity by Territory")
    fig10.update_layout(geo=dict(showframe=False, projection_type='natural earth'))
    st.plotly_chart(fig10, use_container_width=True)
