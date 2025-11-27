import streamlit as st


def sidebar_controls():
    """Shared sidebar that persists across pages within the same session."""
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

    # Use unique keys that don't conflict with session_state initialization
    # The widgets will use these keys directly without pre-setting session_state
    price_area = st.sidebar.selectbox(
        "Select Price Area",
        options=list(PRICE_AREA_COORDS.keys()),
        index=0,  # Default to NO1
        key="sidebar_price_area",
    )
    city, lat, lon = PRICE_AREA_COORDS[price_area]

    year = st.sidebar.selectbox(
        "Select Year",
        options=years,
        index=years.index(2021),  # Default to 2021
        key="sidebar_year",
    )

    month = st.sidebar.selectbox(
        "Select Month",
        options=months,
        index=1,  # Default to "01"
        key="sidebar_month_sel",
        format_func=lambda x: "All months" if x == "ALL" else x,
    )

    return price_area, city, lat, lon, year, month
