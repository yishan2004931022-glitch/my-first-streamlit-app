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

# ✨ 帶有左側綠色裝飾條的大標題
def section_header(text):
    st.markdown(f"""
        <div style='border-left: 10px solid {SPOTIFY_GREEN}; padding-left: 20px; margin-top: 50px; margin-bottom: 10px;'>
            <h2 style='color: #333333; font-size: 34px; font-weight: 800; font-family: "Arial Black"; margin: 0;'>
            {text}
            </h2>
        </div>
        """, unsafe_allow_html=True)

# ✨ 綠色圖表小副標題樣式
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
    # 自動診斷：列出目前目錄檔案
    available_files = os.listdir('.')
    target_file = None
    if 'Final database.csv.gz' in available_files:
        target_file = 'Final database.csv.gz'
    elif 'Final database.zip' in available_files:
        target_file = 'Final database.zip'
    
    if not target_file:
        st.error(f"❌ 找不到資料檔！目前目錄內只有：{available_files}")
        return None

    try:
        if target_file.endswith('.gz'):
            df = pd.read_csv(target_file, compression='gzip', low_memory=False)
        else:
            df = pd.read_csv(target_file, compression='zip', low_memory=False)
    except Exception as e:
        st.error(f"❌ 讀取資料錯誤: {e}")
        return None

    # 數值轉換
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
if df is not None:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=50)
        st.title("Analytics Panel")
        year_range = st.slider("📅 Year Range", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
        search_query = st.text_input("🔍 Search Artist Name", "")
        
        df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
        if search_query:
            df_filtered = df_filtered[df_filtered['Artist'].str.contains(search_query, case=False, na=False)]
        
        top_n = st.slider("🏆 Top Genres Count", 3, 15, 5)
        
        # 修正後的 CSV 下載按鈕 (使用 utf-8-sig 解決 Excel 亂碼)
        if not df_filtered.empty:
            csv_data = df_filtered.to_csv(index=False).encode('utf-8-sig')
            st.download_button(label="📥 Download current data (.csv)", data=csv_data, file_name='spotify_export.csv', mime='text/csv')

    # --- 5. 主頁面內容 ---
    st.title("🎵 Spotify Intelligence Dashboard")

    # 📊 KPI 指標卡
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Tracks", f"{len(df_filtered):,}")
    m2.metric("Avg Popularity", f"{df_filtered['Popularity'].mean():.1f}")
    m3.metric("Superstars", f"{len(df_filtered[df_filtered['Artist_followers'] > 1000000]['Artist'].unique())}")
    m4.metric("Avg Tempo", f"{df_filtered['tempo'].mean():.0f} BPM")
    m5.metric("Top Genre", df_filtered['Genre'].mode()[0] if not df_filtered.empty else "N/A")

    tab1, tab2, tab3 = st.tabs(["📈 Market Strategy", "🎛️ AI Lab & AI", "🌍 Global Map"])

    # === TAB 1: 市場策略 (1-5 題) ===
    with tab1:
        section_header("1. Market Trend Evolution")
        yearly = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
        fig1 = apply_chart_style(px.line(yearly, x='Year', y='Popularity', markers=True, height=500), "Global Popularity Evolution")
        fig1.update_traces(line_color=SPOTIFY_BLACK, marker=dict(size=10, color=SPOTIFY_GREEN))
        st.plotly_chart(fig1, width='stretch')

        section_header("2. Single vs. Album Strategy")
        top_genres = df_filtered['Genre'].value_counts().head(top_n).index
        df_strat = df_filtered[df_filtered['Genre'].isin(top_genres)]
        fig2 = apply_chart_style(px.box(df_strat, x='Album/Single', y='Popularity', color='Album/Single', facet_col='Genre', facet_col_wrap=5, height=700, color_discrete_map={'single': SPOTIFY_GREEN, 'album': "#B3B3B3"}), "Format Performance")
        fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
        st.plotly_chart(fig2, width='stretch')

        section_header("3. Content Strategy (Explicit Content)")
        df_exp = df_filtered[df_filtered['Genre'].isin(top_genres)]
        avg_exp = df_exp.groupby(['Genre', 'Explicit_Label'])['Popularity'].mean().reset_index()
        fig3 = apply_chart_style(px.bar(avg_exp, x='Genre', y='Popularity', color='Explicit_Label', barmode='group', color_discrete_map={'Explicit 🔞': SPOTIFY_BLACK, 'Clean 🟢': SPOTIFY_GREEN}, height=550), "Impact of Explicit Lyrics")
        st.plotly_chart(fig3, width='stretch')

        section_header("4. The Superstar Effect")
        art_stats = df_filtered.groupby('Artist').agg({'Artist_followers': 'mean', 'Popularity': 'max', 'Title': 'count'}).reset_index()
        art_stats = art_stats[art_stats['Title'] > 2]
        if len(art_stats) > 1:
            st.write(f"📊 **Correlation:** `{art_stats['Artist_followers'].corr(art_stats['Popularity']):.2f}`")
            fig4 = apply_chart_style(px.scatter(art_stats, x='Artist_followers', y='Popularity', hover_name='Artist', log_x=True, trendline="ols", trendline_color_override=SPOTIFY_BLACK, height=650), "Followers vs. Peaks")
            fig4.update_traces(marker=dict(size=8, color=SPOTIFY_GREEN), opacity=0.6)
            st.plotly_chart(fig4, width='stretch')

        section_header("5. Talent Scouting: Dark Horse Radar")
        dark = df_filtered[(df_filtered['Artist_followers'] < 50000) & (df_filtered['Popularity'] > 75)].copy()
        if not dark.empty:
            fig5 = apply_chart_style(px.scatter(dark, x='energy', y='danceability', size='Popularity', color='Popularity', hover_name='Title', color_continuous_scale=['#F0FFF0', SPOTIFY_GREEN], height=750), "Emerging Artist Analysis")
            st.plotly_chart(fig5, width='stretch')

    # === TAB 2: 音樂實驗室 & AI (6-9 題) ===
    with tab2:
        section_header("6. AI Hit Potential Predictor")
        st.write("調整參數以預測歌曲熱度潛力指標。")
        ca1, ca2 = st.columns([1, 2])
        with ca1:
            id = st.slider("Danceability", 0.0, 1.0, 0.6)
            ie = st.slider("Energy", 0.0, 1.0, 0.7)
            il = st.slider("Loudness", -60, 0, -10)
            iv = st.slider("Valence", 0.0, 1.0, 0.5)
            # 預測分數公式模擬：
            # $$Score = (Dance \times 30) + (Energy \times 25) + (\frac{Loud+60}{60} \times 20) + (Valence \times 10) + 15$$
            pred = (id*30 + ie*25 + (il+60)/60*20 + iv*10 + 15)
            st.metric("AI Predicted Hit Score", f"{pred:.1f}")
        with ca2:
            radar = go.Figure(data=go.Scatterpolar(r=[id, ie, (il+60)/60, iv, id], theta=['Dance','Energy','Loudness','Happiness','Dance'], fill='toself', fillcolor='rgba(29, 185, 84, 0.4)', line=dict(color=SPOTIFY_GREEN)))
            radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), height=400)
            st.plotly_chart(radar, width='stretch')

        section_header("7. Tempo Analysis (BPM)")
        def classify_tempo(bpm): return 'Slow (<100)' if bpm < 100 else 'Mainstream (100-140)' if bpm <= 140 else 'Fast (>140)'
        df_filtered['Tempo_Zone'] = df_filtered['tempo'].apply(classify_tempo)
        fig6 = apply_chart_style(px.histogram(df_filtered, x='tempo', color='Tempo_Zone', color_discrete_map={'Slow (<100)': '#B3B3B3', 'Mainstream (100-140)': SPOTIFY_GREEN, 'Fast (>140)': '#535353'}, text_auto='.2s', height=600), "Tempo Sweet Spot")
        fig6.update_traces(xbins=dict(start=0, end=250, size=5), textposition='outside', marker_line_width=1, marker_line_color="white")
        st.plotly_chart(fig6, width='stretch')

        section_header("8. Duration Economics")
        dur = df_filtered.groupby('Year')['duration_min'].mean().reset_index()
        fig7 = apply_chart_style(px.line(dur, x='Year', y='duration_min', markers=True, height=500), "Track Length Trends")
        st.plotly_chart(fig7, width='stretch')

        section_header("9. Feature Correlation Matrix")
        corr = df_filtered[['Popularity', 'danceability', 'energy', 'valence', 'tempo', 'loudness']].corr()
        fig8 = apply_chart_style(px.imshow(corr, text_auto='.2f', color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN], height=600), "Correlation Matrix")
        st.plotly_chart(fig8, width='stretch')

    # === TAB 3: 全球版圖 (10 題) ===
    with tab3:
        section_header("10. Global Market Reach")
        geo = df_filtered.groupby('Country')['Popularity'].mean().reset_index()
        fig10 = apply_chart_style(px.choropleth(geo, locations="Country", locationmode='country names', color="Popularity", color_continuous_scale=['#F5F5F5', SPOTIFY_GREEN, '#106b31'], height=800), "Popularity by Territory")
        st.plotly_chart(fig10, width='stretch')
else:
    st.error("App 無法載入資料。請確認 GitHub 資料夾中包含 'Final database.csv.gz'。")
