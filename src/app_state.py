# src/app_state.py
"""
Centralized application state management for the IND320 Dashboard.
Provides initialization functions, shared state access, and weather data helpers.
"""

import streamlit as st
import pandas as pd
from src.db.mongo_elhub import load_production_silver, load_consumption_silver
from src.api.meteo_api import fetch_meteo_data


# Price area coordinates constant
PRICEAREAS = {
    "NO1": ("Oslo", 59.91, 10.75),
    "NO2": ("Kristiansand", 58.15, 8.00),
    "NO3": ("Trondheim", 63.43, 10.39),
    "NO4": ("Tromsø", 69.65, 18.96),
    "NO5": ("Bergen", 60.39, 5.32),
}

# Default weather variables
DEFAULT_WEATHER_VARS = [
    "temperature_2m",
    "precipitation",
    "windspeed_10m",
    "windgusts_10m",
    "winddirection_10m",
]


def init_app_state():
    """
    Initialize the application state with production and consumption data.
    This function should be called once from the main app.py file.
    
    Sets the following session_state keys:
    - production: DataFrame with production data
    - consumption: DataFrame with consumption data
    - price_area_coords: Dictionary mapping price areas to coordinates
    """
    # Set price area coordinates in session state
    if "price_area_coords" not in st.session_state:
        st.session_state.price_area_coords = PRICEAREAS
    
    # Load production data if not already loaded
    if "production" not in st.session_state:
        try:
            st.session_state.production = load_production_silver()
        except Exception as e:
            st.error(f"Failed to load production data: {e}")
            st.session_state.production = pd.DataFrame()
    
    # Load consumption data if not already loaded
    if "consumption" not in st.session_state:
        try:
            st.session_state.consumption = load_consumption_silver()
        except Exception as e:
            st.error(f"Failed to load consumption data: {e}")
            st.session_state.consumption = pd.DataFrame()


def get_weather(pricearea, start, end, variables=None):
    """
    Fetch weather data for a given price area and date range.
    Results are cached in session_state using a deterministic key.
    
    Parameters
    ----------
    pricearea : str
        Price area code (e.g., 'NO1', 'NO2')
    start : str
        Start date in YYYY-MM-DD format
    end : str
        End date in YYYY-MM-DD format
    variables : list[str], optional
        List of weather variables to fetch. Defaults to common variables.
    
    Returns
    -------
    pd.DataFrame
        Weather data with time index
    
    Raises
    ------
    ValueError
        If the price area is not found in coordinates
    """
    variables = variables or DEFAULT_WEATHER_VARS
    
    # Create deterministic cache key
    key = f"weather__{pricearea}__{start}__{end}__{'_'.join(variables)}"
    
    # Return cached data if available
    if key in st.session_state:
        return st.session_state[key]
    
    # Get coordinates from session state or fallback to constant
    coords = st.session_state.get("price_area_coords") or PRICEAREAS
    
    if pricearea not in coords:
        raise ValueError(f"No coordinates for price area: {pricearea}")
    
    city, lat, lon = coords[pricearea]
    
    # Fetch weather data
    df = fetch_meteo_data(lat, lon, start, end, variables=variables)
    
    # Cache and return
    st.session_state[key] = df
    return df
