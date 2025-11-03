import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from pathlib import Path
import sys
# --- Project imports setup ---
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.ui.sidebar_controls import sidebar_controls

# --- Shared sidebar state (from all pages) ---
price_area, city, lat, lon, year, month = sidebar_controls()

# --- MongoDB client setup ---
@st.cache_resource
def get_mongo_client():
    """Initialize MongoDB client once per session."""
    return MongoClient(st.secrets["mongo"]["uri"])


@st.cache_data(ttl=600)
def load_data():
    """Load data from MongoDB and return as DataFrame (cached for 10 min)."""
    client = get_mongo_client()
    db = client["elhub"]
    collection = db["production_silver"]

    data = list(collection.find({}, {"_id": 0}))
    df = pd.DataFrame(data)

    df["starttime"] = pd.to_datetime(df["starttime"])
    df["month"] = df["starttime"].dt.month
    return df


with st.spinner("Loading data from MongoDB..."):
    df = load_data()

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

# --- Consistent color mapping for all charts ---
COLOR_MAP = {
    "hydro": "#2E8B92",     # teal
    "thermal": "#E6B800",   # warm yellow
    "solar": "#E68A00",     # orange
    "other": "#CBA0FF",     # soft purple
}
CATEGORY_ORDER = {
    "productiongroup": ["hydro", "thermal", "wind", "solar", "other"]
}


# --- Session defaults ---
if "selected_groups" not in st.session_state:
    st.session_state.selected_groups = sorted(df["productiongroup"].unique())

# --- Layout ---
col1, col2 = st.columns(2)

# --- Shared filter function ---
def get_filtered_data(df):
    filtered = df[df["pricearea"] == price_area]
    if month_int != 0:
        filtered = filtered[filtered["month"] == month_int]
    if st.session_state.selected_groups:
        filtered = filtered[
            filtered["productiongroup"].isin(st.session_state.selected_groups)
        ]
    return filtered


# --- Left column: Pie chart ---
with col1:
    st.subheader("Total Production by Energy Source")

    filtered_df = get_filtered_data(df)
    pie_data = filtered_df.groupby("productiongroup")["quantitykwh"].sum().reset_index()

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


# --- Right column: Line chart ---
with col2:
    st.subheader("Production Trends")

    available_groups = [g for g in CATEGORY_ORDER["productiongroup"] if g in df["productiongroup"].unique()]

    selected_groups = st.pills(
        "Select production group(s):",
        options=available_groups,
        selection_mode="multi",
        default=st.session_state.selected_groups,
        key="selected_groups",
    )

    if selected_groups != st.session_state.selected_groups:
        st.session_state.selected_groups = selected_groups

    filtered_df = get_filtered_data(df)

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
        color_discrete_map=COLOR_MAP,
        category_orders=CATEGORY_ORDER,
    )
    st.plotly_chart(fig_line, use_container_width=True)


# --- Footer info ---
with st.expander("ℹ️ About the data"):
    st.markdown(
        """
        **Source:** Elhub API – hourly production data (2021)  
        Data processed in Spark and stored in MongoDB (collection: `production_silver`)  
        Charts show total production by energy source and trend over time.
        """
    )
