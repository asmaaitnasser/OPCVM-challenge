from __future__ import annotations

from pathlib import Path
from typing import Tuple, Optional, List, Dict
import pandas as pd

# =========================
# CONFIG
# =========================
DATA_DIR = Path("src/scraper")

HIST_FILE_CANDIDATES = [
    "wafa_vs_market_comparaison.xlsx",
    "wafa_vs_market_comparison.xlsx",
    "wafa_vs_marche_comparaison.xlsx",
    "wafa_vs_market.xlsx",
]

D30_FILE_CANDIDATES = [
    "wafa_vs_market_30d.xlsx",
    "wafa_vs_marche_30d.xlsx",
    "wafa_vs_market_30j.xlsx",
    "wafa_vs_marche_30j.xlsx",
]


# =========================
# STREAMLIT CACHE DECORATOR
# =========================
def _cache(ttl: int = 3600):
    try:
        import streamlit as st
        return st.cache_data(ttl=ttl)
    except Exception:
        def no_op(fn):  # type: ignore
            return fn
        return no_op


# =========================
# HELPERS
# =========================
def _find_file(candidates: List[str], fallback_contains: List[str]) -> Path:
    for name in candidates:
        p = DATA_DIR / name
        if p.exists():
            return p

    if DATA_DIR.exists():
        for p in DATA_DIR.glob("*.xlsx"):
            low = p.name.lower()
            if any(tok in low for tok in fallback_contains):
                return p

    tried = [str(DATA_DIR / n) for n in candidates]
    raise FileNotFoundError(
        "Fichier introuvable dans src/scraper.\n"
        f"Essayés: {tried}\n"
        f"Fallback contient: {fallback_contains}\n"
        "=> Mets les fichiers excel dans src/scraper/"
    )


def get_hist_file_path() -> Path:
    return _find_file(HIST_FILE_CANDIDATES, fallback_contains=["wafa", "market", "marche", "compar"])


def get_30d_file_path() -> Path:
    return _find_file(D30_FILE_CANDIDATES, fallback_contains=["wafa", "market", "marche", "30d", "30j"])


def get_file_bytes(path: Path) -> Tuple[bytes, str]:
    return path.read_bytes(), path.name


def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.upper().str.strip()
    return df


def _pick_col(df: pd.DataFrame, exact: List[str], contains: Optional[List[str]] = None) -> Optional[str]:
    cols = list(df.columns)
    exact_u = [x.upper() for x in exact]
    for c in exact_u:
        if c in cols:
            return c
    if contains:
        contains_u = [x.upper() for x in contains]
        for col in cols:
            for token in contains_u:
                if token in col:
                    return col
    return None


def _to_datetime_safe(df: pd.DataFrame, col: str) -> None:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")


def _to_numeric_best_effort(s: pd.Series) -> pd.Series:
    # gère "0,123" -> 0.123 et espaces
    if s.dtype == object:
        s = s.astype(str).str.replace(" ", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


@_cache(ttl=3600)
def list_sheets(path: Path) -> List[str]:
    xls = pd.ExcelFile(path)
    return xls.sheet_names


@_cache(ttl=3600)
def load_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet_name)
    df = _normalize_cols(df)

    # auto parse dates
    date_col = _pick_col(df, ["DATE"], contains=["DATE", "DAY", "JOUR", "WEEK"])
    if date_col:
        _to_datetime_safe(df, date_col)

    # normalize common text columns
    for c in ["SOCIETE_DE_GESTION", "CODE_ISIN", "OPCVM", "MARKET", "BENCHMARK"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    # numeric conversion (robuste)
    for c in df.columns:
        cu = str(c).upper()
        # on évite de convertir des colonnes manifestement texte
        if cu in ["OPCVM", "SOCIETE_DE_GESTION", "MARKET", "BENCHMARK", "CATEGORY"]:
            continue

        # si ça ressemble à une mesure
        if any(tok in cu for tok in ["PERF", "RETURN", "OUT", "BETA", "SHARPE", "VOL", "CORR", "SCORE", "ALPHA", "NB_", "P_", "RATE", "RISK"]):
            df[c] = _to_numeric_best_effort(df[c])
        else:
            # tentative safe : si >60% des valeurs deviennent numeric, on garde
            cand = _to_numeric_best_effort(df[c])
            ratio = cand.notna().mean() if len(cand) else 0
            if ratio >= 0.6:
                df[c] = cand

    # sort by date if possible
    if date_col and date_col in df.columns:
        df = df.sort_values(date_col)

    return df


@_cache(ttl=3600)
def load_all_sheets(path: Path) -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}
    for s in list_sheets(path):
        out[s] = load_sheet(path, s)
    return out


def list_companies(df: pd.DataFrame) -> List[str]:
    c = _pick_col(df, ["SOCIETE_DE_GESTION"], contains=["SOCIETE", "GESTION"])
    if not c:
        return ["ALL"]
    vals = df[c].dropna().astype(str).str.strip().tolist()
    uniq = sorted([v for v in set(vals) if v and v.upper() != "NAN"])
    return ["ALL"] + uniq


def filter_company(df: pd.DataFrame, company: str) -> pd.DataFrame:
    if company == "ALL":
        return df
    c = _pick_col(df, ["SOCIETE_DE_GESTION"], contains=["SOCIETE", "GESTION"])
    if not c:
        return df
    return df[df[c].astype(str).str.strip() == company]


def filter_isin(df: pd.DataFrame, isin: str) -> pd.DataFrame:
    if isin == "ALL":
        return df
    if "CODE_ISIN" not in df.columns:
        return df
    return df[df["CODE_ISIN"].astype(str).str.strip() == isin]


def compute_basic_metrics(df: pd.DataFrame) -> Dict[str, float]:
    wafa_perf = _pick_col(df, ["WAFA_PERFORMANCE"], contains=["WAFA", "PERF"])
    market_perf = _pick_col(df, ["MARKET_PERFORMANCE"], contains=["MARKET", "MARCHE", "PERF"])
    outp = _pick_col(df, ["OUTPERFORMANCE"], contains=["OUTPERF", "SURPERF", "ALPHA"])
    corr = _pick_col(df, ["CORRELATION"], contains=["CORR"])
    beta = _pick_col(df, ["BETA"], contains=["BETA"])
    sharpe = _pick_col(df, ["SHARPE_RATIO"], contains=["SHARPE"])

    def mean_or_nan(col: Optional[str]) -> float:
        if not col or col not in df.columns:
            return float("nan")
        return float(pd.to_numeric(df[col], errors="coerce").mean())

    m = {
        "wafa_perf": mean_or_nan(wafa_perf),
        "market_perf": mean_or_nan(market_perf),
        "outperformance": mean_or_nan(outp),
        "correlation": mean_or_nan(corr),
        "beta": mean_or_nan(beta),
        "sharpe": mean_or_nan(sharpe),
        "n_rows": float(len(df)),
    }

    if pd.isna(m["outperformance"]) and not pd.isna(m["wafa_perf"]) and not pd.isna(m["market_perf"]):
        m["outperformance"] = m["wafa_perf"] - m["market_perf"]

    return m
