import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import statsmodels.api as sm

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

# ✨ 自定義大標題函數 (用於章節)
def section_header(text):
    st.markdown(f"<h2 style='color: {SPOTIFY_GREEN}; font-size: 32px; font-weight: 900; margin-top: 30px;'>{text}</h2>", unsafe_allow_html=True)

# ✨ 強力視覺圖表樣式 (加大標題、加粗文字)
def apply_strong_style(fig, title_text):
    fig.update_layout(
        title=dict(
            text=f"<b>{title_text}</b>",
            font=dict(color=SPOTIFY_GREEN, size=28, family="Arial Black"),
            x=0, y=0.95
        ),
        font=dict(family="Arial Black", color="black"),
        margin=dict(t=80, b=50),
        template="simple_white",
        bargap=0.1 # 讓柱子之間有空隙，更好看
    )
    fig.update_xaxes(tickfont=dict(family="Arial Black", size=14, color="black"), title_font=dict(size=16))
    fig.update_yaxes(tickfont=dict(family="Arial Black", size=14, color="black"), title_font=dict(size=16))
    return fig

# --- 3. 資料讀取與強力清洗 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Final database.csv.gz', compression='gzip', low_memory=False)
    except:
        try:
            df = pd.read_csv('Final database.zip', compression='zip', low_memory=False)
        except:
            return None

    # 數值處理
    cols = ['Popularity', 'danceability', 'energy', 'tempo', 'duration_ms', 'Artist_followers']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['Release_date'] = pd.to_datetime(df['Release_date'], format='mixed', errors='coerce')
    df['Year'] = df['Release_date'].dt.year
    df = df.dropna(subset=['Year', 'Popularity', 'Genre', 'Artist', 'tempo'])
    
    # 清理流派 NA
    junk = ['N-A', 'N-a', 'Nan', 'Unknown', 'N/A']
    df = df[~df['Genre'].astype(str).str.title().isin(junk)]
    
    # Explicit 清洗
    if 'Explicit' in df.columns:
        df['Exp_Str'] = df['Explicit'].astype(str).str.lower().str.strip()
        mapping = {'true': 'Explicit 🔞', '1': 'Explicit 🔞', '1.0': 'Explicit 🔞', 'false': 'Clean 🟢', '0': 'Clean 🟢', '0.0': 'Clean 🟢'}
        df['Explicit_Label'] = df['Exp_Str'].map(mapping).fillna('Unknown')

    return df

df = load_data()

# --- 4. 側邊欄 ---
with st.sidebar:
    st.title("🎧 Settings")
    year_range = st.slider("📅 Year Range", int(df['Year'].min()), int(df['Year'].max()), (2010, 2024))
    df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    top_n = st.slider("🏆 Top Genres", 3, 10, 5)

# --- 5. 主頁面 ---
st.title("🎵 Spotify Producer Dashboard")
tab1, tab2, tab3 = st.tabs(["📈 Strategy", "🎛️ Audio Lab", "🌍 Global"])

# === TAB 2: 音樂實驗室 (BPM 優化在此) ===
with tab2:
    section_header("1. Tempo Analysis (BPM)")
    
    # 1.1 分類邏輯 (已移除 Emoji)
    def classify_tempo(bpm):
        if bpm < 100: return 'Slow (Below 100)'
        elif 100 <= bpm <= 140: return 'Mainstream (100-140)'
        else: return 'Fast (Above 140)'
    
    df_filtered['Tempo_Zone'] = df_filtered['tempo'].apply(classify_tempo)
    
    # 1.2 繪製直方圖
    fig_bpm = px.histogram(
        df_filtered, 
        x='tempo', 
        color='Tempo_Zone',
        color_discrete_map={
            'Slow (Below 100)': '#B3B3B3',
            'Mainstream (100-140)': SPOTIFY_GREEN,
            'Fast (Above 140)': '#535353'
        },
        category_orders={'Tempo_Zone': ['Slow (Below 100)', 'Mainstream (100-140)', 'Fast (Above 140)']},
        text_auto=True, # 自動顯示數字
        height=600
    )
    
    # 1.3 柱子加粗與標籤優化
    fig_bpm.update_traces(
        xbins=dict(start=0, end=250, size=5), # 每 5 BPM 一根柱子，變粗關鍵
        textposition='outside',
        marker_line_width=1,
        marker_line_color="white"
    )
    
    # 1.4 套用大標題與加粗樣式
    fig_bpm = apply_strong_style(fig_bpm, "Tempo Distribution: The Sweet Spot (100-140 BPM)")
    fig_bpm.update_layout(xaxis_title="Tempo (BPM)", yaxis_title="Song Count")
    
    # 1.5 加入 120 BPM 基準線
    fig_bpm.add_vline(x=120, line_width=3, line_dash="dash", line_color=SPOTIFY_BLACK)
    
    st.plotly_chart(fig_bpm, use_container_width=True)
    
    st.markdown("---")

    # 2. 決策矩陣 (同步加大標題)
    section_header("2. Decision Matrix")
    corr_features = ['Popularity', 'danceability', 'energy', 'valence', 'tempo', 'loudness']
    corr_matrix = df_filtered[corr_features].corr()
    fig_corr = px.imshow(corr_matrix, text_auto='.2f', aspect='auto',
                        color_continuous_scale=['#FFFFFF', '#C8E6C9', SPOTIFY_GREEN], height=600)
    fig_corr = apply_strong_style(fig_corr, "Which Feature Correlates with Popularity?")
    st.plotly_chart(fig_corr, use_container_width=True)

# === 其餘分頁保持邏輯 (範例簡化，請保留您原本 tab1/tab3 的詳細繪圖程式碼) ===
with tab1:
    section_header("3. Market Strategy Insights")
    st.info("請在此處保留您原本的市場趨勢、發行策略、巨星效應等程式碼，並對圖表調用 apply_strong_style() 即可。")

with tab3:
    section_header("4. Global Market Map")
    # ... 您原本的地圖程式碼 ...

