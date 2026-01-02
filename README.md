# 🤖 AF-Advisory : Assistant Natural Language to SQL (NL2SQL)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![React](https://img.shields.io/badge/React-18-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-orange)
![Tailwind](https://img.shields.io/badge/Tailwind-CSS%20v4-cyan)

**AF-Advisory** est une application intelligente qui permet aux utilisateurs d'analyser leurs données (CSV, Excel) en posant simplement des questions en langage naturel. Fini le SQL complexe : l'IA génère, corrige et exécute les requêtes pour vous.

![Demo NL2SQL](backend/src/img/nl2sql.mp4)

---

## ✨ Fonctionnalités Clés

*   📂 **Support Multi-Format** : Importez vos fichiers `.csv`, `.xls`, ou `.xlsx`. Ils sont automatiquement convertis en base de données SQLite optimisée.
*   💬 **Interrogation en Langage Naturel** : Posez des questions comme *"Combien de clients habitent à Paris ?"* ou *"Donne-moi le top 5 des ventes par région"*.
*   🧠 **Workflow Agentique (LangGraph)** :
    *   Le système ne se contente pas de deviner ; il valide, exécute et **corrige** ses propres erreurs SQL si nécessaire.
    *   Mémoire contextuelle pour des conversations suivies ("Et parmi eux, combien sont actifs ?").
*   📊 **Visualisation de Données** :
    *   Tableau de prévisualisation des données brutes.
    *   Résumé statistique automatique (Nombre de lignes, colonnes, types).
*   🛡️ **Sécurité & Robustesse** :
    *   Exécution en mode **Read-Only** (pas de modification de données).
    *   Validation stricte des chemins de fichiers (anti-directory traversal).
    *   Nettoyage automatique du SQL généré.
*   🎨 **Interface Moderne** :
    *   Frontend React rapide et réactif.
    *   Design épuré avec **Tailwind CSS**.
    *   Mode "Transparence" : Possibilité de voir la requête SQL générée ("See the Reasoning").

---

## 🛠️ Stack Technique

### Backend (`/backend`)
*   **Framework** : FastAPI
*   **Orchestration** : LangGraph (pour le workflow cyclique de l'agent)
*   **LLM** : LangChain + OpenAI GPT-4o (configurable)
*   **Data** : Pandas (conversion), SQLite (moteur de données)
*   **Qualité** : Flake8 (PEP 8)

### Frontend (`/frontend`)
*   **Framework** : React + Vite
*   **Styling** : Tailwind CSS v4
*   **Icônes** : Lucide React
*   **Architecture** : Composants fonctionnels avec Hooks.

---

## 🚀 Installation et Démarrage

### Pré-requis
*   Python 3.10+
*   Node.js 18+
*   Clé API OpenAI (ou autre provider compatible)

### 1. Installation du Backend

```bash
cd backend

# Créer un environnement virtuel
python -m venv .venv

# Activer l'environnement
# Windows :
.venv\Scripts\activate
# Mac/Linux :
# source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
# Créez un fichier .env à la racine de /backend contenant :
# OPENAI_API_KEY=sk-....
```

### 2. Installation du Frontend

```bash
cd frontend

# Installer les dépendances
npm install
```

---

## ▶️ Utilisation

### Lancer le Backend
Dans un terminal (dossier `backend`) :
```bash
uvicorn main:app --reload
```
*Le serveur démarrera sur `http://localhost:8000`*

### Lancer le Frontend
Dans un autre terminal (dossier `frontend`) :
```bash
npm run dev
```
*L'interface sera accessible sur `http://localhost:5173` (ou port indiqué)*

---

## 📂 Structure du Projet

```text
/
├── backend/
│   ├── config/             # Configuration LLM (prompts, providers)
│   ├── databases/          # Stockage des fichiers transformés en .db
│   ├── src/
│   │   ├── api/            # Routes API (upload, query, data)
│   │   ├── text_to_sql/    # Moteur Agentique (Graph, LLM, Executor)
│   │   └── utils/          # Helpers (converters, validators)
│   ├── main.py             # Point d'entrée FastAPI
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/     # Composants React (ChatMessage, etc.)
│   │   ├── App.jsx         # Composant principal
│   │   └── index.css       # Tailwind config
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## 🤝 Contribution
Les contributions sont les bienvenues !
1.  Forkez le projet.
2.  Créez votre branche de fonctionnalité (`git checkout -b feature/AmazingFeature`).
3.  Commitez vos changements (`git commit -m 'Add some AmazingFeature'`).
4.  Poussez vers la branche (`git push origin feature/AmazingFeature`).
5.  Ouvrez une Pull Request.

---

## 📝 License
Distribué sous la licence MIT. Voir `LICENSE` pour plus d'informations.


