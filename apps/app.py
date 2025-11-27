import streamlit as st
from pathlib import Path
import sys

# --- Project imports setup ---
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.app_state import init_app_state

st.set_page_config(page_title="IND320 Dashboard", layout="wide")

# Initialize app state once with loading indicator
with st.spinner("Loading data..."):
    init_app_state()

st.title("IND320 — Data to Decisions Dashboard")
st.markdown("<div style='height: 25px'></div>", unsafe_allow_html=True)
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
/* Center all Streamlit elements on the page */
.main > div {
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* Style for buttons */
div.stButton > button {
    width: 90%;
    max-width: 480px;
    min-height: 160px;
    border-radius: 18px;
    background: linear-gradient(135deg, #308CBA, #256EA3);
    color: #EDEFF2;
    border: none;
    font-size: 18px;
    font-weight: 500;
    transition: all .25s ease;
    cursor: pointer;
    text-align: center;
    padding: 18px;
    margin: auto;
    box-shadow: 0 4px 8px rgba(0,0,0,0.25);
}

/* Hover animation */
div.stButton > button:hover {
    background: linear-gradient(135deg, #2A2A2A, #1E1E1E);
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}

/* Responsive scaling */
@media (max-width: 1600px) {
    div.stButton > button {
        min-height: 140px;
        font-size: 16px;
    }
}
@media (max-width: 1200px) {
    div[data-testid="column"] {
        flex: 1 1 100% !important;
    }
    div.stButton > button {
        width: 100%;
        min-height: 130px;
    }
}
@media (max-width: 800px) {
    div.stButton > button {
        font-size: 15px;
        min-height: 120px;
    }
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
    if st.button(
        "⚡ **Energy Production**\n\n Explore energy data from Elhub", key="energy"
    ):
        st.switch_page("pages/02_Energy_Production.py")

st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)

# --- ROW 2 ---
col3, col4 = st.columns(2, gap="large")
with col3:
    if st.button(
        "🔍 **Production Analyses (STL & Spectrogram)**\n\n Decompose and analyze patterns",
        key="stl",
    ):
        st.switch_page("pages/03_Production_STL_and_Spectrogram.py")
with col4:
    if st.button(
        "🌤️ **Weather Overview**\n\n Data tables and interactive visualizations",
        key="weather_overview",
    ):
        st.switch_page("pages/04_Weather_Overview.py")

st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)

# --- ROW 3 ---
col5, col6 = st.columns(2, gap="large")
with col5:
    if st.button(
        "🧭 **Meteo Analyses**\n\n Outlier and anomaly detection (SPC & LOF)",
        key="meteo_analyses",
    ):
        st.switch_page("pages/05_Meteo_Analyses.py")
with col6:
    st.empty()  # Placeholder for future functionality

st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
