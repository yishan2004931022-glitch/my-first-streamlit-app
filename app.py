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

# ✨ 綠色圖表小副標題樣式 (2026 視覺標準)
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
    fig.update_xaxes(tickfont=dict(color="black", size=12), title_font=dict(family="Arial Black", size=15))
    fig.update_yaxes(tickfont=dict(color="black", size=12), title_font=dict(family="Arial Black", size=15))
    return fig

# --- 3. 資料讀取與強力清洗 ---
@st.cache_data
def load_data():
    all_files = os.listdir('.')
    target = 'Final database.csv.gz' if 'Final database.csv.gz' in all_files else 'Final database.zip'
    
    if target not in all_files:
        st.error(f"❌ 資料檔遺失。目前目錄：{all_files}")
        return None

    try:
        df = pd.read_csv(target, low_memory=False)
        # 數值轉換
        numeric_cols = ['Popularity', 'danceability', 'energy', 'tempo', 'duration_ms', 'Artist_followers', 'loudness', 'valence']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
        df['Year'] = df['Release_date'].dt.year
        df['duration_min'] = df['duration_ms'] / 60000
        
        # 清洗髒數據
        df = df.dropna(subset=['Year', 'Popularity', 'Genre', 'Artist', 'tempo'])
        df['Genre'] = df['Genre'].astype(str).str.title()
        df = df[~df['Genre'].isin(['N-A', 'Nan', 'Unknown', 'N/A'])]
        
        # Explicit 標籤修復
        if 'Explicit' in df.columns:
            df['Explicit_Label'] = df['Explicit'].astype(str).map({'True': 'Explicit 🔞', 'False': 'Clean 🟢', 'true': 'Explicit 🔞', 'false': 'Clean 🟢'}).fillna('Clean 🟢')
            
        return df
    except Exception as e:
        st.error(f"❌ 讀取錯誤: {e}")
        return None

df = load_data()

