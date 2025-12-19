import pandas as pd
import numpy as np

# ======================================================
# CONFIG
# ======================================================
INPUT_FILE = "../scraper/prediction_future_risk.xlsx"

print("📥 Chargement des prédictions t+1...")
df = pd.read_excel(INPUT_FILE, sheet_name=0)

df.columns = df.columns.str.upper().str.strip()

# ======================================================
# 1) Mapping risque
# ======================================================
RISK_MAP = {
    "NORMAL": 0,
    "LOW_RISK": 1,
    "MEDIUM_RISK": 2,
    "HIGH_RISK": 3
}

INV_RISK_MAP = {v: k for k, v in RISK_MAP.items()}

df["RISK_NUM_T1"] = df["PREDICTED_RISK_LABEL"].map(RISK_MAP)

# ======================================================
# 2) Score de persistance du risque
# ======================================================
print("📊 Calcul de la projection 30 jours...")

proj = (
    df.groupby("CODE_ISIN")
      .agg(
          SOCIETE_DE_GESTION=("SOCIETE_DE_GESTION", "first"),
          OPCVM=("OPCVM", "first"),
          LAST_RISK_T1=("PREDICTED_RISK_LABEL", "last"),
          AVG_RISK_T1=("RISK_NUM_T1", "mean"),
          PCT_HIGH_T1=("RISK_NUM_T1", lambda x: (x == 3).mean()),
          PCT_MEDIUM_T1=("RISK_NUM_T1", lambda x: (x >= 2).mean()),
          NB_DAYS=("RISK_NUM_T1", "count")
      )
      .reset_index()
)

# ======================================================
# 3) Projection 30 jours (logique financière)
# ======================================================
proj["RISK_SCORE_30D"] = (
    0.6 * proj["AVG_RISK_T1"] +
    0.4 * (proj["PCT_MEDIUM_T1"] * 3)
)

def risk_class_30d(score):
    if score >= 2.4:
        return "HIGH_RISK"
    elif score >= 1.6:
        return "MEDIUM_RISK"
    elif score >= 0.8:
        return "LOW_RISK"
    else:
        return "NORMAL"

proj["FINAL_RISK_CLASS_30D"] = proj["RISK_SCORE_30D"].apply(risk_class_30d)

# ======================================================
# 4) Probabilités interprétables
# ======================================================
proj["P_HIGH_RISK_30D"] = proj["PCT_HIGH_T1"] * 100
proj["P_MEDIUM_OR_HIGH_30D"] = proj["PCT_MEDIUM_T1"] * 100

# ======================================================
# 5) Feuille WAFA
# ======================================================
wafa_proj = proj[
    proj["SOCIETE_DE_GESTION"]
    .astype(str)
    .str.upper()
    .str.contains("WAFA", na=False)
]

# ======================================================
# 6) Export → AJOUT DE FEUILLES
# ======================================================
with pd.ExcelWriter(
    INPUT_FILE,
    engine="openpyxl",
    mode="a",
    if_sheet_exists="replace"
) as writer:
    proj.to_excel(writer, sheet_name="PROJECTION_30D_ALL", index=False)
    wafa_proj.to_excel(writer, sheet_name="PROJECTION_30D_WAFA", index=False)

print("🎉 Projection 30 jours ajoutée au fichier prediction_future_risk.xlsx")
