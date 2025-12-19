import pandas as pd
import numpy as np

# ======================================================
# CONFIG
# ======================================================
INPUT_FILE = "../scraper/performance_hebdomadaire_asfim_clean.xlsx"
OUTPUT_FILE = "../scraper/features_anomaly_weekly.xlsx"

print("📥 Chargement données weekly clean...")
df = pd.read_excel(INPUT_FILE)

# Sécurité dates
df["WEEK_DATE"] = pd.to_datetime(df["WEEK_DATE"], errors="coerce")
df = df.dropna(subset=["WEEK_DATE"])

# Trier
df = df.sort_values(["CODE_ISIN", "WEEK_DATE"])

# ======================================================
# 1️⃣ RETOUR HEBDOMADAIRE
# ======================================================
if "VL" in df.columns:
    df["RET_1W"] = df.groupby("CODE_ISIN")["VL"].pct_change()
else:
    df["RET_1W"] = df["1_SEMAINE"] / 100

# ======================================================
# 2️⃣ Z-SCORE HEBDOMADAIRE
# ======================================================
def zscore(x):
    return (x - x.mean()) / x.std(ddof=0)

df["ZSCORE_1W"] = df.groupby("CODE_ISIN")["RET_1W"].transform(zscore)

# ======================================================
# 3️⃣ VOLATILITÉ 12 SEMAINES
# ======================================================
df["VOL_12W"] = (
    df.groupby("CODE_ISIN")["RET_1W"]
      .rolling(12)
      .std()
      .reset_index(level=0, drop=True)
)

# ======================================================
# 4️⃣ DRAWDOWN HEBDOMADAIRE
# ======================================================
df["CUM_MAX_VL"] = df.groupby("CODE_ISIN")["VL"].cummax()
df["DRAWDOWN"] = (df["VL"] - df["CUM_MAX_VL"]) / df["CUM_MAX_VL"]

# ======================================================
# 5️⃣ MOMENTUM
# ======================================================
df["MOM_4W"] = (
    df.groupby("CODE_ISIN")["RET_1W"]
      .rolling(4)
      .mean()
      .reset_index(level=0, drop=True)
)

df["MOM_12W"] = (
    df.groupby("CODE_ISIN")["RET_1W"]
      .rolling(12)
      .mean()
      .reset_index(level=0, drop=True)
)

# ======================================================
# 6️⃣ SCORE D’ANOMALIE – RULE BASED
# ======================================================
df["ANOMALY_SCORE_RULES"] = 0

df.loc[df["ZSCORE_1W"].abs() > 3, "ANOMALY_SCORE_RULES"] += 1
df.loc[df["VOL_12W"] > df["VOL_12W"].quantile(0.99), "ANOMALY_SCORE_RULES"] += 1
df.loc[df["DRAWDOWN"] < -0.15, "ANOMALY_SCORE_RULES"] += 1
df.loc[df["MOM_4W"] < df["MOM_12W"], "ANOMALY_SCORE_RULES"] += 1

print("✔ Features anomalies WEEKLY calculées")

# ======================================================
# EXPORT
# ======================================================
df.to_excel(OUTPUT_FILE, index=False)
print(f"🎉 Features anomalies WEEKLY exportées → {OUTPUT_FILE}")
