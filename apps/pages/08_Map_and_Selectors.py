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
# Project imports
# ---------------------------------------------------------
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.ui.sidebar_controls import sidebar_controls


# ---------------------------------------------------------
# Page setup
# ---------------------------------------------------------
st.set_page_config(layout="wide")
st.title("Price Areas – Interactive Map (Leaflet)")


def get_production():
    """Get production data from session state."""
    df = st.session_state.get("production")
    if df is None or df.empty:
        st.error(
            "Production data not available. Please check that the app has been initialized."
        )
        st.stop()
    return df.copy()


def get_consumption():
    """Get consumption data from session state."""
    df = st.session_state.get("consumption")
    if df is None or df.empty:
        st.error(
            "Consumption data not available. Please check that the app has been initialized."
        )
        st.stop()
    return df.copy()


# ---------------------------------------------------------
# Load GeoJSON
# ---------------------------------------------------------
@st.cache_data
def load_geojson():
    with open("data/price_areas.geojson") as f:
        return json.load(f)


geojson_data = load_geojson()


# ---------------------------------------------------------
# Build polygon index + centroid lookup
# ---------------------------------------------------------
@st.cache_data
def build_polygon_index(gj):
    polys = []
    centroids = {}
    id2name = {}

    for feat in gj["features"]:
        fid = feat["properties"]["ElSpotOmr"]
        geom = shape(feat["geometry"])

        polys.append((fid, geom))
        centroids[fid] = (geom.centroid.y, geom.centroid.x)  # lat, lon
        id2name[fid] = fid

    return polys, centroids, id2name


polygons, centroids, id_to_name = build_polygon_index(geojson_data)


def find_price_area(lon, lat):
    pt = Point(lon, lat)
    for fid, poly in polygons:
        if poly.contains(pt) or poly.touches(pt):
            return fid
    return None


# ---------------------------------------------------------
# Session-state defaults (clean and consistent)
# ---------------------------------------------------------
if "selected_area" not in st.session_state:
    st.session_state.selected_area = None

if "selected_fid" not in st.session_state:
    st.session_state.selected_fid = None

if "clicked_lat" not in st.session_state:
    st.session_state.clicked_lat = None

if "clicked_lon" not in st.session_state:
    st.session_state.clicked_lon = None

# Map viewport state
if "center_lat" not in st.session_state:
    st.session_state.center_lat = 65.0

if "center_lon" not in st.session_state:
    st.session_state.center_lon = 15.0

if "zoom" not in st.session_state:
    st.session_state.zoom = 5


# ---------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------
price_area_sidebar, city, lat_sel, lon_sel, year, month = sidebar_controls()

# Manual selection override
if price_area_sidebar != st.session_state.selected_area:
    st.session_state.selected_area = price_area_sidebar
    st.session_state.clicked_lat = None
    st.session_state.clicked_lon = None

    # Move map to centroid
    if st.session_state.selected_area in centroids:
        st.session_state.center_lat, st.session_state.center_lon = centroids[
            st.session_state.selected_area
        ]


# ---------------------------------------------------------
# User choice controls for choropleth coloring
# ---------------------------------------------------------
data_type = st.sidebar.selectbox("Data Type", ["Production", "Consumption"])

df_groups = get_production() if data_type == "Production" else get_consumption()
all_groups = sorted(df_groups["group"].dropna().unique())

group_choice = st.sidebar.selectbox("Select Group", all_groups)

days_back = st.sidebar.slider("Time Interval (days)", 1, 365, 30)

latest_time = df_groups["starttime"].max()
cutoff = latest_time - pd.Timedelta(days=days_back)

df_filtered = df_groups[
    (df_groups["group"] == group_choice) & (df_groups["starttime"] >= cutoff)
]

area_mean = (
    df_filtered.groupby("pricearea")["quantitykwh"]
    .mean()
    .reset_index()
    .rename(columns={"quantitykwh": "mean_kwh"})
)

