import pandas as pd
import numpy as np

# =====================================================
# CONFIG
# =====================================================
DAILY_FILE = "../scraper/anomaly_results_daily.xlsx"
WEEKLY_FILE = "../scraper/anomaly_results_weekly.xlsx"
OUTPUT_FILE = "../scraper/anomaly_cross_daily_weekly.xlsx"

print("📥 Chargement des résultats d’anomalies...")

df_daily = pd.read_excel(DAILY_FILE)
df_weekly = pd.read_excel(WEEKLY_FILE)

# =====================================================
# 1) Préparation dates
# =====================================================
df_daily["DATE"] = pd.to_datetime(df_daily["DATE"])
df_weekly["WEEK_DATE"] = pd.to_datetime(df_weekly["WEEK_DATE"])

# =====================================================
# 2) Flags anomalies
# =====================================================
df_daily["ANOMALY_DAILY_FLAG"] = (df_daily["ANOMALY_SCORE_IF"] < 0).astype(int)
df_weekly["ANOMALY_WEEKLY_FLAG"] = (df_weekly["ANOMALY_SCORE_IF"] < 0).astype(int)

# =====================================================
# 3) Merge asof ISIN par ISIN (SOLUTION ROBUSTE)
# =====================================================
print("🔗 Croisement DAILY ↔ WEEKLY par CODE_ISIN...")

results = []

for isin in df_daily["CODE_ISIN"].unique():
    d_daily = df_daily[df_daily["CODE_ISIN"] == isin].sort_values("DATE")
    d_weekly = df_weekly[df_weekly["CODE_ISIN"] == isin].sort_values("WEEK_DATE")

    if d_weekly.empty:
        d_daily["ANOMALY_WEEKLY_FLAG"] = 0
        results.append(d_daily)
        continue

    merged = pd.merge_asof(
        d_daily,
        d_weekly[["WEEK_DATE", "ANOMALY_WEEKLY_FLAG"]],
        left_on="DATE",
        right_on="WEEK_DATE",
        direction="backward"
    )

    merged["ANOMALY_WEEKLY_FLAG"] = merged["ANOMALY_WEEKLY_FLAG"].fillna(0)
    results.append(merged)

df_cross = pd.concat(results, ignore_index=True)

# =====================================================
# 4) Score combiné
# =====================================================
df_cross["ANOMALY_COMBINED_SCORE"] = (
    2 * df_cross["ANOMALY_WEEKLY_FLAG"] +
    1 * df_cross["ANOMALY_DAILY_FLAG"]
)

# =====================================================
# 5) Classification du risque
# =====================================================
def risk_level(x):
    if x == 3:
        return "HIGH_RISK"
    elif x == 2:
        return "MEDIUM_RISK"
    elif x == 1:
        return "LOW_RISK"
    else:
        return "NORMAL"

df_cross["RISK_LEVEL"] = df_cross["ANOMALY_COMBINED_SCORE"].apply(risk_level)

# =====================================================
# 6) Stats
# =====================================================
print("\n📊 Répartition des niveaux de risque (%) :")
print(df_cross["RISK_LEVEL"].value_counts(normalize=True).round(4) * 100)

# =====================================================
# 7) Export
# =====================================================
df_cross.to_excel(OUTPUT_FILE, index=False)
print(f"\n🎉 Fichier final exporté → {OUTPUT_FILE}")
