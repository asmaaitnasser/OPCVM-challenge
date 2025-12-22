import streamlit as st

def render():
    st.title("FundWatch AI – Dashboard")
    st.subheader("Overview – Wafa Gestion")

    col1, col2, col3 = st.columns(3)

    col1.metric("Anomalies Daily", 12)
    col2.metric("Anomalies Weekly", 5)
    col3.metric("Risk Status", "HIGH")
