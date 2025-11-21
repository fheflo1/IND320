import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from shapely.geometry import shape, Point
import pandas as pd

st.set_page_config(page_title="Price Area Map", layout="wide")
st.title("🔍 Price Areas – Interactive Map (Leaflet)")


# ---------------------------------------------------------
# Load GeoJSON for NO1–NO5
# ---------------------------------------------------------
@st.cache_data
def load_price_area_geojson():
    with open("data/price_areas.geojson") as f:
        return json.load(f)

geojson_data = load_price_area_geojson()


# ---------------------------------------------------------
# Build mapping from ID → Name
# ---------------------------------------------------------
@st.cache_data
def build_id_to_name(gj):
    out = {}
    for feat in gj["features"]:
        fid = feat.get("id") or feat["properties"].get("id")
        name = feat["properties"].get("ElSpotOmr")
        if fid and name:
            out[fid] = name
    return out

id_to_name = build_id_to_name(geojson_data)


# ---------------------------------------------------------
# Build Shapely polygons for hit-testing
# ---------------------------------------------------------
@st.cache_data
def build_polygons(gj):
    polys = []
    for feat in gj["features"]:
        fid = feat.get("id") or feat["properties"].get("id")
        geom = shape(feat["geometry"])
        polys.append((fid, geom))
    return polys

polygons = build_polygons(geojson_data)


def find_price_area(lon, lat):
    """Return the polygon ID of the price area containing the point."""
    pt = Point(lon, lat)
    for fid, poly in polygons:
        if poly.contains(pt) or poly.touches(pt):
            return fid
    return None


# ---------------------------------------------------------
# Session State Defaults
# ---------------------------------------------------------
# Initial map center (Norway midpoint)
if "map_center" not in st.session_state:
    st.session_state.map_center = [64.5, 11.0]

if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 5

if "selected_point" not in st.session_state:
    st.session_state.selected_point = None  # (lat, lon)

if "selected_area" not in st.session_state:
    st.session_state.selected_area = None


# ---------------------------------------------------------
# Build Leaflet Map
# ---------------------------------------------------------
map_col, info_col = st.columns([3, 1])

with map_col:
    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=st.session_state.map_zoom,
        tiles="CartoDB dark_matter",
        control_scale=True
    )

    # Draw all price area polygons (transparent)
    folium.GeoJson(
        geojson_data,
        name="Price Areas",
        style_function=lambda f: {
            "fillOpacity": 0.35,
            "color": "white",
            "weight": 1,
        },
        highlight_function=lambda f: {
            "weight": 3,
            "color": "yellow",
            "fillOpacity": 0.5,
        },
    ).add_to(m)

    # Highlight selected area
    if st.session_state.selected_area:
        selected_features = [
            f for f in geojson_data["features"]
            if f.get("id") == st.session_state.selected_area
            or f["properties"].get("id") == st.session_state.selected_area
        ]

        if selected_features:
            folium.GeoJson(
                {"type": "FeatureCollection", "features": selected_features},
                name="Selected Area",
                style_function=lambda f: {
                    "fillOpacity": 0.15,
                    "color": "red",
                    "weight": 4,
                }
            ).add_to(m)

    # Add selected point marker
    if st.session_state.selected_point:
        lat, lon = st.session_state.selected_point
        folium.Marker(
            location=[lat, lon],
            icon=folium.Icon(color="red"),
            tooltip="Selected Point",
        ).add_to(m)

    # Render map
    map_state = st_folium(
        m,
        height=900,
        width="100%",
        returned_objects=["last_clicked", "zoom", "center"]
    )


# ---------------------------------------------------------
# Process map interaction (click, zoom, pan)
# ---------------------------------------------------------
# Update zoom / center so map stays the same after rerun
if map_state:
    if map_state.get("zoom"):
        st.session_state.map_zoom = map_state["zoom"]
    if map_state.get("center"):
        st.session_state.map_center = [
            map_state["center"]["lat"], map_state["center"]["lng"]
        ]

    # Handle click
    if map_state.get("last_clicked"):
        lat = map_state["last_clicked"]["lat"]
        lon = map_state["last_clicked"]["lng"]

        st.session_state.selected_point = (lat, lon)
        st.session_state.selected_area = find_price_area(lon, lat)

        st.rerun()


# ---------------------------------------------------------
# Right panel: Selection Info
# ---------------------------------------------------------
with info_col:
    st.subheader("Selection Info")

    if st.session_state.selected_point:
        lat, lon = st.session_state.selected_point
        st.write(f"📍 **Lat:** {lat:.6f}")
        st.write(f"📍 **Lon:** {lon:.6f}")
    else:
        st.write("➡ Click the map to select a point.")

    if st.session_state.selected_area:
        area_name = id_to_name.get(st.session_state.selected_area, "Unknown")
        st.success(f"🗺️ Price Area: **{area_name}**")
    else:
        st.error("❌ Outside known price areas")
