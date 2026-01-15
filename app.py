import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

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

# ✨ 帶有左側綠色裝飾條的大標題 (章節編號用)
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

# --- 3. 資料讀取與強力清洗 (含診斷邏輯) ---
@st.cache_data
def load_data():
    # 診斷：確認目前路徑下的檔案
    available_files = os.listdir('.')
    
    # 嘗試讀取不同格式的資料檔
    target_file = None
    if 'Final database.csv.gz' in available_files:
        target_file = 'Final database.csv.gz'
    elif 'Final database.zip' in available_files:
        target_file = 'Final database.zip'
    
    if not target_file:
        st.error(f"❌ 找不到資料檔！目前目錄內檔案：{available_files}")
        return None

    try:
        if target_file.endswith('.gz'):
            df = pd.read_csv(target_file, compression='gzip', low_memory=False)
        else:
            df = pd.read_csv(target_file, compression='zip', low_memory=False)
    except Exception as e:
        st.error(f"❌ 讀取 CSV 時發生錯誤: {e}")
        return None

    # 數值轉換
    numeric_cols = ['Popularity', 'danceability', 'energy', 'tempo', 'duration_ms', 'Artist_followers', 'loudness', 'valence']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 時間與時長
    df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
    df['Year'] = df['Release_date'].dt.year
    df['duration_min'] = df['duration_ms'] / 60000
    
    # 基礎清洗
    df = df.dropna(subset=['Year', 'Popularity', 'Genre', 'Artist', 'tempo'])
    df = df[(df['Popularity'] >= 0) & (df['Popularity'] <= 100)]
    
    # 流派清洗 (移除 N-A, Unknown 等)
    df['Genre'] = df['Genre'].astype(str).str.title()
    df = df[~df['Genre'].isin(['N-A', 'Nan', 'Unknown', 'N/A'])]

    # Explicit 標籤修復
    if 'Explicit' in df.columns:
        df['Exp_Str'] = df['Explicit'].astype(str).str.lower().str.strip()
        mapping = {'true': 'Explicit 🔞', '1': 'Explicit 🔞', 'false': 'Clean 🟢', '0': 'Clean 🟢'}
        df['Explicit_Label'] = df['Exp_Str'].map(mapping).fillna('Clean 🟢')

    return df

