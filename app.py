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

# --- 3. Data Engine (Full Cleaning Step A-E) ---
@st.cache_data
def load_data():
    all_files = os.listdir('.')
    target = 'Final database.csv.gz' if 'Final database.csv.gz' in all_files else 'Final database.zip'
    try:
        df = pd.read_csv(target, low_memory=False)
        # [Step A] Popularity 0-100 only
        df = df[(df['Popularity'] >= 0) & (df['Popularity'] <= 100)].copy()
        # [Step B] Filter Album/Single
        df = df[df['Album/Single'].isin(['single', 'album'])]
        # [Step C] Exclude junk genres
        mask_junk = df['Genre'].astype(str).str.lower().isin(['n-a', 'unknown', 'world-music', 'nan'])
        df = df[~mask_junk]
        # [Step D] Capitalize Genres
        df['Genre'] = df['Genre'].astype(str).str.title().replace({'K-Pop': 'K-Pop'})
        # Numeric Conversions
        num_cols = ['Popularity', 'danceability', 'energy', 'tempo', 'Artist_followers', 'duration_ms', 'loudness', 'valence']
        for c in num_cols:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce')
        # Date & Year
        df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
        df['Year'] = df['Release_date'].dt.year
        df['duration_min'] = df['duration_ms'] / 60000
        if 'Explicit' in df.columns:
            df['Explicit_Label'] = df['Explicit'].astype(str).map({'True': 'Explicit 🔞', 'False': 'Clean 🟢', 'true': 'Explicit 🔞', 'false': 'Clean 🟢'}).fillna('Clean 🟢')
        return df.dropna(subset=['Year', 'Popularity', 'Genre', 'Artist', 'tempo'])
    except: return None

df = load_data()

