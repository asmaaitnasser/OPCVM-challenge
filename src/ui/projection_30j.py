# src/ui/projection_30j.py
from __future__ import annotations

import streamlit as st
import pandas as pd

from src.app.api_projection_30j import (
    load_merged_risk_and_pred,
    get_companies,
    get_fund_options,
    filter_by_company,
    get_row_by_isin,
    get_download_bytes,
)


def _isin_from_option(opt: str) -> str:
    if not opt or opt == "ALL":
        return ""
    if "—" in opt:
        return opt.split("—")[0].strip().upper()
    return opt.strip().upper()


def _pct(x):
    """
    Convertit intelligemment en pourcentage:
    - si x est déjà entre 0 et 1 => *100
    - sinon garde tel quel
    """
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return None
        v = float(x)
        return round(v * 100, 2) if 0 <= v <= 1 else round(v, 2)
    except:
        return None


def _num(x):
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return None
        return float(x)
    except:
        return None


def _dist_table(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if col not in df.columns:
        return pd.DataFrame(columns=["class", "count", "pct"])
    s = df[col].dropna().astype(str)
    if s.empty:
        return pd.DataFrame(columns=["class", "count", "pct"])
    vc = s.value_counts(dropna=True)
    out = pd.DataFrame({
        "class": vc.index,
        "count": vc.values,
        "pct": (vc.values / vc.values.sum() * 100).round(2)
    })
    return out


def render():
    st.title("Projection Risque — T+1 & 30 jours")
    st.caption("Visualisation basée sur les **2 fichiers Excel ML** (pas de calcul en live).")

    # ===== Download buttons (2 fichiers) =====
    cdl1, cdl2 = st.columns(2)
    with cdl1:
        try:
            b, name = get_download_bytes("risk")
            st.download_button(
                "📥 Télécharger fund_risk_score.xlsx",
                data=b,
                file_name=name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"Download Risk indisponible: {e}")

    with cdl2:
        try:
            b, name = get_download_bytes("pred")
            st.download_button(
                "📥 Télécharger prediction_future_risk.xlsx",
                data=b,
                file_name=name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"Download Prediction indisponible: {e}")

    st.divider()

    # ===== Load merged data =====
    try:
        df = load_merged_risk_and_pred()
    except Exception as e:
        st.error(f"Erreur chargement/merge des fichiers: {e}")
        return

    if df.empty:
        st.warning("Aucune donnée trouvée après merge.")
        return

    # ===== Filters =====
    companies = get_companies(df)
    company = st.selectbox("Société de gestion", ["ALL"] + companies, index=0)

    df_c = filter_by_company(df, company)

    fund_options = get_fund_options(df_c if not df_c.empty else df)
    fund_opt = st.selectbox("Fonds (optionnel)", ["ALL"] + fund_options, index=0)
    isin = _isin_from_option(fund_opt)

    st.divider()

    # ==========================
    # SECTION 1 — T+1
    # ==========================
    st.subheader("1) Prédiction T+1 (prochain pas)")

    if df_c.empty:
        st.info("Aucun fonds pour cette société (ou colonne SOCIETE_DE_GESTION absente).")
    else:
        # KPIs société (T+1)
        nb = len(df_c)

        avg_risk_t1 = _pct(df_c["AVG_RISK_T1"].mean()) if "AVG_RISK_T1" in df_c.columns else None
        avg_high_t1 = _pct(df_c["PCT_HIGH_T1"].mean()) if "PCT_HIGH_T1" in df_c.columns else None
        avg_med_t1 = _pct(df_c["PCT_MEDIUM_T1"].mean()) if "PCT_MEDIUM_T1" in df_c.columns else None

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Nb fonds", nb)
        k2.metric("AVG_RISK_T1 (%)", "-" if avg_risk_t1 is None else avg_risk_t1)
        k3.metric("PCT_HIGH_T1 (%)", "-" if avg_high_t1 is None else avg_high_t1)
        k4.metric("PCT_MEDIUM_T1 (%)", "-" if avg_med_t1 is None else avg_med_t1)

        # Distribution T+1
        dist = _dist_table(df_c, "LAST_RISK_T1")
        cA, cB = st.columns([1, 1])
        with cA:
            st.markdown("**Répartition des classes (T+1)**")
            st.dataframe(dist, use_container_width=True, hide_index=True)
        with cB:
            if not dist.empty:
                st.bar_chart(dist.set_index("class")["count"])

        # Top table T+1
        st.markdown("**Top fonds (T+1) — tri par AVG_RISK_T1 puis %HIGH**")
        tmp = df_c.copy()
        for col in ["AVG_RISK_T1", "PCT_HIGH_T1", "PCT_MEDIUM_T1"]:
            if col in tmp.columns:
                tmp[col] = pd.to_numeric(tmp[col], errors="coerce")

        sort_cols = [c for c in ["AVG_RISK_T1", "PCT_HIGH_T1"] if c in tmp.columns]
        if sort_cols:
            tmp = tmp.sort_values(sort_cols, ascending=False)
        cols_show = [c for c in ["CODE_ISIN", "OPCVM", "SOCIETE_DE_GESTION", "LAST_RISK_T1", "AVG_RISK_T1", "PCT_HIGH_T1", "PCT_MEDIUM_T1", "NB_DAYS"] if c in tmp.columns]
        st.dataframe(tmp[cols_show].head(30), use_container_width=True, hide_index=True)

    # Fund details T+1
    if isin:
        st.markdown("### Détail fonds — T+1")
        row = get_row_by_isin(df_c if not df_c.empty else df, isin)
        if row is None:
            st.warning("ISIN introuvable.")
        else:
            name = row.get("OPCVM", "")
            soc = row.get("SOCIETE_DE_GESTION", "")
            cur_class = row.get("CURRENT_FINAL_RISK_CLASS", row.get("CURRENT_RISK_CLASS", ""))
            cur_score = _pct(row.get("CURRENT_RISK_SCORE"))

            t1_class = row.get("LAST_RISK_T1", "")
            t1_avg = _pct(row.get("AVG_RISK_T1"))
            t1_high = _pct(row.get("PCT_HIGH_T1"))
            t1_med = _pct(row.get("PCT_MEDIUM_T1"))

            h1, h2, h3, h4 = st.columns(4)
            h1.metric("Fonds", str(name)[:25])
            h2.metric("Classe actuelle", cur_class if cur_class else "-")
            h3.metric("T+1 Classe", t1_class if t1_class else "-")
            h4.metric("Score actuel (%)", "-" if cur_score is None else cur_score)

            ttab = pd.DataFrame([{
                "ISIN": isin,
                "Société": soc,
                "Actuel Classe": cur_class,
                "T+1 Classe": t1_class,
                "AVG_RISK_T1 (%)": t1_avg,
                "PCT_HIGH_T1 (%)": t1_high,
                "PCT_MEDIUM_T1 (%)": t1_med,
            }])
            st.dataframe(ttab, use_container_width=True, hide_index=True)

    st.divider()

    # ==========================
    # SECTION 2 — 30 DAYS
    # ==========================
    st.subheader("2) Projection sur 30 jours")

    if df_c.empty:
        st.info("Aucun fonds pour cette société.")
    else:
        # KPIs société (30D)
        avg_score_30 = _pct(df_c["RISK_SCORE_30D"].mean()) if "RISK_SCORE_30D" in df_c.columns else None
        avg_p_high_30 = _pct(df_c["P_HIGH_RISK_30D"].mean()) if "P_HIGH_RISK_30D" in df_c.columns else None
        avg_p_medhigh_30 = _pct(df_c["P_MEDIUM_OR_HIGH_30D"].mean()) if "P_MEDIUM_OR_HIGH_30D" in df_c.columns else None

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Nb fonds", len(df_c))
        k2.metric("RISK_SCORE_30D (%)", "-" if avg_score_30 is None else avg_score_30)
        k3.metric("P_HIGH_RISK_30D (%)", "-" if avg_p_high_30 is None else avg_p_high_30)
        k4.metric("P_MEDIUM_OR_HIGH_30D (%)", "-" if avg_p_medhigh_30 is None else avg_p_medhigh_30)

        # Distribution 30D
        dist30 = _dist_table(df_c, "FINAL_RISK_CLASS_30D")
        cA, cB = st.columns([1, 1])
        with cA:
            st.markdown("**Répartition des classes (30D)**")
            st.dataframe(dist30, use_container_width=True, hide_index=True)
        with cB:
            if not dist30.empty:
                st.bar_chart(dist30.set_index("class")["count"])

        # Top table 30D
        st.markdown("**Top fonds (30D) — tri par P_MEDIUM_OR_HIGH_30D puis P_HIGH_RISK_30D**")
        tmp = df_c.copy()
        for col in ["RISK_SCORE_30D", "P_HIGH_RISK_30D", "P_MEDIUM_OR_HIGH_30D"]:
            if col in tmp.columns:
                tmp[col] = pd.to_numeric(tmp[col], errors="coerce")

        sort_cols = [c for c in ["P_MEDIUM_OR_HIGH_30D", "P_HIGH_RISK_30D", "RISK_SCORE_30D"] if c in tmp.columns]
        if sort_cols:
            tmp = tmp.sort_values(sort_cols, ascending=False)

        cols_show = [c for c in ["CODE_ISIN", "OPCVM", "SOCIETE_DE_GESTION", "FINAL_RISK_CLASS_30D", "RISK_SCORE_30D", "P_HIGH_RISK_30D", "P_MEDIUM_OR_HIGH_30D", "NB_DAYS"] if c in tmp.columns]
        st.dataframe(tmp[cols_show].head(30), use_container_width=True, hide_index=True)

    # Fund details 30D
    if isin:
        st.markdown("### Détail fonds — 30 jours")
        row = get_row_by_isin(df_c if not df_c.empty else df, isin)
        if row is None:
            st.warning("ISIN introuvable.")
        else:
            d30_class = row.get("FINAL_RISK_CLASS_30D", "")
            d30_score = _pct(row.get("RISK_SCORE_30D"))
            p_high = _pct(row.get("P_HIGH_RISK_30D"))
            p_medhigh = _pct(row.get("P_MEDIUM_OR_HIGH_30D"))

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("30D Classe", d30_class if d30_class else "-")
            m2.metric("RISK_SCORE_30D (%)", "-" if d30_score is None else d30_score)
            m3.metric("P_HIGH_RISK_30D (%)", "-" if p_high is None else p_high)
            m4.metric("P_MEDIUM_OR_HIGH_30D (%)", "-" if p_medhigh is None else p_medhigh)

            dtab = pd.DataFrame([{
                "ISIN": isin,
                "30D Classe": d30_class,
                "RISK_SCORE_30D (%)": d30_score,
                "P_HIGH_RISK_30D (%)": p_high,
                "P_MEDIUM_OR_HIGH_30D (%)": p_medhigh,
            }])
            st.dataframe(dtab, use_container_width=True, hide_index=True)
