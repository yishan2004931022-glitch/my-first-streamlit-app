import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="Spotify AI Strategy Dashboard",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 視覺風格與自定義函數 ---
SPOTIFY_GREEN = "#1DB954"
SPOTIFY_BLACK = "#191414"

# ✨ 帶有左側綠色裝飾條的大標題
def section_header(text):
    st.markdown(f"""
        <div style='border-left: 10px solid {SPOTIFY_GREEN}; padding-left: 20px; margin-top: 50px; margin-bottom: 10px;'>
            <h2 style='color: #333333; font-size: 34px; font-weight: 800; font-family: "Arial Black"; margin: 0;'>
            {text}
            </h2>
        </div>
        """, unsafe_allow_html=True)

# ✨ 綠色圖表小副標題
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

    numeric_cols = ['Popularity', 'danceability', 'energy', 'tempo', 'duration_ms', 'Artist_followers', 'loudness', 'valence']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
    df['Year'] = df['Release_date'].dt.year
    df['duration_min'] = df['duration_ms'] / 60000
    df = df.dropna(subset=['Year', 'Popularity', 'Genre', 'Artist', 'tempo'])
    
    df['Genre'] = df['Genre'].astype(str).str.title()
    df = df[~df['Genre'].isin(['N-A', 'Nan', 'Unknown', 'N/A'])]

    if 'Explicit' in df.columns:
        df['Exp_Str'] = df['Explicit'].astype(str).str.lower().str.strip()
        mapping = {'true': 'Explicit 🔞', '1': 'Explicit 🔞', 'false': 'Clean 🟢', '0': 'Clean 🟢'}
        df['Explicit_Label'] = df['Exp_Str'].map(mapping).fillna('Clean 🟢')

    return df

df = load_data()

# --- 4. 側邊欄控制 ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=50)
    st.title("Analytics Panel")
    
    # 年份篩選
    year_range = st.slider("📅 Year Range", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
    
    # 🔍 搜尋功能
    search_query = st.text_input("🔍 Search Artist Name", "")
    
    # 🏆 流派數量控制
    top_n = st.slider("🏆 Top Genres Count", 3, 15, 5)
    
    # --- 關鍵修正：資料過濾邏輯 ---
    df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    if search_query:
        df_filtered = df_filtered[df_filtered['Artist'].str.contains(search_query, case=False, na=False)]
    
    st.markdown("---")
    
    # 🔥 修正後的下載邏輯
    if not df_filtered.empty:
        # 使用 utf-8-sig 解決 Excel 中文亂碼問題
        csv_data = df_filtered.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Download current analysis (.csv)",
            data=csv_data,
            file_name=f'spotify_data_{year_range[0]}_{year_range[1]}.csv',
            mime='text/csv'
        )
    else:
        st.warning("⚠️ No data available to download.")

    st.markdown("---")
    st.write("Created by **Selina**")

# --- 5. 主頁面內容 ---
st.title("🎵 Spotify Intelligence Dashboard")

# 📊 商業 KPI 指標卡
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
with col_m1:
    st.metric("Total Tracks", f"{len(df_filtered):,}")
with col_m2:
    st.metric("Avg Popularity", f"{df_filtered['Popularity'].mean():.1f}")
with col_m3:
    st.metric("Superstars", f"{len(df_filtered[df_filtered['Artist_followers'] > 1000000]['Artist'].unique())}")
with col_m4:
    st.metric("Avg Tempo", f"{df_filtered['tempo'].mean():.0f} BPM")
with col_m5:
    dom_genre = df_filtered['Genre'].mode()[0] if not df_filtered.empty else "N/A"
    st.metric("Top Genre", dom_genre)

tab1, tab2, tab3 = st.tabs(["📈 Market Strategy", "🎛️ Audio Lab & AI", "🌍 Global Map"])

