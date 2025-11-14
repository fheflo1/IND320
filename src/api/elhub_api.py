import requests
import pandas as pd
import time
from datetime import datetime, timezone, timedelta

BASE_URL = "https://api.elhub.no/energy-data/v0/price-areas"

PRICE_AREAS = ["NO1","NO2","NO3","NO4","NO5"]


def _iso_cet(dt: datetime) -> str:
    """
    Convert naive datetime to proper CET/CEST ISO8601.
    """
    if dt.tzinfo is None:
        # Auto-detect DST: EU rules → last Sunday in March/October
        # but Python handles this with zoneinfo
        from zoneinfo import ZoneInfo
        dt = dt.replace(tzinfo=ZoneInfo("Europe/Oslo"))
    return dt.isoformat()


def fetch_elhub_data(
    start_time: datetime,
    end_time: datetime,
    dataset: str = "PRODUCTION_PER_GROUP_MBA_HOUR",
    max_retries: int = 5,
) -> pd.DataFrame:
    """
    Fetch Elhub data for ALL price areas for a given dataset and range.
    Returns a flat DataFrame.
    """

    all_records = []

    for area in PRICE_AREAS:

        params = {
            "dataset": dataset,
            "startDate": _iso_cet(start_time),
            "endDate": _iso_cet(end_time),
        }

        url = f"{BASE_URL}/{area}"

        for attempt in range(max_retries):

            try:
                resp = requests.get(url, params=params, timeout=10)
                status = resp.status_code

                if status == 200:
                    data = resp.json()
                    records = _parse_elhub_response(data, area)
                    all_records.extend(records)
                    break  # done with this price area

                elif status == 204:
                    break

                elif status == 429:
                    wait = int(resp.headers.get("Retry-After", 5))
                    print(f"⚠️ Rate limited ({area}). Waiting {wait}s...")
                    time.sleep(wait)
                    continue

                elif status in (500, 503):
                    wait = 2 ** attempt
                    print(f"⚠️ Server error {status}. Retry in {wait}s...")
                    time.sleep(wait)
                    continue

                else:
                    print(f"⚠️ HTTP {status} for {url}")
                    print(resp.text[:200])
                    break

            except Exception as e:
                print(f"❌ Exception ({attempt+1}/{max_retries}): {e}")
                time.sleep(2)

    return pd.DataFrame(all_records)


def _parse_elhub_response(data: dict, area: str):
    """
    Correctly parse both "data" and "included" structures.
    """
    records = []

    # Primary structure
    for item in data.get("data", []):
        attrs = item.get("attributes", {})
        for entry in attrs.get("productionPerGroupMbaHour", []):
            entry["priceArea"] = area
            records.append(entry)

    # Secondary structure: some datasets hide data in "included"
    for inc in data.get("included", []):
        attrs = inc.get("attributes", {})
        for entry in attrs.get("productionPerGroupMbaHour", []):
            entry["priceArea"] = area
            records.append(entry)

    return records
