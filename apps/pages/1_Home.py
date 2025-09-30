import streamlit as st
import pandas as pd
from pathlib import Path
import re
from calendar import month_name

st.title("🏠 Home")

st.info("Tip: The sidebar contains shortcuts to the other pages.")


# --- Last data ---
project_root = Path(__file__).resolve().parents[2]
csv_path = project_root / "data" / "open-meteo-subset.csv"
df = pd.read_csv(csv_path)
df["time"] = pd.to_datetime(df["time"])

# --- Monthly averages widget ---

# prepare monthly averages (grouped by calendar month)
monthly_avg = df.groupby(df["time"].dt.month).mean()

# available months in the data (as numbers) and their display names
available_months = sorted(monthly_avg.index.tolist())
month_options = [f"{m} - {month_name[m]}" for m in available_months]

selected = st.selectbox("Choose month to view monthly averages", month_options)
selected_month = int(selected.split(" - ")[0])

st.subheader(f"Monthly averages — {month_name[selected_month]}")

# helper to extract unit from column name like "temperature_2m (°C)"
_unit_re = re.compile(r"\(([^)]+)\)")

# exclude the time column and non-numeric columns from widgets/display
numeric_cols = [
    c
    for c in monthly_avg.columns
    if c.lower() != "time" and pd.api.types.is_numeric_dtype(monthly_avg[c])
]

row = monthly_avg.loc[selected_month, numeric_cols]

# Display metrics in rows of 3; fall back to a table if many columns
if len(numeric_cols) <= 9:
    for i in range(0, len(numeric_cols), 3):
        cols = st.columns(3)
        for j, col_name in enumerate(numeric_cols[i : i + 3]):
            val = row[col_name]
            if pd.isna(val):
                display = "-"
            else:
                display = f"{val:.1f}"
                m = _unit_re.search(col_name)
                if m:
                    display += f" {m.group(1)}"
            # use the column name (without unit) as metric label
            label = _unit_re.sub("", col_name).strip()
            cols[j].metric(label, display)
else:
    # for many columns show a table (variable, average)
    display_df = (
        row.rename_axis("variable")
        .reset_index()
        .rename(columns={selected_month: "average"})
    )

    # nicer formatting of numeric values and units
    def fmt_val(x, cname):
        if pd.isna(x):
            return "-"
        v = f"{x:.2f}"
        m = _unit_re.search(cname)
        if m:
            v += f" {m.group(1)}"
        return v

    display_df["average"] = [fmt_val(row[c], c) for c in numeric_cols]
    st.table(display_df.set_index("variable"))
