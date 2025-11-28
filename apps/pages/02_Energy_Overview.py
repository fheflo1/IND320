import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

# --- Project imports setup ---
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.ui.sidebar_controls import sidebar_controls

# --- Shared sidebar state (from all pages) ---
price_area, city, lat, lon, year, month = sidebar_controls()

# ------------------------------------------------------------
#                           PRODUCTION
# ------------------------------------------------------------

df_prod = st.session_state.get("production")
if df_prod is None or df_prod.empty:
    st.error(
        "Production data not available. Please check that the app has been initialized."
    )
    st.stop()

df_prod = df_prod.copy()
df_prod["starttime"] = pd.to_datetime(df_prod["starttime"])

# Map 'group' to 'productiongroup' if older data format
if "productiongroup" not in df_prod.columns and "group" in df_prod.columns:
    df_prod["productiongroup"] = df_prod["group"]
if "month" not in df_prod.columns:
    df_prod["month"] = df_prod["starttime"].dt.month

# Convert month string → int
try:
    month_int = int(month)
except Exception:
    month_int = 0

# Month names for titles
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

# --- Consistent color mapping for all charts ---
COLOR_MAP = {
    "hydro": "#2E8B92",  # teal
    "thermal": "#E6B800",  # yellow
    "solar": "#E68A00",  # orange
    "other": "#CBA0FF",  # soft purple
    "wind": "#009991",  # additional color for wind
}
# Same colors for consumption groups
COLOR_MAP_CON = {
    "household": "#2E8B92",  # teal
    "cabin": "#E6B800",  # yellow
    "primary": "#E68A00",  # orange
    "secondary": "#CBA0FF",  # soft purple
    "tertiary": "#009991",  # additional color for tertiary
}

CATEGORY_ORDER = {
    "productiongroup": ["hydro", "thermal", "wind", "solar", "other"],
    "consumptiongroup": ["household", "cabin", "primary", "secondary", "tertiary"],
}

# --- Session defaults ---
if "selected_groups_prod" not in st.session_state:
    st.session_state.selected_groups_prod = sorted(df_prod["productiongroup"].unique())


# --- Filtering helper ---
def get_filtered(df, group_col, selected_groups):
    filtered = df[df["pricearea"] == price_area]
    if month_int != 0:
        filtered = filtered[filtered["month"] == month_int]
    if selected_groups:
        filtered = filtered[filtered[group_col].isin(selected_groups)]
    return filtered


# ============================================================
#   PRODUCTION: PIE + LINE
# ============================================================

st.header("Production Overview")

col1, col2 = st.columns(2)

# --- Left: Pie chart ---
with col1:
    st.subheader("Total Production by Energy Source")

    filtered = get_filtered(
        df_prod, "productiongroup", st.session_state.selected_groups_prod
    )
    pie_data = filtered.groupby("productiongroup")["quantitykwh"].sum().reset_index()

    fig_pie = px.pie(
        pie_data,
        values="quantitykwh",
        names="productiongroup",
        title=f"{month_names[month_int]} – {price_area}",
        color="productiongroup",
        color_discrete_map=COLOR_MAP,
        category_orders=CATEGORY_ORDER,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# --- Right: Line chart ---
with col2:
    st.subheader("Production Trends")

    available_groups = [
        g
        for g in CATEGORY_ORDER["productiongroup"]
        if g in df_prod["productiongroup"].unique()
    ]

    selected_groups_prod = st.pills(
        "Select production group(s):",
        options=available_groups,
        selection_mode="multi",
        default=st.session_state.selected_groups_prod,
        key="selected_groups_prod",
    )

    filtered = get_filtered(df_prod, "productiongroup", selected_groups_prod)
    line_data = (
        filtered.groupby(["starttime", "productiongroup"])["quantitykwh"]
        .sum()
        .reset_index()
    )

    fig_line = px.line(
        line_data,
        x="starttime",
        y="quantitykwh",
        color="productiongroup",
        title=f"Production in {price_area} ({month_names[month_int]})",
        color_discrete_map=COLOR_MAP,
        category_orders=CATEGORY_ORDER,
    )
    st.plotly_chart(fig_line, use_container_width=True)


# Footer
with st.expander("About the data (Production)"):
    st.markdown(
        """
        **Source:** Elhub API – hourly production data (2021)  
        Data processed in Spark and stored in MongoDB (`production_silver`)  
    """
    )


# ------------------------------------------------------------
#                           CONSUMPTION
# ------------------------------------------------------------

st.divider()
st.header("Consumption Overview")

df_cons = st.session_state.get("consumption")
if df_cons is None or df_cons.empty:
    st.error(
        "Consumption data not available. Please check that the app has been initialized."
    )
    st.stop()

df_cons = df_cons.copy()
df_cons["starttime"] = pd.to_datetime(df_cons["starttime"])

if "consumptiongroup" not in df_cons.columns and "group" in df_cons.columns:
    df_cons["consumptiongroup"] = df_cons["group"]
if "month" not in df_cons.columns:
    df_cons["month"] = df_cons["starttime"].dt.month

if "selected_groups_cons" not in st.session_state:
    st.session_state.selected_groups_cons = sorted(df_cons["consumptiongroup"].unique())

col3, col4 = st.columns(2)

# --- Left: Pie chart ---
with col3:
    st.subheader("Total Consumption by Energy Source")

    filtered = get_filtered(
        df_cons, "consumptiongroup", st.session_state.selected_groups_cons
    )
    pie_data = filtered.groupby("consumptiongroup")["quantitykwh"].sum().reset_index()

    fig_pie = px.pie(
        pie_data,
        values="quantitykwh",
        names="consumptiongroup",
        title=f"{month_names[month_int]} – {price_area}",
        color="consumptiongroup",
        color_discrete_map=COLOR_MAP_CON,
        category_orders=CATEGORY_ORDER,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# --- Right: Line chart ---
with col4:
    st.subheader("Consumption Trends")

    available_groups = [
        g
        for g in CATEGORY_ORDER["consumptiongroup"]
        if g in df_cons["consumptiongroup"].unique()
    ]

    selected_groups_cons = st.pills(
        "Select consumption group(s):",
        options=available_groups,
        selection_mode="multi",
        default=st.session_state.selected_groups_cons,
        key="selected_groups_cons",
    )

    filtered = get_filtered(df_cons, "consumptiongroup", selected_groups_cons)
    line_data = (
        filtered.groupby(["starttime", "consumptiongroup"])["quantitykwh"]
        .sum()
        .reset_index()
    )

    fig_line = px.line(
        line_data,
        x="starttime",
        y="quantitykwh",
        color="consumptiongroup",
        title=f"Consumption in {price_area} ({month_names[month_int]})",
        color_discrete_map=COLOR_MAP_CON,
        category_orders=CATEGORY_ORDER,
    )
    st.plotly_chart(fig_line, use_container_width=True)


with st.expander("About the data (Consumption)"):
    st.markdown(
        """
        **Source:** Elhub API – hourly consumption data (2021)  
        Data processed in Spark and stored in MongoDB (`consumption_silver`)
    """
    )
