import sys
from pathlib import Path
import streamlit as st

# --- Project root setup ---
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.app_state import init_app_state
from src.ui.navigation import create_navigation, render_option_menu_navigation

# --- Initialize app state ---
with st.spinner("Loading data and preloading datasets..."):
    init_app_state()

# --- Create navigation (registers pages) and render custom sidebar ---
pg = create_navigation()
render_option_menu_navigation()
pg.run()
