import pandas as pd
import numpy as np

# ======================================================
# CONFIG
# ======================================================
INPUT_FILE = "../scraper/prediction_future_risk.xlsx"
OUTPUT_FILE = "../scraper/wafa_vs_market_30d.xlsx"

print("📥 Chargement projection 30 jours...")
df = pd.read_excel(INPUT_FILE, sheet_name="PROJECTION_30D_ALL")

df.columns = df.columns.str.upper().str.strip()

# ======================================================
# 1️⃣ IDENTIFICATION WAFA
# ======================================================
df["IS_WAFA"] = (
    df["SOCIETE_DE_GESTION"]
    .astype(str)
    .str.upper()
    .str.contains("WAFA", na=False)
)

# ======================================================
# 2️⃣ COMPARAISON NIVEAU FONDS
#     MARKET = FONDS SANS WAFA
# ======================================================
print("📊 Comparaison niveau fonds...")

df_market = df[~df["IS_WAFA"]].copy()
df_wafa = df[df["IS_WAFA"]].copy()

funds_comp = pd.concat([
    df_market.assign(GROUP="MARKET_EX_WAFA"),
    df_wafa.assign(GROUP="WAFA_GESTION")
]).groupby("GROUP").agg(
    NB_FUNDS=("CODE_ISIN", "count"),
    AVG_RISK_SCORE_30D=("RISK_SCORE_30D", "mean"),
    AVG_P_HIGH_RISK_30D=("P_HIGH_RISK_30D", "mean"),
    AVG_P_MEDIUM_HIGH_30D=("P_MEDIUM_OR_HIGH_30D", "mean"),
    PCT_HIGH_RISK_FUNDS=("FINAL_RISK_CLASS_30D",
                          lambda x: (x == "HIGH_RISK").mean() * 100),
    PCT_MEDIUM_HIGH_FUNDS=("FINAL_RISK_CLASS_30D",
                            lambda x: x.isin(["HIGH_RISK", "MEDIUM_RISK"]).mean() * 100)
).reset_index()

# ======================================================
# 3️⃣ COMPARAISON NIVEAU SOCIÉTÉ DE GESTION
# ======================================================
print("🏢 Comparaison niveau société de gestion...")

sg_comp = df_market.groupby("SOCIETE_DE_GESTION").agg(
    NB_FUNDS=("CODE_ISIN", "count"),
    AVG_RISK_SCORE_30D=("RISK_SCORE_30D", "mean"),
    PCT_HIGH_RISK_FUNDS=("FINAL_RISK_CLASS_30D",
                          lambda x: (x == "HIGH_RISK").mean() * 100),
    PCT_MEDIUM_HIGH_FUNDS=("FINAL_RISK_CLASS_30D",
                            lambda x: x.isin(["HIGH_RISK", "MEDIUM_RISK"]).mean() * 100)
).reset_index()

sg_comp = sg_comp.sort_values("AVG_RISK_SCORE_30D", ascending=False)

# ======================================================
# 4️⃣ EXPORT MULTI-FEUILLES
# ======================================================
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    funds_comp.to_excel(writer, sheet_name="FUNDS_COMPARISON", index=False)
    sg_comp.to_excel(writer, sheet_name="SG_COMPARISON", index=False)

print(f"\n🎉 Comparaison WAFA vs Marché (hors WAFA) exportée → {OUTPUT_FILE}")
