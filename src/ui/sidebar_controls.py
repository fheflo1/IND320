import streamlit as st
from src.app_state import PRICE_AREA_COORDS, AVAILABLE_YEARS, AVAILABLE_MONTHS


def sidebar_controls():
    """Shared sidebar that persists across pages within the same session."""
    st.sidebar.markdown("---")
    st.sidebar.header("Select Location and Period")

    # Session state should already be initialized by init_app_state() in app.py
    # This is a fallback for safety
    if "price_area" not in st.session_state:
        st.session_state["price_area"] = "NO1"
    if "year" not in st.session_state:
        st.session_state["year"] = 2021
    if "month_sel" not in st.session_state:
        st.session_state["month_sel"] = "01"

    # Widgets use the current state values
    price_area = st.sidebar.selectbox(
        "Select Price Area",
        options=list(PRICE_AREA_COORDS.keys()),
        index=list(PRICE_AREA_COORDS.keys()).index(st.session_state["price_area"]),
        key="price_area",
    )
    city, lat, lon = PRICE_AREA_COORDS[price_area]

    year = st.sidebar.selectbox(
        "Select Year",
        options=AVAILABLE_YEARS,
        index=AVAILABLE_YEARS.index(st.session_state["year"]),
        key="year",
    )

    month = st.sidebar.selectbox(
        "Select Month",
        options=AVAILABLE_MONTHS,
        index=AVAILABLE_MONTHS.index(st.session_state["month_sel"]),
        key="month_sel",
        format_func=lambda x: "All months" if x == "ALL" else x,
    )

    return price_area, city, lat, lon, year, month
