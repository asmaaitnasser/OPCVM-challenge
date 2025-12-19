import pandas as pd
import numpy as np

# ======================================================
# CONFIG
# ======================================================
FUND_SCORE_FILE = "../scraper/fund_risk_score.xlsx"              # historique par fonds
PRED_30D_FILE    = "../scraper/prediction_future_risk.xlsx"      # projection 30 jours
OUTPUT_FILE      = "../scraper/recommendations.xlsx"

SHEET_FUND_SCORE = "ALL_FUNDS"
SHEET_PRED_30D   = "PROJECTION_30D_ALL"

print("📥 Chargement des fichiers...")
df_hist = pd.read_excel(FUND_SCORE_FILE, sheet_name=SHEET_FUND_SCORE)
df_30d  = pd.read_excel(PRED_30D_FILE, sheet_name=SHEET_PRED_30D)

# ======================================================
# 1) Normalisation minimale
# ======================================================
df_hist.columns = df_hist.columns.str.upper().str.strip()
df_30d.columns  = df_30d.columns.str.upper().str.strip()

# Normaliser SG
if "SOCIETE_DE_GESTION" in df_hist.columns:
    df_hist["SOCIETE_DE_GESTION"] = df_hist["SOCIETE_DE_GESTION"].astype(str).str.upper()
if "SOCIETE_DE_GESTION" in df_30d.columns:
    df_30d["SOCIETE_DE_GESTION"] = df_30d["SOCIETE_DE_GESTION"].astype(str).str.upper()

# ======================================================
# 2) Sélection des colonnes utiles
# ======================================================
# Historique (fund_risk_score)
need_hist = [
    "CODE_ISIN", "SOCIETE_DE_GESTION", "OPCVM",
    "RISK_SCORE", "FINAL_RISK_CLASS", "PCT_HIGH_RISK", "PCT_MEDIUM_HIGH"
]
for c in need_hist:
    if c not in df_hist.columns:
        df_hist[c] = np.nan

df_hist = df_hist[need_hist].copy()

# Projection 30 jours
need_30d = [
    "CODE_ISIN", "SOCIETE_DE_GESTION", "OPCVM",
    "RISK_SCORE_30D", "FINAL_RISK_CLASS_30D",
    "P_HIGH_RISK_30D", "P_MEDIUM_OR_HIGH_30D", "NB_DAYS"
]
for c in need_30d:
    if c not in df_30d.columns:
        df_30d[c] = np.nan

df_30d = df_30d[need_30d].copy()

# ======================================================
# 3) Merge Historique + Futur30
# ======================================================
print("🔗 Fusion des infos (historique + 30 jours)...")
df = pd.merge(df_30d, df_hist, on="CODE_ISIN", how="left", suffixes=("_30D", "_HIST"))

# Harmoniser OPCVM / SG si manque côté 30D
df["SOCIETE_DE_GESTION"] = df["SOCIETE_DE_GESTION_30D"].combine_first(df["SOCIETE_DE_GESTION_HIST"])
df["OPCVM"] = df["OPCVM_30D"].combine_first(df["OPCVM_HIST"])

# Nettoyage colonnes doublons
drop_cols = [c for c in df.columns if c.endswith("_30D") or c.endswith("_HIST")]
# On garde les versions "propres" qu'on vient de créer + les métriques
keep_cols = [
    "CODE_ISIN", "SOCIETE_DE_GESTION", "OPCVM",
    "FINAL_RISK_CLASS", "RISK_SCORE", "PCT_HIGH_RISK", "PCT_MEDIUM_HIGH",
    "FINAL_RISK_CLASS_30D", "RISK_SCORE_30D", "P_HIGH_RISK_30D", "P_MEDIUM_OR_HIGH_30D", "NB_DAYS"
]
df = df[keep_cols].copy()

