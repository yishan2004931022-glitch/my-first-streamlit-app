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

# UI Helper: Section Headers with Green Sidebar
def section_header(text):
    st.markdown(f"""
        <div style='border-left: 10px solid {SPOTIFY_GREEN}; padding-left: 20px; margin-top: 50px; margin-bottom: 10px;'>
            <h2 style='color: #333333; font-size: 34px; font-weight: 800; font-family: "Arial Black"; margin: 0;'>
            {text}
            </h2>
        </div>
        """, unsafe_allow_html=True)

# UI Helper: Standard Plotly Styling
def apply_chart_style(fig, title_text):
    fig.update_layout(
        template="simple_white",
        title=dict(
            text=f"<b>{title_text}</b>",
            font=dict(color=SPOTIFY_GREEN, size=24, family="Arial Black"),
            x=0, y=0.98
        ),
        font=dict(family="Arial", size=14, color="black"),
        margin=dict(t=120, b=50, l=50, r=50)
    )
    return fig

# --- 3. Data Engine (Full Cleaning Step A-E) ---
@st.cache_data
def load_data():
    all_files = os.listdir('.')
    target = 'Final database.csv.gz' if 'Final database.csv.gz' in all_files else 'Final database.zip'
    if target not in all_files:
        st.error("❌ Data file missing.")
        return None
    try:
        df = pd.read_csv(target, low_memory=False)
        # [Step A] Remove dirty data (0-100 only)
        df = df[(df['Popularity'] >= 0) & (df['Popularity'] <= 100)].copy()
        # [Step B] Filter Album/Single
        df = df[df['Album/Single'].isin(['single', 'album'])]
        # [Step C] Exclude junk genres
        mask_junk = df['Genre'].astype(str).str.lower().isin(['n-a', 'unknown', 'world-music', 'nan'])
        df = df[~mask_junk]
        # [Step D] Capitalize Genres (e.g., Pop, Hip-Hop)
        df['Genre'] = df['Genre'].astype(str).str.title().replace({'K-Pop': 'K-Pop'})
        
        # Numeric & Date Conversions
        numeric_cols = ['Popularity', 'danceability', 'energy', 'tempo', 'duration_ms', 'Artist_followers', 'loudness', 'valence']
        for col in numeric_cols:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
        df['Year'] = df['Release_date'].dt.year
        df['duration_min'] = df['duration_ms'] / 60000
        
        if 'Explicit' in df.columns:
            df['Explicit_Label'] = df['Explicit'].astype(str).map({'True': 'Explicit 🔞', 'False': 'Clean 🟢', 'true': 'Explicit 🔞', 'false': 'Clean 🟢'}).fillna('Clean 🟢')
            
        return df.dropna(subset=['Year', 'Popularity', 'Genre', 'Artist', 'tempo'])
    except Exception as e:
        st.error(f"❌ Error: {e}"); return None

df = load_data()

