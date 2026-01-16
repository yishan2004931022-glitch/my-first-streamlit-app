import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="Spotify Producer Strategy Dashboard",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 視覺風格與自定義函數 ---
SPOTIFY_GREEN = "#1DB954"
SPOTIFY_BLACK = "#191414"
SPOTIFY_LIGHT_GREY = "#B3B3B3"
SPOTIFY_DARK_GREY = "#535353"
TRENDLINE_RED = "#FF4B4B"

# ✨ 帶有左側綠色裝飾條的大標題
def section_header(text):
    st.markdown(f"""
        <div style='border-left: 10px solid {SPOTIFY_GREEN}; padding-left: 20px; margin-top: 50px; margin-bottom: 10px;'>
            <h2 style='color: #333333; font-size: 34px; font-weight: 800; font-family: "Arial Black"; margin: 0;'>
            {text}
            </h2>
        </div>
        """, unsafe_allow_html=True)

# ✨ 2026 視覺標準圖表樣式
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

# --- 3. 資料讀取與強力清洗 (整合 Step A-E) ---
@st.cache_data
def load_data():
    all_files = os.listdir('.')
    target = 'Final database.csv.gz' if 'Final database.csv.gz' in all_files else 'Final database.zip'
    if target not in all_files:
        st.error("❌ 資料檔遺失，請檢查 GitHub 儲存庫。")
        return None
    try:
        df = pd.read_csv(target, low_memory=False)
        # [Step A] 剔除髒數據 (Popularity 0-100)
        df = df[(df['Popularity'] >= 0) & (df['Popularity'] <= 100)].copy()
        # [Step B] 過濾 Album/Single
        df = df[df['Album/Single'].isin(['single', 'album'])]
        # [Step C] 排除垃圾流派
        mask_junk = df['Genre'].astype(str).str.lower().isin(['n-a', 'unknown', 'world-music', 'nan'])
        df = df[~mask_junk]
        # [Step D] 流派名稱標準化
        df['Genre'] = df['Genre'].astype(str).str.title().replace({'K-Pop': 'K-Pop', 'K-pop': 'K-Pop'})
        
        # 數值與日期轉換
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
        st.error(f"❌ 讀取錯誤: {e}"); return None

df = load_data()

