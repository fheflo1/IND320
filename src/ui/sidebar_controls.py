import streamlit as st

PRICE_AREA_COORDS = {
    "NO1": ("Oslo", 59.91, 10.75),
    "NO2": ("Kristiansand", 58.15, 8.00),
    "NO3": ("Trondheim", 63.43, 10.39),
    "NO4": ("Tromsø", 69.65, 18.96),
    "NO5": ("Bergen", 60.39, 5.32),
}


def sidebar_controls():
    """Shared sidebar for all pages (persistent via session_state)."""
    st.sidebar.header("Select Location and Period")

    # --- Price Area ---
    if "price_area" not in st.session_state:
        st.session_state["price_area"] = "NO5"

    price_area = st.sidebar.selectbox(
        "Select Price Area",
        options=list(PRICE_AREA_COORDS.keys()),
        index=list(PRICE_AREA_COORDS.keys()).index(st.session_state["price_area"]),
        key="price_area",
    )

    city, lat, lon = PRICE_AREA_COORDS[price_area]

    # --- Year ---
    if "year" not in st.session_state:
        st.session_state["year"] = 2019

    year = st.sidebar.selectbox(
        "Select Year",
        [2018, 2019, 2020, 2021, 2022],
        index=[2018, 2019, 2020, 2021, 2022].index(st.session_state["year"]),
        key="year",
    )

    # --- Month ---
    if "month" not in st.session_state:
        st.session_state["month"] = "01"

    month = st.sidebar.selectbox(
        "Select Month",
        [f"{i:02d}" for i in range(1, 13)],
        index=int(st.session_state["month"]) - 1,
        key="month",
    )

    return price_area, city, lat, lon, year, month
