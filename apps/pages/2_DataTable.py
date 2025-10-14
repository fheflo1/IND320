from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))
import streamlit as st
from src.data import load_csv
from src.analysis.plots import prepare_first_month_table

st.title("📄 DataTable")


@st.cache_data(ttl=600)
def get_data():
    """Load CSV data and cache it for 10 minutes."""
    return load_csv()


@st.cache_data(ttl=600)
def prepare_data(df):
    """Prepare additional tables or visualizations (cached separately)."""
    return prepare_first_month_table(df)


df = get_data()

st.subheader("Raw Data (First 100 Rows)")
st.dataframe(df.head(100), width="stretch")

# Bruk hjelpefunksjonen fra plots.py
df_rows, first_month = prepare_first_month_table(df)

st.subheader("Line Chart of Raw Data for First Month")

st.dataframe(
    df_rows,
    column_config={
        "column": st.column_config.TextColumn("Column", width="small"),
        "first_month": st.column_config.LineChartColumn(
            "First month (values)",
            help="Values for the first month in the dataset",
            width="large",
            y_min=None,
            y_max=None,
        ),
    },
    hide_index=True,
    width="stretch",
    height=1035,
    row_height=200,
)

st.caption(f"Shows first month: {first_month}. Non-numeric columns are excluded.")
