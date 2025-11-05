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

    years = [2018, 2019, 2020, 2021, 2022]
    months = ["ALL"] + [f"{i:02d}" for i in range(1, 13)]

    # --- Step 1: Prepopulate Streamlit session_state if empty ---
    # (Only the first time in an app session)
    if not all(k in st.session_state for k in ["price_area", "year", "month_sel"]):
        st.session_state["price_area"] = "NO1"
        st.session_state["year"] = 2021
        st.session_state["month_sel"] = "01"

    # --- Step 2: Widgets use the current state values ---
    price_area = st.sidebar.selectbox(
        "Select Price Area",
        options=list(PRICE_AREA_COORDS.keys()),
        index=list(PRICE_AREA_COORDS.keys()).index(st.session_state["price_area"]),
        key="price_area",
    )
    city, lat, lon = PRICE_AREA_COORDS[price_area]

    year = st.sidebar.selectbox(
        "Select Year",
        options=years,
        index=years.index(st.session_state["year"]),
        key="year",
    )

    month = st.sidebar.selectbox(
        "Select Month",
        options=months,
        index=months.index(st.session_state["month_sel"]),
        key="month_sel",
        format_func=lambda x: "All months" if x == "ALL" else x,
    )

    # --- Step 3: Return consistent values ---
    return price_area, city, lat, lon, year, month
