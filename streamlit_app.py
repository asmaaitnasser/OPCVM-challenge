import os
import streamlit as st

from src.ui.overview import render as render_overview
from src.ui.anomaly_daily import render as render_anomaly_daily
from src.ui.anomaly_weekly import render as render_anomaly_weekly
from src.ui.projection_30j import render as render_projection_30j
from src.ui.recommendation import render as render_recommendation
from src.ui.wafa_vs_market import render as render_wafa_vs_market

st.set_page_config(page_title="FundWatch AI", layout="wide")

# ✅ URL du frontend React (Landing.jsx)
# Par défaut Vite = 5173. Si tu utilises Next, mets 3000.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

PAGES = [
    "Overview",
    "Anomaly Daily",
    "Anomaly Weekly",
    "Projection 30j",
    "Recommendation",
    "Wafa vs Market",
]

with st.sidebar:
    st.markdown(
        """
        <style>
          .home-link a{
            font-size: 12px;
            text-decoration: none;
            color: #6b7280;
          }
          .home-link a:hover{ text-decoration: underline; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ✅ "Accueil" (petit) -> ouvre la landing React
    st.markdown(
    f'<div class="home-link">🏠 <a href="{FRONTEND_URL}" target="_self">Accueil</a></div>',
    unsafe_allow_html=True,
)

    st.markdown("---")
    st.title("Navigation")
    page = st.selectbox("Navigation", PAGES, index=0, key="page")

# =========================
# ROUTING Streamlit
# =========================
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
