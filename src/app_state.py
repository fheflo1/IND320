# src/app_state.py
"""
Centralized app state initialization for the Streamlit application.
This module should only be called once from apps/app.py on startup.
"""

import streamlit as st

# Centralized price area coordinate definitions
PRICE_AREA_COORDS = {
    "NO1": ("Oslo", 59.91, 10.75),
    "NO2": ("Kristiansand", 58.15, 8.00),
    "NO3": ("Trondheim", 63.43, 10.39),
    "NO4": ("Tromsø", 69.65, 18.96),
    "NO5": ("Bergen", 60.39, 5.32),
}

# Available years and months for sidebar controls
AVAILABLE_YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
AVAILABLE_MONTHS = ["ALL"] + [f"{i:02d}" for i in range(1, 13)]


def init_app_state():
    """
    Initialize app-wide session state with default values.
    Call this exactly once in apps/app.py before any page loads.

    Sets up:
    - price_area, year, month_sel for sidebar controls
    - clicked_lat, clicked_lon for map coordinates
    - selected_area, selected_fid for map selections
    - center_lat, center_lon, zoom for map viewport
    """
    # Sidebar selection defaults
    if "price_area" not in st.session_state:
        st.session_state["price_area"] = "NO1"

    if "year" not in st.session_state:
        st.session_state["year"] = 2021

    if "month_sel" not in st.session_state:
        st.session_state["month_sel"] = "01"

    # Map coordinate state
    if "clicked_lat" not in st.session_state:
        st.session_state["clicked_lat"] = None

    if "clicked_lon" not in st.session_state:
        st.session_state["clicked_lon"] = None

    # Map selection state
    if "selected_area" not in st.session_state:
        st.session_state["selected_area"] = None

    if "selected_fid" not in st.session_state:
        st.session_state["selected_fid"] = None

    # Map viewport state
    if "center_lat" not in st.session_state:
        st.session_state["center_lat"] = 65.0

    if "center_lon" not in st.session_state:
        st.session_state["center_lon"] = 15.0

    if "zoom" not in st.session_state:
        st.session_state["zoom"] = 5
