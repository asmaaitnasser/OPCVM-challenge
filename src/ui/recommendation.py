import streamlit as st
import pandas as pd

from src.app.api_recommendation import (
    load_recommendations_merged,
    load_recommendations_summary,
    get_company_options,
    filter_by_company,
    get_reco_file_bytes,
    build_reco_kpis,
)

def render():
    st.title("Recommendation")
    st.caption("Basé uniquement sur les résultats exportés (Excel) par le pipeline ML.")

    # ===== Load =====
    try:
        df_merged = load_recommendations_merged()
        df_summary = load_recommendations_summary()
    except Exception as e:
        st.error(f"Erreur de chargement des recommandations: {e}")
        st.stop()

    # ===== Download button =====
    try:
        b, fname = get_reco_file_bytes()
        st.download_button(
            label="⬇️ Télécharger le fichier Excel (recommandations)",
            data=b,
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        st.warning(f"Download indisponible: {e}")

    # ===== Company filter =====
    companies = get_company_options(df_merged)
    company = st.selectbox("Société de gestion", companies, index=0)

    df_company = filter_by_company(df_merged, company)

    # ===== KPIs =====
    kpis = build_reco_kpis(df_company)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fonds", int(kpis["total_funds"]))
    c2.metric("Avg Priority", "-" if pd.isna(kpis["avg_priority"]) else round(kpis["avg_priority"], 3))
    c3.metric("Avg Risk Score 30D", "-" if pd.isna(kpis["avg_risk_score_30d"]) else round(kpis["avg_risk_score_30d"], 3))
    c4.metric("Avg P(MEDIUM|HIGH) 30D", "-" if pd.isna(kpis["avg_p_medium_or_high_30d"]) else round(kpis["avg_p_medium_or_high_30d"], 2))

    # ===== Tabs =====
    tab1, tab2, tab3 = st.tabs(["📌 Summary", "📋 Détails", "🚨 Watchlist"])

    # ----------------
    # TAB 1: Summary
    # ----------------
    with tab1:
        st.subheader("Répartition des recommandations (SUMMARY_RECO)")

        if df_summary is None or df_summary.empty:
            st.info("La feuille SUMMARY_RECO est vide ou introuvable.")
        else:
            # si la summary contient toutes sociétés confondues, on l’affiche telle quelle
            st.dataframe(df_summary, use_container_width=True)

            # Bar chart NB_FUNDS par RECOMMENDATION si colonnes dispo
            cols = df_summary.columns
            if "RECOMMENDATION" in cols and "NB_FUNDS" in cols:
                chart_df = df_summary[["RECOMMENDATION", "NB_FUNDS"]].dropna()
                chart_df = chart_df.set_index("RECOMMENDATION")
                st.bar_chart(chart_df)

    # ----------------
    # TAB 2: Détails
    # ----------------
    with tab2:
        st.subheader("Détails par fonds")

        # tentative de colonnes principales
        cols = list(df_company.columns)
        want = []
        for c in [
            "CODE_ISIN", "OPCVM", "SOCIETE_DE_GESTION",
            "RECOMMENDATION", "PRIORITY_SCORE",
            "RISK_SCORE_30D", "AVG_RISK_SCORE_30D",
            "P_MEDIUM_OR_HIGH_30D", "AVG_P_MEDIUM_OR_HIGH_30D",
            "NB_DAYS",
        ]:
            if c in cols:
                want.append(c)

        if not want:
            st.dataframe(df_company.head(200), use_container_width=True)
        else:
            view = df_company[want].copy()

            # Tri "intelligent"
            if "PRIORITY_SCORE" in view.columns:
                view = view.sort_values("PRIORITY_SCORE", ascending=False)
            elif "AVG_PRIORITY_SCORE" in view.columns:
                view = view.sort_values("AVG_PRIORITY_SCORE", ascending=False)

            st.dataframe(view, use_container_width=True, height=520)

        # Top 15 par priorité (graph)
        if "PRIORITY_SCORE" in df_company.columns and "OPCVM" in df_company.columns:
            top = df_company[["OPCVM", "PRIORITY_SCORE"]].copy()
            top["PRIORITY_SCORE"] = pd.to_numeric(top["PRIORITY_SCORE"], errors="coerce")
            top = top.dropna().sort_values("PRIORITY_SCORE", ascending=False).head(15).set_index("OPCVM")
            st.subheader("Top 15 (Priority Score)")
            st.bar_chart(top)

    # ----------------
    # TAB 3: Watchlist
    # ----------------
    with tab3:
        st.subheader("Fonds à surveiller (WATCHLIST / KEEP_WATCH)")

        reco_col = "RECOMMENDATION" if "RECOMMENDATION" in df_company.columns else None
        if not reco_col:
            st.info("Colonne RECOMMENDATION introuvable dans ALL_FUNDS_RECO.")
            st.stop()

        watch = df_company[df_company[reco_col].astype(str).str.contains("WATCH", case=False, na=False)].copy()

        if watch.empty:
            st.success("Aucun fonds Watchlist détecté pour ce filtre.")
        else:
            # affiche trié par priorité si possible
            if "PRIORITY_SCORE" in watch.columns:
                watch["PRIORITY_SCORE"] = pd.to_numeric(watch["PRIORITY_SCORE"], errors="coerce")
                watch = watch.sort_values("PRIORITY_SCORE", ascending=False)

            st.dataframe(watch, use_container_width=True, height=520)
