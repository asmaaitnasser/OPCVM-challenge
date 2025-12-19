import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ======================================================
# CONFIG
# ======================================================
INPUT_FILE = "../scraper/features_anomaly_weekly.xlsx"
OUTPUT_FILE = "../scraper/anomaly_results_weekly.xlsx"

print("📥 Chargement features anomalies weekly...")
df = pd.read_excel(INPUT_FILE)

# ======================================================
# 1️⃣ Sécurité sur la date
# ======================================================
df["WEEK_DATE"] = pd.to_datetime(df["WEEK_DATE"], errors="coerce")
df = df.dropna(subset=["WEEK_DATE", "CODE_ISIN"])

df = df.sort_values(["CODE_ISIN", "WEEK_DATE"])

# ======================================================
# 2️⃣ Sélection des features pour le modèle
# ======================================================
FEATURES = [
    "RET_1W",
    "ZSCORE_1W",
    "VOL_12W",
    "DRAWDOWN",
    "MOM_4W",
    "MOM_12W"
]

X = df[FEATURES].copy()

# Nettoyage final
X = X.replace([np.inf, -np.inf], np.nan)
valid_idx = X.dropna().index
X = X.loc[valid_idx]
df = df.loc[valid_idx]

print(f"✔ Lignes exploitables pour le ML : {len(X)}")

# ======================================================
# 3️⃣ Standardisation
# ======================================================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ======================================================
# 4️⃣ Isolation Forest
# ======================================================
iso = IsolationForest(
    n_estimators=300,
    contamination=0.02,   # ~2% d’anomalies attendues
    random_state=42,
    n_jobs=-1
)

df["ANOMALY_IF"] = iso.fit_predict(X_scaled)
df["ANOMALY_SCORE_IF"] = iso.decision_function(X_scaled)

# Convention : 1 = anomalie
df["ANOMALY_IF"] = df["ANOMALY_IF"].map({1: 0, -1: 1})

# ======================================================
# 5️⃣ Résumé
# ======================================================
anomaly_rate = df["ANOMALY_IF"].mean() * 100

print("✔ Détection d’anomalies WEEKLY terminée")
print(f"✅ Taux d’anomalies détectées : {anomaly_rate:.2f}% (attendu ~2%)")

print("\nTop 10 anomalies weekly :")
print(
    df[df["ANOMALY_IF"] == 1]
    .sort_values("ANOMALY_SCORE_IF")
    .head(10)[
        ["WEEK_DATE", "CODE_ISIN", "RET_1W", "ZSCORE_1W", "VOL_12W",
         "DRAWDOWN", "MOM_4W", "MOM_12W", "ANOMALY_SCORE_RULES", "ANOMALY_SCORE_IF"]
    ]
)

# ======================================================
# 6️⃣ Export
# ======================================================
df.to_excel(OUTPUT_FILE, index=False)
print(f"\n🎉 Résultats exportés → {OUTPUT_FILE}")
