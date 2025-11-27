# src/ui/navigation.py
"""
Reusable navigation component for the IND320 Dashboard.
Provides a consistent sidebar navigation across all pages using option_menu.

This module provides two main functions:
- create_navigation(): Registers all pages with Streamlit's navigation system
- render_option_menu_navigation(): Renders the custom styled sidebar

The navigation uses session_state to track:
- nav_initialized: Prevents auto-navigation on first load (Streamlit reruns
  the script on every interaction, so we need to distinguish between the
  initial page load and user clicks)
- last_selections: Tracks previous menu selections to detect user changes
- _dashboard_page: Stores the dashboard page object for navigation
"""

import streamlit as st
from streamlit_option_menu import option_menu


# -------------------------------------------------------------
# Page map (single source of truth)
# -------------------------------------------------------------
PAGE_MAP = {
    "Energy": {
        "Production & Consumption": "pages/energy/production.py",
        "Production STL & Spectrogram": "pages/energy/stl.py",
        "Sliding Window Correlation": "pages/energy/correlation.py",
    },
    "Weather": {
        "Weather Overview": "pages/weather/overview.py",
        "Meteo Analyses": "pages/weather/meteo.py",
        "Snow Drift": "pages/weather/snowdrift.py",
    },
    "Forecasting": {
        "Forecast SARIMAX": "pages/forecasting/sarimax.py",
    },
    "Data Selection": {
        "Map & Selectors": "pages/data/map_selectors.py",
    },
}


def home_page():
    """Main dashboard home page."""
    st.title("IND320 — Data to Decisions Dashboard")
    st.markdown("<div style='height: 25px'></div>", unsafe_allow_html=True)

    st.info(
        """
        This dashboard presents energy production and meteorological analyses 
        for the IND320 course.  
        Use the sidebar navigation to explore each section.
        """
    )


def create_navigation():
    """
    Create the navigation structure using st.navigation() with st.Page objects.
    This registers all pages so st.switch_page() works properly.

    The dashboard page object is stored in session_state for use by the
    Dashboard button in the sidebar.

    Returns
    -------
    st.navigation
        The navigation object that handles page routing.
    """
    # Create dashboard page object and store in session_state
    dashboard_page = st.Page(home_page, title="Dashboard", icon="🏠")
    st.session_state["_dashboard_page"] = dashboard_page

    # Define all pages with their paths - this registers them with Streamlit
    pages = {
        "Main": [
            dashboard_page,
        ],
        "Energy": [
            st.Page("pages/energy/production.py", title="Production & Consumption", icon="⚡"),
            st.Page(
                "pages/energy/stl.py", title="Production STL & Spectrogram", icon="📈"
            ),
            st.Page(
                "pages/energy/correlation.py",
                title="Sliding Window Correlation",
                icon="🔗",
            ),
        ],
        "Weather": [
            st.Page("pages/weather/overview.py", title="Weather Overview", icon="🌤️"),
            st.Page("pages/weather/meteo.py", title="Meteo Analyses", icon="🌡️"),
            st.Page("pages/weather/snowdrift.py", title="Snow Drift", icon="❄️"),
        ],
        "Forecasting": [
            st.Page("pages/forecasting/sarimax.py", title="Forecast SARIMAX", icon="📉"),
        ],
        "Data Selection": [
            st.Page("pages/data/map_selectors.py", title="Map & Selectors", icon="🗺️"),
        ],
    }

    # Create navigation with hidden position (we use custom sidebar)
    return st.navigation(pages, position="hidden")


def render_option_menu_navigation():
    """
    Render custom option_menu navigation in the sidebar.

    This provides the styled navigation using streamlit_option_menu while
    using st.switch_page() for routing. The function tracks menu selections
    in session_state to detect user changes and trigger navigation only when
    the user actually clicks a different menu item.

    Navigation Logic:
    1. On first load, nav_initialized is False - we store selections but don't navigate
    2. On subsequent interactions, we compare current selections with previous ones
    3. If a selection changed, we navigate to the new page
    4. This prevents auto-navigation loops and unwanted page switches
    """
    # Initialize navigation state if not present
    if "nav_initialized" not in st.session_state:
        st.session_state.nav_initialized = False

    if "last_selections" not in st.session_state:
        st.session_state.last_selections = {}

    with st.sidebar:
        # Dashboard button at top
        if st.button("🏠 Dashboard", use_container_width=True, key="dashboard_btn"):
            dashboard_page = st.session_state.get("_dashboard_page")
            if dashboard_page is not None:
                st.switch_page(dashboard_page)

        st.divider()

        # Energy Menu
        selected_energy = option_menu(
            "Energy",
            options=list(PAGE_MAP["Energy"].keys()),
            icons=["lightning-charge", "bar-chart", "link"],
            default_index=0,
            key="nav_energy_menu",
        )

        # Weather Menu
        selected_weather = option_menu(
            "Weather",
            options=list(PAGE_MAP["Weather"].keys()),
            icons=["cloud-sun", "thermometer", "snow"],
            default_index=0,
            key="nav_weather_menu",
        )

        # Forecasting Menu
        selected_forecast = option_menu(
            "Forecasting",
            options=list(PAGE_MAP["Forecasting"].keys()),
            icons=["graph-down"],
            default_index=0,
            key="nav_forecast_menu",
        )

        # Data Selection Menu
        selected_data = option_menu(
            "Data Selection",
            options=list(PAGE_MAP["Data Selection"].keys()),
            icons=["map"],
            default_index=0,
            key="nav_map_menu",
        )

    # Store current selections
    current_selections = {
        "Energy": selected_energy,
        "Weather": selected_weather,
        "Forecasting": selected_forecast,
        "Data Selection": selected_data,
    }

    # Navigation Logic — only active AFTER first interaction
    # This prevents auto-navigation on initial page load
    if st.session_state.nav_initialized:
        for category, selected_option in current_selections.items():
            prev_selection = st.session_state.last_selections.get(category)

            # If selection changed in this category, navigate
            if prev_selection is not None and prev_selection != selected_option:
                target_path = PAGE_MAP[category].get(selected_option)
                if target_path:
                    st.switch_page(target_path)
                break

    # Store current selections for next comparison
    st.session_state.last_selections = current_selections.copy()

    # Mark navigation as initialized AFTER first render
    st.session_state.nav_initialized = True
