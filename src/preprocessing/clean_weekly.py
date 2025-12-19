import pandas as pd
import numpy as np
import re

# ======================================================
# CONFIG
# ======================================================
INPUT_FILE = "../scraper/performance_hebdomadaire_asfim.xlsx"
OUTPUT_FILE = "../scraper/performance_hebdomadaire_asfim_clean.xlsx"

print("📥 Chargement du fichier WEEKLY...")
df = pd.read_excel(INPUT_FILE)

# ======================================================
# 1) NORMALISATION DES COLONNES
# ======================================================
df.columns = (
    df.columns.astype(str)
      .str.upper()
      .str.strip()
      .str.replace(" ", "_")
      .str.replace("É", "E")
      .str.replace("È", "E")
      .str.replace("Ê", "E")
)

print("✔ Colonnes normalisées")

# ======================================================
# 2) SUPPRESSION UNNAMED
# ======================================================
df = df.loc[:, ~df.columns.str.contains("^UNNAMED")]
print("✔ Colonnes UNNAMED supprimées")

# ======================================================
# 3) EXTRACTION DATE HEBDO DEPUIS SOURCE_FILE
# ======================================================
def extract_date_from_filename(name):
    if pd.isna(name):
        return np.nan

    match = re.search(r"(\d{2}[-_/]\d{2}[-_/]\d{4})", str(name))
    if match:
        return pd.to_datetime(
            match.group(1).replace("_", "-"),
            dayfirst=True,
            errors="coerce"
        )
    return np.nan

df["WEEK_DATE"] = df["SOURCE_FILE"].apply(extract_date_from_filename)
df = df.dropna(subset=["WEEK_DATE"])

print("✔ WEEK_DATE extraite depuis SOURCE_FILE")

# ======================================================
# 4) NETTOYAGE CODE ISIN
# ======================================================
df["CODE_ISIN"] = (
    df["CODE_ISIN"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df = df[df["CODE_ISIN"].str.match(r"^MA[0-9A-Z]+$", na=False)]
print("✔ CODE_ISIN nettoyé")

# ======================================================
# 5) COLONNES CATÉGORIELLES
# ======================================================
TEXT_COLS = ["SENSIBILITE", "PERIODICITE_VL"]

for col in TEXT_COLS:
    if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .replace(["nan", "None", "-", "—", "–", ""], np.nan)
        )

print("✔ Colonnes catégorielles nettoyées")

# ======================================================
# 6) COLONNES NUMÉRIQUES
# ======================================================
NUMERIC_KEYWORDS = [
    "VL", "PERF", "AN", "ANS", "MOIS", "YTD",
    "JOUR", "SEMAINE", "FRAIS", "COMMISSION"
]

EXCLUDED = ["SENSIBILITE", "PERIODICITE_VL"]

numeric_cols = [
    c for c in df.columns
    if any(k in c for k in NUMERIC_KEYWORDS)
    and c not in EXCLUDED
]

print(f"✔ Colonnes numériques détectées : {numeric_cols}")

def clean_numeric(series):
    series = (
        series.astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(r"[^\d\.\-eE]", "", regex=True)
        .replace("", np.nan)
    )
    return pd.to_numeric(series, errors="coerce")

for col in numeric_cols:
    df[col] = clean_numeric(df[col])

print("✔ Conversion numérique terminée")

# ======================================================
# 7) SUPPRESSION DES DOUBLONS
# ======================================================
before = len(df)
df = df.sort_values(["CODE_ISIN", "WEEK_DATE"])
df = df.drop_duplicates(subset=["CODE_ISIN", "WEEK_DATE"], keep="last")
after = len(df)

print(f"✔ Doublons supprimés : {before - after}")

# ======================================================
# 8) EXPORT
# ======================================================
df.to_excel(OUTPUT_FILE, index=False)
print(f"\n🎉 Dataset WEEKLY nettoyé exporté → {OUTPUT_FILE}")
