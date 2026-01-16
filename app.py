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
        <div style='border-left: 8px solid {SPOTIFY_GREEN}; padding-left: 15px; margin-top: 40px; margin-bottom: 20px;'>
            <h2 style='color: #333333; font-size: 28px; font-weight: 800; font-family: "Arial Black"; margin: 0;'>
            {text}
            </h2>
        </div>
        """, unsafe_allow_html=True)

# UI Helper: Plotly Styling Wrapper
def apply_chart_style(fig):
    fig.update_layout(
        template="simple_white",
        font=dict(family="Arial", size=12),
        margin=dict(t=50, b=50, l=20, r=20),
        hoverlabel=dict(bgcolor="white", font_size=13)
    )
    return fig

# --- 3. Data Engine (Optimized Cleaning) ---
@st.cache_data
def load_data():
    files = os.listdir('.')
    target = 'Final database.csv.gz' if 'Final database.csv.gz' in files else 'Final database.zip'
    try:
        df = pd.read_csv(target, low_memory=False)
        # Step A: Data Sanitization (Popularity 0-100 only)
        df = df[(df['Popularity'] >= 0) & (df['Popularity'] <= 100)].copy()
        # Step B: Filter Logic (Standard Release Types)
        df = df[df['Album/Single'].isin(['single', 'album'])]
        # Step C: Clean Genres
        mask_junk = df['Genre'].astype(str).str.lower().isin(['n-a', 'unknown', 'world-music', 'nan'])
        df = df[~mask_junk]
        df['Genre'] = df['Genre'].astype(str).str.title().replace({'K-Pop': 'K-Pop'})
        # Step D: Type Casting
        num_cols = ['Popularity', 'danceability', 'energy', 'tempo', 'Artist_followers', 'duration_ms', 'loudness', 'valence']
        for c in num_cols:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce')
        # Step E: Feature Engineering
        df['Year'] = pd.to_datetime(df['Release_date'], errors='coerce', format='mixed').dt.year
        df['duration_min'] = df['duration_ms'] / 60000
        if 'Explicit' in df.columns:
            df['Explicit_Label'] = df['Explicit'].astype(str).map({
                'True': 'Explicit 🔞', 'False': 'Clean 🟢', 'true': 'Explicit 🔞', 'false': 'Clean 🟢'
            }).fillna('Clean 🟢')
        return df.dropna(subset=['Year', 'Popularity', 'Genre', 'Artist', 'tempo'])
    except Exception as e:
        st.error(f"Data Loading Error: {e}")
        return None

df = load_data()

# --- 4. Sidebar Strategy Panel ---
if df is not None:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=60)
        st.title("Strategy Filters")
        yr_range = st.slider("📅 Year Selection", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
        search_query = st.text_input("🔍 Artist Search", "")
        
        # Core Filtered Data (Global)
        df_f = df[(df['Year'] >= yr_range[0]) & (df['Year'] <= yr_range[1])]
        if search_query:
            df_f = df_f[df_f['Artist'].str.contains(search_query, case=False, na=False)]
        
        top_n_genres = st.slider("🏆 Genre Depth (Top N)", 3, 10, 4)
        
        st.markdown("---")
        if not df_f.empty:
            csv_data = df_f.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Export Analysis (.csv)", csv_data, "spotify_report.csv", "text/csv")
        st.write("Presented by **Selina**")

    # --- 5. Dashboard Header & KPIs ---
    st.title("🎵 Spotify Intelligence Strategy Dashboard")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Tracks", f"{len(df_f):,}")
    kpi2.metric("Avg Popularity", f"{df_f['Popularity'].mean():.1f}")
    kpi3.metric("BPM Median", f"{df_f['tempo'].median():.0f}")
    kpi4.metric("Market Leader", df_f['Genre'].mode()[0] if not df_f.empty else "N/A")

    tabs = st.tabs(["📈 Market Insights", "🎛️ Audio Lab", "🌍 Global Reach"])

    # === TAB 1: MARKET INSIGHTS ===
    with tabs[0]:
        # 1. Market Evolution
        section_header("1. Market Evolution: Trend Analysis")
        y_avg = df_f.groupby('Year')['Popularity'].mean().reset_index()
        m1, m2 = st.columns([1, 2])
        m1.metric("Peak Year", int(y_avg.loc[y_avg['Popularity'].idxmax(), 'Year']))
        m1.write("💡 **Insight:** Historical shifts in listener preferences and streaming adoption.")
        fig1 = px.line(y_avg, x='Year', y='Popularity', markers=True)
        fig1.update_traces(line=dict(color=SPOTIFY_BLACK, width=4), marker=dict(color=SPOTIFY_GREEN, size=10, line=dict(width=2, color='white')))
        st.plotly_chart(apply_chart_style(fig1), width='stretch')

        # 2. Release Strategy
        section_header("2. Release Strategy: Format Performance")
        target_gs = df_f['Genre'].value_counts().head(top_n_genres).index
        df_segment = df_f[df_f['Genre'].isin(target_gs)] # ✨ Variable df_segment defined here
        fig2 = px.box(df_segment, x='Album/Single', y='Popularity', color='Album/Single', facet_col='Genre',
                     color_discrete_map={'single': SPOTIFY_GREEN, 'album': SPOTIFY_LIGHT_GREY},
                     category_orders={'Album/Single': ['single', 'album']})
        fig2.update_traces(boxmean=True)
        fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
        st.plotly_chart(apply_chart_style(fig2), width='stretch')

        # 3. Content Strategy
        section_header("3. Content Strategy: Explicit vs. Clean")
        st.write("💡 **Insight:** Assessing the commercial ceiling of explicit content across genres.")
        avg_exp = df_segment.groupby(['Genre', 'Explicit_Label'])['Popularity'].mean().reset_index()
        fig3 = px.bar(avg_exp, x='Genre', y='Popularity', color='Explicit_Label', barmode='group',
                     color_discrete_map={'Clean 🟢': SPOTIFY_GREEN, 'Explicit 🔞': SPOTIFY_BLACK})
        st.plotly_chart(apply_chart_style(fig3), width='stretch')

        # 4. Superstar Effect
        section_header("4. Superstar Effect: Network Leverage")
        art_s = df_f.groupby('Artist').agg({'Artist_followers':'mean', 'Popularity':'max', 'Title':'count'}).reset_index()
        art_s = art_s[art_s['Title'] > 2]
        if not art_s.empty:
            corr = art_s['Artist_followers'].corr(art_s['Popularity'])
            st.info(f"📊 **Correlation Coefficient: {corr:.2f}** (Social Reach vs. Peak Popularity)")
            fig4 = px.scatter(art_s, x='Artist_followers', y='Popularity', hover_name='Artist', log_x=True, 
                             trendline="ols", trendline_color_override=TRENDLINE_RED, opacity=0.4)
            fig4.update_traces(marker=dict(size=9, color=SPOTIFY_GREEN, line=dict(width=1, color='white')))
            fig4.update_yaxes(range=[-5, 105])
            st.plotly_chart(apply_chart_style(fig4), width='stretch')

    # === TAB 2: AUDIO LAB ===
    with tabs[1]:
        # 5. Dark Horse Radar
        section_header("5. Talent Scouting: Dark Horse Radar")
        st.write("🎯 **Definition:** Followers < 50k & Popularity > 75 (High-impact independent artists)")
        dark = df_f[(df_f['Artist_followers'] < 50000) & (df_f['Popularity'] > 75)].copy()
        if not dark.empty:
            fig5 = px.scatter(dark, x='energy', y='danceability', size='Popularity', color='Popularity',
                             hover_name='Title', color_continuous_scale=['#A0E0A0', SPOTIFY_GREEN], height=700)
            fig5.add_vline(x=0.5, line_dash="dash", line_color="grey")
            fig5.add_hline(y=0.5, line_dash="dash", line_color="grey")
            fig5.add_annotation(x=0.9, y=0.9, text="🔥 Club", showarrow=False, font=dict(size=14, family="Arial Black"))
            fig5.add_annotation(x=0.1, y=0.1, text="🌙 Ballad", showarrow=False, font=dict(size=14, family="Arial Black"))
            st.plotly_chart(apply_chart_style(fig5), width='stretch')
        else:
            st.info("No 'Dark Horse' artists found in this selection.")

        # 6. Tempo Analysis
        section_header("6. Tempo Analysis: The BPM Sweet Spot")
        fig6 = px.histogram(df_f, x='tempo', text_auto='.2s', color_discrete_sequence=[SPOTIFY_GREEN])
        fig6.update_traces(xbins=dict(start=0, end=250, size=10), textposition='outside')
        fig6.add_vline(x=120, line_dash="dash", line_color=SPOTIFY_BLACK, line_width=2)
        fig6.add_annotation(x=120, y=1.08, yref="paper", text="Pop Standard (120 BPM)", showarrow=False, bgcolor="rgba(255,255,255,0.8)")
        st.plotly_chart(apply_chart_style(fig6), width='stretch')

        # 7. Decision Matrix
        section_header("7. Decision Matrix: Feature Influence")
        corr_f = ['Popularity', 'danceability', 'energy', 'valence', 'tempo', 'duration_ms', 'loudness']
        corr_matrix = df_f[corr_f].corr()
        fig7 = px.imshow(corr_matrix, text_auto='.2f', color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN])
        st.plotly_chart(apply_chart_style(fig7), width='stretch')

    # === TAB 3: 全球版圖 ===
    with tab3:
        section_header("Global Market Reach")
        geo = df_filtered.groupby('Country').agg({
            'Popularity': 'mean',
            'Title': 'count'
        }).reset_index()
        
        fig11 = px.choropleth(geo, 
            locations="Country", 
            locationmode='country names', 
            color="Popularity",
            hover_data=["Title"], # 加入歌曲數量資訊
            color_continuous_scale=['#F5F5F5', SPOTIFY_GREEN, '#106b31'],
            projection="natural earth", # 使用更專業的投影
            title="Global Music Popularity Heatmap"
        )
        
        fig11.update_geos(
            showcoastlines=True, coastlinecolor="LightGrey",
            showland=True, landcolor="White",
            showocean=True, oceancolor="LightBlue",
            showlakes=True, lakecolor="LightBlue"
        )





