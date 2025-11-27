"""
App State Module for Streamlit Data Preloading

This module handles preloading all required data when the app starts,
storing everything in st.session_state so pages can access data instantly
without re-fetching.
"""

import streamlit as st
from src.db.mongo_elhub import load_production_silver, load_consumption_silver
from src.api.meteo_api import fetch_meteo_data

# Price area coordinates for weather data fetching
PRICEAREAS = {
    "NO1": ("Oslo", 59.91, 10.75),
    "NO2": ("Kristiansand", 58.15, 8.00),
    "NO3": ("Trondheim", 63.43, 10.39),
    "NO4": ("Tromsø", 69.65, 18.96),
    "NO5": ("Bergen", 60.39, 5.32),
}


def init_app_state():
    """
    Initialize application state by preloading all required data.
    Data is only loaded once per session.
    """
    if "data_loaded" in st.session_state:
        return

    # Load core datasets once
    try:
        st.session_state.production = load_production_silver()
    except Exception as e:
        st.session_state.production = None
        st.warning(f"Could not load production data: {e}")

    try:
        st.session_state.consumption = load_consumption_silver()
    except Exception as e:
        st.session_state.consumption = None
        st.warning(f"Could not load consumption data: {e}")

    # Weather data is fetched on-demand per page due to varying date ranges
    # Store coordinates for easy access
    st.session_state.price_area_coords = PRICEAREAS

    st.session_state.data_loaded = True
