import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from src.app.api_wafa_vs_market import (
    get_hist_file_path,
    get_30d_file_path,
    get_file_bytes,
    load_all_sheets,
    list_companies,
    filter_company,
    filter_isin,
    compute_basic_metrics,
)


def _fmt(x, digits=3):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "-"
    try:
        return round(float(x), digits)
    except Exception:
        return str(x)


def _numeric_cols(df: pd.DataFrame):
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def _render_visuals(df: pd.DataFrame, title_prefix: str):
    """
    Visualisations SAFE:
    - Table (dataframe)
    - Histogramme (matplotlib) => pas d'erreur IntervalIndex
    - Scatter (streamlit)
    - Matrice de corrélation
    """
    if df is None or df.empty:
        st.warning("Aucune donnée pour ce filtre.")
        return

    st.subheader(f"{title_prefix} — Visualisations")

    # limiter pour perf
    max_rows = st.slider(
        f"{title_prefix} — Nb lignes affichées",
        200,
        5000,
        800,
        200,
        key=f"{title_prefix}_rows",
    )
    view = df.tail(max_rows).copy()

    st.dataframe(view, use_container_width=True, height=520)

    num_cols = _numeric_cols(view)
    if len(num_cols) == 0:
        st.info("Aucune colonne numérique exploitable pour des graphes.")
        return

    # =========================
    # 1) Histogramme (matplotlib)
    # =========================
    st.markdown("**Histogramme (colonne numérique)**")
    col = st.selectbox(
        f"{title_prefix} — Colonne",
        options=num_cols,
        index=0,
        key=f"{title_prefix}_hist_col",
    )
    bins = st.slider(
        f"{title_prefix} — Bins",
        5,
        60,
        20,
        5,
        key=f"{title_prefix}_hist_bins",
    )

    s = pd.to_numeric(view[col], errors="coerce").dropna()
    if len(s) > 0:
        fig, ax = plt.subplots()
        ax.hist(s.values, bins=bins)
        ax.set_title(f"Histogramme — {col}")
        ax.set_xlabel(col)
        ax.set_ylabel("Count")
        st.pyplot(fig, use_container_width=True)
    else:
        st.info("Pas de valeurs numériques valides pour l'histogramme.")

    # =========================
    # 2) Scatter X/Y
    # =========================
    if len(num_cols) >= 2:
        st.markdown("**Scatter (X vs Y)**")
        x = st.selectbox(
            f"{title_prefix} — X",
            options=num_cols,
            index=0,
            key=f"{title_prefix}_sc_x",
        )
        y = st.selectbox(
            f"{title_prefix} — Y",
            options=num_cols,
            index=1,
            key=f"{title_prefix}_sc_y",
        )

        scat = view[[x, y]].copy()
        scat[x] = pd.to_numeric(scat[x], errors="coerce")
        scat[y] = pd.to_numeric(scat[y], errors="coerce")
        scat = scat.dropna()

        if len(scat) > 0:
            st.scatter_chart(scat, x=x, y=y)
        else:
            st.info("Pas assez de points valides pour le scatter.")

    # =========================
    # 3) Corr matrix
    # =========================
    if len(num_cols) >= 2:
        st.markdown("**Corrélation (matrice)**")
        corr = view[num_cols].corr(numeric_only=True)
        st.dataframe(corr, use_container_width=True)


