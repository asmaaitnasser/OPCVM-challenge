from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import Tuple, List, Optional, Dict

# =========================
# CONFIG
# =========================
DATA_DIR = Path("src/scraper")

# On essaie plusieurs noms possibles (selon ton pipeline)
RECO_FILE_CANDIDATES = [
    "recommendations.xlsx",
    "recommandations.xlsx",
    "recommendation.xlsx",
    "reco.xlsx",
    "recommendations_results.xlsx",
    "recommender.xlsx",
]

DEFAULT_SHEETS = {
    "MERGED": "ALL_FUNDS_RECO",
    "WAFA": "WAFA_GESTION_RECO",
    "SUMMARY": "SUMMARY_RECO",
}


# =========================
# HELPERS
# =========================
def _find_reco_file() -> Path:
    for name in RECO_FILE_CANDIDATES:
        p = DATA_DIR / name
        if p.exists():
            return p

    # fallback: cherche un fichier qui contient "reco" ou "recommend" dans le nom
    if DATA_DIR.exists():
        for p in DATA_DIR.glob("*.xlsx"):
            n = p.name.lower()
            if "reco" in n or "recommend" in n or "recommand" in n:
                return p

    tried = [str(DATA_DIR / n) for n in RECO_FILE_CANDIDATES]
    raise FileNotFoundError(
        "Fichier de recommandations introuvable dans src/scraper.\n"
        f"J'ai essayé: {tried}\n"
        "=> Mets ton fichier (recommendations.xlsx) dans src/scraper/."
    )


def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.upper().str.strip()
    return df


def _safe_numeric(df: pd.DataFrame, col: str) -> None:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")


def _pick_col(df: pd.DataFrame, exact: List[str], contains: List[str] = None) -> Optional[str]:
    cols = list(df.columns)
    exact = [x.upper() for x in exact]
    for c in exact:
        if c in cols:
            return c
    if contains:
        contains = [x.upper() for x in contains]
        for col in cols:
            for token in contains:
                if token in col:
                    return col
    return None


def _resolve_sheet_name(xls: pd.ExcelFile, desired: str) -> str:
    sheets = xls.sheet_names
    up = {s.upper(): s for s in sheets}
    d = desired.upper()
    if d in up:
        return up[d]
    # fallback: match partiel
    for s in sheets:
        if d in s.upper():
            return s
    raise ValueError(f"Feuille '{desired}' introuvable. Feuilles dispo: {sheets}")


# =========================
# LOADERS (CACHÉS SI STREAMLIT DISPO)
# =========================
def _cache(ttl: int = 3600):
    """
    Décorateur cache_data si streamlit est dispo, sinon no-op.
    """
    try:
        import streamlit as st
        return st.cache_data(ttl=ttl)
    except Exception:
        def no_op(func):
            return func
        return no_op


@_cache(ttl=3600)
def load_recommendations_merged(sheet_name: str = DEFAULT_SHEETS["MERGED"]) -> pd.DataFrame:
    """
    Charge ALL_FUNDS_RECO (ou équivalent) et normalise les colonnes.
    """
    file_path = _find_reco_file()
    xls = pd.ExcelFile(file_path)
    sheet = _resolve_sheet_name(xls, sheet_name)

    df = pd.read_excel(file_path, sheet_name=sheet)
    df = _normalize_cols(df)

    # normalisations utiles (si présentes)
    for c in ["CODE_ISIN", "OPCVM", "SOCIETE_DE_GESTION", "RECOMMENDATION"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    # souvent les % sont en texte avec virgule => on tente numeric
    numeric_candidates = [
        "PRIORITY_SCORE",
        "RISK_SCORE",
        "RISK_SCORE_30D",
        "AVG_RISK_SCORE_30D",
        "P_MEDIUM_OR_HIGH_30D",
        "AVG_P_MEDIUM_OR_HIGH_30D",
        "P_HIGH_RISK_30D",
        "AVG_PRIORITY_SCORE",
        "NB_DAYS",
        "TOTAL_DAYS",
        "PCT_HIGH_RISK",
        "PCT_MEDIUM_HIGH",
    ]
    for c in numeric_candidates:
        _safe_numeric(df, c)

    return df


@_cache(ttl=3600)
def load_recommendations_summary(sheet_name: str = DEFAULT_SHEETS["SUMMARY"]) -> pd.DataFrame:
    """
    Charge SUMMARY_RECO (ou équivalent).
    """
    file_path = _find_reco_file()
    xls = pd.ExcelFile(file_path)
    sheet = _resolve_sheet_name(xls, sheet_name)

    df = pd.read_excel(file_path, sheet_name=sheet)
    df = _normalize_cols(df)

    # numeric safe
    for c in ["NB_FUNDS", "AVG_PRIORITY_SCORE", "AVG_RISK_SCORE_30D", "AVG_P_MEDIUM_OR_HIGH_30D"]:
        _safe_numeric(df, c)

    return df


def get_company_options(df_merged: pd.DataFrame) -> List[str]:
    soc_col = _pick_col(df_merged, ["SOCIETE_DE_GESTION"], contains=["SOCIETE", "GESTION"])
    if not soc_col:
        return ["ALL"]

    vals = (
        df_merged[soc_col]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("NAN", "")
        .tolist()
    )
    uniq = sorted([v for v in set(vals) if v])
    return ["ALL"] + uniq


def filter_by_company(df_merged: pd.DataFrame, company: str) -> pd.DataFrame:
    if company == "ALL":
        return df_merged

    soc_col = _pick_col(df_merged, ["SOCIETE_DE_GESTION"], contains=["SOCIETE", "GESTION"])
    if not soc_col:
        return df_merged

    return df_merged[df_merged[soc_col].astype(str).str.strip() == company]


def get_reco_file_bytes() -> Tuple[bytes, str]:
    p = _find_reco_file()
    return p.read_bytes(), p.name


def build_reco_kpis(df_company: pd.DataFrame) -> Dict[str, float]:
    """
    KPIs robustes même si certaines colonnes manquent.
    """
    reco_col = _pick_col(df_company, ["RECOMMENDATION"], contains=["RECOMMEND"])
    prio_col = _pick_col(df_company, ["PRIORITY_SCORE"], contains=["PRIORITY"])
    risk30_col = _pick_col(df_company, ["AVG_RISK_SCORE_30D", "RISK_SCORE_30D"], contains=["RISK_SCORE_30D"])
    pmed_col = _pick_col(df_company, ["P_MEDIUM_OR_HIGH_30D", "AVG_P_MEDIUM_OR_HIGH_30D"], contains=["MEDIUM_OR_HIGH"])

    total = float(len(df_company))

    kpis = {
        "total_funds": total,
        "avg_priority": float(pd.to_numeric(df_company[prio_col], errors="coerce").mean()) if prio_col else float("nan"),
        "avg_risk_score_30d": float(pd.to_numeric(df_company[risk30_col], errors="coerce").mean()) if risk30_col else float("nan"),
        "avg_p_medium_or_high_30d": float(pd.to_numeric(df_company[pmed_col], errors="coerce").mean()) if pmed_col else float("nan"),
    }

    if reco_col:
        vc = df_company[reco_col].astype(str).str.strip().value_counts()
        for k in ["STABLE_REINFORCE", "IMPROVING_KEEP_WATCH", "WATCHLIST"]:
            kpis[f"count_{k.lower()}"] = float(vc.get(k, 0))

    return kpis
