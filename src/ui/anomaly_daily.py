import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("src/scraper")
FILE = DATA_DIR / "anomaly_results_daily.xlsx"

# Limites anti-freeze (tu peux ajuster)
MAX_CHART_POINTS_DEFAULT = 1200
MAX_TABLE_ROWS_DEFAULT = 1200


@st.cache_data(ttl=3600, show_spinner=False)
def load_daily() -> pd.DataFrame:
    if not FILE.exists():
        raise FileNotFoundError(f"Fichier introuvable: {FILE}")

    # Lecture brute
    df = pd.read_excel(FILE)

    # Normaliser noms colonnes
    df.columns = df.columns.astype(str).str.upper().str.strip()

    # Parse date (soft)
    if "DATE" in df.columns:
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

    # Normaliser colonnes filtres (soft)
    if "SOCIETE_DE_GESTION" in df.columns:
        df["SOCIETE_DE_GESTION"] = (
            df["SOCIETE_DE_GESTION"].astype(str).str.upper().str.strip()
        )

    if "CODE_ISIN" in df.columns:
        df["CODE_ISIN"] = df["CODE_ISIN"].astype(str).str.strip()

    # Convertir quelques colonnes numériques utiles si elles existent
    for c in ["ANOMALY_SCORE_IF", "VOL_20D", "DRAWDOWN", "ZSCORE_1J", "RET_1J"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def _infer_anomaly_count(df: pd.DataFrame) -> int:
    """Compter anomalies de façon robuste."""
    for c in ["ANOMALY_LABEL_IF", "ANOMALY_FLAG", "ANOMALY_LABEL", "IS_ANOMALY"]:
        if c in df.columns:
            s = df[c]
            # IF classique: -1 anomalie / 1 normal
            if c == "ANOMALY_LABEL_IF":
                return int((pd.to_numeric(s, errors="coerce") == -1).sum())

            # bool / numeric / string
            if s.dtype == bool:
                return int(s.sum())

            sn = pd.to_numeric(s, errors="coerce")
            if sn.notna().any():
                return int((sn.astype("Int64") == 1).sum())

            ss = s.astype(str).str.upper().str.strip()
            return int(ss.isin(["-1", "ANOMALY", "TRUE", "1"]).sum())
    return 0


def _downsample_time_series(df_ts: pd.DataFrame, date_col: str, max_points: int) -> pd.DataFrame:
    """
    Anti-freeze: agrège par date + downsample si trop de points.
    df_ts doit contenir date_col + colonnes numériques.
    """
    if df_ts.empty:
        return df_ts

    d = df_ts.copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[date_col]).sort_values(date_col)

    # Agrégation par date (si plusieurs lignes par jour)
    num_cols = [c for c in d.columns if c != date_col]
    d = d.groupby(pd.Grouper(key=date_col, freq="D"))[num_cols].mean(numeric_only=True).reset_index()
    d = d.dropna(subset=[date_col])

    if len(d) <= max_points:
        return d

    step = int(np.ceil(len(d) / max_points))
    return d.iloc[::step, :]


def _histogram_series(s: pd.Series, bins: int) -> pd.Series:
    """Histogramme robuste (évite value_counts() sur continu)."""
    x = pd.to_numeric(s, errors="coerce").dropna().values
    if x.size == 0:
        return pd.Series(dtype=float)

    counts, edges = np.histogram(x, bins=bins)
    labels = [f"{edges[i]:.4g}–{edges[i+1]:.4g}" for i in range(len(counts))]
    return pd.Series(counts, index=labels)


