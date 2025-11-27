import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

# --- Project imports setup ---
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.ui.sidebar_controls import sidebar_controls

# --- Page title ---
st.title("Energy Production & Consumption")
st.markdown("Compare production and consumption data by energy source and time period.")

# --- Shared sidebar state (from all pages) ---
price_area, city, lat, lon, year, month = sidebar_controls()

# --- Load production data from session_state ---
df_prod = st.session_state.get("production")
has_production = df_prod is not None and not df_prod.empty

# --- Load consumption data from session_state ---
df_cons = st.session_state.get("consumption")
has_consumption = df_cons is not None and not df_cons.empty

if not has_production and not has_consumption:
    st.error(
        "Neither production nor consumption data is available. Please check that the app has been initialized."
    )
    st.stop()

# --- Prepare production data ---
if has_production:
    df_prod = df_prod.copy()
    df_prod["starttime"] = pd.to_datetime(df_prod["starttime"])
    # Map 'group' to 'productiongroup' for backward compatibility
    if "productiongroup" not in df_prod.columns and "group" in df_prod.columns:
        df_prod["productiongroup"] = df_prod["group"]
    if "month" not in df_prod.columns:
        df_prod["month"] = df_prod["starttime"].dt.month

# --- Prepare consumption data ---
if has_consumption:
    df_cons = df_cons.copy()
    df_cons["starttime"] = pd.to_datetime(df_cons["starttime"])
    # Map 'group' to 'consumptiongroup' for backward compatibility
    if "consumptiongroup" not in df_cons.columns and "group" in df_cons.columns:
        df_cons["consumptiongroup"] = df_cons["group"]
    if "month" not in df_cons.columns:
        df_cons["month"] = df_cons["starttime"].dt.month

# --- Convert sidebar month (string like "01") → int ---
try:
    month_int = int(month)
except Exception:
    month_int = 0