# === TAB 1: 市場策略 (題目 1-5) ===
with tab1:
    section_header("1. Market Trend Evolution")
    yearly = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
    fig1 = px.line(yearly, x='Year', y='Popularity', markers=True, height=500)
    fig1.update_traces(line=dict(color=SPOTIFY_BLACK, width=4), marker=dict(size=10, color=SPOTIFY_GREEN))
    fig1 = apply_chart_style(fig1, "Average Global Popularity Evolution")
    st.plotly_chart(fig1, width='stretch') # ✅ 2026 最新語法

    st.markdown("---")

    section_header("2. Single vs. Album Strategy")
    top_genres_list = df_filtered['Genre'].value_counts().head(top_n).index
    df_strat = df_filtered[df_filtered['Genre'].isin(top_genres_list)]
    fig2 = px.box(df_strat, x='Album/Single', y='Popularity', color='Album/Single',
                 facet_col='Genre', facet_col_wrap=5, height=700,
                 color_discrete_map={'single': SPOTIFY_GREEN, 'album': "#B3B3B3"})
    fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
    fig2 = apply_chart_style(fig2, f"Format Performance: Top {top_n} Genres")
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2, width='stretch')

    st.markdown("---")

    section_header("3. Content Strategy (Explicit Content)")
    df_exp = df_filtered[df_filtered['Genre'].isin(top_genres_list)]
    if not df_exp.empty:
        avg_exp = df_exp.groupby(['Genre', 'Explicit_Label'])['Popularity'].mean().reset_index()
        fig3 = px.bar(avg_exp, x='Genre', y='Popularity', color='Explicit_Label', barmode='group',
                     color_discrete_map={'Explicit 🔞': SPOTIFY_BLACK, 'Clean 🟢': SPOTIFY_GREEN}, height=550)
        fig3 = apply_chart_style(fig3, "The Impact of Explicit Content on Popularity")
        fig3.update_layout(legend_title_text="")
        st.plotly_chart(fig3, width='stretch')

    st.markdown("---")

    section_header("4. The Superstar Effect")
    art_stats = df_filtered.groupby('Artist').agg({'Artist_followers': 'mean', 'Popularity': 'max', 'Title': 'count'}).reset_index()
    art_stats = art_stats[art_stats['Title'] > 2]
    if len(art_stats) > 1:
        corr_val = art_stats['Artist_followers'].corr(art_stats['Popularity'])
        st.write(f"📊 **Stat Correlation:** `{corr_val:.2f}` (Artist Followers vs. Chart Success)")
        fig4 = px.scatter(art_stats, x='Artist_followers', y='Popularity', hover_name='Artist', 
                         log_x=True, trendline="ols", trendline_color_override=SPOTIFY_BLACK, height=650)
        fig4.update_traces(marker=dict(size=8, color=SPOTIFY_GREEN), opacity=0.6)
        fig4 = apply_chart_style(fig4, "Social Reach vs. Peak Chart Popularity")
        st.plotly_chart(fig4, width='stretch')

    st.markdown("---")

    section_header("5. Talent Scouting: Dark Horse Radar")
    dark = df_filtered[(df_filtered['Artist_followers'] < 50000) & (df_filtered['Popularity'] > 75)].copy()
    if not dark.empty:
        fig5 = px.scatter(dark, x='energy', y='danceability', size='Popularity', color='Popularity',
                         hover_name='Title', hover_data=['Artist'],
                         color_continuous_scale=['#F0FFF0', SPOTIFY_GREEN], height=750)
        fig5.add_vline(x=0.5, line_dash="dash", line_color="grey")
        fig5.add_hline(y=0.5, line_dash="dash", line_color="grey")
        fig5.add_annotation(x=0.9, y=0.9, text="<b>🔥 CLUB</b>", showarrow=False, font=dict(size=16))
        fig5.add_annotation(x=0.1, y=0.9, text="<b>🍷 GROOVE</b>", showarrow=False, font=dict(size=16))
        fig5.add_annotation(x=0.9, y=0.1, text="<b>⚡ POWER</b>", showarrow=False, font=dict(size=16))
        fig5.add_annotation(x=0.1, y=0.1, text="<b>🌙 BALLAD</b>", showarrow=False, font=dict(size=16))
        fig5 = apply_chart_style(fig5, "High-Impact Tracks from Emerging Artists")
        st.plotly_chart(fig5, width='stretch')

