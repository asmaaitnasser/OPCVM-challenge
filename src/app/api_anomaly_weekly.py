import pandas as pd
from pathlib import Path
import streamlit as st

DATA_DIR = Path("src/scraper")
WEEKLY_FILE = DATA_DIR / "anomaly_results_weekly.xlsx"


def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.upper().str.strip()
    return df


def _to_datetime_safe(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _infer_anomaly_flag(df: pd.DataFrame) -> pd.Series:
    cols = df.columns

    if "ANOMALY_LABEL_IF" in cols:
        return df["ANOMALY_LABEL_IF"] == -1

    for c in ["ANOMALY_WEEKLY_FLAG", "ANOMALY_FLAG_IF", "ANOMALY_FLAG", "IS_ANOMALY"]:
        if c in cols:
            s = df[c]
            if s.dtype == bool:
                return s
            return pd.to_numeric(s, errors="coerce").fillna(0).astype(int) == 1

    if "ANOMALY_SCORE_IF" in cols:
        x = pd.to_numeric(df["ANOMALY_SCORE_IF"], errors="coerce")
        thr = x.quantile(0.02)
        return x <= thr

    return pd.Series([False] * len(df), index=df.index)


@st.cache_data(ttl=3600)
def load_weekly_anomalies() -> pd.DataFrame:
    if not WEEKLY_FILE.exists():
        raise FileNotFoundError(f"Fichier introuvable: {WEEKLY_FILE}")

    df = pd.read_excel(WEEKLY_FILE)
    df = _normalize_cols(df)

    # Date weekly
    df = _to_datetime_safe(df, "WEEK_DATE")

    # Text normalization
    if "SOCIETE_DE_GESTION" in df.columns:
        df["SOCIETE_DE_GESTION"] = df["SOCIETE_DE_GESTION"].astype(str).str.upper().str.strip()

    if "CODE_ISIN" in df.columns:
        df["CODE_ISIN"] = df["CODE_ISIN"].astype(str).str.upper().str.strip()

    if "OPCVM" in df.columns:
        df["OPCVM"] = df["OPCVM"].astype(str).str.strip()
    elif "DENOMINATION_OPCVM" in df.columns:
        df["DENOMINATION_OPCVM"] = df["DENOMINATION_OPCVM"].astype(str).str.strip()

    # Flag anomalies
    df["IS_ANOMALY"] = _infer_anomaly_flag(df)

    # Numeric conversions (safe)
    numeric_candidates = [
        "RET_1W", "ZSCORE_1W", "VOL_12W", "DRAWDOWN",
        "MOM_4W", "MOM_12W",
        "ANOMALY_SCORE_IF", "ANOMALY_SCORE_RULES",
    ]
    for c in numeric_candidates:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "WEEK_DATE" in df.columns:
        df = df.sort_values("WEEK_DATE")

    return df


def get_weekly_filters(df: pd.DataFrame):
    companies = ["ALL"]
    if "SOCIETE_DE_GESTION" in df.columns:
        companies += sorted([x for x in df["SOCIETE_DE_GESTION"].dropna().unique().tolist() if x])

    funds = []
    if "CODE_ISIN" in df.columns:
        name_col = "OPCVM" if "OPCVM" in df.columns else ("DENOMINATION_OPCVM" if "DENOMINATION_OPCVM" in df.columns else None)

        if name_col:
            tmp = df[["CODE_ISIN", name_col]].drop_duplicates()
            funds = [f"{r['CODE_ISIN']} — {r[name_col]}" for _, r in tmp.iterrows()]
        else:
            funds = sorted(df["CODE_ISIN"].dropna().unique().tolist())

    return companies, funds
