import streamlit as st


def sidebar_controls():
    """
    Shared sidebar controls that persist across pages within the same session.
    
    All selections (price_area, year, month) are stored in st.session_state
    and will persist when navigating between pages. This means if you select
    a year on one page, that selection will be maintained when you navigate
    to another page.
    
    Returns:
        tuple: (price_area, city, lat, lon, year, month)
    """
    st.sidebar.header("Select Location and Period")

    PRICE_AREA_COORDS = {
        "NO1": ("Oslo", 59.91, 10.75),
        "NO2": ("Kristiansand", 58.15, 8.00),
        "NO3": ("Trondheim", 63.43, 10.39),
        "NO4": ("Tromsø", 69.65, 18.96),
        "NO5": ("Bergen", 60.39, 5.32),
    }

    years = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
    months = ["ALL"] + [f"{i:02d}" for i in range(1, 13)]
    price_areas = list(PRICE_AREA_COORDS.keys())

    # Initialize session_state with defaults ONLY if not already set
    # This ensures selections persist across page navigation
    if "sidebar_price_area" not in st.session_state:
        st.session_state.sidebar_price_area = "NO1"
    if "sidebar_year" not in st.session_state:
        st.session_state.sidebar_year = 2021
    if "sidebar_month_sel" not in st.session_state:
        st.session_state.sidebar_month_sel = "01"

    # Widgets read from and write to session_state automatically via their keys
    # No index parameter needed - the session_state value is used
    price_area = st.sidebar.selectbox(
        "Select Price Area",
        options=price_areas,
        key="sidebar_price_area",
    )
    city, lat, lon = PRICE_AREA_COORDS[price_area]

    year = st.sidebar.selectbox(
        "Select Year",
        options=years,
        key="sidebar_year",
    )

    month = st.sidebar.selectbox(
        "Select Month",
        options=months,
        key="sidebar_month_sel",
        format_func=lambda x: "All months" if x == "ALL" else x,
    )

    return price_area, city, lat, lon, year, month