# --- 4. 執行主程式 ---
def run_dashboard():
    df_raw = load_data()
    if df_raw is None:
        st.stop()

    # --- 側邊欄控制 ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=50)
        st.title("Analytics Panel")
        
        # 4.1 核心過濾器
        year_range = st.slider("📅 Year Range", int(df_raw['Year'].min()), int(df_raw['Year'].max()), (2010, 2024))
        search_query = st.text_input("🔍 Search Artist Name", "")
        
        # 應用過濾邏輯
        df_filtered = df_raw[(df_raw['Year'] >= year_range[0]) & (df_raw['Year'] <= year_range[1])]
        if search_query:
            df_filtered = df_filtered[df_filtered['Artist'].str.contains(search_query, case=False, na=False)]
        
        st.markdown("---")
        top_n = st.slider("🏆 Top Genres Count", 3, 15, 5)
        
        # 4.2 修正後的下載功能 (在過濾後才生成)
        if not df_filtered.empty:
            csv_data = df_filtered.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Download current analysis (.csv)",
                data=csv_data,
                file_name=f'spotify_analysis_{year_range[0]}_{year_range[1]}.csv',
                mime='text/csv'
            )
        else:
            st.warning("No data found for selected filters.")
        
        st.markdown("---")
        st.write("Created by **Selina**")

    # --- 5. 主頁面：KPI 指標卡 ---
    st.title("🎵 Spotify Intelligence Strategy Dashboard")
    
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

    # --- 6. 分頁內容 ---
    tab1, tab2, tab3 = st.tabs(["📈 Market Strategy", "🎛️ Audio Lab & AI", "🌍 Global Map"])

    # === TAB 1: 市場策略 (題目 1-5) ===
    with tab1:
        section_header("1. Market Trend Evolution")
        yearly = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
        fig1 = apply_chart_style(px.line(yearly, x='Year', y='Popularity', markers=True, height=500), "Yearly Popularity Trend")
        fig1.update_traces(line=dict(color=SPOTIFY_BLACK, width=4), marker=dict(size=10, color=SPOTIFY_GREEN))
        st.plotly_chart(fig1, width='stretch') # ✅ 2026 語法

        section_header("2. Single vs. Album Strategy")
        top_genres_list = df_filtered['Genre'].value_counts().head(top_n).index
        df_strat = df_filtered[df_filtered['Genre'].isin(top_genres_list)]
        fig2 = apply_chart_style(px.box(df_strat, x='Album/Single', y='Popularity', color='Album/Single', facet_col='Genre', facet_col_wrap=5, height=700, color_discrete_map={'single': SPOTIFY_GREEN, 'album': "#B3B3B3"}), "Format Performance by Genre")
        fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
        st.plotly_chart(fig2, width='stretch')

        section_header("3. Content Strategy (Explicit Content)")
        df_exp = df_filtered[df_filtered['Genre'].isin(top_genres_list)]
        avg_exp = df_exp.groupby(['Genre', 'Explicit_Label'])['Popularity'].mean().reset_index()
        fig3 = apply_chart_style(px.bar(avg_exp, x='Genre', y='Popularity', color='Explicit_Label', barmode='group', color_discrete_map={'Explicit 🔞': SPOTIFY_BLACK, 'Clean 🟢': SPOTIFY_GREEN}, height=550), "Impact of Explicit Lyrics")
        st.plotly_chart(fig3, width='stretch')

        section_header("4. The Superstar Effect")
        art_stats = df_filtered.groupby('Artist').agg({'Artist_followers': 'mean', 'Popularity': 'max', 'Title': 'count'}).reset_index()
        art_stats = art_stats[art_stats['Title'] > 2]
        if len(art_stats) > 1:
            st.write(f"📊 **Follower-Popularity Correlation:** `{art_stats['Artist_followers'].corr(art_stats['Popularity']):.2f}`")
            fig4 = apply_chart_style(px.scatter(art_stats, x='Artist_followers', y='Popularity', hover_name='Artist', log_x=True, trendline="ols", trendline_color_override=SPOTIFY_BLACK, height=650), "Followers vs. Global Peaks")
            fig4.update_traces(marker=dict(size=8, color=SPOTIFY_GREEN), opacity=0.6)
            st.plotly_chart(fig4, width='stretch')

        section_header("5. Talent Scouting: Dark Horse Radar")
        dark = df_filtered[(df_filtered['Artist_followers'] < 50000) & (df_filtered['Popularity'] > 75)].copy()
        if not dark.empty:
            fig5 = apply_chart_style(px.scatter(dark, x='energy', y='danceability', size='Popularity', color='Popularity', hover_name='Title', color_continuous_scale=['#F0FFF0', SPOTIFY_GREEN], height=750), "High-Potential Emerging Artists")
            fig5.add_vline(x=0.5, line_dash="dash", line_color="grey")
            fig5.add_hline(y=0.5, line_dash="dash", line_color="grey")
            st.plotly_chart(fig5, width='stretch')

    # === TAB 2: 音樂實驗室 & AI (題目 6-9) ===
    with tab2:
        # 🔮 AI 預測功能
        section_header("6. AI Hit Potential Predictor")
        st.write("調整參數，AI 將計算該音色特徵的「爆紅潛力指數」。")
        col_ai_l, col_ai_r = st.columns([1, 2])
        with col_ai_l:
            in_d = st.slider("Danceability", 0.0, 1.0, 0.6)
            in_e = st.slider("Energy", 0.0, 1.0, 0.7)
            in_l = st.slider("Loudness (dB)", -60, 0, -10)
            in_v = st.slider("Valence", 0.0, 1.0, 0.5)
            pred = (in_d * 30) + (in_e * 25) + ((in_l+60)/60 * 20) + (in_v * 10) + 15
            st.metric("Predicted Hit Score", f"{pred:.1f} / 100")
        with col_ai_r:
            radar = go.Figure(data=go.Scatterpolar(r=[in_d, in_e, (in_l+60)/60, in_v, in_d], theta=['Dance','Energy','Loudness','Valence','Dance'], fill='toself', fillcolor='rgba(29, 185, 84, 0.4)', line=dict(color=SPOTIFY_GREEN)))
            radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), height=400)
            st.plotly_chart(radar, width='stretch')

        section_header("7. Tempo Analysis (BPM)")
        def classify_tempo(bpm): return 'Slow (<100)' if bpm < 100 else 'Mainstream (100-140)' if bpm <= 140 else 'Fast (>140)'
        df_filtered['Tempo_Zone'] = df_filtered['tempo'].apply(classify_tempo)
        fig6 = apply_chart_style(px.histogram(df_filtered, x='tempo', color='Tempo_Zone', color_discrete_map={'Slow (<100)': '#B3B3B3', 'Mainstream (100-140)': SPOTIFY_GREEN, 'Fast (>140)': '#535353'}, text_auto='.2s', height=600), "Tempo Distribution (Jupyter Style)")
        fig6.update_traces(xbins=dict(start=0, end=250, size=5), textposition='outside', marker_line_width=1, marker_line_color="white")
        fig6.add_vline(x=120, line_width=3, line_dash="dash", line_color=SPOTIFY_BLACK, annotation_text="120 BPM")
        st.plotly_chart(fig6, width='stretch')

        section_header("8. Duration Economics")
        dur = df_filtered.groupby('Year')['duration_min'].mean().reset_index()
        fig7 = apply_chart_style(px.line(dur, x='Year', y='duration_min', markers=True, height=500), "Are Songs Getting Shorter?")
        st.plotly_chart(fig7, width='stretch')

        section_header("9. Feature Correlation Matrix")
        corr = df_filtered[['Popularity', 'danceability', 'energy', 'valence', 'tempo', 'loudness']].corr()
        fig8 = apply_chart_style(px.imshow(corr, text_auto='.2f', color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN], height=600), "Which Audio Features Drive Popularity?")
        st.plotly_chart(fig8, width='stretch')

    # === TAB 3: 全球版圖 (題目 10) ===
    with tab3:
        section_header("10. Global Market Reach")
        geo = df_filtered.groupby('Country')['Popularity'].mean().reset_index()
        fig10 = apply_chart_style(px.choropleth(geo, locations="Country", locationmode='country names', color="Popularity", color_continuous_scale=['#F5F5F5', SPOTIFY_GREEN, '#106b31'], height=800), "Global Popularity Heatmap")
        fig10.update_layout(geo=dict(showframe=False, projection_type='natural earth'))
        st.plotly_chart(fig10, width='stretch')

if __name__ == "__main__":
    run_dashboard()
