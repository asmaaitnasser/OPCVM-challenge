import pandas as pd
import numpy as np

INPUT_FILE = "../scraper/performance_quotidienne_asfim_clean.xlsx"
OUTPUT_FILE = "../scraper/features_anomaly_daily.xlsx"

print("📥 Chargement données daily clean...")
df = pd.read_excel(INPUT_FILE)

# Sécurité
df["DATE"] = pd.to_datetime(df["DATE"])
df = df.sort_values(["CODE_ISIN", "DATE"])

# ======================================================
# 1) RETOUR JOURNALIER (si VL dispo)
# ======================================================
if "VL" in df.columns:
    df["RET_1J"] = df.groupby("CODE_ISIN")["VL"].pct_change()
else:
    df["RET_1J"] = df["1_JOUR"] / 100

# ======================================================
# 2) Z-SCORE DES PERFORMANCES
# ======================================================
def zscore(x):
    return (x - x.mean()) / x.std(ddof=0)

df["ZSCORE_1J"] = df.groupby("CODE_ISIN")["RET_1J"].transform(zscore)

if "1_SEMAINE" in df.columns:
    df["ZSCORE_1W"] = df.groupby("CODE_ISIN")["1_SEMAINE"].transform(zscore)
else:
    df["ZSCORE_1W"] = np.nan

# ======================================================
# 3) VOLATILITÉ ROLLING 20 JOURS
# ======================================================
df["VOL_20D"] = (
    df.groupby("CODE_ISIN")["RET_1J"]
      .rolling(20)
      .std()
      .reset_index(level=0, drop=True)
)

# ======================================================
# 4) DRAWDOWN
# ======================================================
df["CUM_MAX_VL"] = df.groupby("CODE_ISIN")["VL"].cummax()
df["DRAWDOWN"] = (df["VL"] - df["CUM_MAX_VL"]) / df["CUM_MAX_VL"]

# ======================================================
# 5) SCORE D’ANOMALIE (RÈGLES SIMPLES)
# ======================================================
df["ANOMALY_SCORE_RULES"] = 0

df.loc[df["ZSCORE_1J"].abs() > 3, "ANOMALY_SCORE_RULES"] += 1
df.loc[df["ZSCORE_1W"].abs() > 3, "ANOMALY_SCORE_RULES"] += 1
df.loc[df["VOL_20D"] > df["VOL_20D"].quantile(0.99), "ANOMALY_SCORE_RULES"] += 1
df.loc[df["DRAWDOWN"] < -0.1, "ANOMALY_SCORE_RULES"] += 1

print("✔ Features anomalies calculées")

# ======================================================
# 6) EXPORT
# ======================================================
df.to_excel(OUTPUT_FILE, index=False)
print(f"🎉 Features anomalies exportées → {OUTPUT_FILE}")