# --- 4. 側邊欄控制與過濾邏輯 ---
if df is not None:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=50)
        st.title("Admin Strategy Panel")
        year_range = st.slider("📅 Year Range", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
        search_query = st.text_input("🔍 Search Artist Name", "")
        
        # 動態過濾資料 (供後續所有題目使用)
        df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
        if search_query:
            df_filtered = df_filtered[df_filtered['Artist'].str.contains(search_query, case=False, na=False)]
        
        top_n = st.slider("🏆 Top Genres Count", 3, 10, 4)
        
        st.markdown("---")
        # 📥 修正後的 CSV 下載按鈕 (確保下載的是過濾後的最新資料)
        if not df_filtered.empty:
            csv_export = df_filtered.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Export Current Data (.csv)",
                data=csv_export,
                file_name=f"spotify_analysis_{year_range[0]}_{year_range[1]}.csv",
                mime="text/csv"
            )
        st.write("Created by **Selina**")

    # --- 5. 主頁面內容 ---
    st.title("🎵 Spotify Intelligence Strategy Dashboard")

    # 📊 KPI 商業指標卡
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Tracks", f"{len(df_filtered):,}")
    m2.metric("Avg Popularity", f"{df_filtered['Popularity'].mean():.1f}")
    m3.metric("Superstars", f"{len(df_filtered[df_filtered['Artist_followers'] > 1000000]['Artist'].unique())}")
    m4.metric("Avg Tempo", f"{df_filtered['tempo'].mean():.0f} BPM")
    m5.metric("Top Genre", df_filtered['Genre'].mode()[0] if not df_filtered.empty else "N/A")

    tab1, tab2, tab3 = st.tabs(["📈 Market Strategy", "🎛️ Audio Lab & AI", "🌍 Global Map"])

    # === TAB 1: 市場策略 (1-5 題) ===
    with tab1:
        # 1. 市場趨勢
        section_header("Market Trend Evolution")
        yearly = df_filtered.groupby('Year')['Popularity'].mean().reset_index()
        fig1 = px.line(yearly, x='Year', y='Popularity', markers=True, height=500)
        fig1.update_traces(line=dict(color=SPOTIFY_BLACK, width=4), marker=dict(size=10, color=SPOTIFY_GREEN))
        st.plotly_chart(apply_chart_style(fig1, "Global Popularity Evolution"), width='stretch')

        # 2. 發行策略 (箱型圖 + 平均值虛線)
        section_header("Single vs. Album Strategy")
        target_gs = df_filtered['Genre'].value_counts().head(top_n).index
        df_segment = df_filtered[df_filtered['Genre'].isin(target_gs)]
        fig2 = px.box(df_segment, x='Album/Single', y='Popularity', color='Album/Single', 
                     facet_col='Genre', facet_col_wrap=4, height=700, 
                     color_discrete_map={'single': SPOTIFY_GREEN, 'album': SPOTIFY_LIGHT_GREY},
                     category_orders={'Album/Single': ['single', 'album']})
        fig2.update_traces(boxmean=True)
        fig2.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
        st.plotly_chart(apply_chart_style(fig2, "Format Strategy Performance"), width='stretch')

        # 3. 內容分級策略
        # === Replace the Content Strategy section in your Tab 1 with this code ===

        section_header("3. Content Strategy (Explicit Lyrics)")
        
        # --- 1. Strategic Insights (Professional English) ---
        # Add high-level interpretations for stakeholders/professors
        st.markdown("""
        ### 🚫 Does Explicit Content Drive Popularity?
        This analysis compares the average popularity of **Clean 🟢** vs. **Explicit 🔞** tracks across top genres to determine if lyric content impacts commercial success.
        
        * **The Genre Factor**: The impact of explicit lyrics is highly **genre-dependent**. While explicit versions show a slight advantage in genres like **Hip Hop** and **Latin**, 'Clean' tracks perform equally well or better in mainstream **Pop**.
        * **Strategic Implication**: Explicit content is not a universal driver of popularity. The decision to use it should align with audience expectations within specific musical cultures rather than being a default strategy for attention.
        ---
        """)
        
        # --- 2. Data Preparation ---
        # We use the 'df_segment' data which is already filtered to your Top N Genres in previous steps.
        # Group by Genre and Label to find average popularity.
        avg_exp = df_segment.groupby(['Genre', 'Explicit_Label'])['Popularity'].mean().reset_index()
        
        # --- 3. Plotting Logic (Spotify Theme & Grouped Bars) ---
        fig3 = px.bar(avg_exp, 
                     x='Genre', 
                     y='Popularity', 
                     color='Explicit_Label', 
                     barmode='group',  # ✨ Crucial: Places bars side-by-side for comparison
                     # Map colors to match the Spotify aesthetic in your image
                     color_discrete_map={'Clean 🟢': SPOTIFY_GREEN, 'Explicit 🔞': SPOTIFY_BLACK},
                     height=600)
        
        # --- 4. Chart Optimization (English & Layout) ---
        fig3.update_layout(
            xaxis_title="", # Remove unnecessary axis label
            yaxis_title="Average Popularity Score",
            legend_title="Content Rating",
            # Move legend to the top for a cleaner look
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Apply the standard 2026 styling wrapper and render
        st.plotly_chart(apply_chart_style(fig3, "Explicit vs. Clean Popularity by Genre"), width='stretch')

        # 4. 巨星效應 (統計強化版)
        section_header("4. Market Power: The Superstar Effect")
        
        # --- 1. 數據計算 ---
        # 抓取每個藝人的最高人氣作品
        artist_stats = df_filtered.groupby('Artist').agg({
            'Artist_followers': 'mean',
            'Popularity': 'max',
            'Title': 'count'
        }).reset_index()
        
        # 排除資料量過少的樣本
        artist_stats = artist_stats[artist_stats['Title'] > 2]
        
        if len(artist_stats) > 2:
            # 計算統計指標
            corr_value = artist_stats['Artist_followers'].corr(artist_stats['Popularity'])
            
            # --- 2. 關鍵指標列 (放在圖表上方，不擋圖) ---
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Correlation Coefficient", f"{corr_value:.2f}", help="Close to 1 means high impact of followers on hits.")
            with col_stat2:
                st.metric("Analysis Sample", f"{len(artist_stats)} Artists")
            with col_stat3:
                st.write("💡 **Insight:** Low correlation suggests content quality drives hits more than follower count.")
        
            # --- 3. 繪圖邏輯 (極簡 Spotify 風) ---
            fig4 = px.scatter(artist_stats, 
                             x='Artist_followers', 
                             y='Popularity', 
                             hover_name='Artist',
                             log_x=True,               # 粉絲數分佈廣，必用 Log 軸
                             trendline="ols", 
                             trendline_color_override="#333333", # 黑色趨勢線，更顯眼
                             opacity=0.4,              # 增加透明度，重疊處顏色變深，更容易看分佈
                             height=600)
            
            # 設定 Spotify 綠色點點，白色邊框增加質感
            fig4.update_traces(marker=dict(
                size=9, 
                color=SPOTIFY_GREEN, 
                line=dict(width=1, color='white')
            ))
        
            # 優化座標軸文字
            fig4.update_layout(
                xaxis_title="Social Reach (Total Followers)",
                yaxis_title="Peak Popularity Score",
                template="simple_white",
                margin=dict(t=20, b=40) # 縮小邊距讓圖更大
            )
            
            # 使用 2026 最新語法顯示圖表
            st.plotly_chart(fig4, width='stretch')
            
        else:
            st.info("Searching for more data points to calculate correlation...")

        # 5. 黑馬雷達 (象限分析)
        # === Replace the Dark Horse section in your Tab 1 with this code ===

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

    # === TAB 2: 音樂實驗室 & AI (6-10 題) ===
    with tab2:
        # 6. 音色分佈 (隨機抽樣版)
        section_header("6. Audio Feature Distribution")
        df_sample = df_filtered.sample(n=min(2000, len(df_filtered)), random_state=42) 
        fig_scatter = px.scatter(df_sample, x='energy', y='danceability', color='Popularity', 
                                color_continuous_scale=['#F0F0F0', SPOTIFY_GREEN], opacity=0.6, height=700)
        fig_scatter.update_traces(marker=dict(size=8, line=dict(width=1, color='DarkSlateGrey')))
        st.plotly_chart(apply_chart_style(fig_scatter, "Feature Distribution: Energy vs. Danceability"), width='stretch')

        # 7. 爆紅基因 (2D 密度圖)
        section_header("Hit Song DNA: The Sweet Spot")
        hit_songs = df_filtered[df_filtered['Popularity'] > 80]
        if not hit_songs.empty:
            fig_density = px.density_contour(hit_songs, x='energy', y='danceability', nbinsx=20, nbinsy=20, height=700)
            fig_density.update_traces(contours_coloring="fill", contours_showlabels=True, colorscale='Greens')
            st.plotly_chart(apply_chart_style(fig_density, "Hit Song DNA: Hotspot Analysis"), width='stretch')

        # 8. 節奏分析 (BPM 優化版)
        section_header("Tempo Analysis: BPM Distribution")
        def classify_tempo(bpm): return 'Slow (<100)' if bpm < 100 else 'Mainstream (100-140)' if bpm <= 140 else 'Fast (>140)'
        df_filtered['Tempo_Zone'] = df_filtered['tempo'].apply(classify_tempo)
        fig_tempo = px.histogram(df_filtered, x='tempo', color='Tempo_Zone', text_auto='.2s', 
                                color_discrete_map={'Slow (<100)': SPOTIFY_LIGHT_GREY, 'Mainstream (100-140)': SPOTIFY_GREEN, 'Fast (>140)': SPOTIFY_DARK_GREY},
                                category_orders={'Tempo_Zone': ['Slow (<100)', 'Mainstream (100-140)', 'Fast (>140)']}, height=650)
        fig_tempo.update_traces(xbins=dict(start=0, end=250, size=10), textposition='outside')
        fig_tempo.add_vline(x=120, line_width=2, line_dash="dash", line_color='#333333')
        fig_tempo.add_annotation(x=120, y=1.08, yref="paper", text="Pop Standard (120 BPM)", showarrow=False, font=dict(size=14, family="Arial Black"), bgcolor="rgba(255,255,255,0.8)")
        st.plotly_chart(apply_chart_style(fig_tempo, "BPM Distribution & Sweet Spot"), width='stretch')

        # 9. 影響力權重矩陣
        section_header("Decision Matrix: Audio Influence Power")
        corr_f = ['Popularity', 'danceability', 'energy', 'valence', 'tempo', 'duration_ms', 'loudness']
        corr_m = df_filtered[corr_f].corr()
        st.plotly_chart(apply_chart_style(px.imshow(corr_m, text_auto='.2f', color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN], height=600), "Correlation Matrix: Feature Influence"), width='stretch')

        # 10. AI 預測器
        section_header("AI Hit Potential Predictor")
        ca1, ca2 = st.columns([1, 2])
        with ca1:
            id = st.slider("Danceability", 0.0, 1.0, 0.6); ie = st.slider("Energy", 0.0, 1.0, 0.7); il = st.slider("Loudness", -60, 0, -10); iv = st.slider("Valence", 0.0, 1.0, 0.5)
            st.metric("Predicted Hit Score", f"{(id*30 + ie*25 + (il+60)/60*20 + iv*10 + 15):.1f}")
        with ca2:
            radar = go.Figure(data=go.Scatterpolar(r=[id, ie, (il+60)/60, iv, id], theta=['Dance','Energy','Loud','Happy','Dance'], fill='toself', fillcolor='rgba(29, 185, 84, 0.4)', line=dict(color=SPOTIFY_GREEN)))
            radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), height=400)
            st.plotly_chart(radar, width='stretch')

    # === TAB 3: 全球版圖 ===
    with tab3:
        section_header("Global Market Reach")
        geo = df_filtered.groupby('Country')['Popularity'].mean().reset_index()
        fig11 = px.choropleth(geo, locations="Country", locationmode='country names', color="Popularity", color_continuous_scale=['#F5F5F5', SPOTIFY_GREEN, '#106b31'], height=800)
        st.plotly_chart(apply_chart_style(fig11, "Territory Performance Heatmap"), width='stretch')