def render():
    st.title("Wafa vs Market")
    st.caption("Comparaison performance & risque vs benchmark (Historique + Horizon 30 jours) — toutes feuilles.")

    # ========= Load all sheets =========
    try:
        hist_path = get_hist_file_path()
        d30_path = get_30d_file_path()

        hist_sheets = load_all_sheets(hist_path)
        d30_sheets = load_all_sheets(d30_path)
    except Exception as e:
        st.error(f"Erreur de chargement Wafa vs Market: {e}")
        st.stop()

    # ========= Download buttons =========
    colA, colB = st.columns(2)
    with colA:
        b1, f1 = get_file_bytes(hist_path)
        st.download_button(
            "⬇️ Télécharger Excel (Historique)",
            data=b1,
            file_name=f1,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with colB:
        b2, f2 = get_file_bytes(d30_path)
        st.download_button(
            "⬇️ Télécharger Excel (30 jours)",
            data=b2,
            file_name=f2,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.divider()

    # ========= Choisir une feuille “référence” pour filtres =========
    def _first_df_with_company(sheets_dict):
        for _, d in sheets_dict.items():
            if "SOCIETE_DE_GESTION" in d.columns:
                return d
        return next(iter(sheets_dict.values()))

    df_ref = _first_df_with_company(hist_sheets)
    companies = list_companies(df_ref)
    company = st.selectbox("Société de gestion", companies, index=0)

    isin = "ALL"
    if "CODE_ISIN" in df_ref.columns:
        isins = df_ref["CODE_ISIN"].dropna().astype(str).str.strip().unique().tolist()
        isins = ["ALL"] + sorted(isins)
        isin = st.selectbox("Filtrer par ISIN", isins, index=0)

    st.divider()
    show_all = st.checkbox("Afficher toutes les feuilles (Historique + 30j)", value=False)

    # ========= HISTORIQUE =========
    st.header("📈 Historique — Toutes feuilles")
    if not show_all:
        hist_sheet_name = st.selectbox("Feuille (Historique)", options=list(hist_sheets.keys()))
        df_hist = filter_isin(filter_company(hist_sheets[hist_sheet_name], company), isin)

        m = compute_basic_metrics(df_hist)
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Wafa Perf (avg)", _fmt(m["wafa_perf"]))
        c2.metric("Market Perf (avg)", _fmt(m["market_perf"]))
        c3.metric("Outperformance (avg)", _fmt(m["outperformance"]))
        c4.metric("Corr (avg)", _fmt(m["correlation"]))
        c5.metric("Beta (avg)", _fmt(m["beta"]))
        c6.metric("Sharpe (avg)", _fmt(m["sharpe"]))
        st.caption(f"Lignes: {int(m['n_rows'])}")

        _render_visuals(df_hist, f"Historique — {hist_sheet_name}")
    else:
        for sname, df in hist_sheets.items():
            with st.expander(f"Historique — Feuille: {sname}", expanded=False):
                dff = filter_isin(filter_company(df, company), isin)
                m = compute_basic_metrics(dff)
                c1, c2, c3 = st.columns(3)
                c1.metric("Outperf(avg)", _fmt(m["outperformance"]))
                c2.metric("Beta(avg)", _fmt(m["beta"]))
                c3.metric("Sharpe(avg)", _fmt(m["sharpe"]))
                st.caption(f"Lignes: {int(m['n_rows'])}")
                _render_visuals(dff, f"Historique — {sname}")

    st.divider()

    # ========= 30 JOURS =========
    st.header("🗓️ Horizon 30 jours — Toutes feuilles")
    if not show_all:
        d30_sheet_name = st.selectbox("Feuille (30 jours)", options=list(d30_sheets.keys()))
        df_30 = filter_isin(filter_company(d30_sheets[d30_sheet_name], company), isin)

        m = compute_basic_metrics(df_30)
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Wafa Perf (avg)", _fmt(m["wafa_perf"]))
        c2.metric("Market Perf (avg)", _fmt(m["market_perf"]))
        c3.metric("Outperformance (avg)", _fmt(m["outperformance"]))
        c4.metric("Corr (avg)", _fmt(m["correlation"]))
        c5.metric("Beta (avg)", _fmt(m["beta"]))
        c6.metric("Sharpe (avg)", _fmt(m["sharpe"]))
        st.caption(f"Lignes: {int(m['n_rows'])}")

        _render_visuals(df_30, f"30 jours — {d30_sheet_name}")
    else:
        for sname, df in d30_sheets.items():
            with st.expander(f"30 jours — Feuille: {sname}", expanded=False):
                dff = filter_isin(filter_company(df, company), isin)
                m = compute_basic_metrics(dff)
                c1, c2, c3 = st.columns(3)
                c1.metric("Outperf(avg)", _fmt(m["outperformance"]))
                c2.metric("Beta(avg)", _fmt(m["beta"]))
                c3.metric("Sharpe(avg)", _fmt(m["sharpe"]))
                st.caption(f"Lignes: {int(m['n_rows'])}")
                _render_visuals(dff, f"30 jours — {sname}")
