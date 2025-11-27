import streamlit as st
from pathlib import Path
import sys

# --- Project imports setup ---
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.app_state import init_app_state

st.set_page_config(page_title="IND320 Dashboard", layout="wide")

# Initialize app state and preload data
init_app_state()

# --- Navigation Structure ---
NAVIGATION = {
    "🏠 Home": {
        "pages": ["Home Data Overview"],
        "files": {"Home Data Overview": "pages/01_Home_Data_Overview.py"},
    },
    "🗺️ Data Selection": {
        "pages": ["Map & Selectors"],
        "files": {"Map & Selectors": "pages/Map_and_Selectors.py"},
    },
    "⚡ Energy": {
        "pages": [
            "Energy Production",
            "Production STL & Spectrogram",
            "Sliding Window Correlation",
        ],
        "files": {
            "Energy Production": "pages/02_Energy_Production.py",
            "Production STL & Spectrogram": "pages/03_Production_STL_and_Spectrogram.py",
            "Sliding Window Correlation": "pages/Sliding_Window_Correlation.py",
        },
    },
    "🌦️ Weather": {
        "pages": ["Weather Overview", "Meteo Analyses", "Snow Drift"],
        "files": {
            "Weather Overview": "pages/04_Weather_Data_and_Line_Charts.py",
            "Meteo Analyses": "pages/06_Meteo_Analyses.py",
            "Snow Drift": "pages/Snow_Drift.py",
        },
    },
    "🔮 Forecasting": {
        "pages": ["SARIMAX Forecast"],
        "files": {"SARIMAX Forecast": "pages/Forecast_SARIMAX.py"},
    },
}

# --- Initialize navigation state ---
if "nav_section" not in st.session_state:
    st.session_state.nav_section = "🏠 Home"
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Home Data Overview"

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")

section = st.sidebar.selectbox(
    "Section",
    options=list(NAVIGATION.keys()),
    index=list(NAVIGATION.keys()).index(st.session_state.nav_section),
    key="nav_section",
)

# Get pages for selected section
section_pages = NAVIGATION[section]["pages"]

# Radio buttons for subpages
page = st.sidebar.radio(
    f"{section} Pages:",
    options=section_pages,
    key="nav_page_radio",
)

# Update session state
st.session_state.nav_page = page

st.sidebar.divider()

# --- Main Content Area ---
st.title("IND320 — Data to Decisions Dashboard")
st.markdown("<div style='height: 25px'></div>", unsafe_allow_html=True)
st.info(
    """
    This dashboard presents energy production and meteorological analyses 
    for the IND320 course.  
    Use the sidebar navigation to explore each section, or click the buttons below.
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

# --- Navigation button to go to selected page ---
selected_file = NAVIGATION[section]["files"].get(page)
if selected_file:
    if st.sidebar.button(f"Go to {page}", key="nav_go_button"):
        st.switch_page(selected_file)

st.sidebar.divider()
st.sidebar.caption("💡 Select a section and page, then click 'Go to' to navigate.")

# --- Quick Access Buttons on Home Page ---
st.subheader("Quick Access")

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
        "🌤️ **Weather Data and Line Charts**\n\n Detailed weather observations",
        key="weather_data",
    ):
        st.switch_page("pages/04_Weather_Data_and_Line_Charts.py")

st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)

# --- ROW 3 ---
col5, col6 = st.columns(2, gap="large")
with col5:
    if st.button(
        "📊 **Weather Plots**\n\n Interactive visualizations of meteorological data",
        key="weather_plots",
    ):
        st.switch_page("pages/05_Weather_Plots.py")
with col6:
    if st.button(
        "🧭 **Meteo Analyses**\n\n Outlier and anomaly detection (SPC & LOF)",
        key="meteo_analyses",
    ):
        st.switch_page("pages/06_Meteo_Analyses.py")

st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)

# --- ROW 4 ---
col7, col8 = st.columns(2, gap="large")
with col7:
    if st.button(
        "🗺️ **Map & Selectors**\n\n Interactive price area map",
        key="map_selectors",
    ):
        st.switch_page("pages/Map_and_Selectors.py")
with col8:
    if st.button(
        "🔮 **SARIMAX Forecast**\n\n Energy forecasting with weather",
        key="forecast",
    ):
        st.switch_page("pages/Forecast_SARIMAX.py")

st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
