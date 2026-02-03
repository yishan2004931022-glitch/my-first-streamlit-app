import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Spotify Strategy Dashboard 2026",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Professional Visual Constants ---
SPOTIFY_GREEN = "#1DB954"
SPOTIFY_BLACK = "#191414"
SPOTIFY_LIGHT_GREY = "#B3B3B3"
SPOTIFY_DARK_GREY = "#535353"
TRENDLINE_RED = "#FF4B4B"

# UI Helper: Section Headers
def section_header(text):
    st.markdown(f"""
        <div style='border-left: 10px solid {SPOTIFY_GREEN}; padding-left: 20px; margin-top: 50px; margin-bottom: 10px;'>
            <h2 style='color: #333333; font-size: 30px; font-weight: 800; font-family: "Arial Black"; margin: 0;'>
            {text}
            </h2>
        </div>
        """, unsafe_allow_html=True)

# UI Helper: Standard Plotly Styling (2026 Version)
def apply_chart_style(fig, title_text):
    fig.update_layout(
        template="simple_white",
        title=dict(
            text=f"<b>{title_text}</b>",
            font=dict(color=SPOTIFY_GREEN, size=22, family="Arial Black"),
            x=0, y=0.98
        ),
        font=dict(family="Arial", size=14, color="black"),
        margin=dict(t=120, b=50, l=50, r=50)
    )
    return fig

# --- 3. Data Engine ---
@st.cache_data
def load_data():
    all_files = os.listdir('.')
    target = 'Final database.csv.gz' if 'Final database.csv.gz' in all_files else 'Final database.zip'
    try:
        df = pd.read_csv(target, low_memory=False)
        df = df[(df['Popularity'] >= 0) & (df['Popularity'] <= 100)].copy()
        df = df[df['Album/Single'].isin(['single', 'album'])]
        mask_junk = df['Genre'].astype(str).str.lower().isin(['n-a', 'unknown', 'world-music', 'nan'])
        df = df[~mask_junk]
        df['Genre'] = df['Genre'].astype(str).str.title().replace({'K-Pop': 'K-Pop'})
        num_cols = ['Popularity', 'danceability', 'energy', 'tempo', 'Artist_followers', 'duration_ms', 'loudness', 'valence']
        for c in num_cols:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce')
        df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
        df['Year'] = df['Release_date'].dt.year
        if 'Explicit' in df.columns:
            df['Explicit_Label'] = df['Explicit'].astype(str).map({'True': 'Explicit 🔞', 'False': 'Clean 🟢', 'true': 'Explicit 🔞', 'false': 'Clean 🟢'}).fillna('Clean 🟢')
        return df.dropna(subset=['Year', 'Popularity', 'Genre', 'Artist', 'tempo'])
    except: return None

df = load_data()