def render():
    st.title("Anomaly Daily")
    st.caption("Visualisation des anomalies quotidiennes (anomaly_results_daily.xlsx) ")

    # Download Excel (bytes)
    try:
        excel_bytes = FILE.read_bytes()
        st.download_button(
            label="⬇️ Télécharger le fichier Excel (Daily Anomalies)",
            data=excel_bytes,
            file_name=FILE.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        st.warning(f"Impossible de préparer le téléchargement: {e}")

    # Load data
    try:
        df_all = load_daily()
    except Exception as e:
        st.error(str(e))
        return

    if "CODE_ISIN" not in df_all.columns:
        st.error("Colonne CODE_ISIN introuvable dans anomaly_results_daily.xlsx")
        return

    # Options performance
    st.divider()
    colP1, colP2, colP3 = st.columns([1.2, 1.2, 1.6])
    with colP1:
        max_points = st.slider("Max points par graphe", 200, 5000, MAX_CHART_POINTS_DEFAULT, 100)
    with colP2:
        max_rows = st.slider("Max lignes tableau", 200, 20000, MAX_TABLE_ROWS_DEFAULT, 200)
    with colP3:
        fast_mode = st.toggle("Mode rapide (recommandé)", value=True, help="Agrège par date + downsample pour éviter le freeze navigateur")

    st.divider()

    # Filtres
    colA, colB, colC = st.columns([1.4, 1.4, 1.2])
    df = df_all

    # Société
    if "SOCIETE_DE_GESTION" in df.columns:
        companies = sorted([c for c in df["SOCIETE_DE_GESTION"].dropna().unique().tolist() if c and c != "NAN"])
        selected_company = colA.selectbox("Société de gestion", ["(ALL)"] + companies, index=0)
        if selected_company != "(ALL)":
            df = df[df["SOCIETE_DE_GESTION"] == selected_company]
    else:
        colA.info("Colonne SOCIETE_DE_GESTION absente → affichage ALL.")
        selected_company = "(ALL)"

    # ISIN
    isins = sorted(df["CODE_ISIN"].dropna().astype(str).unique().tolist())
    selected_isin = colB.selectbox("Fonds (CODE_ISIN)", ["(ALL)"] + isins, index=0)
    if selected_isin != "(ALL)":
        df = df[df["CODE_ISIN"].astype(str) == str(selected_isin)]

    # Date
    if "DATE" in df.columns and df["DATE"].notna().any():
        min_d = df["DATE"].min()
        max_d = df["DATE"].max()
        start, end = colC.date_input(
            "Période",
            value=(min_d.date(), max_d.date()),
            min_value=min_d.date(),
            max_value=max_d.date(),
        )
        dstart = pd.to_datetime(start)
        dend = pd.to_datetime(end) + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1)
        df = df[(df["DATE"] >= dstart) & (df["DATE"] <= dend)]
    else:
        colC.info("Pas de DATE exploitable → pas de filtre période.")

    # Résumé
    st.subheader("Résumé")
    total_rows = int(len(df))
    total_anom = _infer_anomaly_count(df)

    c1, c2, c3 = st.columns(3)
    c1.metric("Nb lignes", total_rows)
    c2.metric("Nb anomalies", total_anom)
    c3.metric("Taux anomalies (%)", round((total_anom / total_rows * 100), 2) if total_rows else 0.0)

    # Table (limit)
    st.subheader("Table (limitée)")
    if df.empty:
        st.warning("Aucune donnée après filtres.")
        return

    df_view = df
    if "DATE" in df_view.columns:
        df_view = df_view.sort_values("DATE", ascending=False)

    if fast_mode and len(df_view) > max_rows:
        st.info(f"Affichage limité à {max_rows} lignes (sur {len(df_view)}). Augmente 'Max lignes tableau' si besoin.")
        df_view = df_view.head(max_rows)

    st.dataframe(df_view, use_container_width=True, height=520)

    # Graphes
    st.subheader("Graphes (optimisés)")
    if fast_mode:
        st.caption("Mode rapide activé : agrégation par date + downsample anti-freeze.")

    # 1) Anomaly Score IF (time series)
    if "DATE" in df.columns and "ANOMALY_SCORE_IF" in df.columns:
        tmp = df[["DATE", "ANOMALY_SCORE_IF"]].dropna()
        if not tmp.empty:
            if fast_mode:
                tmp = _downsample_time_series(tmp, "DATE", max_points=max_points)
            tmp = tmp.set_index("DATE")
            st.line_chart(tmp["ANOMALY_SCORE_IF"], height=260)

    # 2) VOL / DRAWDOWN / ZSCORE (time series)
    metrics = [c for c in ["VOL_20D", "DRAWDOWN", "ZSCORE_1J"] if c in df.columns]
    if "DATE" in df.columns and metrics:
        tmp2 = df[["DATE"] + metrics].dropna()
        if not tmp2.empty:
            if fast_mode:
                tmp2 = _downsample_time_series(tmp2, "DATE", max_points=max_points)
            tmp2 = tmp2.set_index("DATE")
            st.line_chart(tmp2[metrics], height=320)

    # 3) Histogramme (vrai histogramme)
    if "ANOMALY_SCORE_IF" in df.columns:
        st.subheader("Distribution anomaly_score_if (histogramme)")
        bins = st.slider("Bins histogramme", 5, 80, 25, 5)
        hist = _histogram_series(df["ANOMALY_SCORE_IF"], bins=bins)
        if hist.empty:
            st.info("Pas de valeurs valides pour ANOMALY_SCORE_IF.")
        else:
            st.bar_chart(hist, height=260)
