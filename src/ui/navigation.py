# src/ui/navigation.py
"""
Reusable navigation component for the IND320 Dashboard.
Provides a consistent sidebar navigation across all pages.
"""

import streamlit as st
from streamlit_option_menu import option_menu


# -------------------------------------------------------------
# Page map (single source of truth)
# -------------------------------------------------------------
PAGE_MAP = {
    "Main": {
        "Dashboard": "app.py",
    },
    "Energy": {
        "Data Overview": "pages/energy/home.py",
        "Energy Production": "pages/energy/production.py",
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


def _get_current_page():
    """Determine which page is currently displayed."""
    # Get the current script path from st.context
    try:
        current_file = st.context.current_script_path
        if current_file:
            # Extract just the relative path from apps/
            if "apps/" in current_file:
                current_file = current_file.split("apps/")[-1]
            elif current_file.endswith("app.py"):
                current_file = "app.py"
            return current_file
    except Exception:
        pass
    return None


def _find_page_category_and_index(current_page):
    """Find which category and index the current page belongs to."""
    if current_page is None:
        return None, None, None

    for category, pages in PAGE_MAP.items():
        for idx, (name, path) in enumerate(pages.items()):
            if current_page and (
                current_page.endswith(path) or path.endswith(current_page)
            ):
                return category, name, idx
    return None, None, None


def _handle_navigation(category, selected_option, current_page, current_category):
    """Handle navigation when user selects an option from a menu."""
    target_path = PAGE_MAP[category].get(selected_option)
    if not target_path:
        return

    # Check if we're already on the target page
    if current_page:
        if current_page.endswith(target_path) or target_path.endswith(current_page):
            return

    # Navigate to the selected page
    st.switch_page(target_path)


def render_navigation():
    """
    Render the sidebar navigation menu.

    This function should be called at the start of every page to ensure
    consistent navigation across the application.

    The navigation uses session_state to track:
    - nav_initialized: Whether navigation has been initialized (prevents auto-jump)
    - last_selections: Track what was selected in each menu to detect changes
    """
    # Initialize navigation state if not present
    if "nav_initialized" not in st.session_state:
        st.session_state.nav_initialized = False

    if "last_selections" not in st.session_state:
        st.session_state.last_selections = {}

    # Track which page we're on to highlight correctly
    current_page = _get_current_page()
    current_category, current_page_name, current_idx = _find_page_category_and_index(
        current_page
    )

    with st.sidebar:
        # Main Dashboard link
        if st.button("🏠 Dashboard", use_container_width=True):
            if not current_page or not current_page.endswith("app.py"):
                st.switch_page("app.py")

        st.divider()

        # Track selections from each menu
        selections = {}

        # Energy Menu
        energy_default = 0
        if current_category == "Energy" and current_idx is not None:
            energy_default = current_idx
        selections["Energy"] = option_menu(
            "Energy",
            options=list(PAGE_MAP["Energy"].keys()),
            default_index=energy_default,
            key="nav_energy_menu",
        )

        # Weather Menu
        weather_default = 0
        if current_category == "Weather" and current_idx is not None:
            weather_default = current_idx
        selections["Weather"] = option_menu(
            "Weather",
            options=list(PAGE_MAP["Weather"].keys()),
            default_index=weather_default,
            key="nav_weather_menu",
        )

        # Forecasting Menu
        forecast_default = 0
        if current_category == "Forecasting" and current_idx is not None:
            forecast_default = current_idx
        selections["Forecasting"] = option_menu(
            "Forecasting",
            options=list(PAGE_MAP["Forecasting"].keys()),
            default_index=forecast_default,
            key="nav_forecast_menu",
        )

        # Data Selection Menu
        data_default = 0
        if current_category == "Data Selection" and current_idx is not None:
            data_default = current_idx
        selections["Data Selection"] = option_menu(
            "Data Selection",
            options=list(PAGE_MAP["Data Selection"].keys()),
            default_index=data_default,
            key="nav_map_menu",
        )

    # Navigation Logic — only active AFTER first interaction
    if st.session_state.nav_initialized:
        # Check if user clicked on a different page by comparing with last selections
        for category, selected_option in selections.items():
            if category == "Main":
                continue

            # Get previous selection for this category
            prev_selection = st.session_state.last_selections.get(category)

            # If selection changed in this category, navigate
            if prev_selection is not None and prev_selection != selected_option:
                _handle_navigation(
                    category, selected_option, current_page, current_category
                )
                break

    # Store current selections for next comparison
    st.session_state.last_selections = selections.copy()

    # Mark navigation as initialized AFTER first render
    st.session_state.nav_initialized = True
