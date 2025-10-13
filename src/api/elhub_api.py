import requests
import pandas as pd
import time
from datetime import datetime, timezone, timedelta

BASE_URL = "https://api.elhub.no/energy-data/v0/price-areas"

def _iso_date(dt: datetime) -> str:
    """Return ISO8601 with +02:00 offset."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone(timedelta(hours=2)))
    return dt.isoformat()

def fetch_elhub_data(start_time: datetime, end_time: datetime, max_retries: int = 3) -> pd.DataFrame:
    """
    Fetch production data from Elhub API for given time range.
    Returns a flat DataFrame with hourly production per price area.
    """
    params = {
        "dataset": "PRODUCTION_PER_GROUP_MBA_HOUR",
        "startDate": _iso_date(start_time),
        "endDate": _iso_date(end_time),
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(BASE_URL, params=params)
            status = response.status_code

            if status == 200:
                data = response.json()
                return _parse_elhub_response(data)

            elif status == 204:
                print(f"ℹ️ No data for {start_time.date()} → {end_time.date()}")
                return pd.DataFrame()

            elif status == 429:
                wait = int(response.headers.get("Retry-After", 5))
                print(f"⚠️ Rate limited. Waiting {wait} seconds...")
                time.sleep(wait)
                continue

            else:
                print(f"⚠️ HTTP {status}: {response.url}")
                print(response.text[:200])
                return pd.DataFrame()

        except Exception as e:
            print(f"❌ Request failed ({attempt+1}/{max_retries}): {e}")
            time.sleep(2)

    return pd.DataFrame()


def _parse_elhub_response(data: dict) -> pd.DataFrame:
    """Flatten JSON:API structure into a DataFrame."""
    if "data" not in data:
        print("⚠️ Unexpected response keys:", data.keys())
        return pd.DataFrame()

    records = []
    for item in data["data"]:
        attrs = item.get("attributes", {})
        area_name = attrs.get("name", None)
        mba_list = attrs.get("productionPerGroupMbaHour", [])
        for mba in mba_list:
            mba["meteringgridarea"] = area_name
            records.append(mba)

    return pd.DataFrame(records)
