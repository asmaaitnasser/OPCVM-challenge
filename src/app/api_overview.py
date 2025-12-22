import pandas as pd
from pathlib import Path

DATA_DIR = Path("src/scraper")

def get_overview_metrics():
    # --- Anomalies daily ---
    df_daily = pd.read_excel(DATA_DIR / "anomaly_results_daily.xlsx")
    anomalies_daily = len(df_daily)

    # --- Anomalies weekly ---
    df_weekly = pd.read_excel(DATA_DIR / "anomaly_results_weekly.xlsx")
    anomalies_weekly = len(df_weekly)

    # --- Risk score ---
    df_risk = pd.read_excel(DATA_DIR / "fund_risk_score.xlsx")
    risk_score = df_risk.iloc[-1]["risk_level"]  # adapte si nom différent

    # --- Performance YTD ---
    df_perf = pd.read_excel(DATA_DIR / "performance_quotidienne_asfim_clean.xlsx")
    performance_ytd = round(df_perf["performance"].iloc[-1] * 100, 2)

    return {
        "anomalies_daily": anomalies_daily,
        "anomalies_weekly": anomalies_weekly,
        "performance_ytd": performance_ytd,
        "risk_status": risk_score,
    }
