import streamlit as st
import folium
from streamlit_folium import st_folium
import branca.colormap as cm
import json
import pandas as pd
from shapely.geometry import shape, Point
from pathlib import Path
import sys

# ---------------------------------------------------------
# Project imports setup
# ---------------------------------------------------------
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# We intentionally DO NOT import sidebar_controls here
# to avoid drawing a price-area selector on this page.


# ---------------------------------------------------------
# Page setup
# ---------------------------------------------------------
st.set_page_config(layout="wide")
st.title("Price Areas – Interactive Map")


# ---------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------
def normalize_pa(code: str | None) -> str | None:
    """Normalize price-area code: remove spaces, keep None as None."""
    if code is None:
        return None
    return str(code).replace(" ", "")


def get_data(dfname: str) -> pd.DataFrame:
    """Get a dataframe from session_state and fail fast if missing."""
    df = st.session_state.get(dfname)
    if df is None or df.empty:
        st.error(f"{dfname.capitalize()} data not available. Please initialize the app.")
        st.stop()
    return df.copy()


def get_production() -> pd.DataFrame:
    return get_data("production")


def get_consumption() -> pd.DataFrame:
    return get_data("consumption")


# ---------------------------------------------------------
# Load GeoJSON (cached)
# ---------------------------------------------------------
@st.cache_data
def load_geojson():
    with open("data/price_areas.geojson") as f:
        return json.load(f)


geojson_data = load_geojson()


# ---------------------------------------------------------
# Build polygon index + centroids (cached, using NORMALIZED codes)
# ---------------------------------------------------------
@st.cache_data
def build_polygon_index(gj):
    polys = []
    centroids = {}
    norm_to_raw = {}
    for feat in gj["features"]:
        raw = feat["properties"]["ElSpotOmr"]
        fid = normalize_pa(raw)
        geom = shape(feat["geometry"])
        polys.append((fid, geom))
        centroids[fid] = (geom.centroid.y, geom.centroid.x)
        norm_to_raw[fid] = raw
    return polys, centroids, norm_to_raw


polygons, centroids, norm_to_raw = build_polygon_index(geojson_data)


def find_price_area(lon, lat):
    pt = Point(lon, lat)
    for fid, poly in polygons:
        if poly.contains(pt) or poly.touches(pt):
            return fid  # normalized id
    return None


# ---------------------------------------------------------
# Session-state defaults
# ---------------------------------------------------------
defaults = {
    "selected_area": None,   # normalized code like "NO5"
    "clicked_lat": None,
    "clicked_lon": None,
}
for key, val in defaults.items():
    st.session_state.setdefault(key, val)


# ---------------------------------------------------------
# Sidebar: ONLY analysis controls, no price-area selector
# ---------------------------------------------------------
with st.sidebar:
    st.header("Analysis Settings")

    data_type = st.selectbox("Data Type", ["Production", "Consumption"])
    df_groups = get_production() if data_type == "Production" else get_consumption()

    # Normalize pricearea column once
    df_groups = df_groups.copy()
    df_groups["pricearea"] = df_groups["pricearea"].apply(normalize_pa)

    all_groups = sorted(df_groups["group"].dropna().unique())
    group_choice = st.selectbox("Select Group", all_groups)

    days_back = st.slider("Time Interval (days)", 1, 365, 30)


# ---------------------------------------------------------
# Compute area means for choropleth (cached)
# ---------------------------------------------------------
@st.cache_data
def compute_area_mean(df: pd.DataFrame, group: str, days_back: int) -> pd.DataFrame:
    """Compute mean kWh per pricearea for a given group and time window."""
    df = df.copy()
    df["starttime"] = pd.to_datetime(df["starttime"])

    latest_time = df["starttime"].max()
    cutoff = latest_time - pd.Timedelta(days=days_back)

    df_filtered = df[(df["group"] == group) & (df["starttime"] >= cutoff)]

    area_mean = (
        df_filtered.groupby("pricearea")["quantitykwh"]
        .mean()
        .reset_index()
        .rename(columns={"quantitykwh": "mean_kwh"})
    )
    return area_mean


area_mean = compute_area_mean(df_groups, group_choice, days_back)
mean_lookup = dict(zip(area_mean["pricearea"], area_mean["mean_kwh"]))


# ---------------------------------------------------------
# Cached colormap
# ---------------------------------------------------------
@st.cache_resource
def build_colormap(vmin, vmax):
    return cm.linear.YlOrRd_09.scale(vmin, vmax)


if not area_mean.empty:
    colormap = build_colormap(area_mean["mean_kwh"].min(), area_mean["mean_kwh"].max())
else:
    colormap = build_colormap(0, 1)  # fallback


