# src/db/mongo_elhub.py
import pandas as pd
from pymongo import MongoClient
import streamlit as st


# ---------------------------------------------------------
# 1. Connect to MongoDB (cached)
# ---------------------------------------------------------
@st.cache_resource
def get_mongo_client():
    USR, PWD = open("No_sync/MongoDB").read().splitlines()
    uri = (
        "mongodb+srv://{}:{}@ind320-cluster-fh.93gnbd4.mongodb.net/"
        "?retryWrites=true&w=majority&appName=IND320-cluster-fh"
    )
    return MongoClient(uri.format(USR, PWD))


# ---------------------------------------------------------
# 2. Load collection into Pandas
# ---------------------------------------------------------
def load_collection_as_df(collection_name: str) -> pd.DataFrame:
    """
    Load an entire MongoDB collection (production_silver or consumption_silver)
    into a Pandas DataFrame with proper timestamp conversion.
    """
    client = get_mongo_client()
    db = client["elhub"]
    col = db[collection_name]

    # Fetch all documents
    docs = list(col.find({}))
    if not docs:
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(docs)

    # Drop the MongoDB object ID
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])

    # Convert timestamps
    for colname in ["starttime", "endtime"]:
        if colname in df.columns:
            df[colname] = pd.to_datetime(df[colname])

    return df


# ---------------------------------------------------------
# 3. Convenience loaders
# ---------------------------------------------------------
@st.cache_data
def load_production_silver() -> pd.DataFrame:
    df = load_collection_as_df("production_silver")
    df = df.rename(columns={"productiongroup": "group"})
    return df


@st.cache_data
def load_consumption_silver() -> pd.DataFrame:
    df = load_collection_as_df("consumption_silver")
    df = df.rename(columns={"consumptiongroup": "group"})
    return df
