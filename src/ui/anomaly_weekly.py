import streamlit as st
import pandas as pd
from pathlib import Path

from src.app.api_anomaly_weekly import load_weekly_anomalies, get_weekly_filters

DATA_DIR = Path("src/scraper")
WEEKLY_FILE = DATA_DIR / "anomaly_results_weekly.xlsx"


def _download_excel_button():
    if not WEEKLY_FILE.exists():
        st.warning(f"Fichier introuvable: {WEEKLY_FILE}")
        return

    data = WEEKLY_FILE.read_bytes()
    st.download_button(
        label="⬇️ Télécharger anomaly_results_weekly.xlsx",
        data=data,
        file_name="anomaly_results_weekly.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render():
    st.title("Anomaly Weekly")
    st.caption("Visualisation des anomalies hebdomadaires (depuis le fichier Excel généré).")

    # Bouton download
    _download_excel_button()

    # Chargement (cache)
    try:
        df = load_weekly_anomalies()
    except Exception as e:
        st.error(str(e))
        return

    if df.empty:
        st.info("Aucune donnée weekly.")
        return

    # Filtres
    companies, funds = get_weekly_filters(df)

    colA, colB, colC = st.columns([1.2, 2.2, 1.2])
    with colA:
        company = st.selectbox("Société de gestion", companies, index=0)
    with colB:
        fund_pick = st.selectbox("Fonds (ISIN — Nom)", ["ALL"] + funds, index=0)
    with colC:
        only_anom = st.checkbox("Afficher seulement anomalies", value=False)

    dff = df.copy()

    if company != "ALL" and "SOCIETE_DE_GESTION" in dff.columns:
        dff = dff[dff["SOCIETE_DE_GESTION"] == company]

    if fund_pick != "ALL" and "CODE_ISIN" in dff.columns:
        isin = fund_pick.split("—")[0].strip()
        dff = dff[dff["CODE_ISIN"] == isin]

    if only_anom and "IS_ANOMALY" in dff.columns:
        dff = dff[dff["IS_ANOMALY"] == True]

    # KPI
    total_rows = len(dff)
    total_anom = int(dff["IS_ANOMALY"].sum()) if "IS_ANOMALY" in dff.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Lignes", total_rows)
    k2.metric("Anomalies", total_anom)
    k3.metric("% Anomalies", round((total_anom / total_rows) * 100, 2) if total_rows else 0)
    k4.metric("Nb fonds", dff["CODE_ISIN"].nunique() if "CODE_ISIN" in dff.columns else 0)

    st.divider()

    # Charts (si colonnes existent)
    if "WEEK_DATE" in dff.columns:
        # Série anomalies dans le temps
        if "IS_ANOMALY" in dff.columns:
            ts = (
                dff.groupby("WEEK_DATE")["IS_ANOMALY"]
                .sum()
                .reset_index(name="ANOMALIES")
                .sort_values("WEEK_DATE")
            )
            st.subheader("Anomalies par semaine")
            st.line_chart(ts.set_index("WEEK_DATE")[["ANOMALIES"]])

        # Courbes utiles si dispo
        numeric_cols = [c for c in ["RET_1W", "VOL_12W", "MOM_4W", "MOM_12W", "ZSCORE_1W", "DRAWDOWN"] if c in dff.columns]
        if numeric_cols:
            st.subheader("Indicateurs hebdomadaires (série temporelle)")
            tmp = dff[["WEEK_DATE"] + numeric_cols].dropna(subset=["WEEK_DATE"]).sort_values("WEEK_DATE")
            tmp = tmp.groupby("WEEK_DATE")[numeric_cols].mean()
            st.line_chart(tmp)

    st.divider()

    st.subheader("Tableau détaillé")
    # Affiche un tableau propre (colonnes clés en premier)
    preferred = [c for c in ["WEEK_DATE", "CODE_ISIN", "OPCVM", "DENOMINATION_OPCVM", "SOCIETE_DE_GESTION", "IS_ANOMALY"] if c in dff.columns]
    remaining = [c for c in dff.columns if c not in preferred]
    show_cols = preferred + remaining

    st.dataframe(dff[show_cols], use_container_width=True)
