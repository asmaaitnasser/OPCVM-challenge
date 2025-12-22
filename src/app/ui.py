import streamlit as st

def render_overview(metrics):
    st.title("FundWatch AI – Dashboard")
    st.subheader("Overview – Wafa Gestion")

    col1, col2, col3 = st.columns(3)

    col1.metric("Anomalies Daily", metrics["anomalies_daily"])
    col2.metric("Anomalies Weekly", metrics["anomalies_weekly"])
    col3.metric("Risk Status", metrics["risk_status"])
