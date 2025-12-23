# 🚀 Guide de Déploiement - OPCVM Challenge

**Auteur :** Maha
**Date :** 23 Décembre 2025
**Projet :** OPCVM Challenge - FundWatch AI

---

## 📌 Vue d'ensemble

Ce document résume tous les changements effectués pour déployer l'application OPCVM Challenge en ligne.

### 🌐 URLs de production

- **Frontend Landing Page** : https://opcvm-challenge.vercel.app
- **Backend API FastAPI** : https://opcvm-challenge.onrender.com
- **Dashboard Streamlit** : https://opcvm-streamlit.onrender.com

---

## 📋 Changements effectués

### 1. Backend FastAPI

#### 📄 `requirements.txt` (renommé de `requirement.txt`)

**Raison :** Respecter la convention standard et ajouter les dépendances FastAPI.

**Changements :**
- ✅ Renommé `requirement.txt` → `requirements.txt`
- ✅ Ajout de FastAPI et Uvicorn :
  ```txt
  fastapi==0.104.1
  uvicorn[standard]==0.24.0
  ```

- ✅ Mise à jour des dépendances pour compatibilité Python 3.13 :
  ```txt
  streamlit==1.39.0      # était 1.28.0
  pandas==2.2.3          # était 2.1.1
  numpy==1.26.4          # était 1.25.2
  matplotlib==3.9.2      # était 3.7.2
  selenium==4.27.1       # était 4.11.2
  webdriver-manager==4.0.2  # était 3.8.6
  requests==2.32.3       # était 2.31.0
  scikit-learn==1.5.2    # était 1.3.0
  ```

---

#### 📄 `api_main.py`

**Raison :** Configurer FastAPI avec CORS pour permettre les requêtes du frontend.

**Code ajouté :**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.app.api_overview import router as overview_router

app = FastAPI()

# Configuration CORS pour permettre les requêtes du frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifiez votre domaine Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview_router, prefix="/api")
```

---

#### 📄 `src/app/api_overview.py`

**Raison :** Ajouter un router FastAPI pour exposer l'endpoint `/api/overview`.

**Code ajouté (à la fin du fichier) :**
```python
# ======================================================
# FastAPI Router
# ======================================================
from fastapi import APIRouter

router = APIRouter()

@router.get("/overview")
def api_overview():
    """
    Endpoint API pour récupérer les métriques overview.
    """
    return get_overview_metrics()
```

**Endpoint disponible :** `GET https://opcvm-challenge.onrender.com/api/overview`

---

### 2. Frontend React

#### 📄 `frontend/.env.production` (nouveau fichier)

**Raison :** Configurer l'URL de l'API backend en production.

**Contenu :**
```env
VITE_API_URL=https://opcvm-challenge.onrender.com
```

---

#### 📄 `frontend/src/components/Navbar.jsx`

**Raison :** Mettre à jour le lien du bouton "Accéder au Dashboard" pour pointer vers le dashboard Streamlit en production.

**Changement (ligne 20) :**
```javascript
// Avant
onClick={() => window.location.href = "http://localhost:8501"}

// Après
onClick={() => window.location.href = "https://opcvm-streamlit.onrender.com"}
```

---

#### 📄 `frontend/src/sections/Hero.jsx`

**Raison :** Mettre à jour le lien du bouton "Explorer le Dashboard".

**Changement (ligne 31) :**
```javascript
// Avant
onClick={() => window.location.href = "http://localhost:8501"}

// Après
onClick={() => window.location.href = "https://opcvm-streamlit.onrender.com"}
```

---

### 3. Configuration Git

#### 📄 `.gitignore`

**Raison :** Permettre l'ajout des fichiers parquet au repository pour le déploiement.

**Ajout (après la ligne 9) :**
```gitignore
# Allow parquet files in scraper directory
!src/scraper/*.parquet
```

---

#### 📦 Fichiers de données ajoutés

**Raison :** Fournir les données nécessaires pour que l'API fonctionne en production.

**Fichiers ajoutés :**
- ✅ `src/scraper/anomaly_results_daily.parquet` (5.9 MB)
- ✅ `src/scraper/anomaly_results_weekly.parquet` (5.2 MB)

---

## 📝 Commits effectués

### Liste des commits (dans l'ordre chronologique)

```bash
# Commit 1: ea23b7e
git commit -m "Add deployment configuration for Render - Rename requirement.txt to requirements.txt - Add FastAPI and Uvicorn dependencies - Add CORS middleware"

# Commit 2: 77c05fe
git commit -m "Update dependencies for Python 3.13 compatibility"

# Commit 3: bde7240
git commit -m "Add FastAPI router to api_overview endpoint"

# Commit 4: 6cb5057
git commit -m "Add production environment config for frontend"

# Commit 5: 2c56464
git commit -m "Update dashboard links to production Streamlit URL"

# Commit 6: c555581
git commit -m "Add data files for production deployment"
```

### Voir l'historique des commits

```bash
git log --oneline -6
```

---

## 🛠️ Configuration des déploiements

### 1️⃣ Backend FastAPI sur Render

**Service :** Web Service
**URL :** https://opcvm-challenge.onrender.com

**Configuration :**
- **Name :** opcvm-challenge
- **Build Command :** `pip install -r requirements.txt`
- **Start Command :** `uvicorn api_main:app --host 0.0.0.0 --port $PORT`
- **Environment :** Python 3.13.4