# --- 4. Sidebar & Filters ---
if df is not None:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=50)
        st.title("Strategy Panel")
        year_range = st.slider("📅 Year Range", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
        search_query = st.text_input("🔍 Search Artist", "")
        df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
        if search_query:
            df_filtered = df_filtered[df_filtered['Artist'].str.contains(search_query, case=False, na=False)]
        top_n = st.slider("🏆 Top Genres Depth", 3, 10, 4)
        
        if not df_filtered.empty:
            csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Export Current Data", csv, "report.csv", "text/csv")
        st.write("Presented by **Selina**")

    # --- 5. Main Content ---
    st.title("🎵 Spotify Intelligence Strategy Dashboard")
    
    # KPI Row
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Tracks", f"{len(df_filtered):,}")
    m2.metric("Avg Pop", f"{df_filtered['Popularity'].mean():.1f}")
    m3.metric("Superstars", f"{len(df_filtered[df_filtered['Artist_followers'] > 1000000]['Artist'].unique())}")
    m4.metric("Avg Tempo", f"{df_filtered['tempo'].mean():.0f} BPM")
    m5.metric("Top Genre", df_filtered['Genre'].mode()[0] if not df_filtered.empty else "N/A")

    tab1, tab2, tab3 = st.tabs(["📈 Market Strategy", "🎛️ Audio Lab & AI", "🌍 Global Reach"])

    # === TAB 1: Market Strategy ===
    with tab1:
        # Q1: Market Trend
        section_header("1. Market Trend Evolution")
        yearly = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
        fig1 = px.line(yearly, x='Year', y='Popularity', markers=True, height=500)
        fig1.update_traces(line=dict(color=SPOTIFY_BLACK, width=4), marker=dict(size=10, color=SPOTIFY_GREEN, line=dict(width=2, color="white")))
        st.plotly_chart(apply_chart_style(fig1, "Global Popularity Evolution"), width='stretch')

        # Q2: Release Strategy
        section_header("2. Single vs. Album Strategy")
        target_gs = df_filtered['Genre'].value_counts().head(top_n).index
        df_segment = df_filtered[df_filtered['Genre'].isin(target_gs)]
        fig2 = px.box(df_segment, x='Album/Single', y='Popularity', color='Album/Single', 
                     facet_col='Genre', facet_col_wrap=4, height=700, 
                     color_discrete_map={'single': SPOTIFY_GREEN, 'album': SPOTIFY_LIGHT_GREY},
                     category_orders={'Album/Single': ['single', 'album']})
        fig2.update_traces(boxmean=True)
        fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
        st.plotly_chart(apply_chart_style(fig2, "Format Strategy Performance"), width='stretch')

        # Q3: Content Strategy
        section_header("3. Content Strategy: Explicit vs. Clean")
        avg_exp = df_segment.groupby(['Genre', 'Explicit_Label'])['Popularity'].mean().reset_index()
        fig3 = px.bar(avg_exp, x='Genre', y='Popularity', color='Explicit_Label', barmode='group', 
                     color_discrete_map={'Clean 🟢': SPOTIFY_GREEN, 'Explicit 🔞': SPOTIFY_BLACK}, height=550)
        st.plotly_chart(apply_chart_style(fig3, "Explicit vs. Clean Popularity Analysis"), width='stretch')

        # Q4: Superstar Effect (OLS Trendline & Corr)
        section_header("4. The Superstar Effect: Correlation Analysis")
        art_s = df_filtered.groupby('Artist').agg({'Artist_followers':'mean', 'Popularity':'max', 'Title':'count'}).reset_index()
        art_s = art_s[art_s['Title'] > 2]
        if not art_s.empty:
            corr_val = art_s['Artist_followers'].corr(art_s['Popularity'])
            st.info(f"📊 **Correlation Coefficient: {corr_val:.2f}** (Followers vs. Peak Popularity)")
            fig4 = px.scatter(art_s, x='Artist_followers', y='Popularity', hover_name='Artist', log_x=True, 
                             trendline="ols", trendline_color_override=TRENDLINE_RED, opacity=0.5, height=650)
            fig4.update_traces(marker=dict(size=8, color=SPOTIFY_GREEN, line=dict(width=1, color='white')))
            fig4.update_yaxes(range=[-5, 105])
            st.plotly_chart(apply_chart_style(fig4, "Social Reach vs. Peak Popularity"), width='stretch')

        # Q5: Dark Horse Radar (Quadrants & Definitions)
        section_header("5. Talent Scouting: Dark Horse Radar")
        st.markdown("### 🕵️ What is a 'Dark Horse'? (Followers < 50k & Popularity > 75)")
        dark = df_filtered[(df_filtered['Artist_followers'] < 50000) & (df_filtered['Popularity'] > 75)].copy()
        if not dark.empty:
            fig5 = px.scatter(dark, x='energy', y='danceability', size='Popularity', color='Popularity', 
                             hover_name='Title', color_continuous_scale=['#A0E0A0', SPOTIFY_GREEN], height=750)
            fig5.add_vline(x=0.5, line_dash="dash", line_color="grey")
            fig5.add_hline(y=0.5, line_dash="dash", line_color="grey")
            fig5.add_annotation(x=0.9, y=0.9, text="🔥 Club", showarrow=False, font=dict(size=14, family="Arial Black"))
            fig5.add_annotation(x=0.1, y=0.1, text="🌙 Ballad", showarrow=False, font=dict(size=14, family="Arial Black"))
            
            # Top 3 Highlights
            top_h = dark.nlargest(3, 'Popularity')
            for i, row in top_h.iterrows():
                fig5.add_annotation(x=row['energy'], y=row['danceability'], text=f"<b>{row['Title'][:15]}</b>", 
                                   showarrow=True, arrowhead=1, ax=0, ay=-40, font=dict(size=11), bgcolor="rgba(255,255,255,0.7)")
            st.plotly_chart(apply_chart_style(fig5, "Dark Horse Quadrant Analysis"), width='stretch')

    # === TAB 2: Audio Lab & AI ===
    with tab2:
        # Q6: Tempo Analysis (120 BPM High Annotation)
        section_header("6. Tempo Analysis: The Sweet Spot")
        def classify_tempo(bpm): return 'Slow (<100)' if bpm < 100 else 'Mainstream (100-140)' if bpm <= 140 else 'Fast (>140)'
        df_filtered['Tempo_Zone'] = df_filtered['tempo'].apply(classify_tempo)
        fig6 = px.histogram(df_filtered, x='tempo', color='Tempo_Zone', text_auto='.2s', height=650,
                           color_discrete_map={'Slow (<100)': SPOTIFY_LIGHT_GREY, 'Mainstream (100-140)': SPOTIFY_GREEN, 'Fast (>140)': SPOTIFY_DARK_GREY},
                           category_orders={'Tempo_Zone': ['Slow (<100)', 'Mainstream (100-140)', 'Fast (>140)']})
        fig6.update_traces(xbins=dict(start=0, end=250, size=10), textposition='outside')
        fig6.add_vline(x=120, line_dash="dash", line_color=SPOTIFY_BLACK, line_width=2)
        fig6.add_annotation(x=120, y=1.08, yref="paper", text="Pop Standard (120 BPM)", showarrow=False, 
                            font=dict(size=14, family="Arial Black"), bgcolor="rgba(255,255,255,0.8)")
        st.plotly_chart(apply_chart_style(fig6, "BPM Distribution Analysis"), width='stretch')

        # Q7: AI Hit Potential Predictor
        section_header("7. AI Hit Potential Predictor")
        c_a1, c_a2 = st.columns([1, 2])
        with c_a1:
            id = st.slider("Danceability", 0.0, 1.0, 0.6); ie = st.slider("Energy", 0.0, 1.0, 0.7); il = st.slider("Loudness", -60, 0, -10); iv = st.slider("Valence", 0.0, 1.0, 0.5)
            score = (id*30 + ie*25 + (il+60)/60*20 + iv*15 + 10)
            st.metric("Predicted Hit Score", f"{score:.1f} / 100")
        with c_a2:
            radar = go.Figure(data=go.Scatterpolar(r=[id, ie, (il+60)/60, iv, id], theta=['Dance','Energy','Loud','Happy','Dance'], fill='toself', fillcolor='rgba(29, 185, 84, 0.4)', line=dict(color=SPOTIFY_GREEN)))
            radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), height=400)
            st.plotly_chart(radar, width='stretch')

        # Q8: Correlation Matrix
        section_header("8. Feature Influence Matrix")
        corr_f = ['Popularity', 'danceability', 'energy', 'valence', 'tempo', 'duration_ms', 'loudness']
        st.plotly_chart(apply_chart_style(px.imshow(df_filtered[corr_f].corr(), text_auto='.2f', color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN]), "Correlation Matrix"), width='stretch')

    # === TAB 3: Global Reach ===
    with tab3:
        section_header("9. Global Market Reach")
        geo = df_filtered.groupby('Country')['Popularity'].mean().reset_index()
        fig9 = px.choropleth(geo, locations="Country", locationmode='country names', color="Popularity", color_continuous_scale=['#F5F5F5', SPOTIFY_GREEN, '#106b31'], height=800)
        st.plotly_chart(apply_chart_style(fig9, "Average Popularity by Territory"), width='stretch')
