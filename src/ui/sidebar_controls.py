import streamlit as st

def sidebar_controls():
    """Shared sidebar for selecting location and period across all pages (persistent state)."""

    st.sidebar.header("Select Location and Period")

    PRICE_AREA_COORDS = {
        "NO1": ("Oslo", 59.91, 10.75),
        "NO2": ("Kristiansand", 58.15, 8.00),
        "NO3": ("Trondheim", 63.43, 10.39),
        "NO4": ("Tromsø", 69.65, 18.96),
        "NO5": ("Bergen", 60.39, 5.32),
    }

    # --- Initialize session_state defaults ONCE ---
    st.session_state.setdefault("price_area", "NO1")
    st.session_state.setdefault("year", 2022)
    st.session_state.setdefault("month_sel", "ALL")  # default to all months

    # --- Widgets use current session_state values ---
    price_area = st.sidebar.selectbox(
        "Select Price Area",
        options=list(PRICE_AREA_COORDS.keys()),
        index=list(PRICE_AREA_COORDS.keys()).index(st.session_state.price_area),
        key="price_area",
    )

    city, lat, lon = PRICE_AREA_COORDS[price_area]

    year = st.sidebar.selectbox(
        "Select Year",
        [2018, 2019, 2020, 2021, 2022],
        index=[2018, 2019, 2020, 2021, 2022].index(st.session_state.year),
        key="year",
    )

    # --- Month selection ---
    months = ["ALL"] + [f"{i:02d}" for i in range(1, 13)]

    # Safely find index of current month_sel
    try:
        current_index = months.index(st.session_state.month_sel)
    except ValueError:
        current_index = 0  # fallback to "ALL"

    month = st.sidebar.selectbox(
        "Select Month",
        months,
        index=current_index,
        format_func=lambda x: "All months" if x == "ALL" else x,
        key="month_sel",
    )

    # --- Return full state ---
    return price_area, city, lat, lon, year, month
