from pathlib import Path
import pandas as pd
import streamlit as st

st.title("📄 DataTable")


@st.cache_data
def load_data() -> pd.DataFrame:
    # `pages/` → repo-rot er én mappe opp
    project_root = Path().cwd()
    data_file = project_root / "data" / "open-meteo-subset.csv"

    df = pd.read_csv(data_file)
    return df


# st.column_config.LineChartColumn()
df = load_data()
st.subheader("Raw Data (First 100 Rows)")

st.dataframe(df.head(100), width="stretch")

# Finn første måned i datasettet og filtrer til den
df["time"] = pd.to_datetime(df["time"])
first_month = df["time"].dt.to_period("M").min()
fm = df[df["time"].dt.to_period("M") == first_month].reset_index(drop=True)

# Ta kun numeriske kolonner (utelukk 'time')
num_cols = fm.select_dtypes(include="number").columns.tolist()

# Bygg en rad per kolonne med verdiene for første måned som liste
rows = [
    {"column": col, "first_month": fm[col].astype(float).tolist()} for col in num_cols
]
df_rows = pd.DataFrame(rows)

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