def style_area(feature):
    raw_pa = feature["properties"]["ElSpotOmr"]
    pa = normalize_pa(raw_pa)
    val = mean_lookup.get(pa)
    if val is None:
        return {"fillOpacity": 0, "color": "orange", "weight": 1}
    return {
        "fillColor": colormap(val),
        "fillOpacity": 0.6,
        "color": "white",
        "weight": 1,
    }


# ---------------------------------------------------------
# Create base map
# ---------------------------------------------------------
def create_base_map(geojson_data):
    # Center either on selected area or on Norway as default
    if st.session_state.selected_area and st.session_state.selected_area in centroids:
        center = centroids[st.session_state.selected_area]
    else:
        center = (65.0, 15.0)

    m = folium.Map(
        location=list(center),
        zoom_start=5,
        tiles="OpenStreetMap",
    )

    # Base boundaries without hover highlight (no blue box)
    folium.GeoJson(
        geojson_data,
        name="Price Areas",
        style_function=lambda f: {"color": "white", "weight": 1, "fillOpacity": 0},
        highlight_function=lambda x: {"weight": 0},
    ).add_to(m)

    return m


# ---------------------------------------------------------
# Add dynamic layers (choropleth + selected border + marker)
# ---------------------------------------------------------
def add_dynamic_layers(m):
    """Add colored polygons, selected area outline, and click marker."""

    # Choropleth with tooltip showing price area
    folium.GeoJson(
        geojson_data,
        name="Choropleth",
        style_function=style_area,
        tooltip=folium.GeoJsonTooltip(
            fields=["ElSpotOmr"],
            aliases=["Price Area:"],
            labels=True,
        ),
    ).add_to(m)

    # Selected area border (match normalized id to raw feature id)
    if st.session_state.selected_area:
        sel_norm = st.session_state.selected_area
        sel_features = [
            f
            for f in geojson_data["features"]
            if normalize_pa(f["properties"]["ElSpotOmr"]) == sel_norm
        ]
        if sel_features:
            folium.GeoJson(
                {"type": "FeatureCollection", "features": sel_features},
                style_function=lambda f: {
                    "fillColor": "#00000000",
                    "color": "red",
                    "weight": 3,
                },
            ).add_to(m)

    # Click marker (pointer)
    if st.session_state.clicked_lat is not None and st.session_state.clicked_lon is not None:
        folium.Marker(
            location=[st.session_state.clicked_lat, st.session_state.clicked_lon],
            icon=folium.Icon(color="red"),
        ).add_to(m)

    return m


# ---------------------------------------------------------
# Render the dynamic map
#   returned_objects only has "last_clicked"
#   → panning/zooming does NOT trigger reruns.
#   → app reruns only when user clicks.
# ---------------------------------------------------------
base_map = create_base_map(geojson_data)
dynamic_map = add_dynamic_layers(base_map)

map_out = st_folium(
    dynamic_map,
    height=850,
    use_container_width=True,
    key="folium_map",
    returned_objects=["last_clicked"],
)

# ---------------------------------------------------------
# Update state from map click
# ---------------------------------------------------------
if map_out.get("last_clicked"):
    lat = map_out["last_clicked"]["lat"]
    lon = map_out["last_clicked"]["lng"]

    if (lat, lon) != (st.session_state.clicked_lat, st.session_state.clicked_lon):
        st.session_state.clicked_lat = lat
        st.session_state.clicked_lon = lon

        area_norm = find_price_area(lon, lat)  # normalized id (e.g. "NO5")
        st.session_state.selected_area = area_norm


# ---------------------------------------------------------
# Sidebar Info (no price area selector, just info)
# ---------------------------------------------------------
with st.sidebar:
    st.subheader("Selection Info")
    st.write(f"Lat: {st.session_state.clicked_lat or '-'}")
    st.write(f"Lon: {st.session_state.clicked_lon or '-'}")

    if st.session_state.selected_area:
        raw_label = norm_to_raw.get(st.session_state.selected_area, st.session_state.selected_area)
        st.success(f"Price Area: **{raw_label}**")
    else:
        st.info("Click on the map to select a price area.")


# ---------------------------------------------------------
# ENERGY TABLE (Only show relevant type, after click)
# ---------------------------------------------------------
st.subheader(f"{data_type} Data for Selected Price Area")

if not st.session_state.selected_area:
    st.info("Click on the map to select a price area.")
else:
    pa_norm = st.session_state.selected_area

    # Use the SAME normalized pricearea column as earlier
    df_sel = df_groups[
        (df_groups["pricearea"] == pa_norm) & (df_groups["group"] == group_choice)
    ]

    if df_sel.empty:
        st.warning(f"No {data_type.lower()} data available for this area and group.")
    else:
        st.dataframe(df_sel, use_container_width=True)
