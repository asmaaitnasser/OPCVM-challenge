import pandas as pd
import numpy as np

# ======================================================
# CONFIG
# ======================================================
INPUT_FILE = "../scraper/anomaly_cross_daily_weekly.xlsx"
OUTPUT_FILE = "../scraper/fund_risk_score.xlsx"

print("📥 Chargement des anomalies croisées...")
df = pd.read_excel(INPUT_FILE)

# ======================================================
# 1) Normalisation minimale
# ======================================================
df.columns = df.columns.str.upper().str.strip()
df["RISK_LEVEL"] = df["RISK_LEVEL"].str.upper()

# ======================================================
# 2) Mapping des scores de risque
# ======================================================
RISK_MAP = {
    "NORMAL": 0,
    "LOW_RISK": 1,
    "MEDIUM_RISK": 2,
    "HIGH_RISK": 3
}

df["RISK_POINTS"] = df["RISK_LEVEL"].map(RISK_MAP).fillna(0)

# ======================================================
# 3) Agrégation par fonds (CODE_ISIN)
# ======================================================
print("📊 Calcul des scores par fonds...")

agg = df.groupby("CODE_ISIN").agg(
    SOCIETE_DE_GESTION=("SOCIETE_DE_GESTION", "first"),
    OPCVM=("OPCVM", "first"),
    TOTAL_DAYS=("RISK_LEVEL", "count"),
    HIGH_RISK_DAYS=("RISK_LEVEL", lambda x: (x == "HIGH_RISK").sum()),
    MEDIUM_RISK_DAYS=("RISK_LEVEL", lambda x: (x == "MEDIUM_RISK").sum()),
    LOW_RISK_DAYS=("RISK_LEVEL", lambda x: (x == "LOW_RISK").sum()),
    RISK_SCORE=("RISK_POINTS", "mean"),
    LAST_RISK_LEVEL=("RISK_LEVEL", "last")
).reset_index()

# ======================================================
# 4) Pourcentages
# ======================================================
agg["PCT_HIGH_RISK"] = agg["HIGH_RISK_DAYS"] / agg["TOTAL_DAYS"] * 100
agg["PCT_MEDIUM_HIGH"] = (
    (agg["HIGH_RISK_DAYS"] + agg["MEDIUM_RISK_DAYS"]) / agg["TOTAL_DAYS"] * 100
)

# ======================================================
# 🔥 4.5) FINAL_RISK_CLASS (AJOUT)
# ======================================================
def final_risk_class(row):
    if row["PCT_HIGH_RISK"] >= 10:
        return "HIGH_RISK"
    elif row["PCT_MEDIUM_HIGH"] >= 20:
        return "MEDIUM_RISK"
    else:
        return "LOW_RISK"

agg["FINAL_RISK_CLASS"] = agg.apply(final_risk_class, axis=1)

print("✔ FINAL_RISK_CLASS calculée")

# ======================================================
# 5) Classement global
# ======================================================
agg = agg.sort_values("RISK_SCORE", ascending=False)

print(f"✔ Fonds analysés : {len(agg)}")

# ======================================================
# 6) Feuille WAFA GESTION
# ======================================================
wafa_df = agg[
    agg["SOCIETE_DE_GESTION"]
    .astype(str)
    .str.upper()
    .str.contains("WAFA", na=False)
]

print(f"✔ Fonds WAFA Gestion : {len(wafa_df)}")

# ======================================================
# 7) Export Excel multi-feuilles
# ======================================================
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    agg.to_excel(writer, sheet_name="ALL_FUNDS", index=False)
    wafa_df.to_excel(writer, sheet_name="WAFA_GESTION", index=False)

print(f"\n🎉 Scoring de risque exporté → {OUTPUT_FILE}")
