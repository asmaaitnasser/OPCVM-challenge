import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st
from datetime import datetime, timedelta

DATA_DIR = Path("src/scraper")
WAFA_NAME = "WAFA GESTION"

# ======================================================
# Helpers (anti-erreurs)
# ======================================================
def _safe_read_excel(path: Path, sheet_name=None) -> pd.DataFrame:
    """Lit un excel sans crash. Si fichier/feuille absent -> DataFrame vide."""
    try:
        if not path.exists():
            return pd.DataFrame()
        if sheet_name is None:
            return pd.read_excel(path)
        # si sheet_name existe, sinon fallback première feuille
        xls = pd.ExcelFile(path)
        if sheet_name in xls.sheet_names:
            return pd.read_excel(path, sheet_name=sheet_name)
        return pd.read_excel(path, sheet_name=xls.sheet_names[0])
    except Exception:
        return pd.DataFrame()

def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    df.columns = df.columns.astype(str).str.upper().str.strip()
    return df

def _to_datetime_col(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if df.empty:
        return df
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def _is_wafa(df: pd.DataFrame) -> pd.Series:
    if df.empty or "SOCIETE_DE_GESTION" not in df.columns:
        return pd.Series([False] * len(df))
    return (
        df["SOCIETE_DE_GESTION"]
        .astype(str)
        .str.upper()
        .str.contains("WAFA", na=False)
    )

def _pick_col(df: pd.DataFrame, candidates) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None

def _as_percent(x: float) -> float:
    """Convertit un ratio en %, et garde un % si déjà en %."""
    if pd.isna(x):
        return np.nan
    try:
        x = float(x)
    except Exception:
        return np.nan
    # heuristique: si petit (|x|<=1.5) => ratio, sinon déjà %
    if abs(x) <= 1.5:
        return x * 100.0
    return x

def _risk_to_num(s: str) -> int:
    s = str(s).upper().strip()
    if s in ["NORMAL", "OK", "LOW", "LOW_RISK", "LOWRISK"]:
        return 1 if s != "NORMAL" else 0
    if s in ["MEDIUM", "MEDIUM_RISK", "MEDIUMRISK"]:
        return 2
    if s in ["HIGH", "HIGH_RISK", "HIGHRISK", "CRITICAL"]:
        return 3
    return 0

def _risk_num_to_label(n: float) -> str:
    if pd.isna(n):
        return "UNKNOWN"
    if n >= 2.5:
        return "HIGH_RISK"
    if n >= 1.5:
        return "MEDIUM_RISK"
    if n >= 0.5:
        return "LOW_RISK"
    return "NORMAL"

def _anomaly_mask(df: pd.DataFrame) -> pd.Series:
    """Détecte les lignes anomalie selon colonnes disponibles."""
    if df.empty:
        return pd.Series([], dtype=bool)

    cols = df.columns
    # Plusieurs conventions possibles dans tes fichiers
    if "ANOMALY_LABEL_IF" in cols:
        return df["ANOMALY_LABEL_IF"].fillna(0).astype(float).eq(-1)
    if "ANOMALY_FLAG_IF" in cols:
        return df["ANOMALY_FLAG_IF"].fillna(0).astype(int).eq(1)
    if "ANOMALY_DAILY_FLAG" in cols:
        return df["ANOMALY_DAILY_FLAG"].fillna(0).astype(int).eq(1)
    if "ANOMALY_WEEKLY_FLAG" in cols:
        return df["ANOMALY_WEEKLY_FLAG"].fillna(0).astype(int).eq(1)

    # fallback: si aucune colonne => considérer "tout" comme évènement (évite crash)
    return pd.Series([True] * len(df))

def _dominant_anomaly_type(df_anom: pd.DataFrame) -> str:
    """
    Retourne: 'volatilité' / 'drawdown' / 'z-score' / 'mixte'
    Basé sur les anomalies daily (ou cross) selon colonnes disponibles.
    """
    if df_anom.empty:
        return "N/A"

    # on essaie de scorer quel facteur "explique" le + les anomalies
    # z-score: abs(ZSCORE_1J) ; drawdown: abs(DRAWDOWN) ; vol: VOL_20D
    z_col = _pick_col(df_anom, ["ZSCORE_1J", "ZSCORE", "Z_SCORE", "ZSCORE_1D"])
    d_col = _pick_col(df_anom, ["DRAWDOWN", "MAX_DRAWDOWN", "DD"])
    v_col = _pick_col(df_anom, ["VOL_20D", "VOL_30D", "VOLATILITY_30D", "VOLATILITY"])

    scores = {"z-score": 0, "drawdown": 0, "volatilité": 0}

    for _, r in df_anom.iterrows():
        z = abs(float(r[z_col])) if z_col in df_anom.columns and pd.notna(r.get(z_col)) else 0.0
        d = abs(float(r[d_col])) if d_col in df_anom.columns and pd.notna(r.get(d_col)) else 0.0
        v = float(r[v_col]) if v_col in df_anom.columns and pd.notna(r.get(v_col)) else 0.0

        best = max([("z-score", z), ("drawdown", d), ("volatilité", v)], key=lambda t: t[1])[0]
        if (z + d + v) == 0:
            continue
        scores[best] += 1

    if sum(scores.values()) == 0:
        return "mixte"

    return max(scores.items(), key=lambda kv: kv[1])[0]


@st.cache_data(ttl=3600)
def load_data():
    """
    Charge TOUS les fichiers utiles (sans crash).
    """
    df_daily = _normalize_cols(_safe_read_excel(DATA_DIR / "anomaly_results_daily.xlsx"))
    df_weekly = _normalize_cols(_safe_read_excel(DATA_DIR / "anomaly_results_weekly.xlsx"))
    df_cross = _normalize_cols(_safe_read_excel(DATA_DIR / "anomaly_cross_daily_weekly.xlsx"))
    df_risk = _normalize_cols(_safe_read_excel(DATA_DIR / "fund_risk_score.xlsx", sheet_name="ALL_FUNDS"))
    if df_risk.empty:
        # fallback si pas de feuille ALL_FUNDS
        df_risk = _normalize_cols(_safe_read_excel(DATA_DIR / "fund_risk_score.xlsx"))

    df_pred = _normalize_cols(_safe_read_excel(DATA_DIR / "prediction_future_risk.xlsx", sheet_name="PROJECTION_30D_ALL"))
    if df_pred.empty:
        df_pred = _normalize_cols(_safe_read_excel(DATA_DIR / "prediction_future_risk.xlsx"))

    df_perf = _normalize_cols(_safe_read_excel(DATA_DIR / "performance_quotidienne_asfim_clean.xlsx"))
    return df_daily, df_weekly, df_cross, df_risk, df_pred, df_perf


def get_overview_metrics():
    """
    KPI OVERVIEW demandés:
    - Score risque global (0-100)
    - Evolution risque vs J-1
    - Type anomalie dominante (vol / drawdown / zscore)
    - Perf YTD / 30j / hebdo + sur/sous-perf vs marché
    - Volatilité 30j / max drawdown / z-score moyen
    - Signal ML global (STABLE / MONITOR / REDUCE)
    - Qualité des données: total fonds, % valide, dernière MAJ
    """
    try:
        df_daily, df_weekly, df_cross, df_risk, df_pred, df_perf = load_data()

        # Parse dates (si présentes)
        df_daily = _to_datetime_col(df_daily, "DATE")
        df_cross = _to_datetime_col(df_cross, "DATE")
        df_weekly = _to_datetime_col(df_weekly, "WEEK_DATE")
        df_perf = _to_datetime_col(df_perf, "DATE")
        df_risk = _to_datetime_col(df_risk, "DATE")  # parfois absent
        df_pred = _to_datetime_col(df_pred, "DATE")  # généralement absent dans projection 30d

        # ======================================================
        # 0) DATA QUALITY + LAST UPDATE
        # ======================================================
        total_funds = int(df_risk["CODE_ISIN"].nunique()) if "CODE_ISIN" in df_risk.columns and not df_risk.empty else 0

        # taux de données valides: sur cross (dernier 30j) si possible
        valid_pct = np.nan
        last_update = None

        # last_update: max des dates dispo
        dates_candidates = []
        for _df, col in [(df_daily, "DATE"), (df_cross, "DATE"), (df_weekly, "WEEK_DATE"), (df_perf, "DATE")]:
            if not _df.empty and col in _df.columns:
                dmax = _df[col].dropna().max()
                if pd.notna(dmax):
                    dates_candidates.append(dmax)

        if dates_candidates:
            last_update = max(dates_candidates).isoformat()

        # valid % from cross last 30 days if date exists
        if not df_cross.empty and "DATE" in df_cross.columns:
            dmax = df_cross["DATE"].dropna().max()
            if pd.notna(dmax):
                cutoff = dmax - pd.Timedelta(days=30)
                sub = df_cross[df_cross["DATE"] >= cutoff].copy()
                core_cols = [c for c in ["RET_1J", "ZSCORE_1J", "VOL_20D", "DRAWDOWN", "ANOMALY_COMBINED_SCORE", "RISK_LEVEL"] if c in sub.columns]
                if len(core_cols) >= 2 and len(sub) > 0:
                    valid_pct = (sub[core_cols].notna().all(axis=1).mean()) * 100.0

        # fallback valid_pct
        if pd.isna(valid_pct):
            # si pas cross: on estime via perf
            if not df_perf.empty:
                cols = [c for c in ["YTD", "1_MOIS", "1_SEMAINE"] if c in df_perf.columns]
                if cols:
                    valid_pct = (df_perf[cols].notna().all(axis=1).mean()) * 100.0
                else:
                    valid_pct = 0.0
            else:
                valid_pct = 0.0

        # ======================================================
        # 1) ANOMALIES daily/weekly (WAFA)
        # ======================================================
        daily_wafa = df_daily[_is_wafa(df_daily)] if not df_daily.empty else pd.DataFrame()
        weekly_wafa = df_weekly[_is_wafa(df_weekly)] if not df_weekly.empty else pd.DataFrame()

        anomalies_daily = int(_anomaly_mask(daily_wafa).sum()) if not daily_wafa.empty else 0
        anomalies_weekly = int(_anomaly_mask(weekly_wafa).sum()) if not weekly_wafa.empty else 0

        # ======================================================
        # 2) RISK SCORE GLOBAL (0-100) + RISK STATUS (WAFA)
        # ======================================================
        risk_status = "UNKNOWN"
        risk_score_100 = np.nan

        risk_wafa = df_risk[_is_wafa(df_risk)] if not df_risk.empty else pd.DataFrame()

        # risk score numeric: basé sur RISK_SCORE (0..3) => *100/3
        if not risk_wafa.empty:
            if "RISK_SCORE" in risk_wafa.columns:
                mean_rs = risk_wafa["RISK_SCORE"].astype(float).replace([np.inf, -np.inf], np.nan).dropna().mean()
                if pd.notna(mean_rs):
                    risk_score_100 = float(np.clip((mean_rs / 3.0) * 100.0, 0.0, 100.0))

            # risk class: prendre la "pire" classe ou la plus fréquente
            class_col = _pick_col(risk_wafa, ["FINAL_RISK_CLASS", "RISK_CLASS", "RISK_LEVEL", "RISK_STATUS"])
            if class_col:
                # pire classe (max num) pour éviter de minimiser
                tmp = risk_wafa[class_col].astype(str).map(_risk_to_num)
                if tmp.notna().any():
                    risk_status = _risk_num_to_label(tmp.max())

        # fallback risk score if missing
        if pd.isna(risk_score_100):
            # approxim via pct medium/high si dispo
            if not risk_wafa.empty and "PCT_MEDIUM_HIGH" in risk_wafa.columns:
                x = risk_wafa["PCT_MEDIUM_HIGH"].astype(float).replace([np.inf, -np.inf], np.nan).dropna().mean()
                if pd.notna(x):
                    risk_score_100 = float(np.clip(x, 0.0, 100.0))
            else:
                risk_score_100 = 0.0

        # ======================================================
        # 3) EVOLUTION RISQUE vs J-1 (sur cross)
        # ======================================================
        risk_change_pct = np.nan
        risk_change_dir = "—"

        cross_wafa = df_cross[_is_wafa(df_cross)] if not df_cross.empty else pd.DataFrame()
        if not cross_wafa.empty and "DATE" in cross_wafa.columns:
            cross_wafa = cross_wafa.dropna(subset=["DATE"]).sort_values("DATE")
            if "RISK_LEVEL" in cross_wafa.columns:
                cross_wafa["_RISK_NUM"] = cross_wafa["RISK_LEVEL"].astype(str).map(_risk_to_num)
            elif "RISK_LEVEL_NUM" in cross_wafa.columns:
                cross_wafa["_RISK_NUM"] = pd.to_numeric(cross_wafa["RISK_LEVEL_NUM"], errors="coerce")
            else:
                cross_wafa["_RISK_NUM"] = np.nan

            # moyenne par date
            by_date = cross_wafa.groupby(cross_wafa["DATE"].dt.date)["_RISK_NUM"].mean().dropna()
            if len(by_date) >= 2:
                today = float(by_date.iloc[-1])
                prev = float(by_date.iloc[-2])
                if prev != 0:
                    risk_change_pct = ((today - prev) / abs(prev)) * 100.0
                else:
                    risk_change_pct = 0.0 if today == 0 else 100.0

                if risk_change_pct > 0:
                    risk_change_dir = "↑"
                elif risk_change_pct < 0:
                    risk_change_dir = "↓"
                else:
                    risk_change_dir = "→"

        # ======================================================
        # 4) TYPE D’ANOMALIE DOMINANTE
        # ======================================================
        dom_type = "N/A"
        if not daily_wafa.empty:
            anom_rows = daily_wafa[_anomaly_mask(daily_wafa)]
            dom_type = _dominant_anomaly_type(anom_rows)
        elif not cross_wafa.empty:
            dom_type = _dominant_anomaly_type(cross_wafa)

        # ======================================================
        # 5) PERFORMANCE (YTD / 30j / hebdo) + SUR/SOUS PERF
        # ======================================================
        perf_ytd = np.nan
        perf_30d = np.nan
        perf_w = np.nan
        outperf_ytd = np.nan
        outperf_30d = np.nan
        outperf_w = np.nan

        if not df_perf.empty:
            # pour être safe, on prend le dernier snapshot par fund (si DATE dispo)
            perf_df = df_perf.copy()
            if "DATE" in perf_df.columns:
                perf_df = perf_df.dropna(subset=["DATE"]).sort_values("DATE")
                if "CODE_ISIN" in perf_df.columns:
                    perf_df = perf_df.groupby("CODE_ISIN", as_index=False).tail(1)

            wafa_perf = perf_df[_is_wafa(perf_df)]
            market_perf = perf_df[~_is_wafa(perf_df)]

            ytd_col = _pick_col(perf_df, ["YTD", "PERFORMANCE_YTD", "PERF_YTD"])
            m1_col = _pick_col(perf_df, ["1_MOIS", "30J", "M30", "PERF_30J", "PERFORMANCE_30D"])
            w1_col = _pick_col(perf_df, ["1_SEMAINE", "W1", "PERF_1W", "PERFORMANCE_WEEKLY"])

            def _mean_pct(_df, col):
                if _df.empty or col is None or col not in _df.columns:
                    return np.nan
                vals = _df[col].apply(_as_percent).replace([np.inf, -np.inf], np.nan).dropna()
                return float(vals.mean()) if len(vals) else np.nan

            perf_ytd = _mean_pct(wafa_perf, ytd_col)
            perf_30d = _mean_pct(wafa_perf, m1_col)
            perf_w = _mean_pct(wafa_perf, w1_col)

            market_ytd = _mean_pct(market_perf, ytd_col)
            market_30d = _mean_pct(market_perf, m1_col)
            market_w = _mean_pct(market_perf, w1_col)

            if pd.notna(perf_ytd) and pd.notna(market_ytd):
                outperf_ytd = perf_ytd - market_ytd
            if pd.notna(perf_30d) and pd.notna(market_30d):
                outperf_30d = perf_30d - market_30d
            if pd.notna(perf_w) and pd.notna(market_w):
                outperf_w = perf_w - market_w

        # ======================================================
        # 6) STABILITÉ & VOLATILITÉ (sur cross)
        # ======================================================
        vol_30 = np.nan
        max_dd = np.nan
        zscore_mean = np.nan

        if not cross_wafa.empty and "DATE" in cross_wafa.columns:
            dmax = cross_wafa["DATE"].dropna().max()
            if pd.notna(dmax):
                cutoff = dmax - pd.Timedelta(days=30)
                sub = cross_wafa[cross_wafa["DATE"] >= cutoff].copy()

                vol_col = _pick_col(sub, ["VOL_30D", "VOL_20D", "VOLATILITY_30D", "VOLATILITY"])
                dd_col = _pick_col(sub, ["DRAWDOWN", "MAX_DRAWDOWN", "DD"])
                z_col = _pick_col(sub, ["ZSCORE_1J", "ZSCORE", "Z_SCORE", "ZSCORE_1D"])

                if vol_col:
                    vol_30 = float(pd.to_numeric(sub[vol_col], errors="coerce").dropna().mean()) if len(sub) else np.nan
                if dd_col:
                    max_dd = float(pd.to_numeric(sub[dd_col], errors="coerce").dropna().min()) if len(sub) else np.nan
                if z_col:
                    zscore_mean = float(pd.to_numeric(sub[z_col], errors="coerce").abs().dropna().mean()) if len(sub) else np.nan

        # ======================================================
        # 7) SIGNAL ML GLOBAL (STABLE / MONITOR / REDUCE) via projection 30D
        # ======================================================
        ml_signal = "STABLE"
        if not df_pred.empty:
            pred_wafa = df_pred[_is_wafa(df_pred)]
            class30_col = _pick_col(pred_wafa, ["FINAL_RISK_CLASS_30D", "FINAL_RISK_CLASS", "RISK_CLASS_30D"])
            if not pred_wafa.empty and class30_col:
                classes = pred_wafa[class30_col].astype(str).str.upper()
                pct_high = (classes.eq("HIGH_RISK") | classes.eq("HIGH")).mean() * 100.0
                pct_med_high = (classes.isin(["HIGH_RISK", "MEDIUM_RISK", "HIGH", "MEDIUM"])).mean() * 100.0

                # règles simples & robustes
                if pct_high >= 10:
                    ml_signal = "REDUCE"
                elif pct_med_high >= 20:
                    ml_signal = "MONITOR"
                else:
                    ml_signal = "STABLE"

        # ======================================================
        # OUTPUT
        # ======================================================
        return {
            "societe": WAFA_NAME,

            # Risque
            "risk_score_100": round(float(risk_score_100), 2) if pd.notna(risk_score_100) else None,
            "risk_change_dir": risk_change_dir,
            "risk_change_pct": round(float(risk_change_pct), 2) if pd.notna(risk_change_pct) else None,
            "risk_status": risk_status,

            # Anomalies
            "anomalies_daily": anomalies_daily,
            "anomalies_weekly": anomalies_weekly,
            "dominant_anomaly_type": dom_type,

            # Performance
            "performance_ytd_pct": round(float(perf_ytd), 2) if pd.notna(perf_ytd) else None,
            "performance_30d_pct": round(float(perf_30d), 2) if pd.notna(perf_30d) else None,
            "performance_weekly_pct": round(float(perf_w), 2) if pd.notna(perf_w) else None,
            "outperf_ytd_vs_market": round(float(outperf_ytd), 2) if pd.notna(outperf_ytd) else None,
            "outperf_30d_vs_market": round(float(outperf_30d), 2) if pd.notna(outperf_30d) else None,
            "outperf_weekly_vs_market": round(float(outperf_w), 2) if pd.notna(outperf_w) else None,

            # Stabilité & Volatilité
            "volatility_30d": round(float(vol_30), 6) if pd.notna(vol_30) else None,
            "max_drawdown_30d": round(float(max_dd), 6) if pd.notna(max_dd) else None,
            "zscore_mean_30d": round(float(zscore_mean), 4) if pd.notna(zscore_mean) else None,

            # ML & Décision
            "ml_signal": ml_signal,

            # Qualité des données
            "total_funds_analyzed": total_funds,
            "valid_data_pct": round(float(valid_pct), 2) if pd.notna(valid_pct) else 0.0,
            "last_update": last_update,

            "status": "success",
        }

    except Exception as e:
        # ZERO CRASH: on renvoie un dict cohérent
        return {
            "societe": WAFA_NAME,
            "risk_score_100": None,
            "risk_change_dir": "—",
            "risk_change_pct": None,
            "risk_status": "ERROR",
            "anomalies_daily": 0,
            "anomalies_weekly": 0,
            "dominant_anomaly_type": "N/A",
            "performance_ytd_pct": None,
            "performance_30d_pct": None,
            "performance_weekly_pct": None,
            "outperf_ytd_vs_market": None,
            "outperf_30d_vs_market": None,
            "outperf_weekly_vs_market": None,
            "volatility_30d": None,
            "max_drawdown_30d": None,
            "zscore_mean_30d": None,
            "ml_signal": "STABLE",
            "total_funds_analyzed": 0,
            "valid_data_pct": 0.0,
            "last_update": None,
            "status": f"error: {str(e)}",
        }


# ======================================================
# FastAPI Router
# ======================================================
from fastapi import APIRouter

router = APIRouter()

@router.get("/overview")
def api_overview():
    """
    Endpoint API pour récupérer les métriques overview.
    """
    return get_overview_metrics()
