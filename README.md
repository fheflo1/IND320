# IND320: Data to Decisions

## Project Description

This repository accompanies the IND320 course at NMBU.  
Throughout the course, I work with data collection, processing, visualization, and decision support.

### The project combines:

- an **ETL pipeline** (Elhub + meteorological data) using **PySpark** and **Cassandra/MongoDB**
- an interactive **Streamlit dashboard** for analysis and decision support

### Main tasks:

- Fetch, clean and store energy data from **Elhub** and weather data from **Open-Meteo**
- Build **bronze–silver–gold** style data pipelines
- Store data in **Cassandra** (raw/processed) and expose analysis tables via **MongoDB**
- Visualize key insights in an interactive **Streamlit** dashboard
- Run **forecasting** (SARIMAX) and weather–energy analyses

---

## Streamlit Dashboard

### App Link

👉 **Deployed app:** <https://ind320-fheflo1.streamlit.app/>

The dashboard presents energy production/consumption and meteorological data in a Power-BI–like interface to support data-driven decisions.

### Navigation (pages)

The app is organized into the following pages:

- **Home** – short description, latest snapshot and navigation help  
- **Data Overview** – high-level overview of available production/consumption data  
- **Energy Overview** – production & consumption aggregations and time-series views  
- **Energy STL & Spectrogram** – STL decomposition and frequency analysis of production  
- **Energy Forecast** – SARIMAX forecasting using weather as exogenous variables  
- **Weather Overview** – descriptive statistics and plots of meteo data  
- **Weather Outliers & Anomalies** – outlier and anomaly detection on weather series  
- **Weather & Energy Correlation** – sliding-window correlations between weather and energy  
- **Map of Price Areas** – interactive Leaflet map with price areas and linked energy data  
- **Snow Drift** – snow drift calculation and visualization based on meteo + map selection  

---

## Running the Dashboard Locally

From the project root:

```bash
pip install -r requirements.txt

# Run the Streamlit app
streamlit run apps/Home.py
The app expects that production, consumption and meteo silver tables have been loaded into MongoDB (via the notebooks described below) and are accessible through the helper functions in src/db/mongo_elhub.py.

Data Pipelines
Both Elhub and meteorological data follow a layered pipeline, implemented in notebooks and reusable Python modules.

Elhub: Bronze → Silver → Gold
Location: notebooks/elhub/

01_cassandra_setup.ipynb
Create keyspaces and tables in Cassandra for raw and processed Elhub data.

02_elhub_bronze.ipynb
Fetch raw production/consumption data from the Elhub API and store it in Cassandra (bronze).

03_elhub_silver.ipynb
Clean, standardize and enrich bronze data into analysis-ready silver tables.

04_elhub_gold.ipynb
Aggregate silver data into higher-level, business-ready gold tables (e.g. daily/weekly summaries).

05_db_connections.ipynb
Connect Cassandra ↔ MongoDB and push relevant silver/gold tables into MongoDB for use by Streamlit.

Meteo: Bronze → Silver
Location: notebooks/meteo/

01_meteo_bronze.ipynb
Download raw meteorological data (e.g. from Open-Meteo) and store in bronze tables.

02_meteo_silver.ipynb
Clean, interpolate and reshape meteo data into silver tables aligned with the Elhub data.

Reports
Location: notebooks/reports/

01_report.ipynb, 02_report.ipynb, 03_report.ipynb, 04_report.ipynb
Jupyter notebooks used to generate course deliverables; each has a corresponding exported *.pdf.

Project Structure
Using the current layout (see screenshots in the repo), the important pieces are:
```
```bash
Kopier kode
.
├─ apps/
│  ├─ .streamlit/
│  │   ├─ config.toml              # Streamlit theme/config
│  │   └─ secrets.toml             # Local secrets (ignored in Git)
│  ├─ pages/
│  │   ├─ 01_Data_Overview.py
│  │   ├─ 02_Energy_Overview.py
│  │   ├─ 03_Energy_STL_&_Spectrogram.py
│  │   ├─ 04_Energy_Forecast.py
│  │   ├─ 05_Weather_Overview.py
│  │   ├─ 06_Weather_Outliers_&_Anomalies.py
│  │   ├─ 07_Weather_&_Energy_Correlation.py
│  │   ├─ 08_Map_of_Price_Areas.py
│  │   └─ 09_Snow_Drift.py
│  └─ Home.py                      # Entry point for the dashboard
│
├─ notebooks/
│  ├─ elhub/
│  │   ├─ 01_cassandra_setup.ipynb
│  │   ├─ 02_elhub_bronze.ipynb
│  │   ├─ 03_elhub_silver.ipynb
│  │   ├─ 04_elhub_gold.ipynb
│  │   └─ 05_db_connections.ipynb
│  ├─ meteo/
│  │   ├─ 01_meteo_bronze.ipynb
│  │   └─ 02_meteo_silver.ipynb
│  └─ reports/
│      ├─ 01_report.ipynb / 01_report.pdf
│      ├─ 02_report.ipynb / 02_report.pdf
│      ├─ 03_report.ipynb / 03_report.pdf
│      └─ 04_report.ipynb
│
├─ src/
│  ├─ analysis/
│  │   ├─ __init__.py
│  │   ├─ anomaly_detection.py     # Weather/energy outlier logic
│  │   └─ plots.py                 # General plotting utilities (energy side)
│  │
│  ├─ api/
│  │   ├─ __init__.py
│  │   ├─ elhub_api.py             # Functions for calling the Elhub API
│  │   └─ meteo_api.py             # Functions for calling the meteo API
│  │
│  ├─ data/
│  │   ├─ __init__.py
│  │   └─ load_data.py             # Helpers to load data into the app
│  │
│  ├─ db/
│  │   └─ mongo_elhub.py           # MongoDB access for production/consumption tables
│  │
│  ├─ forecast/
│  │   ├─ __init__.py
│  │   └─ sarimax_utils.py         # SARIMAX prep/fit/forecast utilities
│  │
│  └─ ui/
│      ├─ __init__.py
│      ├─ sidebar_controls.py      # Shared sidebar controls for several pages
│      ├─ app_state.py             # Small helpers for managing Streamlit session state
│      └─ plots_meteo_report.py    # Meteo-specific plotting for reports/dashboard
│
├─ .cache.sqlite                   # Streamlit cache (ignored / local)
├─ .gitignore
├─ README.md                       # This file
└─ requirements.txt
```
## Technology Stack