**Endpoints disponibles :**
- `GET /api/overview` - Récupère les métriques overview

---

### 2️⃣ Dashboard Streamlit sur Render

**Service :** Web Service
**URL :** https://opcvm-streamlit.onrender.com

**Configuration :**
- **Name :** opcvm-streamlit
- **Build Command :** `pip install -r requirements.txt`
- **Start Command :** `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
- **Environment :** Python 3.13.4

---

### 3️⃣ Frontend React sur Vercel

**Service :** Web Application
**URL :** https://opcvm-challenge.vercel.app

**Configuration :**
- **Framework Preset :** Vite
- **Root Directory :** `frontend`
- **Build Command :** `npm run build`
- **Output Directory :** `dist`
- **Node Version :** 18.x

**Déploiement automatique :** À chaque push sur la branche `main`

---

## 🏗️ Architecture finale

```
┌─────────────────────────────────────────────────────┐
│           Frontend (Vercel)                         │
│     https://opcvm-challenge.vercel.app              │
│                                                     │
│  • Landing page avec présentation du projet        │
│  • Boutons de navigation vers le dashboard         │
│  • Design responsive avec Tailwind CSS             │
└──────────────┬──────────────────────────────────────┘
               │
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌──────────────────┐   ┌──────────────────────────────┐
│  Backend API     │   │  Dashboard Streamlit         │
│  (Render)        │   │  (Render)                    │
│                  │   │                              │
│  FastAPI         │   │  • Interface utilisateur     │
│  • /api/overview │   │  • Visualisations            │
│  • CORS enabled  │   │  • Analyses ML               │
│  • JSON API      │   │  • Prédictions               │
└──────────────────┘   └──────────────────────────────┘
```

---

## 📊 Résumé des changements

| Catégorie | Nombre |
|-----------|--------|
| Fichiers modifiés | 8 |
| Fichiers créés | 2 |
| Commits | 6 |
| Services déployés | 3 |
| URLs publiques | 3 |

---

## 🔄 Pour récupérer ces changements

Si vous travaillez sur un fork ou un autre ordinateur, voici comment récupérer tous ces changements :

```bash
# 1. Récupérer les derniers changements
git pull origin main

# 2. Vérifier l'historique des commits
git log --oneline -10

# 3. Voir tous les fichiers modifiés
git diff HEAD~6 HEAD --name-only

# 4. Voir le détail des changements
git diff HEAD~6 HEAD
```

---

## ⚠️ Points importants à noter

### Pour la production :

1. **Fichiers de données manquants**
   Les fichiers Excel suivants sont référencés dans le code mais absents du repository :
   - `anomaly_cross_daily_weekly.xlsx`
   - `fund_risk_score.xlsx`
   - `prediction_future_risk.xlsx`
   - `performance_quotidienne_asfim_clean.xlsx`

   **Solution :** Le code utilise des fonctions `_safe_read_excel()` qui retournent des DataFrames vides si les fichiers sont absents, évitant ainsi les crashes.

2. **CORS en production**
   Actuellement, `allow_origins=["*"]` accepte toutes les origines. Pour plus de sécurité, il est recommandé de spécifier uniquement le domaine Vercel :
   ```python
   allow_origins=["https://opcvm-challenge.vercel.app"]
   ```

3. **Modèles ML**
   Les modèles de machine learning (fichiers `.pkl`, `.joblib`) ne sont pas inclus dans le repository. Ils devront être ajoutés ou régénérés en production si nécessaire.

---

## 🔑 Variables d'environnement

### Backend (Render)
Aucune variable d'environnement requise actuellement.

### Frontend (Vercel)
- `VITE_API_URL` : Défini dans `frontend/.env.production`

### Streamlit (Render)
Aucune variable d'environnement requise actuellement.

---

## 🧪 Tester l'application

### 1. Tester le backend API
```bash
curl https://opcvm-challenge.onrender.com/api/overview
```

### 2. Tester le frontend
Ouvrir https://opcvm-challenge.vercel.app dans un navigateur

### 3. Tester le dashboard
Ouvrir https://opcvm-streamlit.onrender.com dans un navigateur

---

## 📞 Support

Pour toute question ou problème :
- Vérifier les logs sur Render : https://dashboard.render.com
- Vérifier les déploiements sur Vercel : https://vercel.com/dashboard
- Consulter la documentation FastAPI : https://fastapi.tiangolo.com
- Consulter la documentation Streamlit : https://docs.streamlit.io

---

## ✅ Checklist de déploiement

- [x] Backend FastAPI déployé sur Render
- [x] Dashboard Streamlit déployé sur Render
- [x] Frontend React déployé sur Vercel
- [x] CORS configuré pour permettre les requêtes cross-origin
- [x] URLs de production mises à jour dans le frontend
- [x] Fichiers de données parquet ajoutés au repository
- [x] Dépendances mises à jour pour Python 3.13
- [ ] Ajouter les fichiers Excel manquants (optionnel)
- [ ] Ajouter les modèles ML (optionnel)
- [ ] Restreindre CORS aux domaines autorisés (recommandé)

---

**🎉 L'application est maintenant déployée et accessible publiquement !**

---

*Généré le 23 Décembre 2025 par Maha avec Claude Code*