mean_lookup = dict(zip(area_mean["pricearea"], area_mean["mean_kwh"]))

colormap = cm.linear.YlOrRd_09.scale(
    area_mean["mean_kwh"].min(), area_mean["mean_kwh"].max()
)


def style_area(feature):
    pa = feature["properties"]["ElSpotOmr"]
    value = mean_lookup.get(pa)

    if value is None:
        return {"fillOpacity": 0, "color": "white", "weight": 1}

    return {
        "fillColor": colormap(value),
        "fillOpacity": 0.5,
        "color": "white",
        "weight": 1,
    }


# ---------------------------------------------------------
# Build Leaflet Map
# ---------------------------------------------------------
m = folium.Map(
    location=[st.session_state.center_lat, st.session_state.center_lon],
    zoom_start=st.session_state.zoom,
    tiles="CartoDB dark_matter",
)

# Choropleth
folium.GeoJson(
    geojson_data,
    name="Choropleth",
    style_function=style_area,
    highlight_function=lambda feat: {"weight": 0},
    tooltip=folium.GeoJsonTooltip(
        fields=["ElSpotOmr"],
        aliases=["Price Area:"],
        labels=True,
    ),
).add_to(m)

# Selected area outline (red)
if st.session_state.selected_fid:
    selected_features = [
        f
        for f in geojson_data["features"]
        if f["properties"]["ElSpotOmr"] == st.session_state.selected_fid
    ]
    folium.GeoJson(
        {"type": "FeatureCollection", "features": selected_features},
        style_function=lambda f: {
            "fillColor": "#00000000",
            "color": "red",
            "weight": 3,
        },
        highlight_function=lambda x: {"weight": 0},
    ).add_to(m)

# Click marker
if st.session_state.clicked_lat is not None:
    folium.Marker(
        location=[st.session_state.clicked_lat, st.session_state.clicked_lon],
        icon=folium.Icon(color="red"),
    ).add_to(m)


# ---------------------------------------------------------
# Render map
# ---------------------------------------------------------
map_out = st_folium(
    m,
    height=900,
    width="100%",
    key="leaflet_map",
    returned_objects=["last_clicked", "zoom", "center"],
)


# ---------------------------------------------------------
# Update states
# ---------------------------------------------------------
clicked = map_out.get("last_clicked")
if clicked:
    st.session_state.clicked_lat = clicked["lat"]
    st.session_state.clicked_lon = clicked["lng"]

    st.session_state.selected_fid = find_price_area(clicked["lng"], clicked["lat"])

if map_out.get("zoom"):
    st.session_state.zoom = map_out["zoom"]

if map_out.get("center"):
    st.session_state.center_lat = map_out["center"]["lat"]
    st.session_state.center_lon = map_out["center"]["lng"]


# ---------------------------------------------------------
# Sidebar Info
# ---------------------------------------------------------
with st.sidebar:
    st.subheader("Selection Info")

    st.write(f"Lat: {st.session_state.clicked_lat or '-'}")
    st.write(f"Lon: {st.session_state.clicked_lon or '-'}")

    if st.session_state.selected_area:
        st.success(f"Price Area: **{st.session_state.selected_area}**")
    else:
        st.error("No price area selected")


# ---------------------------------------------------------
# Load & show energy data
# ---------------------------------------------------------
st.subheader("Energy Data for Selected Price Area")

if not st.session_state.selected_area:
    st.info("Select a price area")
else:
    pa = st.session_state.selected_area

    df_prod = get_production()
    df_con = get_consumption()

    df_prod_sel = df_prod[
        (df_prod["pricearea"] == pa) & (df_prod["group"] == group_choice)
    ]

    df_con_sel = df_con[(df_con["pricearea"] == pa) & (df_con["group"] == group_choice)]

    st.write("### Production")
    st.dataframe(df_prod_sel, use_container_width=True)

    st.write("### Consumption")
    st.dataframe(df_con_sel, use_container_width=True)
