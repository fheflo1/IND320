from pathlib import Path
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

st.title("📈 Plots")

@st.cache_data
def load_data() -> pd.DataFrame:
    project_root = Path(__file__).resolve().parents[1]
    return pd.read_csv(project_root / "data" / "open-meteo-subset.csv")

df = load_data()
df["time"] = pd.to_datetime(df["time"])

# Velg kolonne(r)
cols_all = [c for c in df.columns if c != "time"]
choice = st.selectbox("Velg kolonne", options=["(Alle)"] + cols_all, index=0)

# Velg måned (subset for lesbarhet)
df["month"] = df["time"].dt.to_period("M").astype(str)
months = sorted(df["month"].unique())
month_sel = st.select_slider("Velg måned", options=months, value=months[0])

dfm = df[df["month"] == month_sel]

fig, ax = plt.subplots(figsize=(12, 5))

if choice == "(Alle)":
    for c in cols_all:
        ax.plot(dfm["time"], dfm[c], lw=1, label=c)
    ax.legend(ncol=2, fontsize=9)
else:
    ax.plot(dfm["time"], dfm[choice], lw=1.5, label=choice)
    ax.legend(fontsize=9)

ax.set_title(f"Tidsserie – {choice if choice!='(Alle)' else 'alle kolonner'} ({month_sel})")
ax.set_xlabel("Tid")
ax.set_ylabel("Verdi")
ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
ax.grid(alpha=0.3)

st.pyplot(fig)
st.caption("Tips: Denne siden er bare et utgangspunkt – du kan senere legge til flere filtre og styling.")
