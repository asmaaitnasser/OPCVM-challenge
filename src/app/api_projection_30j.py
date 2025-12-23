# src/app/api_projection_30j.py
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional
import pandas as pd
import streamlit as st

DATA_DIR = Path("src/scraper")

RISK_FILE = DATA_DIR / "fund_risk_score.xlsx"
PRED_FILE = DATA_DIR / "prediction_future_risk.xlsx"

RISK_SHEET = "ALL_FUNDS"
PRED_SHEET_CANDIDATES = ["PROJECTION_30D_ALL", "PROJECTION_30D_WAFA", "PROJECTION_30D_MARKET", "WAFA_GESTION", "ALL_MARKET"]


def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.upper().str.strip()
    return df


def _norm_text(df: pd.DataFrame, col: str) -> None:
    if col in df.columns:
        df[col] = df[col].astype(str).str.upper().str.strip()


def _to_num(df: pd.DataFrame, col: str) -> None:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")


def _pick_sheet(xls_path: Path, candidates: List[str]) -> str:
    xf = pd.ExcelFile(xls_path)
    sheets = [s.upper().strip() for s in xf.sheet_names]
    mapping = {s.upper().strip(): s for s in xf.sheet_names}
    for c in candidates:
        if c.upper().strip() in sheets:
            return mapping[c.upper().strip()]
    # fallback: first sheet
    return xf.sheet_names[0]


@st.cache_data(ttl=3600)
def load_risk_all_funds() -> pd.DataFrame:
    if not RISK_FILE.exists():
        raise FileNotFoundError(f"Fichier introuvable: {RISK_FILE}")

    df = pd.read_excel(RISK_FILE, sheet_name=RISK_SHEET)
    df = _normalize_cols(df)

    # normalize key columns
    for c in ["CODE_ISIN", "OPCVM", "SOCIETE_DE_GESTION", "FINAL_RISK_CLASS", "LAST_RISK_LEVEL"]:
        _norm_text(df, c)

    _to_num(df, "RISK_SCORE")
    _to_num(df, "PCT_HIGH_RISK")
    _to_num(df, "PCT_MEDIUM_HIGH")

    if "CODE_ISIN" in df.columns:
        df = df.drop_duplicates("CODE_ISIN")

    return df


@st.cache_data(ttl=3600)
def load_projection_30d() -> pd.DataFrame:
    """
    Charge prediction_future_risk.xlsx (sheet PROJECTION_30D_ALL si existe)
    et retourne un DF standardisé.
    """
    if not PRED_FILE.exists():
        raise FileNotFoundError(f"Fichier introuvable: {PRED_FILE}")

    sheet = _pick_sheet(PRED_FILE, PRED_SHEET_CANDIDATES)
    df = pd.read_excel(PRED_FILE, sheet_name=sheet)
    df = _normalize_cols(df)

    for c in ["CODE_ISIN", "OPCVM", "SOCIETE_DE_GESTION", "LAST_RISK_T1", "FINAL_RISK_CLASS_30D"]:
        _norm_text(df, c)

    for c in [
        "AVG_RISK_T1", "PCT_HIGH_T1", "PCT_MEDIUM_T1",
        "RISK_SCORE_30D", "P_HIGH_RISK_30D", "P_MEDIUM_OR_HIGH_30D",
        "NB_DAYS"
    ]:
        _to_num(df, c)

    if "CODE_ISIN" in df.columns:
        df = df.drop_duplicates("CODE_ISIN")

    return df


@st.cache_data(ttl=3600)
def load_merged_risk_and_pred() -> pd.DataFrame:
    """
    Merge fund_risk_score.xlsx (ALL_FUNDS) + prediction_future_risk.xlsx (PROJECTION_30D_ALL)
    sur CODE_ISIN.
    """
    df_risk = load_risk_all_funds()
    df_pred = load_projection_30d()

    if "CODE_ISIN" not in df_pred.columns:
        raise ValueError("prediction_future_risk.xlsx: colonne CODE_ISIN introuvable")
    if "CODE_ISIN" not in df_risk.columns:
        raise ValueError("fund_risk_score.xlsx: colonne CODE_ISIN introuvable")

    df = df_pred.merge(
        df_risk[["CODE_ISIN", "FINAL_RISK_CLASS", "RISK_SCORE", "PCT_HIGH_RISK", "PCT_MEDIUM_HIGH", "OPCVM", "SOCIETE_DE_GESTION"]]
            .rename(columns={
                "FINAL_RISK_CLASS": "CURRENT_FINAL_RISK_CLASS",
                "RISK_SCORE": "CURRENT_RISK_SCORE",
                "PCT_HIGH_RISK": "CURRENT_PCT_HIGH_RISK",
                "PCT_MEDIUM_HIGH": "CURRENT_PCT_MEDIUM_HIGH",
                "OPCVM": "RISK_OPCVM",
                "SOCIETE_DE_GESTION": "RISK_SOCIETE_DE_GESTION",
            }),
        on="CODE_ISIN",
        how="left",
        suffixes=("", "_RISK")
    )

    # Harmonize display name/company columns
    if "OPCVM" not in df.columns and "RISK_OPCVM" in df.columns:
        df["OPCVM"] = df["RISK_OPCVM"]
    if "SOCIETE_DE_GESTION" not in df.columns and "RISK_SOCIETE_DE_GESTION" in df.columns:
        df["SOCIETE_DE_GESTION"] = df["RISK_SOCIETE_DE_GESTION"]

    _norm_text(df, "OPCVM")
    _norm_text(df, "SOCIETE_DE_GESTION")

    return df


def get_companies(df: pd.DataFrame) -> List[str]:
    if "SOCIETE_DE_GESTION" not in df.columns:
        return []
    return sorted([x for x in df["SOCIETE_DE_GESTION"].dropna().unique().tolist() if x])


def get_fund_options(df: pd.DataFrame) -> List[str]:
    if "CODE_ISIN" not in df.columns:
        return []
    if "OPCVM" in df.columns:
        tmp = df[["CODE_ISIN", "OPCVM"]].drop_duplicates()
        return [f"{r['CODE_ISIN']} — {r['OPCVM']}" for _, r in tmp.iterrows()]
    return sorted(df["CODE_ISIN"].dropna().unique().tolist())


def filter_by_company(df: pd.DataFrame, company: str) -> pd.DataFrame:
    if not company or company == "ALL":
        return df
    if "SOCIETE_DE_GESTION" not in df.columns:
        return df.iloc[0:0]
    return df[df["SOCIETE_DE_GESTION"] == company]


def get_row_by_isin(df: pd.DataFrame, isin: str) -> Optional[pd.Series]:
    if not isin or "CODE_ISIN" not in df.columns:
        return None
    sub = df[df["CODE_ISIN"] == isin]
    if sub.empty:
        return None
    return sub.iloc[0]


def get_download_bytes(which: str) -> Tuple[bytes, str]:
    """
    which = 'risk' or 'pred'
    """
    if which == "risk":
        path = RISK_FILE
        name = "fund_risk_score.xlsx"
    else:
        path = PRED_FILE
        name = "prediction_future_risk.xlsx"

    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {path}")

    return path.read_bytes(), name