- **Apache Cassandra** – main storage for raw and processed Elhub data used in the ETL steps  
- **MongoDB** – serves cleaned/silver/gold tables to the Streamlit dashboard  
- **Apache Spark (PySpark)** – data transformation and ETL in the notebooks  
- **Streamlit** – interactive dashboard and visualizations  
- **Python** – API calls, cleaning, modelling and analysis  
- **Statsmodels** – SARIMAX forecasting  
- **Pandas / NumPy** – data wrangling and numeric analysis

---

## Getting Started (ETL + Dashboard)

### Set up databases
Start local instances of **Cassandra** and **MongoDB** (e.g. via Docker or local services) before running the pipelines.

### Run Elhub pipeline
- notebooks/elhub/01_cassandra_setup.ipynb — create keyspaces and tables in **Cassandra**  
- notebooks/elhub/02_elhub_bronze.ipynb — ingest raw Elhub data into bronze tables  
- notebooks/elhub/03_elhub_silver.ipynb — clean, standardize and enrich into silver tables  
- notebooks/elhub/04_elhub_gold.ipynb — aggregate silver into business-ready gold tables  
- notebooks/elhub/05_db_connections.ipynb — push relevant silver/gold tables into **MongoDB**

### Run Meteo pipeline
- notebooks/meteo/01_meteo_bronze.ipynb — ingest raw meteorological data (e.g. Open‑Meteo)  
- notebooks/meteo/02_meteo_silver.ipynb — clean, interpolate and align meteo data to silver

### Install dependencies and run the dashboard
```bash
pip install -r requirements.txt
streamlit run apps/Home.py
```
- Ensure the silver tables (production, consumption and meteo) are available in **MongoDB** for the dashboard to load.
- Use the app sidebar to navigate pages, interact with filters, STL decomposition, forecasts, correlations and maps.

```bash
pip install -r requirements.txt
streamlit run apps/Home.py
```
### Explore the dashboard
- Use the navigation in the left sidebar to open the different analysis pages.
- Interact with filters, STL decomposition, forecast controls, correlation sliders, and maps to explore the data.