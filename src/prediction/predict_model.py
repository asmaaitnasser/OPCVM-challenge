import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# ======================================================
# CONFIG
# ======================================================
INPUT_FILE = "../scraper/anomaly_cross_daily_weekly.xlsx"
OUTPUT_FILE = "../scraper/prediction_future_risk.xlsx"
SPLIT_DATE = "2024-12-31"

# ======================================================
# 1) Chargement des données
# ======================================================
print("📥 Chargement dataset pour prédiction future...")
df = pd.read_excel(INPUT_FILE)

df.columns = df.columns.str.upper().str.strip()

df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
df = df.dropna(subset=["DATE"])

# ======================================================
# 2) Encodage du RISK_LEVEL
# ======================================================
RISK_MAP = {
    "NORMAL": 0,
    "LOW_RISK": 1,
    "MEDIUM_RISK": 2,
    "HIGH_RISK": 3
}

df["RISK_LEVEL_NUM"] = df["RISK_LEVEL"].map(RISK_MAP)

# ======================================================
# 3) Création de la TARGET FUTURE (t+1)
# ======================================================
df = df.sort_values(["CODE_ISIN", "DATE"])

df["TARGET_RISK_T_PLUS_1"] = (
    df.groupby("CODE_ISIN")["RISK_LEVEL_NUM"]
      .shift(-1)
)

df = df.dropna(subset=["TARGET_RISK_T_PLUS_1"])
df["TARGET"] = df["TARGET_RISK_T_PLUS_1"].astype(int)

print("✔ Target future créée")

# ======================================================
# 4) Sélection des FEATURES (PAS DE FUTUR)
# ======================================================
FEATURES = [
    "RET_1J",
    "ZSCORE_1J",
    "ZSCORE_1W",
    "VOL_20D",
    "DRAWDOWN",
    "ANOMALY_SCORE_RULES",
    "ANOMALY_SCORE_IF",
    "ANOMALY_COMBINED_SCORE"
]

df = df.dropna(subset=FEATURES)

X = df[FEATURES]
y = df["TARGET"]

# ======================================================
# 5) Split temporel (FINANCE SAFE)
# ======================================================
train_mask = df["DATE"] <= pd.to_datetime(SPLIT_DATE)

X_train = X[train_mask]
y_train = y[train_mask]

X_test = X[~train_mask]
y_test = y[~train_mask]

print(f"✔ Train size : {len(X_train)}")
print(f"✔ Test size  : {len(X_test)}")

# ======================================================
# 6) Modèle Random Forest
# ======================================================
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=8,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# ======================================================
# 7) Évaluation
# ======================================================
y_pred = model.predict(X_test)

print("\n📊 Classification Report")
print(classification_report(y_test, y_pred))

print("\n📉 Confusion Matrix")
print(confusion_matrix(y_test, y_pred))

# ======================================================
# 8) Importance des features
# ======================================================
feat_importance = pd.Series(
    model.feature_importances_,
    index=FEATURES
).sort_values(ascending=False)

print("\n🔍 Feature importance")
print(feat_importance)

# ======================================================
# 9) Export des prédictions (ALL + WAFA)
# ======================================================
df_test = df.loc[X_test.index].copy()
df_test["PREDICTED_RISK_T_PLUS_1"] = y_pred

INV_RISK_MAP = {v: k for k, v in RISK_MAP.items()}
df_test["PREDICTED_RISK_LABEL"] = df_test["PREDICTED_RISK_T_PLUS_1"].map(INV_RISK_MAP)

# -------- FEUILLE WAFA GESTION --------
df_wafa = df_test[
    df_test["SOCIETE_DE_GESTION"]
    .astype(str)
    .str.upper()
    .str.contains("WAFA", na=False)
]

# -------- EXPORT MULTI-FEUILLES --------
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    df_test.to_excel(writer, sheet_name="ALL_MARKET", index=False)
    df_wafa.to_excel(writer, sheet_name="WAFA_GESTION", index=False)

print(f"\n🎉 Prédiction future exportée → {OUTPUT_FILE}")
print(f"✔ Lignes marché : {len(df_test)}")
print(f"✔ Lignes WAFA   : {len(df_wafa)}")
