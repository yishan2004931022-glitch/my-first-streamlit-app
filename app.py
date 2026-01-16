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
        st.title("Strategy Panel")
        year_range = st.slider("📅 Year Selection", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
        search_query = st.text_input("🔍 Search Artist Name", "")
        
        # --- KEY: Define df_filtered here to avoid NameError ---
        df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
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
        # --- Q1: Market Evolution ---
        section_header("Market Trend Evolution")
        yearly = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
        
        # ✨ 優化 1：Insight 往左移、變成一行不換行
        # 使用不對稱比例 [0.6, 0.6, 4] 讓前兩個指標佔比小，把第三欄 Insight 往左推
        m1, m2, m3 = st.columns([0.6, 0.6, 4]) 
        m1.metric("Peak Year", int(yearly.loc[yearly['Popularity'].idxmax(), 'Year']))
        m2.metric("Market Avg", f"{yearly['Popularity'].mean():.1f}")
        # white-space: nowrap 確保絕對不換行
        m3.markdown(f"""
            <div style='padding-top:28px; white-space: nowrap; color: #535353; font-size: 18px;'>
                💡 <b>Insight:</b> Analysis of market volatility and streaming adoption trends.
            </div>
            """, unsafe_allow_html=True)
        
        fig1 = px.line(yearly, x='Year', y='Popularity', markers=True, height=500)
        fig1.update_traces(line=dict(color=SPOTIFY_BLACK, width=3), marker=dict(size=8, color=SPOTIFY_GREEN, line=dict(width=2, color='white')))
        st.plotly_chart(apply_chart_style(fig1, "Global Popularity Evolution"), width='stretch')

        # 2. Release Strategy
        section_header("Single vs. Album Strategy")
        target_gs = df_filtered['Genre'].value_counts().head(top_n).index
        df_segment = df_filtered[df_filtered['Genre'].isin(target_gs)]
    
        fig2 = px.box(df_segment, x='Album/Single', y='Popularity', color='Album/Single', 
                     facet_col='Genre', facet_col_wrap=4, 
                     height=900,  # 增加總高度
                     facet_row_spacing=0.1, # 增加行與行之間的間距
                     color_discrete_map={'single': SPOTIFY_GREEN, 'album': SPOTIFY_LIGHT_GREY},
                     category_orders={'Album/Single': ['single', 'album']})
        
        fig2.update_traces(boxmean=True)
        fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
        st.plotly_chart(apply_chart_style(fig2, "Format Strategy Performance"), width='stretch')

        # 3. Content Strategy
        section_header("Content Strategy: Explicit vs. Clean")
        st.markdown("💡 **Insight:** Assessing the commercial performance of lyrics rating.")
        avg_exp = df_segment.groupby(['Genre', 'Explicit_Label'])['Popularity'].mean().reset_index()
        fig3 = px.bar(avg_exp, x='Genre', y='Popularity', color='Explicit_Label', barmode='group',
                     color_discrete_map={'Clean 🟢': SPOTIFY_GREEN, 'Explicit 🔞': SPOTIFY_BLACK})
        st.plotly_chart(apply_chart_style(fig3, "Content Rating vs. Popularity"), width='stretch')

        # 4. Superstar Effect
        section_header("The Superstar Effect: Correlation Analysis")
        art_s = df_filtered.groupby('Artist').agg({'Artist_followers':'mean', 'Popularity':'max', 'Title':'count'}).reset_index()
        art_s = art_s[art_s['Title'] > 2]
        if not art_s.empty:
            corr_val = art_s['Artist_followers'].corr(art_s['Popularity'])
            st.info(f"📊 **Correlation Coefficient: {corr_val:.2f}** (Social Reach vs. Peak Popularity)")
            fig4 = px.scatter(art_s, x='Artist_followers', y='Popularity', hover_name='Artist', log_x=True, 
                             trendline="ols", trendline_color_override=TRENDLINE_RED, opacity=0.5, height=650)
            fig4.update_traces(marker=dict(size=8, color=SPOTIFY_GREEN, line=dict(width=1, color='white')))
            fig4.update_yaxes(range=[-5, 105])
            st.plotly_chart(apply_chart_style(fig4, "Social Leverage vs. Market Ceiling"), width='stretch')

        # 5. Dark Horse Radar (Integrated your specific code)
        section_header("Talent Scouting: Dark Horse Radar")
        st.markdown("""
        ### 🕵️ What is a "Dark Horse" Artist?
        Tracks with **'Low Cost, High Impact'** potential:
        * **Micro-Influencer**: Followers **< 50,000**.
        * **Global Hit**: Popularity score **> 75**.
        """)
        dark_horses = df_filtered[(df_filtered['Artist_followers'] < 50000) & (df_filtered['Popularity'] > 75)].copy()

        if not dark_horses.empty:
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.info("**🔥Club (Top-Right)**: High energy & danceability. Perfect for parties.")
                st.info("**🍷Groove (Top-Left)**: Low energy but high danceability. Ideal for chill vibes.")
            with col_info2:
                st.info("**⚡Power (Bottom-Right)**: High energy but low danceability. Typical for Rock.")
                st.info("**🌙Ballad (Bottom-Left)**: Low energy and danceability. Emotional and slow.")

            fig9 = px.scatter(dark_horses, x='energy', y='danceability', size='Popularity', color='Popularity',     
                             hover_name='Title', hover_data=['Artist', 'Artist_followers'],
                             color_continuous_scale=['#A0E0A0', SPOTIFY_GREEN], size_max=20, height=700)
            
            fig9.add_vline(x=0.5, line_width=1, line_dash="dash", line_color="grey")
            fig9.add_hline(y=0.5, line_width=1, line_dash="dash", line_color="grey")

            fig9.add_annotation(x=0.9, y=0.9, text="<b>🔥Club</b>", showarrow=False, font=dict(size=14))
            fig9.add_annotation(x=0.1, y=0.9, text="<b>🍷Groove</b>", showarrow=False, font=dict(size=14))
            fig9.add_annotation(x=0.9, y=0.1, text="<b>⚡Power</b>", showarrow=False, font=dict(size=14))
            fig9.add_annotation(x=0.1, y=0.1, text="<b>🌙Ballad</b>", showarrow=False, font=dict(size=14))

            top_h = dark_horses.nlargest(3, 'Popularity')
            for i, row in top_h.iterrows():
                fig9.add_annotation(x=row['energy'], y=row['danceability'], text=f"<b>TOP: {row['Title'][:15]}</b>",
                                   showarrow=True, arrowhead=2, ax=0, ay=-40, font=dict(color=SPOTIFY_BLACK, size=12, family="Arial Black"),
                                   bgcolor="rgba(255,255,255,0.8)", bordercolor=SPOTIFY_GREEN, borderwidth=1)

            fig9.update_xaxes(range=[-0.05, 1.05], title="Energy")
            fig9.update_yaxes(range=[-0.05, 1.05], title="Danceability")
            st.plotly_chart(apply_chart_style(fig9, "Dark Horse Radar: Quadrant Strategy"), width='stretch')
        else:
            st.warning("⚠️ No tracks matching the 'Dark Horse' definition found.")

    # === TAB 2: Audio Lab & AI ===
    with tab2:
        # --- Q6: Audio Feature Diversity (散佈圖) ---
        section_header("Audio Feature Diversity: Market Exploration")
        
        # 抽樣以維持效能
        df_sample = df_filtered.sample(n=min(2000, len(df_filtered)), random_state=42)
        
        # 計算相關係數 (Energy vs. Popularity) 作為指標
        corr_val = df_sample['energy'].corr(df_sample['Popularity'])
        
        # ✨ 優化排版：傳遞「多樣性」價值
        f6_m1, f6_m2, f6_m3 = st.columns([0.6, 0.6, 4])
        f6_m1.metric("Sample", f"{len(df_sample)}")
        f6_m2.metric("Corr", f"{corr_val:.2f}")
        f6_m3.markdown(f"""
            <div style='padding-top:28px; white-space: nowrap; color: #535353; font-size: 16px;'>
                💡 <b>Diversity Insight:</b> While high-vibe tracks are popular, hits exist across the entire spectrum, showing market openness to various styles.
            </div>
            """, unsafe_allow_html=True)
    
        fig6 = px.scatter(df_sample, x='energy', y='danceability', color='Popularity', 
                         color_continuous_scale=['#F0F0F0', SPOTIFY_GREEN], opacity=0.6, height=700)
        fig6.update_traces(marker=dict(size=9, line=dict(width=1, color='white')))
        
        st.plotly_chart(apply_chart_style(fig6, "Audio Feature Distribution: The Broad Market"), width='stretch')
    
        # --- Q7: Hit Song DNA (密度圖) ---
        section_header("Hit Song DNA: The Strategic Blueprint")
        
        # 只針對 Popularity > 80 的歌曲進行建模
        hit_songs = df_filtered[df_filtered['Popularity'] > 80]
        
        if not hit_songs.empty:
            # 計算甜點區集中度 (落在 0.6-0.8 區間的比例)
            in_sweet_spot = hit_songs[(hit_songs['energy'] > 0.6) & (hit_songs['danceability'] > 0.6)]
            concentration = (len(in_sweet_spot) / len(hit_songs)) * 100
            
            # ✨ 優化排版：傳遞「精準成功」價值
            f7_m1, f7_m2 = st.columns([1, 4])
            f7_m1.metric("Hit Density", f"{concentration:.1f}%")
            f7_m2.markdown(f"""
                <div style='padding-top:28px; white-space: nowrap; color: #535353; font-size: 16px;'>
                    🎯 <b>Precision Strategy:</b> For Pop > 80, the 'Safe Zone' is statistically narrowed to the 0.6-0.8 window. This is the blueprint for mass success.
                </div>
                """, unsafe_allow_html=True)
    
            fig7 = px.density_contour(hit_songs, x='energy', y='danceability', nbinsx=20, nbinsy=20, height=700)
            # 優化密度圖視覺：使用填充色塊增加「重量感」
            fig7.update_traces(contours_coloring="fill", contours_showlabels=True, colorscale='Greens', opacity=0.8)
            
            st.plotly_chart(apply_chart_style(fig7, "Hit DNA: Statistically Probable Success Zone"), width='stretch')
        else:
            st.warning("Not enough high-popularity tracks (Pop > 80) to generate a DNA profile for this selection.")

        # 8. Tempo Analysis (The 120BPM logic you optimized)
        section_header("Tempo Analysis: The Sweet Spot")
        def classify_tempo(bpm): return 'Slow (<100)' if bpm < 100 else 'Mainstream (100-140)' if bpm <= 140 else 'Fast (>140)'
        df_filtered['Tempo_Zone'] = df_filtered['tempo'].apply(classify_tempo)
        fig8 = px.histogram(df_filtered, x='tempo', color='Tempo_Zone', text_auto='.2s', height=650,
                           color_discrete_map={'Slow (<100)': SPOTIFY_LIGHT_GREY, 'Mainstream (100-140)': SPOTIFY_GREEN, 'Fast (>140)': SPOTIFY_DARK_GREY},
                           category_orders={'Tempo_Zone': ['Slow (<100)', 'Mainstream (100-140)', 'Fast (>140)']})
        fig8.update_traces(xbins=dict(start=0, end=250, size=10), textposition='outside')
        fig8.add_vline(x=120, line_dash="dash", line_color=SPOTIFY_BLACK, line_width=2)
        fig8.add_annotation(x=120, y=1.08, yref="paper", text="Pop Standard (120 BPM)", showarrow=False, 
                            font=dict(size=14, family="Arial Black"), bgcolor="rgba(255,255,255,0.8)")
        st.plotly_chart(apply_chart_style(fig8, "Tempo Distribution Strategy"), width='stretch')

        # 9. AI Prediction (Radar)
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
        
        # 1. 數據計算
        geo = df_filtered.groupby('Country')['Popularity'].mean().reset_index()
        
        # 2. 抓取 Top Market (修正邏輯，確保抓到完整名稱)
        if not geo.empty:
            top_country_row = geo.loc[geo['Popularity'].idxmax()]
            top_country_name = top_country_row['Country']
            top_country_pop = top_country_row['Popularity']
        else:
            top_country_name = "N/A"
            top_country_pop = 0

        # 3. 顯示指標與 Insight
        # ✨ 優化比例：[1.2, 0.8, 3.5] 加寬第一欄以顯示完整國家名 (如 Norway, Netherlands)
        g1, g2, g3 = st.columns([1.2, 0.8, 3.5])
        
        # 顯示完整國家名稱
        g1.metric("Top Market 🏆", top_country_name)
        g2.metric("Avg Pop", f"{top_country_pop:.1f}")
        
        # 一行 Insight
        g3.markdown(f"""
            <div style='padding-top:28px; white-space: nowrap; color: #535353; font-size: 16px;'>
                💡 <b>Global Insight:</b> High-consumption clusters identified in Northern Europe & North America. 
                Leading Market: <b>{top_country_name}</b>.
            </div>
            """, unsafe_allow_html=True)

        # 4. 繪製地圖 (保持你之前的優化樣式)
        fig10 = px.choropleth(
            geo, 
            locations="Country", 
            locationmode='country names', 
            color="Popularity",
            hover_name="Country",
            color_continuous_scale=['#F0FDF4', SPOTIFY_GREEN, '#14532D'], 
            height=700
        )

        fig10.update_layout(
            margin={"r":0, "t":0, "l":0, "b":0},
            geo=dict(
                showframe=False,
                showcoastlines=False,
                projection_type='natural earth',
                showocean=True, oceancolor='#F8FAFC',
                showland=True, landcolor='#FFFFFF',
            ),
            coloraxis_colorbar=dict(title="Popularity", thickness=15, len=0.6)
        )
        
        st.plotly_chart(fig10, width='stretch')