# === TAB 2: 音樂實驗室 & AI (題目 6-9) ===
with tab2:
    # 🔮 AI 爆紅預測器
    section_header("6. AI Hit Potential Predictor")
    st.write("調整音色參數，即時預測這組特徵的 **流行潛力指數**。")
    
    col_ai_left, col_ai_right = st.columns([1, 2])
    with col_ai_left:
        in_dance = st.slider("Danceability", 0.0, 1.0, 0.6)
        in_energy = st.slider("Energy", 0.0, 1.0, 0.7)
        in_loud = st.slider("Loudness (dB)", -60, 0, -10)
        in_valence = st.slider("Valence (Happiness)", 0.0, 1.0, 0.5)
        pred_score = (in_dance * 30) + (in_energy * 25) + ((in_loud+60)/60 * 20) + (in_valence * 10) + 15
        st.metric("Predicted Hit Score", f"{pred_score:.1f} / 100")
    
    with col_ai_right:
        radar_fig = go.Figure(data=go.Scatterpolar(
            r=[in_dance, in_energy, (in_loud+60)/60, in_valence, in_dance],
            theta=['Danceability','Energy','Loudness','Valence','Danceability'],
            fill='toself', fillcolor='rgba(29, 185, 84, 0.4)', line=dict(color=SPOTIFY_GREEN)
        ))
        radar_fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False, height=400)
        st.plotly_chart(radar_fig, width='stretch')

    st.markdown("---")

    # Q5. BPM 分析 (Jupyter 紮實版)
    section_header("7. Tempo Analysis (BPM)")
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
    fig6 = apply_chart_style(fig6, "Tempo Distribution: The Sweet Spot (100-140 BPM)")
    fig6.add_vline(x=120, line_width=3, line_dash="dash", line_color=SPOTIFY_BLACK, annotation_text="120 BPM Pop Standard")
    st.plotly_chart(fig6, width='stretch')

    st.markdown("---")

    # Q7. 歌曲長度趨勢
    section_header("8. Duration Economics")
    dur_trend = df_filtered.groupby('Year')['duration_min'].mean().reset_index()
    fig7 = px.line(dur_trend, x='Year', y='duration_min', markers=True, height=500)
    fig7.update_traces(line_color=SPOTIFY_BLACK, marker=dict(color=SPOTIFY_GREEN, size=8))
    fig7 = apply_chart_style(fig7, "The Streaming Effect: Avg Track Duration")
    st.plotly_chart(fig7, width='stretch')

    st.markdown("---")

    # Q10. 相關性矩陣
    section_header("9. Audio Feature Correlation Matrix")
    corr_cols = ['Popularity', 'danceability', 'energy', 'valence', 'tempo', 'loudness']
    corr_mat = df_filtered[corr_cols].corr()
    fig8 = px.imshow(corr_mat, text_auto='.2f', aspect='auto',
                    color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN], height=600)
    fig8 = apply_chart_style(fig8, "Which Audio Features Drive Success?")
    st.plotly_chart(fig8, width='stretch')

# === TAB 3: 全球版圖 (題目 10) ===
with tab3:
    section_header("10. Global Market Reach")
    geo_data = df_filtered.groupby('Country')['Popularity'].mean().reset_index()
    fig10 = px.choropleth(geo_data, locations="Country", locationmode='country names', color="Popularity",
                         color_continuous_scale=['#F5F5F5', SPOTIFY_GREEN, '#106b31'], height=800)
    fig10 = apply_chart_style(fig10, "Average Track Performance by Territory")
    fig10.update_layout(geo=dict(showframe=False, projection_type='natural earth'))
    st.plotly_chart(fig10, width='stretch')
