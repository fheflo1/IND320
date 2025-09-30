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

# --- CSS for large buttons with two text levels ---
st.markdown("""
<style>
div.stButton > button {
    width: 650px;
    height: 200px;
    border-radius: 16px;
    background: #804EA0;
    color: #EDEFF2;
    border: 1px solid rgba(255,255,255,0.10);
    transition: all .2s ease;
    cursor: pointer;
    text-align: center;
    padding: 20px;
}
div.stButton > button:hover {
    background: #2A2A2A;
    border-color: rgba(255,255,255,0.20);
    transform: translateY(-4px);
    box-shadow: 0 10px 30px rgba(0,0,0,.35);
}
.big-title {
    font-size: 28px;
    font-weight: bold;
    display: block;
    margin-bottom: 8px;
}
.small-sub {
    font-size: 16px;
    color: #bbb;
    display: block;
}
</style>
""", unsafe_allow_html=True)

# ---- 2x2 GRID WITH BUTTONS ----
col1, col2 = st.columns(2, gap="large")

with col1:
    if st.button("🏠 **Home**\n\n Welcome to the dashboard", key="home"):
        st.switch_page("pages/1_Home.py")

with col2:
    if st.button("📄 **DataTable**\n\n Explore raw data and tables", key="data"):
        st.switch_page("pages/2_DataTable.py")

st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)

col3, col4 = st.columns(2, gap="large")

with col3:
    if st.button("📈 **Plots**\n\n See interactive visualizations", key="plots"):
        st.switch_page("pages/3_Plots.py")

with col4:
    if st.button("🧪 **Dummy**\n\n Experimental page with test plots", key="dummy"):
        st.switch_page("pages/4_Dummy.py")