# --- Month names for titles ---
month_names = {
    0: "All year",
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

# --- Consistent color mapping for production charts ---
PROD_COLOR_MAP = {
    "hydro": "#2E8B92",  # teal
    "thermal": "#E6B800",  # warm yellow
    "solar": "#E68A00",  # orange
    "other": "#CBA0FF",  # soft purple
}
PROD_CATEGORY_ORDER = {"productiongroup": ["hydro", "thermal", "wind", "solar", "other"]}

# --- Consistent color mapping for consumption charts ---
CONS_COLOR_MAP = {
    "business": "#3498DB",  # blue
    "industry": "#E74C3C",  # red
    "private": "#2ECC71",  # green
    "other": "#9B59B6",  # purple
}
CONS_CATEGORY_ORDER = {"consumptiongroup": ["business", "industry", "private", "other"]}


# --- Session defaults ---
if "selected_groups" not in st.session_state:
    if has_production:
        st.session_state.selected_groups = sorted(df_prod["productiongroup"].unique())
    else:
        st.session_state.selected_groups = []

if "selected_cons_groups" not in st.session_state:
    if has_consumption:
        st.session_state.selected_cons_groups = sorted(df_cons["consumptiongroup"].unique())
    else:
        st.session_state.selected_cons_groups = []


# --- Shared filter function for production ---
def get_filtered_production(df):
    filtered = df[df["pricearea"] == price_area]
    if month_int != 0:
        filtered = filtered[filtered["month"] == month_int]
    if st.session_state.selected_groups:
        filtered = filtered[
            filtered["productiongroup"].isin(st.session_state.selected_groups)
        ]
    return filtered


# --- Shared filter function for consumption ---
def get_filtered_consumption(df):
    filtered = df[df["pricearea"] == price_area]
    if month_int != 0:
        filtered = filtered[filtered["month"] == month_int]
    if st.session_state.selected_cons_groups:
        filtered = filtered[
            filtered["consumptiongroup"].isin(st.session_state.selected_cons_groups)
        ]
    return filtered


# =============================================================================
# PRODUCTION SECTION
# =============================================================================
if has_production:
    st.header("⚡ Energy Production")
    
    col1, col2 = st.columns(2)

    # --- Left column: Production Pie chart ---
    with col1:
        st.subheader("Total Production by Energy Source")

        filtered_df = get_filtered_production(df_prod)
        pie_data = filtered_df.groupby("productiongroup")["quantitykwh"].sum().reset_index()

        fig_pie = px.pie(
            pie_data,
            values="quantitykwh",
            names="productiongroup",
            title=f"{month_names[month_int]} – {price_area}",
            color="productiongroup",
            color_discrete_map=PROD_COLOR_MAP,
            category_orders=PROD_CATEGORY_ORDER,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- Right column: Production Line chart ---
    with col2:
        st.subheader("Production Trends")

        available_groups = [
            g
            for g in PROD_CATEGORY_ORDER["productiongroup"]
            if g in df_prod["productiongroup"].unique()
        ]

        selected_groups = st.pills(
            "Select production group(s):",
            options=available_groups,
            selection_mode="multi",
            default=st.session_state.selected_groups,
            key="selected_groups",
        )

        if selected_groups != st.session_state.selected_groups:
            st.session_state.selected_groups = selected_groups

        filtered_df = get_filtered_production(df_prod)

        line_data = (
            filtered_df.groupby(["starttime", "productiongroup"])["quantitykwh"]
            .sum()
            .reset_index()
        )

        fig_line = px.line(
            line_data,
            x="starttime",
            y="quantitykwh",
            color="productiongroup",
            title=f"Production in {price_area} ({month_names[month_int]})",
            color_discrete_map=PROD_COLOR_MAP,
            category_orders=PROD_CATEGORY_ORDER,
        )
        st.plotly_chart(fig_line, use_container_width=True)
else:
    st.warning("Production data not available.")


# =============================================================================
# CONSUMPTION SECTION
# =============================================================================
st.divider()

if has_consumption:
    st.header("🔌 Energy Consumption")
    
    col3, col4 = st.columns(2)

    # --- Left column: Consumption Pie chart ---
    with col3:
        st.subheader("Total Consumption by Sector")

        filtered_cons = get_filtered_consumption(df_cons)
        cons_pie_data = filtered_cons.groupby("consumptiongroup")["quantitykwh"].sum().reset_index()

        fig_cons_pie = px.pie(
            cons_pie_data,
            values="quantitykwh",
            names="consumptiongroup",
            title=f"{month_names[month_int]} – {price_area}",
            color="consumptiongroup",
            color_discrete_map=CONS_COLOR_MAP,
            category_orders=CONS_CATEGORY_ORDER,
        )
        st.plotly_chart(fig_cons_pie, use_container_width=True)

    # --- Right column: Consumption Line chart ---
    with col4:
        st.subheader("Consumption Trends")

        available_cons_groups = [
            g
            for g in CONS_CATEGORY_ORDER["consumptiongroup"]
            if g in df_cons["consumptiongroup"].unique()
        ]

        selected_cons_groups = st.pills(
            "Select consumption group(s):",
            options=available_cons_groups,
            selection_mode="multi",
            default=st.session_state.selected_cons_groups,
            key="selected_cons_groups",
        )

        if selected_cons_groups != st.session_state.selected_cons_groups:
            st.session_state.selected_cons_groups = selected_cons_groups

        filtered_cons = get_filtered_consumption(df_cons)

        cons_line_data = (
            filtered_cons.groupby(["starttime", "consumptiongroup"])["quantitykwh"]
            .sum()
            .reset_index()
        )

        fig_cons_line = px.line(
            cons_line_data,
            x="starttime",
            y="quantitykwh",
            color="consumptiongroup",
            title=f"Consumption in {price_area} ({month_names[month_int]})",
            color_discrete_map=CONS_COLOR_MAP,
            category_orders=CONS_CATEGORY_ORDER,
        )
        st.plotly_chart(fig_cons_line, use_container_width=True)
else:
    st.warning("Consumption data not available.")


# --- Footer info ---
with st.expander("About the data"):
    st.markdown(
        """
        **Source:** Elhub API – hourly production and consumption data  
        Data processed in Spark and stored in MongoDB  
        - Production: `production_silver` collection  
        - Consumption: `consumption_silver` collection  
        
        Charts show total energy by source/sector and trends over time.
        Use the sidebar to filter by price area, year, and month.
        """
    )