# --- 4. Sidebar Strategy Filters ---
if df is not None:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=50)
        st.title("Strategy Panel")
        
        # ✨ 修正點 1：將變數名稱改為 yr，解決 NameError
        yr = st.slider("📅 Year Selection", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
        search_query = st.text_input("🔍 Search Artist Name", "")
        
        df_filtered = df[(df['Year'] >= yr[0]) & (df['Year'] <= yr[1])]
        if search_query:
            df_filtered = df_filtered[df_filtered['Artist'].str.contains(search_query, case=False, na=False)]
        
        top_n = st.slider("🏆 Top Genres Count", 3, 10, 4)
        if not df_filtered.empty:
            csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Export Current Data", csv, "spotify_report.csv", "text/csv")
        st.write("Presented by **Selina**")

    # --- 5. Main Dashboard KPIs ---
    st.title("🎵 Spotify Intelligence Strategy Dashboard")
    
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Tracks", f"{len(df_filtered):,}")
    k2.metric("Avg Pop", f"{df_filtered['Popularity'].mean():.1f}")
    k3.metric("Superstars", f"{len(df_filtered[df_filtered['Artist_followers'] > 1000000]['Artist'].unique())}")
    k4.metric("Avg Tempo", f"{df_filtered['tempo'].mean():.0f}")
    k5.metric("Top Genre", df_filtered['Genre'].mode()[0] if not df_filtered.empty else "N/A")

    tab1, tab2, tab3 = st.tabs(["📈 Market Strategy", "🎛️ Audio Lab & AI", "🌍 Global Reach"])

    # === TAB 1: Market Strategy ===
    with tab1:
        section_header("Market Trend Evolution")
        yearly = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
        m1, m2, m3 = st.columns([0.6, 0.6, 4]) 
        m1.metric("Peak Year", int(yearly.loc[yearly['Popularity'].idxmax(), 'Year']))
        m2.metric("Market Avg", f"{yearly['Popularity'].mean():.1f}")
        m3.markdown(f"""
            <div style='padding-top:28px; white-space: nowrap; color: #535353; font-size: 16px;'>
                💡 <b>Insight:</b> Analysis of market volatility and streaming adoption trends.
            </div>
            """, unsafe_allow_html=True)
        
        fig1 = px.line(yearly, x='Year', y='Popularity', markers=True, height=500)
        fig1.update_traces(line=dict(color=SPOTIFY_BLACK, width=3), marker=dict(size=8, color=SPOTIFY_GREEN, line=dict(width=2, color='white')))
        st.plotly_chart(apply_chart_style(fig1, "Global Popularity Evolution"), width='stretch')

        section_header("Single vs. Album Strategy")
        target_gs = df_filtered['Genre'].value_counts().head(top_n).index
        df_segment = df_filtered[df_filtered['Genre'].isin(target_gs)]
        fig2 = px.box(df_segment, x='Album/Single', y='Popularity', color='Album/Single', 
                     facet_col='Genre', facet_col_wrap=4, height=900, facet_row_spacing=0.1, 
                     color_discrete_map={'single': SPOTIFY_GREEN, 'album': SPOTIFY_LIGHT_GREY},
                     category_orders={'Album/Single': ['single', 'album']})
        fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
        st.plotly_chart(apply_chart_style(fig2, "Format Strategy Performance"), width='stretch')

        section_header("The Superstar Effect: Correlation Analysis")
        art_s = df_filtered.groupby('Artist').agg({'Artist_followers':'mean', 'Popularity':'max', 'Title':'count'}).reset_index()
        art_s = art_s[art_s['Title'] > 2]
        if not art_s.empty:
            corr_val = art_s['Artist_followers'].corr(art_s['Popularity'])
            sm1, sm2 = st.columns([0.6, 4])
            sm1.metric("Corr", f"{corr_val:.2f}")
            sm2.markdown(f"<div style='padding-top:28px; color: #535353; font-size: 16px;'>💡 <b>Insight:</b> Correlation between Social Reach and Peak Market Ceiling.</div>", unsafe_allow_html=True)
            fig4 = px.scatter(art_s, x='Artist_followers', y='Popularity', hover_name='Artist', log_x=True, 
                             trendline="ols", trendline_color_override=TRENDLINE_RED, opacity=0.5, height=650)
            fig4.update_traces(marker=dict(size=8, color=SPOTIFY_GREEN, line=dict(width=1, color='white')))
            st.plotly_chart(apply_chart_style(fig4, "Social Leverage Analysis"), width='stretch')

        section_header("Talent Scouting: Dark Horse Radar")
        dark_horses = df_filtered[(df_filtered['Artist_followers'] < 50000) & (df_filtered['Popularity'] > 75)].copy()
        if not dark_horses.empty:
            fig9 = px.scatter(dark_horses, x='energy', y='danceability', size='Popularity', color='Popularity',     
                             hover_name='Title', hover_data=['Artist'], color_continuous_scale=['#A0E0A0', SPOTIFY_GREEN], height=700)
            fig9.add_vline(x=0.5, line_dash="dash", line_color="grey")
            fig9.add_hline(y=0.5, line_dash="dash", line_color="grey")
            st.plotly_chart(apply_chart_style(fig9, "Dark Horse Radar: Quadrant Strategy"), width='stretch')

    # === TAB 2: Audio Lab & AI ===
    with tab2:
        section_header("Special Feature: Top 10 Genres Migration")
        # ✨ 動畫圖修正：確保數據完整
        top_10_anim = df_filtered.groupby('Genre')['Popularity'].mean().nlargest(10).index.tolist()
        df_anim_raw = df_filtered[df_filtered['Genre'].isin(top_10_anim)].copy()
        df_anim = df_anim_raw.groupby(['Year', 'Genre']).agg({'energy':'mean', 'danceability':'mean', 'Popularity':'mean', 'Title':'count'}).reset_index()
        df_anim = df_anim.sort_values('Year')
        
        # 固定座標軸 [0, 1] 避免晃動
        fig_anim = px.scatter(df_anim, x="energy", y="danceability", animation_frame="Year", animation_group="Genre",
                             size="Title", color="Genre", hover_name="Genre", size_max=60,
                             range_x=[0, 1], range_y=[0, 1], height=700, color_discrete_sequence=px.colors.qualitative.Bold)
        fig_anim.update_layout(margin={"t": 30, "b": 0}, sliders=[{"currentvalue": {"prefix": "Year: "}}])
        
        st.plotly_chart(apply_chart_style(fig_anim, f"Evolution of Top 10 Leaders ({yr[0]}-{yr[1]})"), width='stretch')
        st.markdown("<div style='color: #535353; font-size: 16px;'>💡 <b>Insight:</b> Press play to watch how market leaders migrate toward the high-energy 'Hit Zone'.</div>", unsafe_allow_html=True)

        section_header("Audio Feature Diversity: Market Exploration")
        df_sample = df_filtered.sample(n=min(2000, len(df_filtered)), random_state=42)
        corr_val_audio = df_sample['energy'].corr(df_sample['Popularity'])
        f6_m1, f6_m2, f6_m3 = st.columns([0.6, 0.6, 4])
        f6_m1.metric("Sample", len(df_sample))
        f6_m2.metric("Corr", f"{corr_val_audio:.2f}")
        f6_m3.markdown("<div style='padding-top:28px; color: #535353; font-size: 16px;'>💡 <b>Insight:</b> High-vibe tracks are popular, but the market shows openness to various styles.</div>", unsafe_allow_html=True)
        fig6 = px.scatter(df_sample, x='energy', y='danceability', color='Popularity', color_continuous_scale=['#F0F0F0', SPOTIFY_GREEN], opacity=0.6, height=700)
        st.plotly_chart(apply_chart_style(fig6, "Audio Feature Distribution"), width='stretch')

        section_header("Hit Song DNA: The Strategic Blueprint")
        hit_songs = df_filtered[df_filtered['Popularity'] > 80]
        if not hit_songs.empty:
            f7_m1, f7_m2 = st.columns([1, 4])
            f7_m1.metric("High-Impact Hits", len(hit_songs))
            f7_m2.markdown("<div style='padding-top:28px; color: #535353; font-size: 16px;'>🎯 <b>Blueprint:</b> Most global hits cluster in the 0.6-0.8 Audio DNA window.</div>", unsafe_allow_html=True)
            fig7 = px.density_contour(hit_songs, x='energy', y='danceability', nbinsx=20, nbinsy=20, height=700)
            fig7.update_traces(contours_coloring="fill", colorscale='Greens', opacity=0.8)
            st.plotly_chart(apply_chart_style(fig7, "Hit DNA: Concentration Analysis"), width='stretch')

        section_header("Tempo Analysis: The Sweet Spot")
        fig8 = px.histogram(df_filtered, x='tempo', color_discrete_sequence=[SPOTIFY_GREEN], text_auto='.2s', height=650)
        fig8.update_traces(xbins=dict(start=0, end=250, size=10), textposition='outside')
        fig8.add_vline(x=120, line_dash="dash", line_color=SPOTIFY_BLACK, line_width=2)
        fig8.add_annotation(x=120, y=1.08, yref="paper", text="Pop Standard (120 BPM)", showarrow=False, font=dict(size=14, family="Arial Black"), bgcolor="rgba(255,255,255,0.8)")
        st.plotly_chart(apply_chart_style(fig8, "Tempo Distribution Strategy"), width='stretch')

        section_header("AI Hit Potential Predictor")
        ca1, ca2 = st.columns([1, 2])
        with ca1:
            id = st.slider("Danceability", 0.0, 1.0, 0.6); ie = st.slider("Energy", 0.0, 1.0, 0.7); il = st.slider("Loudness", -60, 0, -10); iv = st.slider("Valence", 0.0, 1.0, 0.5)
            score = (id*30 + ie*25 + (il+60)/60*20 + iv*15 + 10)
            st.metric("Predicted Hit Score", f"{score:.1f} / 100")
        with ca2:
            radar = go.Figure(data=go.Scatterpolar(r=[id, ie, (il+60)/60, iv, id], theta=['Dance','Energy','Loud','Valence','Dance'], fill='toself', fillcolor='rgba(29, 185, 84, 0.4)', line=dict(color=SPOTIFY_GREEN)))
            radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), height=400)
            st.plotly_chart(radar, width='stretch')

    # === TAB 3: Global Reach ===
    with tab3:
        section_header("8. Global Market Reach")
        geo = df_filtered.groupby('Country')['Popularity'].mean().reset_index()
        top_country_name = geo.loc[geo['Popularity'].idxmax(), 'Country'] if not geo.empty else "N/A"
        top_country_pop = geo.loc[geo['Popularity'].idxmax(), 'Popularity'] if not geo.empty else 0
        g1, g2, g3 = st.columns([1.2, 0.8, 3.5])
        g1.metric("Top Market 🏆", top_country_name)
        g2.metric("Avg Pop", f"{top_country_pop:.1f}")
        g3.markdown(f"<div style='padding-top:28px; color: #535353; font-size: 16px;'>💡 <b>Global Insight:</b> Leading Market: <b>{top_country_name}</b>. High-consumption hotspots identified.</div>", unsafe_allow_html=True)
        fig10 = px.choropleth(geo, locations="Country", locationmode='country names', color="Popularity", color_continuous_scale=['#F0FDF4', SPOTIFY_GREEN, '#14532D'], height=700)
        fig10.update_layout(margin={"r":0, "t":0, "l":0, "b":0}, geo=dict(showframe=False, projection_type='natural earth', showocean=True, oceancolor='#F8FAFC'))
        st.plotly_chart(fig10, width='stretch')
