import streamlit as st
import pandas as pd
from pathlib import Path

DATA_DIR = Path("src/scraper")
FILE = DATA_DIR / "anomaly_results_daily.xlsx"

@st.cache_data(ttl=3600)
def load_daily():
    if not FILE.exists():
        raise FileNotFoundError(f"Fichier introuvable: {FILE}")
    df = pd.read_excel(FILE)
    df.columns = df.columns.str.upper().str.strip()
    if "DATE" in df.columns:
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    # normaliser société si présente
    if "SOCIETE_DE_GESTION" in df.columns:
        df["SOCIETE_DE_GESTION"] = df["SOCIETE_DE_GESTION"].astype(str).str.upper().str.strip()
    if "CODE_ISIN" in df.columns:
        df["CODE_ISIN"] = df["CODE_ISIN"].astype(str).str.strip()
    return df


def render():
    st.title("Anomaly Daily")
    st.caption("Visualisation des anomalies quotidiennes (depuis anomaly_results_daily.xlsx)")

    # ✅ Download button
    try:
        with open(FILE, "rb") as f:
            st.download_button(
                label="⬇️ Télécharger le fichier Excel (Daily Anomalies)",
                data=f,
                file_name="anomaly_results_daily.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    except Exception as e:
        st.warning(f"Impossible de préparer le téléchargement: {e}")

    # ✅ Load
    try:
        df = load_daily()
    except Exception as e:
        st.error(str(e))
        return

    if "CODE_ISIN" not in df.columns:
        st.error("Colonne CODE_ISIN introuvable dans anomaly_results_daily.xlsx")
        return

    # ✅ Sélection société + ISIN + période
    colA, colB, colC = st.columns([1.4, 1.4, 1.2])

    # --- Sélection société ---
    if "SOCIETE_DE_GESTION" in df.columns:
        companies = sorted([c for c in df["SOCIETE_DE_GESTION"].dropna().unique().tolist() if c and c != "NAN"])
        selected_company = colA.selectbox("Société de gestion", ["(ALL)"] + companies, index=0)

        if selected_company != "(ALL)":
            df = df[df["SOCIETE_DE_GESTION"] == selected_company]
    else:
        colA.info("Colonne SOCIETE_DE_GESTION absente → affichage ALL.")
        selected_company = "(ALL)"

    # --- Sélection ISIN ---
    isins = sorted(df["CODE_ISIN"].dropna().astype(str).unique().tolist())
    selected_isin = colB.selectbox("Fonds (CODE_ISIN)", ["(ALL)"] + isins, index=0)

    if selected_isin != "(ALL)":
        df = df[df["CODE_ISIN"].astype(str) == str(selected_isin)]

    # --- Filtre date ---
    if "DATE" in df.columns and df["DATE"].notna().any():
        min_d = df["DATE"].min()
        max_d = df["DATE"].max()
        start, end = colC.date_input(
            "Période",
            value=(min_d.date(), max_d.date()),
            min_value=min_d.date(),
            max_value=max_d.date(),
        )
        df = df[(df["DATE"] >= pd.to_datetime(start)) & (df["DATE"] <= pd.to_datetime(end))]

    # ✅ Summary
    st.subheader("Résumé")
    total_rows = len(df)

    anomaly_col = None
    for c in ["ANOMALY_LABEL_IF", "ANOMALY_FLAG", "ANOMALY_LABEL"]:
        if c in df.columns:
            anomaly_col = c
            break

    if anomaly_col:
        if df[anomaly_col].dtype != "O":
            total_anom = int((df[anomaly_col] == -1).sum())
        else:
            total_anom = int(df[anomaly_col].astype(str).isin(["-1", "ANOMALY", "1", "TRUE"]).sum())
    else:
        total_anom = 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Nb lignes", total_rows)
    c2.metric("Nb anomalies", total_anom)
    c3.metric("Taux anomalies (%)", round((total_anom / total_rows * 100), 2) if total_rows else 0.0)

    # ✅ Table
    st.subheader("Table")
    if "DATE" in df.columns:
        st.dataframe(df.sort_values("DATE", ascending=False), use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

    # ✅ Graphes
    st.subheader("Graphes")

    # 1) Anomaly Score IF
    if "DATE" in df.columns and "ANOMALY_SCORE_IF" in df.columns:
        tmp = df[["DATE", "ANOMALY_SCORE_IF"]].dropna().sort_values("DATE")
        if not tmp.empty:
            st.line_chart(tmp.set_index("DATE")["ANOMALY_SCORE_IF"])

    # 2) Volatilité / Drawdown / Zscore
    metrics = [c for c in ["VOL_20D", "DRAWDOWN", "ZSCORE_1J"] if c in df.columns]
    if "DATE" in df.columns and metrics:
        tmp2 = df[["DATE"] + metrics].dropna().sort_values("DATE")
        if not tmp2.empty:
            st.line_chart(tmp2.set_index("DATE")[metrics])

    # 3) Histogramme des scores
    if "ANOMALY_SCORE_IF" in df.columns:
        st.subheader("Distribution anomaly_score_if")
        st.bar_chart(df["ANOMALY_SCORE_IF"].dropna().value_counts().head(30))