# --- 4. Sidebar Strategy Filters ---
if df is not None:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=50)
        st.title("Admin Strategy Panel")
        year_range = st.slider("📅 Year Selection", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
        search_query = st.text_input("🔍 Search Artist Name", "")
        # Global Filter
        df_f = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
        if search_query:
            df_f = df_f[df_f['Artist'].str.contains(search_query, case=False, na=False)]
        top_n = st.slider("🏆 Top Genres Count", 3, 10, 4)
        if not df_f.empty:
            csv = df_f.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Export Current Data", csv, "spotify_report.csv", "text/csv")
        st.write("Presented by **Selina**")

    # --- 5. Main Content ---
    st.title("🎵 Spotify Intelligence Strategy Dashboard")
    
    # KPI metrics row
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Tracks", f"{len(df_f):,}")
    k2.metric("Avg Pop", f"{df_f['Popularity'].mean():.1f}")
    k3.metric("Superstars", f"{len(df_f[df_f['Artist_followers'] > 1000000]['Artist'].unique())}")
    k4.metric("Avg BPM", f"{df_f['tempo'].mean():.0f}")
    k5.metric("Top Genre", df_f['Genre'].mode()[0] if not df_f.empty else "N/A")

    tab1, tab2, tab3 = st.tabs(["📈 Market Strategy", "🎛️ Audio Lab & AI", "🌍 Global Reach"])

    # === TAB 1: Market Strategy ===
    with tab1:
        # 1. Market Trend
        section_header("1. Market Trend Evolution")
        yearly = df_f.groupby('Year')['Popularity'].mean().reset_index()
        m1, m2 = st.columns([1, 3])
        m1.metric("Peak Popularity Year", int(yearly.loc[yearly['Popularity'].idxmax(), 'Year']))
        m1.write("💡 **Insight:** Analysis of market volatility and streaming adoption.")
        fig1 = px.line(yearly, x='Year', y='Popularity', markers=True, height=500)
        fig1.update_traces(line=dict(color=SPOTIFY_BLACK, width=4), marker=dict(size=12, color=SPOTIFY_GREEN, line=dict(width=2, color='white')))
        st.plotly_chart(apply_chart_style(fig1, "Global Popularity Evolution"), width='stretch')

        # 2. Release Strategy
        section_header("2. Single vs. Album Strategy")
        target_gs = df_f['Genre'].value_counts().head(top_n).index
        df_segment = df_f[df_f['Genre'].isin(target_gs)]
        fig2 = px.box(df_segment, x='Album/Single', y='Popularity', color='Album/Single', facet_col='Genre', facet_col_wrap=4,
                     color_discrete_map={'single': SPOTIFY_GREEN, 'album': SPOTIFY_LIGHT_GREY},
                     category_orders={'Album/Single': ['single', 'album']})
        fig2.update_traces(boxmean=True)
        fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
        st.plotly_chart(apply_chart_style(fig2, "Format Performance by Top Genres"), width='stretch')

        # 3. Content Strategy
        section_header("3. Content Strategy: Explicit vs. Clean")
        st.write("💡 **Insight:** Strategic comparison of commercial performance between content ratings.")
        avg_exp = df_segment.groupby(['Genre', 'Explicit_Label'])['Popularity'].mean().reset_index()
        fig3 = px.bar(avg_exp, x='Genre', y='Popularity', color='Explicit_Label', barmode='group',
                     color_discrete_map={'Clean 🟢': SPOTIFY_GREEN, 'Explicit 🔞': SPOTIFY_BLACK})
        st.plotly_chart(apply_chart_style(fig3, "The Impact of Content Rating on Popularity"), width='stretch')

        # 4. Superstar Effect
        section_header("4. The Superstar Effect: Peak Analysis")
        art_s = df_f.groupby('Artist').agg({'Artist_followers':'mean', 'Popularity':'max', 'Title':'count'}).reset_index()
        art_s = art_s[art_s['Title'] > 2]
        if not art_s.empty:
            corr_val = art_s['Artist_followers'].corr(art_s['Popularity'])
            st.info(f"📊 **Correlation Coefficient: {corr_val:.2f}** (Social Reach vs. Peak Popularity)")
            fig4 = px.scatter(art_s, x='Artist_followers', y='Popularity', hover_name='Artist', log_x=True, 
                             trendline="ols", trendline_color_override=TRENDLINE_RED, opacity=0.5, height=650)
            fig4.update_traces(marker=dict(size=8, color=SPOTIFY_GREEN, line=dict(width=1, color='white')))
            fig4.update_yaxes(range=[-5, 105])
            st.plotly_chart(apply_chart_style(fig4, "Social Leverage vs. Market Ceiling"), width='stretch')

        # 5. Dark Horse Radar
        section_header("5. Talent Scouting: Dark Horse Radar")
        
        # --- 1. Strategic Definitions (English) ---
        st.markdown("""
        ### 🕵️ What is a "Dark Horse" Artist?
        We identify tracks with **'Low Cost, High Impact'** potential using two key metrics:
        * **Micro-Influencer (Low Followers)**: Artists with **< 50,000** followers (emerging talent or independent artists).
        * **Global Hit (High Popularity)**: Popularity score **> 75** (already making a significant impact on global Spotify charts).
        ---
        """)
        
        # --- 2. Data Processing ---
        # Use filtered data and ensure no dirty data
        dark_horses = df_filtered[(df_filtered['Artist_followers'] < 50000) & 
                                  (df_filtered['Popularity'] > 75)].copy()
        
        if not dark_horses.empty:
            # Quadrant Strategy Explanations
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.info("**🔥 Club (Top-Right)**: High energy & high danceability. Perfect for dance floors and parties.")
                st.info("**🍷 Groove (Top-Left)**: Low energy but high danceability. Ideal for chill-out or cafe vibes.")
            with col_info2:
                st.info("**⚡ Power (Bottom-Right)**: High energy but low danceability. Typical for Rock or high-intensity tracks.")
                st.info("**🌙 Ballad (Bottom-Left)**: Low energy and low danceability. Emotional and slow tracks.")
        
            # --- 3. Plotting Logic ---
            fig9 = px.scatter(dark_horses, 
                             x='energy', 
                             y='danceability', 
                             size='Popularity',      
                             color='Popularity',     
                             hover_name='Title',     
                             hover_data=['Artist', 'Artist_followers'],
                             color_continuous_scale=['#A0E0A0', SPOTIFY_GREEN], 
                             size_max=20, 
                             height=700)
        
            # --- 4. Strategic Quadrants ---
            fig9.add_vline(x=0.5, line_width=1, line_dash="dash", line_color="grey")
            fig9.add_hline(y=0.5, line_width=1, line_dash="dash", line_color="grey")
        
            # Labels for the quadrants
            fig9.add_annotation(x=0.9, y=0.9, text="<b>🔥 Club</b>", showarrow=False, font=dict(color="black", size=14))
            fig9.add_annotation(x=0.1, y=0.9, text="<b>🍷 Groove</b>", showarrow=False, font=dict(color="black", size=14))
            fig9.add_annotation(x=0.9, y=0.1, text="<b>⚡ Power</b>", showarrow=False, font=dict(color="black", size=14))
            fig9.add_annotation(x=0.1, y=0.1, text="<b>🌙 Ballad</b>", showarrow=False, font=dict(color="black", size=14))
        
            # --- 5. Top 3 Dark Horse Highlights ---
            top_horses = dark_horses.nlargest(3, 'Popularity')
            for i, row in top_horses.iterrows():
                fig9.add_annotation(
                    x=row['energy'], y=row['danceability'],
                    text=f"<b>TOP: {row['Title'][:15]}</b>",
                    showarrow=True, arrowhead=2, ax=0, ay=-40,
                    font=dict(color=SPOTIFY_BLACK, size=12, family="Arial Black"),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor=SPOTIFY_GREEN,
                    borderwidth=1
                )
        
            # Layout Optimization
            fig9.update_xaxes(range=[-0.05, 1.05], title="Energy")
            fig9.update_yaxes(range=[-0.05, 1.05], title="Danceability")
            
            st.plotly_chart(apply_chart_style(fig9, "Dark Horse Radar: Quadrant Strategy"), width='stretch')
            
            # Detailed Data Table
            with st.expander("📄 View Detailed Dark Horse Artist List"):
                st.dataframe(dark_horses[['Artist', 'Title', 'Popularity', 'Artist_followers', 'Genre']]
                             .sort_values(by='Popularity', ascending=False), width='stretch')
        
        else:
            st.warning("⚠️ No tracks matching the 'Dark Horse' definition found in the current selection. Try adjusting the Year Range.")

    # === TAB 2: Audio Lab & AI ===
    with tab2:
        # 6. Audio Feature Sampling
        section_header("6. Audio Feature Distribution (Sampled)")
        df_sample = df_f.sample(n=min(2000, len(df_f)), random_state=42)
        fig6 = px.scatter(df_sample, x='energy', y='danceability', color='Popularity', color_continuous_scale=['#F0F0F0', SPOTIFY_GREEN], opacity=0.6, height=700)
        fig6.update_traces(marker=dict(size=8, line=dict(width=1, color='DarkSlateGrey')))
        st.plotly_chart(apply_chart_style(fig6, "Energy vs. Danceability Distribution"), width='stretch')

        # 7. Hit Song DNA
        section_header("7. Hit Song DNA: The Sweet Spot")
        hit_songs = df_f[df_f['Popularity'] > 80]
        if not hit_songs.empty:
            fig7 = px.density_contour(hit_songs, x='energy', y='danceability', nbinsx=20, nbinsy=20, height=700)
            fig7.update_traces(contours_coloring="fill", contours_showlabels=True, colorscale='Greens')
            st.plotly_chart(apply_chart_style(fig7, "Concentration of High-Impact Tracks"), width='stretch')

        # 8. Tempo Analysis
        section_header("8. Tempo Analysis: The Sweet Spot")
        def classify_tempo(bpm): return 'Slow (<100)' if bpm < 100 else 'Mainstream (100-140)' if bpm <= 140 else 'Fast (>140)'
        df_f['Tempo_Zone'] = df_f['tempo'].apply(classify_tempo)
        fig8 = px.histogram(df_f, x='tempo', color='Tempo_Zone', text_auto='.2s', height=650,
                           color_discrete_map={'Slow (<100)': SPOTIFY_LIGHT_GREY, 'Mainstream (100-140)': SPOTIFY_GREEN, 'Fast (>140)': SPOTIFY_DARK_GREY},
                           category_orders={'Tempo_Zone': ['Slow (<100)', 'Mainstream (100-140)', 'Fast (>140)']})
        fig8.update_traces(xbins=dict(start=0, end=250, size=10), textposition='outside')
        fig8.add_vline(x=120, line_dash="dash", line_color=SPOTIFY_BLACK, line_width=2)
        fig8.add_annotation(x=120, y=1.08, yref="paper", text="Pop Standard (120 BPM)", showarrow=False, 
                            font=dict(size=14, family="Arial Black"), bgcolor="rgba(255,255,255,0.8)")
        st.plotly_chart(apply_chart_style(fig8, "Tempo Distribution Strategy"), width='stretch')

        # 9. AI Prediction
        section_header("9. AI Hit Potential Predictor")
        c1, c2 = st.columns([1, 2])
        with c1:
            id = st.slider("Danceability", 0.0, 1.0, 0.6); ie = st.slider("Energy", 0.0, 1.0, 0.7); il = st.slider("Loudness", -60, 0, -10); iv = st.slider("Valence", 0.0, 1.0, 0.5)
            st.metric("Predicted Hit Score", f"{(id*30 + ie*25 + (il+60)/60*20 + iv*15 + 10):.1f} / 100")
        with c2:
            radar = go.Figure(data=go.Scatterpolar(r=[id, ie, (il+60)/60, iv, id], theta=['Dance','Energy','Loud','Valence','Dance'], fill='toself', fillcolor='rgba(29, 185, 84, 0.4)', line=dict(color=SPOTIFY_GREEN)))
            radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), height=400)
            st.plotly_chart(radar, width='stretch')

        # 10. Correlation Matrix
        section_header("10. Decision Matrix: Feature Influence")
        corr_f = ['Popularity', 'danceability', 'energy', 'valence', 'tempo', 'duration_ms', 'loudness']
        fig10 = px.imshow(df_f[corr_f].corr(), text_auto='.2f', color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN])
        st.plotly_chart(apply_chart_style(fig10, "Which Features Drive Success?"), width='stretch')

    # === TAB 3: Global Reach ===
    with tab3:
        section_header("11. Global Market Reach")
        geo = df_f.groupby('Country')['Popularity'].mean().reset_index()
        fig11 = px.choropleth(geo, locations="Country", locationmode='country names', color="Popularity", color_continuous_scale=['#F5F5F5', SPOTIFY_GREEN, '#106B31'], height=800)
        fig11.update_layout(geo=dict(showframe=False, projection_type='natural earth'))
        st.plotly_chart(apply_chart_style(fig11, "Global Market Popularity Heatmap"), width='stretch')

