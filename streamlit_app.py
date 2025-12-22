import streamlit as st

from src.ui.overview import render as render_overview
from src.ui.anomaly_daily import render as render_anomaly_daily
from src.ui.anomaly_weekly import render as render_anomaly_weekly
from src.ui.projection_30j import render as render_projection_30j
from src.ui.recommendation import render as render_recommendation
from src.ui.wafa_vs_market import render as render_wafa_vs_market

st.set_page_config(
    page_title="FundWatch AI",
    layout="wide"
)

# ✅ SIDEBAR UNIQUE
st.sidebar.title("FundWatch AI")

page = st.sidebar.selectbox(
    "Navigation",
    [
        "Overview",
        "Anomaly Daily",
        "Anomaly Weekly",
        "Projection 30j",
        "Recommendation",
        "Wafa vs Market",
    ]
)

st.sidebar.markdown("---")

# ✅ ROUTING CENTRAL
if page == "Overview":
    render_overview()

elif page == "Anomaly Daily":
    render_anomaly_daily()

elif page == "Anomaly Weekly":
    render_anomaly_weekly()

elif page == "Projection 30j":
    render_projection_30j()

elif page == "Recommendation":
    render_recommendation()

elif page == "Wafa vs Market":
    render_wafa_vs_market()
