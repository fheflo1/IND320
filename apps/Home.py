import sys
from pathlib import Path
import streamlit as st

# --- Project root setup ---
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.app_state import init_app_state


def main():
    # --- Page config ---
    st.set_page_config(
        page_title="IND320 Dashboard",
        layout="wide",
    )

    # --- Initialize app state once ---
    with st.spinner("Loading data and preloading datasets..."):
        init_app_state()

    # --- Main content ---
    st.title("IND320 — Data to Decisions Dashboard")
    st.markdown("<div style='height: 25px'></div>", unsafe_allow_html=True)

    st.info(
        """
        This dashboard presents energy production and meteorological analyses 
        for the IND320 course.  
        Use the built-in Streamlit navigation (left sidebar) to explore the sections.
        """
    )


if __name__ == "__main__":
    main()
