import streamlit as st

st.set_page_config(page_title="IND320 Dashboard", layout="wide")

st.title("IND320 — Data to Decisions Dashboard")
st.info(
    """
    This dashboard presents energy production and meteorological analyses 
    for the IND320 course.  
    Use the buttons below or the sidebar to explore each section.
    """
)

# --- CSS for consistent button layout ---
st.markdown(
    """
<style>
div.stButton > button {
    width: 650px;
    height: 200px;
    border-radius: 16px;
    background: #308CBA;
    color: #EDEFF2;
    border: 1px solid rgba(255,255,255,0.10);
    transition: all .2s ease;
    cursor: pointer;
    text-align: center;
    padding: 20px;
}
div.stButton > button:hover {
    background: #2A2A2A;
    border-color: rgba(255,255,255,0.20);
    transform: translateY(-4px);
    box-shadow: 0 10px 30px rgba(0,0,0,.35);
}
.big-title {
    font-size: 28px;
    font-weight: bold;
    display: block;
    margin-bottom: 8px;
}
.small-sub {
    font-size: 16px;
    color: #bbb;
    display: block;
}
</style>
""",
    unsafe_allow_html=True,
)

# --- ROW 1 ---
col1, col2 = st.columns(2, gap="large")
with col1:
    if st.button("🏠 **Home Overview**\n\n Data overview and summaries", key="home"):
        st.switch_page("pages/01_Home_Data_Overview.py")
with col2:
    if st.button("⚡ **Energy Production**\n\n Explore energy data from Elhub", key="energy"):
        st.switch_page("pages/02_Energy_Production.py")

st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)

# --- ROW 2 ---
col3, col4 = st.columns(2, gap="large")
with col3:
    if st.button("🔍 **Production Analyses (STL & Spectrogram)**\n\n Decompose and analyze patterns", key="stl"):
        st.switch_page("pages/03_Production_STL_and_Spectrogram.py")
with col4:
    if st.button("🌤️ **Weather Data and Line Charts**\n\n Detailed weather observations", key="weather_data"):
        st.switch_page("pages/04_Weather_Data_and_Line_Charts.py")

st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)

# --- ROW 3 ---
col5, col6 = st.columns(2, gap="large")
with col5:
    if st.button("📊 **Weather Plots**\n\n Interactive visualizations of meteorological data", key="weather_plots"):
        st.switch_page("pages/05_Weather_Plots.py")
with col6:
    if st.button("🧭 **Meteo Analyses**\n\n Outlier and anomaly detection (SPC & LOF)", key="meteo_analyses"):
        st.switch_page("pages/06_Meteo_Analyses.py")

st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)

# --- ROW 4 (Dummy / Future work) ---
col7, col8 = st.columns(2, gap="large")
with col7:
    if st.button("🧪 **Dummy / Sandbox**\n\n Experimental and development area", key="dummy"):
        st.switch_page("pages/07_Dummy.py")
with col8:
    st.write("")  # for alignment
