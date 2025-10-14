# IND320: Data to Decisions

## Project Description

This repository accompanies the IND320 course at NMBU.  
Throughout the course, I work with data collection, processing, visualization, and decision support.  
The project combines a **Streamlit dashboard** for visualization and an **ETL pipeline** built with **PySpark** and **Cassandra** to manage and analyze energy production data from Elhub.

In this project I:
- Fetch, clean, and store energy data from APIs (Elhub)
- Build data pipelines using PySpark and Cassandra
- Visualize key insights in an interactive Streamlit dashboard
- Train forecasting and machine-learning models
- Use tools such as Docker, PySpark, and Cassandra

---

## Streamlit Dashboard

### App Link
[https://ind320-fheflo1.streamlit.app/](https://ind320-fheflo1.streamlit.app/)

The dashboard presents energy and environmental data in a clear, interactive way—similar to Power BI—to support data-driven decision-making.

### Navigation
- **Home:** Overview and summary  
- **Data Table:** Filter and explore raw data  
- **Plots:** Visualize trends and KPIs  
- **Dummy:** Experimental/testing page  

---

## Local Run

To run the dashboard locally:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data Pipeline (Elhub, PySpark, Cassandra)

The data pipeline follows the **bronze–silver–gold architecture**, separating ingestion, storage, transformation, and analysis.  
Each stage is represented by a dedicated Jupyter notebook in the `notebooks/` folder, while reusable code is located in `src/`.

### Architecture Overview

| Layer  | Purpose | Example Output |
|---------|----------|----------------|
| **Bronze** | Raw data directly from the Elhub API, stored unmodified in Cassandra. | `production_raw` |
| **Silver** | Cleaned and standardized data ready for analysis. | `production_silver` |
| **Gold** | Aggregated and business-ready data for reporting and insights. | `production_summary` |

---

### Project Structure

```bash
.
├─ apps/
│  ├─ app.py
│  └─ pages/ 
│     ├─ 1_Home.py
│     ├─ 2_DataTable.py
│     ├─ 3_Plots.py
│     ├─ 4_Visualization.py
│     └─ 5_Dummy.py
│
├─ notebooks/
│  ├─ 01_cassandra_setup.ipynb        # Creates keyspaces and tables in Cassandra
│  ├─ 02_elhub_bronze.ipynb           # Fetches raw data from the Elhub API and stores it in Cassandra
│  ├─ 03_elhub_silver.ipynb           # Cleans and standardizes bronze data
│  ├─ 04_elhub_gold.ipynb             # Aggregates and analyzes silver data
│  ├─ 05_db_connections.ipynb         # Connects to MongoDB and insterts cleaned data from Cassandra 
│  └─ reports/                        # Contains exported notebooks (PDF) for course deliverables
│
├─ src/
│  ├─ api/
│  │   └── elhub_api.py               # Functions for fetching and parsing Elhub API data
│  │
│  └─ analysis/
│      └── plots.py                   # Visualizations and KPI generation
│
├─ data/
│  └── open-meteo-subset.csv
│
└─ requirements.txt
```

### Technology Stack

- **Apache Cassandra** – distributed storage for raw and processed data  
- **Apache Spark (PySpark)** – data transformation and ETL  
- **Streamlit** – dashboard and visualization  
- **Python** – API handling, data cleaning, and analysis  

---

### Getting Started

1. Start the local Cassandra service (e.g., via Homebrew or Docker).  
2. Run `01_cassandra_setup.ipynb` to create the keyspaces and tables.  
3. Run `02_elhub_bronze.ipynb` to fetch and store raw data from the Elhub API.  
4. Continue with `03_elhub_silver.ipynb` for cleaning and transformation.  
5. Optionally, use `04_elhub_gold.ipynb` for aggregation and analysis.  
6. View and explore the final data through the Streamlit dashboard.
