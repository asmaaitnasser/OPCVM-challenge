import pandas as pd
import numpy as np
import os
import re

# -----------------------------------------------
# Chemins des fichiers d'entrée
# -----------------------------------------------
DAILY_FILE = "../scraper/performance_quotidienne_asfim.xlsx"
WEEKLY_FILE = "../scraper/performance_hebdomadaire_asfim.xlsx"
OUTPUT_FILE = "../scraper/dataset_fusion_asfim.xlsx"

print("📥 Chargement des fichiers ...")

df_daily = pd.read_excel(DAILY_FILE)
df_weekly = pd.read_excel(WEEKLY_FILE)

# -----------------------------------------------
# Fonction extraction date depuis "source_file"
# -----------------------------------------------
def extract_date(x):
    m = re.search(r"(\d{2}[-_/]\d{2}[-_/]\d{4})", str(x))
    if m:
        # format type 08-12-2025 → jour-mois-année
        return pd.to_datetime(m.group(1).replace("_", "-").replace("/", "-"),
                              format="%d-%m-%Y",
                              dayfirst=True,
                              errors="coerce")
    return None

# -----------------------------------------------
# 1) TRAITEMENT DAILY
# -----------------------------------------------
print("\n🔧 Préparation DAILY...")

df_daily.columns = [c.upper().strip() for c in df_daily.columns]

df_daily["DATE"] = df_daily["SOURCE_FILE"].apply(extract_date)
df_daily = df_daily.dropna(subset=["DATE"])

# Normaliser ISIN
daily_isin = [c for c in df_daily.columns if "ISIN" in c][0]
df_daily["CODE_ISIN"] = df_daily[daily_isin].astype(str).str.strip()

# ⚠️ merge_asof exige que les clés "on" soient triées
df_daily = df_daily.sort_values(["DATE", "CODE_ISIN"]).reset_index(drop=True)

print("✔ DAILY prêt.")

# -----------------------------------------------
# 2) TRAITEMENT WEEKLY
# -----------------------------------------------
print("\n🔧 Préparation WEEKLY...")

df_weekly.columns = [c.upper().strip() for c in df_weekly.columns]

df_weekly["WEEK_DATE"] = df_weekly["SOURCE_FILE"].apply(extract_date)
df_weekly = df_weekly.dropna(subset=["WEEK_DATE"])

weekly_isin = [c for c in df_weekly.columns if "ISIN" in c][0]
df_weekly["CODE_ISIN"] = df_weekly[weekly_isin].astype(str).str.strip()

# ⚠️ idem : tri d'abord par WEEK_DATE, puis ISIN
df_weekly = df_weekly.sort_values(["WEEK_DATE", "CODE_ISIN"]).reset_index(drop=True)

print("✔ WEEKLY prêt.")

# -----------------------------------------------
# 3) FUSION DAILY + WEEKLY (merge_asof)
# -----------------------------------------------
print("\n🔗 Fusion intelligente (merge_asof)...")

df_merged = pd.merge_asof(
    df_daily,
    df_weekly,
    left_on="DATE",
    right_on="WEEK_DATE",
    by="CODE_ISIN",
    direction="backward"
)

print("✔ Fusion terminée !")

# -----------------------------------------------
# 4) Nettoyage final + export
# -----------------------------------------------
df_merged.columns = [
    c.upper().replace(" ", "_").replace("É", "E").replace("È", "E")
    for c in df_merged.columns
]

df_merged.to_excel(OUTPUT_FILE, index=False)
print(f"\n🎉 DATASET FINAL GÉNÉRÉ → {OUTPUT_FILE}")
