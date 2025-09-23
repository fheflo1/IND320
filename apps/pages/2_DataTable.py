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

#st.column_config.LineChartColumn()
df = load_data()
st.subheader("Rådata")
st.dataframe(
    df,
    # Only show first month for each column using column config
    column_config={
        "time": st.column_config.LineChartColumn(
            "Tid", format="YYYY-MM-DD HH:mm", width="medium"
        ),
        "temperature_2m": st.column_config.LineChartColumn(
            "Temperatur (°C)", width="medium"
        ),
        "rain": st.column_config.LineChartColumn(
            "Nedbør (mm)", width="medium"
        ),
        "cloudcover": st.column_config.LineChartColumn(
            "Skydekke (%)", width="medium"
        ),
        "windspeed_10m": st.column_config.LineChartColumn(
            "Vindhastighet (m/s)", width="medium"
        ),
    },
    use_container_width=True,
)

st.caption("Data lastet fra `data/open-meteo-subset.csv` med caching for fart.")
