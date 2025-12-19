import pandas as pd
import numpy as np

INPUT_FILE = "../scraper/performance_quotidienne_asfim_clean.xlsx"
REPORT_FILE = "../scraper/sanity_report_daily.xlsx"

print("📥 Chargement...")
df = pd.read_excel(INPUT_FILE)

# Colonnes attendues minimum
required = ["CODE_ISIN", "DATE", "VL"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Colonnes manquantes : {missing}")

# Types
df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
df = df.dropna(subset=["DATE", "CODE_ISIN"])

# Stats de base
summary = pd.DataFrame({
    "metric": [
        "rows", "unique_isin", "min_date", "max_date",
        "missing_VL", "missing_1_JOUR", "missing_1_SEMAINE", "missing_YTD"
    ],
    "value": [
        len(df),
        df["CODE_ISIN"].nunique(),
        df["DATE"].min(),
        df["DATE"].max(),
        df["VL"].isna().sum() if "VL" in df.columns else np.nan,
        df["1_JOUR"].isna().sum() if "1_JOUR" in df.columns else np.nan,
        df["1_SEMAINE"].isna().sum() if "1_SEMAINE" in df.columns else np.nan,
        df["YTD"].isna().sum() if "YTD" in df.columns else np.nan,
    ]
})

# Duplicates (même fonds, même date)
dups = df.duplicated(subset=["CODE_ISIN", "DATE"]).sum()
dup_df = pd.DataFrame({"duplicated_CODE_ISIN_DATE": [dups]})

# Valeurs suspectes (VL <= 0, perf absurdes)
suspects = []
if "VL" in df.columns:
    suspects.append(("VL<=0", int((df["VL"] <= 0).sum())))
for col in ["1_JOUR", "1_SEMAINE", "1_MOIS", "YTD"]:
    if col in df.columns:
        suspects.append((f"{col} abs>50", int((df[col].abs() > 50).sum())))
suspects_df = pd.DataFrame(suspects, columns=["rule", "count"])

# Export report
with pd.ExcelWriter(REPORT_FILE, engine="openpyxl") as w:
    summary.to_excel(w, sheet_name="summary", index=False)
    dup_df.to_excel(w, sheet_name="duplicates", index=False)
    suspects_df.to_excel(w, sheet_name="suspects", index=False)

print(f"✅ Report généré : {REPORT_FILE}")
