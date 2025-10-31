import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient


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

    # Ensure correct types and add month column
    df["starttime"] = pd.to_datetime(df["starttime"])
    df["month"] = df["starttime"].dt.month
    return df


with st.spinner("Loading data from MongoDB..."):
    df = load_data()


col1, col2 = st.columns(2)


if "price_area" not in st.session_state:
    st.session_state.price_area = sorted(df["pricearea"].unique())[0]

if "month" not in st.session_state:
    st.session_state.month = 0  # Default to "All year"

if "selected_groups" not in st.session_state:
    st.session_state.selected_groups = sorted(df["productiongroup"].unique())


with col1:
    st.subheader("Total production by energy source")

    # Price area selection (radio)
    price_area = st.radio(
        "Select price area:",
        sorted(df["pricearea"].unique()),
        index=sorted(df["pricearea"].unique()).index(st.session_state.price_area),
        key="price_area",
    )

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

    # Filter data for price area and current month (shared with line chart)
    pie_df = df[df["pricearea"] == st.session_state.price_area]
    if st.session_state.month != 0:
        pie_df = pie_df[pie_df["month"] == st.session_state.month]

    # Aggregate for pie chart
    pie_data = pie_df.groupby("productiongroup")["quantitykwh"].sum().reset_index()

    # Pie chart
    fig_pie = px.pie(
        pie_data,
        values="quantitykwh",
        names="productiongroup",
        title=f"{month_names[st.session_state.month]} – {st.session_state.price_area}",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    st.plotly_chart(fig_pie, use_container_width=True)


with col2:
    st.subheader("Production trends")

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

    # Pills for selecting production groups
    selected_groups = st.pills(
        "Select production group(s):",
        options=sorted(df["productiongroup"].unique()),
        selection_mode="multi",
        default=st.session_state.selected_groups,
        key="selected_groups",
    )

    # Month selector
    month = st.selectbox(
        "Select month:",
        month_names.keys(),
        format_func=lambda x: month_names[x],
        index=st.session_state.month,
        key="month",
    )

    # Filter data based on selections
    line_df = df[df["pricearea"] == st.session_state.price_area]
    if st.session_state.month != 0:
        line_df = line_df[line_df["month"] == st.session_state.month]
    if st.session_state.selected_groups:
        line_df = line_df[
            line_df["productiongroup"].isin(st.session_state.selected_groups)
        ]

    # Aggregate for line chart
    line_data = (
        line_df.groupby(["starttime", "productiongroup"])["quantitykwh"]
        .sum()
        .reset_index()
    )

    # Line chart
    fig_line = px.line(
        line_data,
        x="starttime",
        y="quantitykwh",
        color="productiongroup",
        title=f"Production in {st.session_state.price_area} ({month_names[st.session_state.month]})",
    )
    st.plotly_chart(fig_line, use_container_width=True)


with st.expander("ℹ️ About the data"):
    st.markdown(
        """
    **Source:** Elhub API – hourly production data (2021)  
    Data processed in Spark and stored in MongoDB (collection: `production_silver`)  
    Charts show total production by energy source and trend over time.
    """
    )
