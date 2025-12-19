import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ======================================================
# CONFIG
# ======================================================
INPUT_FILE = "../scraper/features_anomaly_daily.xlsx"
OUTPUT_FILE = "../scraper/anomaly_results_daily.xlsx"

FEATURES = [
    "RET_1J",
    "ZSCORE_1J",
    "ZSCORE_1W",
    "VOL_20D",
    "DRAWDOWN"
]

print("📥 Chargement features anomalies daily...")
df = pd.read_excel(INPUT_FILE)

# ======================================================
# 1) Sélection & nettoyage des features
# ======================================================
X = df[FEATURES].copy()

# Remplacer inf par NaN
X = X.replace([np.inf, -np.inf], np.nan)

# Supprimer lignes incomplètes pour le ML
valid_idx = X.dropna().index
X = X.loc[valid_idx]

print(f"✔ Lignes exploitables pour le ML : {len(X)}")

# ======================================================
# 2) Standardisation
# ======================================================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ======================================================
# 3) Modèle Isolation Forest
# ======================================================
model = IsolationForest(
    n_estimators=200,
    contamination=0.02,   # ~2% anomalies
    random_state=42,
    n_jobs=-1
)

model.fit(X_scaled)

# ======================================================
# 4) Scores & labels
# ======================================================
df.loc[valid_idx, "ANOMALY_SCORE_IF"] = model.decision_function(X_scaled)
df.loc[valid_idx, "ANOMALY_LABEL_IF"] = model.predict(X_scaled)

# Convention lisible
df["ANOMALY_FLAG_IF"] = (df["ANOMALY_LABEL_IF"] == -1).astype(int)

print("✔ Détection d’anomalies par Isolation Forest terminée")

anom_rate = df["ANOMALY_FLAG_IF"].mean()
print(f"✅ Taux d’anomalies détectées: {anom_rate:.3%} (attendu ~2%)")

top = df[df["ANOMALY_FLAG_IF"] == 1].sort_values("ANOMALY_SCORE_IF").head(10)
print("\nTop 10 anomalies (aperçu):")
print(top[["DATE", "CODE_ISIN", "RET_1J", "ZSCORE_1J", "VOL_20D", "DRAWDOWN", "ANOMALY_SCORE_RULES", "ANOMALY_SCORE_IF"]])

# ======================================================
# 5) Export
# ======================================================
df.to_excel(OUTPUT_FILE, index=False)
print(f"🎉 Résultats exportés → {OUTPUT_FILE}")
