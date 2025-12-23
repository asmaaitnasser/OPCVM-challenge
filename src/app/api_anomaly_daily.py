import pandas as pd
from pathlib import Path
import streamlit as st

DATA_DIR = Path("src/scraper")
DAILY_FILE = DATA_DIR / "anomaly_results_daily.xlsx"


def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.upper().str.strip()
    return df


def _to_datetime_safe(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _infer_anomaly_flag(df: pd.DataFrame) -> pd.Series:
    """
    Retourne une série booléenne indiquant si la ligne est une anomalie.
    Compatible avec plusieurs conventions possibles.
    """
    cols = df.columns

    if "ANOMALY_LABEL_IF" in cols:
        # convention IsolationForest: -1 anomalie / 1 normal
        return df["ANOMALY_LABEL_IF"] == -1

    for c in ["ANOMALY_DAILY_FLAG", "ANOMALY_FLAG_IF", "ANOMALY_FLAG", "IS_ANOMALY"]:
        if c in cols:
            s = df[c]
            if s.dtype == bool:
                return s
            # numeric/string -> 1 = anomalie
            return pd.to_numeric(s, errors="coerce").fillna(0).astype(int) == 1

    # fallback : score élevé => anomalie (si dispo)
    if "ANOMALY_SCORE_IF" in cols:
        # seuil arbitraire "safe" si rien d’autre n’existe : top 2%
        x = pd.to_numeric(df["ANOMALY_SCORE_IF"], errors="coerce")
        thr = x.quantile(0.02)  # les scores IF "plus faibles" sont souvent plus anormaux
        return x <= thr

    return pd.Series([False] * len(df), index=df.index)


@st.cache_data(ttl=3600)
def load_daily_anomalies() -> pd.DataFrame:
    if not DAILY_FILE.exists():
        raise FileNotFoundError(f"Fichier introuvable: {DAILY_FILE}")

    df = pd.read_excel(DAILY_FILE)
    df = _normalize_cols(df)

    # Date
    df = _to_datetime_safe(df, "DATE")

    # Normalisations textuelles utiles
    if "SOCIETE_DE_GESTION" in df.columns:
        df["SOCIETE_DE_GESTION"] = (
            df["SOCIETE_DE_GESTION"].astype(str).str.upper().str.strip()
        )

    if "CODE_ISIN" in df.columns:
        df["CODE_ISIN"] = df["CODE_ISIN"].astype(str).str.upper().str.strip()

    if "OPCVM" in df.columns:
        df["OPCVM"] = df["OPCVM"].astype(str).str.strip()

    # Flag anomalies
    df["IS_ANOMALY"] = _infer_anomaly_flag(df)

    # Try convert numeric columns safely
    numeric_candidates = [
        "RET_1J", "ZSCORE_1J", "VOL_20D", "DRAWDOWN", "ANOMALY_SCORE_IF",
        "ANOMALY_SCORE_RULES"
    ]
    for c in numeric_candidates:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # tri
    if "DATE" in df.columns:
        df = df.sort_values("DATE")

    return df


def get_daily_filters(df: pd.DataFrame):
    companies = ["ALL"]
    if "SOCIETE_DE_GESTION" in df.columns:
        companies += sorted([x for x in df["SOCIETE_DE_GESTION"].dropna().unique().tolist() if x])

    funds = []
    if "CODE_ISIN" in df.columns:
        if "OPCVM" in df.columns:
            tmp = df[["CODE_ISIN", "OPCVM"]].drop_duplicates()
            funds = [f"{r['CODE_ISIN']} — {r['OPCVM']}" for _, r in tmp.iterrows()]
        else:
            funds = sorted(df["CODE_ISIN"].dropna().unique().tolist())

    return companies, funds