# --- 4. 側邊欄控制 (含搜尋與下載) ---
if df is not None:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=50)
        st.title("Admin Strategy Panel")
        
        year_range = st.slider("📅 Year Range", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
        search_query = st.text_input("🔍 Search Artist Name", "")
        
        # 資料篩選
        df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
        if search_query:
            df_filtered = df_filtered[df_filtered['Artist'].str.contains(search_query, case=False, na=False)]
        
        top_n = st.slider("🏆 Top Genres Count", 3, 15, 5)
        
        st.markdown("---")
        # 下載功能
        if not df_filtered.empty:
            csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Export Current Analysis (.csv)", csv, f"spotify_{year_range[0]}.csv", "text/csv")
        
        st.write("Created by **Selina**")

    # --- 5. 主頁面內容 ---
    st.title("🎵 Spotify Intelligence Strategy Dashboard")

    # 📊 商業 KPI 指標卡
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Tracks", f"{len(df_filtered):,}")
    m2.metric("Avg Popularity", f"{df_filtered['Popularity'].mean():.1f}")
    m3.metric("Superstars", f"{len(df_filtered[df_filtered['Artist_followers'] > 1000000]['Artist'].unique())}")
    m4.metric("Avg Tempo", f"{df_filtered['tempo'].mean():.0f} BPM")
    m5.metric("Top Genre", df_filtered['Genre'].mode()[0] if not df_filtered.empty else "N/A")

    tab1, tab2, tab3 = st.tabs(["📈 Market Strategy", "🎛️ Audio Lab & AI", "🌍 Global Map"])

    # === TAB 1: 市場策略 (1-5 題) ===
    with tab1:
        section_header("1. Market Trend Evolution")
        yearly = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
        fig1 = apply_chart_style(px.line(yearly, x='Year', y='Popularity', markers=True, height=500), "Global Popularity Evolution")
        fig1.update_traces(line_color=SPOTIFY_BLACK, width=4, marker=dict(size=10, color=SPOTIFY_GREEN))
        st.plotly_chart(fig1, width='stretch')

        section_header("2. Single vs. Album Strategy")
        top_gs = df_filtered['Genre'].value_counts().head(top_n).index
        df_strat = df_filtered[df_filtered['Genre'].isin(top_gs)]
        fig2 = apply_chart_style(px.box(df_strat, x='Album/Single', y='Popularity', color='Album/Single', facet_col='Genre', facet_col_wrap=5, height=700, color_discrete_map={'single': SPOTIFY_GREEN, 'album': "#B3B3B3"}), "Format Strategy Performance")
        fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
        st.plotly_chart(fig2, width='stretch')

        section_header("3. Content Strategy (Explicit Lyrics)")
        avg_exp = df_strat.groupby(['Genre', 'Explicit_Label'])['Popularity'].mean().reset_index()
        fig3 = apply_chart_style(px.bar(avg_exp, x='Genre', y='Popularity', color='Explicit_Label', barmode='group', color_discrete_map={'Explicit 🔞': SPOTIFY_BLACK, 'Clean 🟢': SPOTIFY_GREEN}, height=550), "Explicit vs. Clean Popularity")
        st.plotly_chart(fig3, width='stretch')

        section_header("4. The Superstar Effect")
        art_s = df_filtered.groupby('Artist').agg({'Artist_followers': 'mean', 'Popularity': 'max'}).reset_index()
        try:
            fig4 = apply_chart_style(px.scatter(art_s, x='Artist_followers', y='Popularity', log_x=True, trendline="ols", height=650), "Network Size vs. Chart Success")
            fig4.update_traces(marker=dict(size=8, color=SPOTIFY_GREEN), opacity=0.6)
            st.plotly_chart(fig4, width='stretch')
        except:
            st.plotly_chart(px.scatter(art_s, x='Artist_followers', y='Popularity', log_x=True), width='stretch')

        section_header("5. Dark Horse Radar")
        dark = df_filtered[(df_filtered['Artist_followers'] < 50000) & (df_filtered['Popularity'] > 75)].copy()
        if not dark.empty:
            fig5 = apply_chart_style(px.scatter(dark, x='energy', y='danceability', size='Popularity', color='Popularity', height=750), "Emerging Artist Analysis")
            fig5.add_vline(x=0.5, line_dash="dash"); fig5.add_hline(y=0.5, line_dash="dash")
            st.plotly_chart(fig5, width='stretch')

    # === TAB 2: 音樂實驗室 & AI (6-9 題) ===
    with tab2:
        section_header("6. AI Hit Potential Predictor")
        ca1, ca2 = st.columns([1, 2])
        with ca1:
            id = st.slider("Danceability", 0.0, 1.0, 0.6); ie = st.slider("Energy", 0.0, 1.0, 0.7); il = st.slider("Loudness", -60, 0, -10); iv = st.slider("Valence", 0.0, 1.0, 0.5)
            score = (id*30 + ie*25 + (il+60)/60*20 + iv*10 + 15)
            st.metric("Predicted Hit Score", f"{score:.1f} / 100")
        with ca2:
            radar = go.Figure(data=go.Scatterpolar(r=[id, ie, (il+60)/60, iv, id], theta=['Dance','Energy','Loud','Happy','Dance'], fill='toself', fillcolor='rgba(29, 185, 84, 0.4)', line=dict(color=SPOTIFY_GREEN)))
            radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), height=400)
            st.plotly_chart(radar, width='stretch')

        section_header("7. Tempo Analysis (BPM)")
        fig6 = apply_chart_style(px.histogram(df_filtered, x='tempo', color_discrete_sequence=[SPOTIFY_GREEN], text_auto='.2s', height=600), "Tempo Sweet Spot")
        fig6.update_traces(xbins=dict(size=5), textposition='outside')
        st.plotly_chart(fig6, width='stretch')

        section_header("8. Duration Economics")
        dur = df_filtered.groupby('Year')['duration_min'].mean().reset_index()
        fig7 = apply_chart_style(px.line(dur, x='Year', y='duration_min', markers=True, height=500), "Track Length Trends")
        st.plotly_chart(fig7, width='stretch')

        section_header("9. Audio Feature Correlation Matrix")
        corr = df_filtered[['Popularity', 'danceability', 'energy', 'valence', 'tempo', 'loudness']].corr()
        fig8 = apply_chart_style(px.imshow(corr, text_auto='.2f', color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN], height=600), "Feature Correlations")
        st.plotly_chart(fig8, width='stretch')

    # === TAB 3: 全球版圖 (10 題) ===
    with tab3:
        section_header("10. Global Market Reach")
        geo = df_filtered.groupby('Country')['Popularity'].mean().reset_index()
        fig10 = apply_chart_style(px.choropleth(geo, locations="Country", locationmode='country names', color="Popularity", color_continuous_scale=['#F5F5F5', SPOTIFY_GREEN, '#106b31'], height=800), "Popularity by Territory")
        fig10.update_layout(geo=dict(showframe=False, projection_type='natural earth'))
        st.plotly_chart(fig10, width='stretch')
