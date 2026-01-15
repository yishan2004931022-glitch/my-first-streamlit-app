import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="Spotify Producer Dashboard",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 視覺風格定義 ---
SPOTIFY_GREEN = "#1DB954"
SPOTIFY_BLACK = "#191414"

# ✨ 自定義標題函數
def section_header(text):
    st.markdown(f"<h2 style='color: {SPOTIFY_GREEN}; font-size: 28px; font-weight: 700; margin-top: 30px;'>{text}</h2>", unsafe_allow_html=True)

# ✨ 回歸原本的圖表樣式 (移除強制的加粗與大號字體)
def apply_original_style(fig, title_text):
    fig.update_layout(
        template="simple_white",
        title=dict(
            text=title_text,
            font=dict(color=SPOTIFY_GREEN, size=22) # 回到標準大小
        ),
        font=dict(size=12), # 回到標準字體大小，不強制加粗
        margin=dict(t=80, b=50),
    )
    return fig

# --- 3. 資料讀取與清洗 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Final database.csv.gz', compression='gzip', low_memory=False)
    except:
        try:
            df = pd.read_csv('Final database.zip', compression='zip', low_memory=False)
        except:
            return None

    # 數值轉換
    numeric_cols = ['Popularity', 'danceability', 'energy', 'tempo', 'duration_ms', 'Artist_followers']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
    df['Year'] = df['Release_date'].dt.year
    df = df.dropna(subset=['Year', 'Popularity', 'Genre', 'Artist', 'tempo'])
    
    df['Genre'] = df['Genre'].astype(str).str.title()
    
    if 'Explicit' in df.columns:
        df['Exp_Str'] = df['Explicit'].astype(str).str.lower().str.strip()
        mapping = {'true': 'Explicit 🔞', 'false': 'Clean 🟢'}
        df['Explicit_Label'] = df['Exp_Str'].map(mapping).fillna('Unknown')

    return df

df = load_data()

# --- 4. 側邊欄 ---
with st.sidebar:
    st.title("🎧 Settings")
    year_range = st.slider("📅 Year Range", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
    df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    top_n = st.slider("🏆 Top Genres", 3, 15, 5)

# --- 5. 主頁面 ---
st.title("🎵 Spotify Producer Dashboard")

tab1, tab2, tab3 = st.tabs(["📈 Strategy", "🎛️ Audio Lab", "🌍 Global"])

# === TAB 2: 音樂實驗室 (已改回原本的直方圖設定) ===
with tab2:
    section_header("1. Tempo Analysis (BPM)")
    
    # 分類標籤
    def classify_tempo(bpm):
        if bpm < 100: return 'Slow'
        elif 100 <= bpm <= 140: return 'Mainstream'
        else: return 'Fast'
    
    df_filtered['Tempo_Zone'] = df_filtered['tempo'].apply(classify_tempo)
    
    # 繪製直方圖 (改回預設：Bar 不再強制加粗，移除每 5 BPM 一組的限制)
    fig_bpm = px.histogram(
        df_filtered, 
        x='tempo', 
        color='Tempo_Zone',
        color_discrete_map={
            'Slow': '#B3B3B3',
            'Mainstream': SPOTIFY_GREEN,
            'Fast': '#535353'
        },
        category_orders={'Tempo_Zone': ['Slow', 'Mainstream', 'Fast']},
        height=500
    )
    
    # 移除 xbins 設定，讓 Plotly 自動決定 Bar 的細緻度 (回歸原始細 Bar 視覺)
    fig_bpm.update_traces(textposition='outside') 
    
    # 套用原始輕盈樣式
    fig_bpm = apply_original_style(fig_bpm, "Tempo Distribution")
    st.plotly_chart(fig_bpm, use_container_width=True)

    st.markdown("---")

    # 2. 相關性矩陣
    section_header("2. Feature Correlation")
    corr_features = ['Popularity', 'danceability', 'energy', 'tempo', 'loudness']
    corr_matrix = df_filtered[corr_features].corr()
    fig_corr = px.imshow(corr_matrix, text_auto='.2f', aspect='auto',
                        color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN], height=500)
    fig_corr = apply_original_style(fig_corr, "Audio Feature Correlation Matrix")
    st.plotly_chart(fig_corr, use_container_width=True)

# === TAB 1: 市場策略 (同步回歸原始視覺) ===
with tab1:
    section_header("3. Market Strategy Insights")
    top_genres_list = df_filtered['Genre'].value_counts().head(top_n).index
    df_strat = df_filtered[df_filtered['Genre'].isin(top_genres_list)]
    
    fig_box = px.box(df_strat, x='Album/Single', y='Popularity', color='Album/Single',
                    facet_col='Genre', facet_col_wrap=5, height=600,
                    color_discrete_map={'single': SPOTIFY_GREEN, 'album': "#B3B3B3"})
    fig_box = apply_original_style(fig_box, "Format Performance by Genre")
    st.plotly_chart(fig_box, use_container_width=True)
