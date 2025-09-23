import streamlit as st

st.set_page_config(page_title="IND320 Weather App", layout="wide")

st.title("IND320 – Weather Dashboard")
st.write(
    "Velkommen! Dette er forsiden til din Streamlit-app. "
    "Bruk sidemenyen for å navigere videre."
)

with st.sidebar:
    st.header("Navigasjon")
    st.page_link("app.py", label="🏠 Hjem")
    st.page_link("pages/2_DataTable.py", label="📄 DataTable")
    st.page_link("pages/3_Plots.py", label="📈 Plots")
    st.page_link("pages/4_Dummy.py", label="🧪 Dummy")