# ======================================================
# 4) Recommandation (règles métier)
# ======================================================
def reco_rule(hist, fut):
    hist = str(hist).upper()
    fut  = str(fut).upper()

    stable_hist = hist in ["NORMAL", "LOW_RISK"]
    stable_fut  = fut  in ["NORMAL", "LOW_RISK"]

    if stable_hist and stable_fut:
        return "STABLE_REINFORCE"
    if stable_hist and fut == "MEDIUM_RISK":
        return "MONITOR"
    if (hist in ["NORMAL", "LOW_RISK", "MEDIUM_RISK"]) and fut == "HIGH_RISK":
        return "REDUCE_EXPOSURE"
    if hist == "HIGH_RISK" and fut == "HIGH_RISK":
        return "REVIEW_STRATEGY"
    if (hist in ["MEDIUM_RISK", "HIGH_RISK"]) and stable_fut:
        return "IMPROVING_KEEP_WATCH"
    return "WATCHLIST"

df["RECOMMENDATION"] = df.apply(
    lambda r: reco_rule(r["FINAL_RISK_CLASS"], r["FINAL_RISK_CLASS_30D"]),
    axis=1
)

# ======================================================
# 5) Priority score (tri)
# ======================================================
RISK_MAP = {"NORMAL": 0, "LOW_RISK": 1, "MEDIUM_RISK": 2, "HIGH_RISK": 3}

hist_pts = df["FINAL_RISK_CLASS"].astype(str).str.upper().map(RISK_MAP).fillna(0)
fut_pts  = df["FINAL_RISK_CLASS_30D"].astype(str).str.upper().map(RISK_MAP).fillna(0)

# Score de base (futur plus important)
df["PRIORITY_SCORE"] = 0.65 * fut_pts + 0.35 * hist_pts

# Bonus si probabilité medium/high élevée (si dispo)
if "P_MEDIUM_OR_HIGH_30D" in df.columns:
    df["PRIORITY_SCORE"] += (df["P_MEDIUM_OR_HIGH_30D"].fillna(0) / 100.0) * 0.75

df["PRIORITY_SCORE"] = df["PRIORITY_SCORE"].round(4)

# ======================================================
# 6) Commentaire technique (court)
# ======================================================
def comment(r):
    return (
        f"Hist={r['FINAL_RISK_CLASS']} (score={r['RISK_SCORE']}); "
        f"Futur30={r['FINAL_RISK_CLASS_30D']} (score30={r['RISK_SCORE_30D']}); "
        f"P(M/H)30={r.get('P_MEDIUM_OR_HIGH_30D', np.nan)}"
    )

df["COMMENTAIRE_TECH"] = df.apply(comment, axis=1)

# ======================================================
# 7) Tri final + feuille WAFA
# ======================================================
df = df.sort_values(["PRIORITY_SCORE", "P_MEDIUM_OR_HIGH_30D"], ascending=False)

df_wafa = df[
    df["SOCIETE_DE_GESTION"]
    .astype(str).str.upper()
    .str.contains("WAFA", na=False)
].copy()

# ======================================================
# 8) Synthèse
# ======================================================
summary = (
    df.groupby("RECOMMENDATION")
      .agg(
          NB_FUNDS=("CODE_ISIN", "count"),
          AVG_PRIORITY=("PRIORITY_SCORE", "mean"),
          AVG_RISK_SCORE_30D=("RISK_SCORE_30D", "mean"),
          AVG_P_MEDIUM_OR_HIGH_30D=("P_MEDIUM_OR_HIGH_30D", "mean")
      )
      .reset_index()
      .sort_values("NB_FUNDS", ascending=False)
)

# ======================================================
# 9) Export multi-feuilles
# ======================================================
print("💾 Export Excel...")
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="ALL_FUNDS_RECO", index=False)
    df_wafa.to_excel(writer, sheet_name="WAFA_GESTION_RECO", index=False)
    summary.to_excel(writer, sheet_name="SUMMARY_RECO", index=False)

print(f"🎉 Recommandations exportées → {OUTPUT_FILE}")
