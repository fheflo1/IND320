import streamlit as st

st.set_page_config(page_title="IND320 Weather App", layout="wide")

st.title("IND320 – Weather Dashboard")
st.info(
    """
    This is a Streamlit app for the course IND320: Data to Decisions.\n
    So far, it contains interesting pages about meteorological data from Norway.\n
    Use the sidebar to navigate between the pages.\n
    """
)

with st.sidebar:
    st.header("Navigasjon")
    st.page_link("app.py", label="🏠 Hjem")
    st.page_link("pages/2_DataTable.py", label="📄 DataTable")
    st.page_link("pages/3_Plots.py", label="📈 Plots")
