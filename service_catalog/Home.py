"""Infrahub Service Catalog - Main Application Entry Point."""

import streamlit as st  # type: ignore[import-untyped]
from utils import display_logo

# Configure page layout - must be first Streamlit command
st.set_page_config(
    page_title="Infrahub Service Catalog",
    page_icon="mdi:server",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

# Display logo in sidebar
display_logo()

# Define pages with hierarchical structure
home_page = st.Page("pages/0_Dashboard.py", title="Home", icon=":material/home:", default=True, url_path="dashboard")

service_catalog_pages = [
    st.Page("pages/1_Create_Segment.py", title="Add Network Segment", icon=":material/lan:"),
    st.Page("pages/2_Add_Server.py", title="Add Server", icon=":material/dns:"),
    st.Page("pages/3_Create_Tenant.py", title="Create Tenant", icon=":material/group:"),
]

visibility_pages = [
    st.Page("pages/4_Fabric_View.py", title="Fabric Design", icon=":material/account_tree:"),
]

# Create navigation with sections
pg = st.navigation(
    {
        "": [home_page],
        "Service Catalog": service_catalog_pages,
        "Visibility": visibility_pages,
    }
)

# Run the selected page
pg.run()
