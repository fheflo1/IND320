from pathlib import Path
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

st.title("📈 Plots")


@st.cache_data
def load_data() -> pd.DataFrame:
    # `pages/` → repo-rot er én mappe opp
    project_root = Path().cwd()
    data_file = project_root / "data" / "open-meteo-subset.csv"

    df = pd.read_csv(data_file)
    return df


df = load_data()

if "time" not in df.columns:
    st.error("Dataframe is missing the 'time' column. Check the CSV file.")
else:
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"])

    # Choose column(s) to plot
    cols_all = [c for c in df.columns if c not in ("time",)]
    choice = st.selectbox("Choose column", options=["(All)"] + cols_all, index=0)

    # Choose month (subset for readability)
    df["month"] = df["time"].dt.to_period("M").astype(str)
    months = sorted(df["month"].unique())
    if not months:
        st.info("No data points available after filtering.")
    else:
        month_sel = st.select_slider("Choose month", options=months, value=months[0])

        dfm = df[df["month"] == month_sel]

        if dfm.empty:
            st.info(f"No data for selected month: {month_sel}")
        else:
            fig, ax = plt.subplots(figsize=(12, 5))

            if choice == "(All)":
                for c in cols_all:
                    ax.plot(dfm["time"], dfm[c], lw=1, label=c)
                ax.legend(ncol=2, fontsize=9)
            else:
                ax.plot(dfm["time"], dfm[choice], lw=1.5, label=choice)
                ax.legend(fontsize=9)

            ax.set_title(
                f"Time series – {choice if choice != '(All)' else 'all columns'} ({month_sel})"
            )
            ax.set_xlabel("Time")
            ax.set_ylabel("Value")
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            ax.tick_params(axis="x", rotation=45)
            ax.grid(alpha=0.3)
            fig.tight_layout()

            st.pyplot(fig)
            st.caption(
                "Tips: This page is just a starting point – you can later add more filters and styling."
            )
