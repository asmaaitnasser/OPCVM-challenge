import pandas as pd
import numpy as np

# ======================================================
# CONFIG
# ======================================================
INPUT_FILE = "../scraper/fund_risk_score.xlsx"
OUTPUT_FILE = "../scraper/wafa_vs_market_comparaison.xlsx"

print("📥 Chargement du scoring des fonds...")
df = pd.read_excel(INPUT_FILE, sheet_name="ALL_FUNDS")

# Normalisation
df.columns = df.columns.str.upper().str.strip()
df["SOCIETE_DE_GESTION"] = df["SOCIETE_DE_GESTION"].astype(str).str.upper()

# ======================================================
# 1) Séparation Wafa / Marché
# ======================================================
df_wafa = df[df["SOCIETE_DE_GESTION"].str.contains("WAFA", na=False)]
df_market = df[~df["SOCIETE_DE_GESTION"].str.contains("WAFA", na=False)]

print(f"✔ Fonds marché : {len(df_market)}")
print(f"✔ Fonds Wafa Gestion : {len(df_wafa)}")

# ======================================================
# 2) Fonction de résumé statistique
# ======================================================
def risk_summary(df):
    return {
        "NB_FUNDS": len(df),
        "AVG_RISK_SCORE": df["RISK_SCORE"].mean(),
        "MEDIAN_RISK_SCORE": df["RISK_SCORE"].median(),
        "STD_RISK_SCORE": df["RISK_SCORE"].std(),
        "AVG_PCT_HIGH_RISK": df["PCT_HIGH_RISK"].mean(),
        "AVG_PCT_MEDIUM_HIGH": df["PCT_MEDIUM_HIGH"].mean(),
        "PCT_FUNDS_HIGH_RISK": (df["FINAL_RISK_CLASS"] == "HIGH_RISK").mean() * 100,
        "PCT_FUNDS_MEDIUM_HIGH": (
            df["FINAL_RISK_CLASS"].isin(["HIGH_RISK", "MEDIUM_RISK"])
        ).mean() * 100
    }

summary_market = risk_summary(df_market)
summary_wafa = risk_summary(df_wafa)

# ======================================================
# 3) Tableau comparatif
# ======================================================
comparison = pd.DataFrame.from_dict(
    {
        "MARKET": summary_market,
        "WAFA_GESTION": summary_wafa
    },
    orient="columns"
)

comparison["DIFF_WAFA_MINUS_MARKET"] = (
    comparison["WAFA_GESTION"] - comparison["MARKET"]
)

comparison = comparison.round(3)

# ======================================================
# 4) Répartition des classes de risque (%)
# ======================================================
def risk_distribution(df):
    return (
        df["FINAL_RISK_CLASS"]
        .value_counts(normalize=True)
        .mul(100)
        .round(2)
    )

dist_market = risk_distribution(df_market)
dist_wafa = risk_distribution(df_wafa)

dist_df = pd.concat(
    [dist_market, dist_wafa],
    axis=1,
    keys=["MARKET_%", "WAFA_%"]
).fillna(0)

# ======================================================
# 5) Interprétation automatique (bonus)
# ======================================================
interpretation = []

if summary_wafa["AVG_RISK_SCORE"] < summary_market["AVG_RISK_SCORE"]:
    interpretation.append("Wafa Gestion présente un score de risque moyen inférieur au marché.")
else:
    interpretation.append("Wafa Gestion présente un score de risque moyen supérieur au marché.")

if summary_wafa["PCT_FUNDS_HIGH_RISK"] < summary_market["PCT_FUNDS_HIGH_RISK"]:
    interpretation.append("Wafa Gestion a une proportion plus faible de fonds HIGH_RISK.")
else:
    interpretation.append("Wafa Gestion a une proportion plus élevée de fonds HIGH_RISK.")

if summary_wafa["STD_RISK_SCORE"] < summary_market["STD_RISK_SCORE"]:
    interpretation.append("La dispersion des risques est plus faible chez Wafa (gestion plus stable).")
else:
    interpretation.append("La dispersion des risques est plus élevée chez Wafa.")

interpretation_df = pd.DataFrame(
    {"INTERPRETATION": interpretation}
)

# ======================================================
# 6) Export Excel
# ======================================================
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    comparison.to_excel(writer, sheet_name="SUMMARY_COMPARISON")
    dist_df.to_excel(writer, sheet_name="RISK_DISTRIBUTION")
    df_wafa.to_excel(writer, sheet_name="WAFA_FUNDS_DETAIL", index=False)
    interpretation_df.to_excel(writer, sheet_name="INTERPRETATION", index=False)

print(f"\n🎉 Comparaison Wafa vs Marché exportée → {OUTPUT_FILE}")
