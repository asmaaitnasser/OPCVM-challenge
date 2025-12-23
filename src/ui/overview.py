import streamlit as st
from src.app.api_overview import get_overview_metrics


def _fmt_pct(x):
    if x is None:
        return "N/A"
    try:
        return f"{float(x):.2f}%"
    except Exception:
        return "N/A"


def _fmt_num(x, digits=2, suffix=""):
    if x is None:
        return "N/A"
    try:
        return f"{float(x):.{digits}f}{suffix}"
    except Exception:
        return "N/A"


def _fmt_score_100(x):
    if x is None:
        return "N/A"
    try:
        return f"{float(x):.0f} / 100"
    except Exception:
        return "N/A"


def render():
    data = get_overview_metrics()

    st.title("📊 FundWatch AI – Dashboard")
    st.subheader("🔍 Overview – Wafa Gestion")

    # =========================
    # 1) RISQUE
    # =========================
    st.markdown("### ⚠️ Risque")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Score de risque global", _fmt_score_100(data.get("risk_score_100")))
    c2.metric(
        "Évolution vs J-1",
        "N/A" if data.get("risk_change_pct") is None else f"{data.get('risk_change_dir', '—')} {_fmt_num(data.get('risk_change_pct'), 2, '%')}",
    )
    c3.metric("Statut de risque", data.get("risk_status", "N/A"))
    c4.metric("Type anomalie dominante", data.get("dominant_anomaly_type", "N/A"))

    # =========================
    # 2) ANOMALIES
    # =========================
    st.markdown("### 🚨 Anomalies")

    a1, a2, a3 = st.columns(3)
    a1.metric("Nombre d’anomalies journalières", int(data.get("anomalies_daily", 0)))
    a2.metric("Nombre d’anomalies hebdomadaires", int(data.get("anomalies_weekly", 0)))
    # petit rappel utile
    a3.metric("Signal ML global", data.get("ml_signal", "N/A"))

    # =========================
    # 3) PERFORMANCE
    # =========================
    st.markdown("### 📈 Performance")

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Performance YTD", _fmt_pct(data.get("performance_ytd_pct")))
    p2.metric("Performance 30 jours", _fmt_pct(data.get("performance_30d_pct")))
    p3.metric("Performance hebdomadaire", _fmt_pct(data.get("performance_weekly_pct")))

    # Sur/sous perf -> on affiche en "points de %"
    out30 = data.get("outperf_30d_vs_market")
    if out30 is None:
        p4.metric("Sur/sous-perf vs marché (30j)", "N/A")
    else:
        try:
            out30 = float(out30)
            arrow = "↑" if out30 > 0 else ("↓" if out30 < 0 else "→")
            p4.metric("Sur/sous-perf vs marché (30j)", f"{arrow} {out30:.2f} pts")
        except Exception:
            p4.metric("Sur/sous-perf vs marché (30j)", "N/A")

    # =========================
    # 4) STABILITÉ & VOLATILITÉ
    # =========================
    st.markdown("### 📊 Stabilité & Volatilité")

    v1, v2, v3 = st.columns(3)
    v1.metric("Volatilité ~30 jours", _fmt_num(data.get("volatility_30d"), 6))
    v2.metric("Max drawdown ~30 jours", _fmt_num(data.get("max_drawdown_30d"), 6))
    v3.metric("Z-score moyen ~30 jours", _fmt_num(data.get("zscore_mean_30d"), 4))

    # =========================
    # 5) ML & DÉCISION + QUALITÉ DONNÉES
    # =========================
    st.markdown("### 🤖 Machine Learning & Décision")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Signal ML", data.get("ml_signal", "N/A"))
    m2.metric("Fonds analysés", int(data.get("total_funds_analyzed", 0)))
    m3.metric("Taux données valides", _fmt_pct(data.get("valid_data_pct")))
    m4.metric("Dernière mise à jour", data.get("last_update", None) or "N/A")

    # =========================
    # 6) DEBUG (optionnel)
    # =========================
    if data.get("status", "") != "success":
        st.warning(f"Statut: {data.get('status')}")
        st.json(data)
