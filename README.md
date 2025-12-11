# ImmoAnalytics - Plateforme d'Analyse Immobilière Intelligente

## 🎯 Description

ImmoAnalytics est une plateforme moderne et intuitive d'analyse immobilière développée pour le marché sénégalais. Elle permet de visualiser, explorer et analyser les données immobilières provenant de trois sources principales (CoinAfrique, ExpatDakar, LogerDakar) avec une intelligence artificielle intégrée pour faciliter la recherche.

## ✨ Fonctionnalités principales

### 🏠 Tableaux de bord interactifs
- **KPIs en temps réel** : Prix moyen, médian, nombre de propriétés
- **Graphiques dynamiques** : Distribution des prix, tendances temporelles
- **Analyses avancées** : Comparaisons par source, quartier, type de bien
- **Export de données** : CSV, Excel pour analyses approfondies
- **Sidebar intelligente** : Navigation contextuelle selon le rôle utilisateur

### 🤖 Recherche IA Intelligente (NEW)
- **Chatbot conversationnel** : Recherche en langage naturel
- **Extraction NLP** : Compréhension automatique des critères (budget, localisation, type)
- **Détection automatique** : Identification vente/location par IA
- **Filtrage intelligent** : Mise à jour automatique des filtres selon la conversation
- **Favoris** : Sauvegarde et gestion des propriétés favorites
- **Interface moderne** : Glass morphism design avec animations

### 🔍 Explorateur de données avancé
- **Filtres multi-critères** : Ville, quartier, type, prix, surface, chambres
- **Recherche full-text** : Recherche dans titres et descriptions
- **Analyse géographique** : Par quartier et commune
- **Tableaux dynamiques** : Tri, pagination, recherche instantanée
- **Export flexible** : CSV, Excel, JSON

### 🗺️ Carte interactive
- **Visualisation Mapbox** : Clustering intelligent des propriétés
- **Géolocalisation précise** : Marqueurs avec infobulles détaillées
- **Filtres géographiques** : Zoom par zone, rayon de recherche
- **Heat map** : Densité des prix par zone
- **Itinéraires** : Calcul de distances et temps de trajet

### 🔐 Sécurité et authentification renforcée
- **Système d'authentification sécurisé** : Flask-Login + JWT
- **Gestion des rôles granulaire** : Admin, Analyste, Viewer avec permissions spécifiques
- **Redirections intelligentes** : Routage automatique selon le rôle après connexion
- **Audit logging** : Traçabilité complète des actions utilisateurs
- **Sessions sécurisées** : Protection CSRF, XSS, injection SQL
- **Hashage bcrypt** : Mots de passe sécurisés

### 👑 Administration complète
- **Gestion des utilisateurs** : Création, modification, suppression, activation/désactivation
- **Attribution des rôles** : Système de permissions flexible
- **Surveillance système** : Métriques de performance, logs en temps réel
- **Configuration dashboards** : Personnalisation par rôle
- **Export massif** : Données utilisateurs et propriétés
- **Statistiques d'utilisation** : Activité par utilisateur et fonctionnalité

### 🎨 Interface utilisateur moderne
- **Design Glass Morphism** : Effets de transparence et flou
- **Sidebar adaptative** : Navigation contextuelle selon le rôle
- **Responsive design** : Mobile-first, adapté à tous les écrans
- **Animations GSAP** : Transitions fluides et élégantes
- **Dark mode ready** : Thème sombre disponible
- **Accessibilité** : ARIA labels, navigation clavier

## 🏗️ Architecture technique

### Stack technologique
- **Backend**: 
  - Python 3.11+
  - Flask 3.0.0 (API REST)
  - Dash 2.14.2 (Dashboards interactifs)
  - SQLAlchemy 2.0.23 (ORM)
  
- **Frontend**: 
  - Bootstrap 5.3.0
  - Dash Bootstrap Components
  - Dash Mantine Components
  - Font Awesome 6.4.0
  - GSAP 3.12.2 (Animations)
  
- **Base de données**: 
  - PostgreSQL (Neon Cloud)
  - Connexions poolées
  - Indexes optimisés
  
- **Cache & Sessions**: 
  - Redis 5.0.1
  - Session management
  - Rate limiting
  
- **Intelligence Artificielle**:
  - NLP (Natural Language Processing)
  - Pattern matching avancé
  - Classification automatique vente/location
  
- **Conteneurisation**: 
  - Docker & Docker Compose
  - Multi-stage builds
  - Health checks intégrés
  
- **Visualisations**: 
  - Plotly.js
  - Mapbox GL JS
  - Chart.js

### Structure du projet optimisée
```
immoanalytics/
├── app/
│   ├── auth/                      # Système d'authentification
│   │   ├── auth.py               # Routes et logique auth
│   │   ├── decorators.py         # @login_required, @admin_required
│   │   └── models.py             # User, AuditLog models
│   │
│   ├── dashboards/               # Applications Dash
│   │   ├── viewer_dashboard.py  # Dashboard Recherche IA
│   │   ├── analytics_dashboard.py
│   │   ├── map_dashboard.py
│   │   ├── admin_panel.py
│   │   └── modern_main_dashboard.py
│   │
│   ├── database/                 # Base de données
│   │   ├── models.py            # Modèles SQLAlchemy
│   │   ├── config.py            # Configuration DB
│   │   └── migrations/          # Alembic migrations
│   │
│   ├── components/              # Composants réutilisables
│   │   ├── dash_sidebar_component.py  # Sidebar pour Dash
│   │   ├── ai_assistant.py      # Chatbot IA
│   │   └── filters.py           # Filtres communs
│   │
│   ├── templates/               # Templates Jinja2
│   │   ├── base.html           # Template de base avec sidebar
│   │   ├── index.html          # Page d'accueil
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   ├── profile.html
│   │   │   └── settings.html
│   │   └── errors/
│   │       ├── 403.html
│   │       ├── 404.html
│   │       └── 500.html
│   │
│   ├── static/                  # Assets statiques
│   │   ├── css/
│   │   │   └── modern-ui.css
│   │   ├── js/
│   │   │   ├── animations.js
│   │   │   └── main.js
│   │   └── img/
│   │
│   ├── utils/                   # Utilitaires
│   │   ├── helpers.py
│   │   ├── validators.py
│   │   └── data_processing.py
│   │
│   ├── config.py               # Configuration globale
│   ├── __init__.py            # Factory Flask app
│   └── main.py                # Point d'entrée
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── tests/                      # Tests unitaires
│   ├── test_auth.py
│   ├── test_dashboards.py
│   └── test_api.py
│
├── docs/                       # Documentation
│   ├── AUTHENTICATION_README.md
│   ├── INSTALLATION.md
│   ├── SIDEBAR_INTEGRATION_GUIDE.md
│   └── API_DOCUMENTATION.md
│
├── .env.example               # Exemple de configuration
├── .gitignore
├── requirements.txt           # Dépendances Python
├── run.py                    # Script de lancement
└── README.md                 # Ce fichier
```

## 🚀 Installation et démarrage

### Prérequis
- **Docker** et **Docker Compose** (recommandé)
- **Python 3.11+** (pour développement local)
- **PostgreSQL 13+** (ou compte Neon)
- **Redis 5.0+** (optionnel, pour cache)

### Option 1 : Installation rapide avec Docker (Recommandé)

1. **Cloner le dépôt** :
```bash
git clone https://github.com/votreusername/immoanalytics.git
cd immoanalytics
```

2. **Configurer les variables d'environnement** :
```bash
cp .env.example .env
nano .env  # Éditer avec vos configurations
```

3. **Lancer avec Docker Compose** :
```bash
docker-compose up -d
```

4. **Initialiser la base de données** :
```bash
docker-compose exec web flask init-db
docker-compose exec web flask create-demo-users
```

5. **Accéder à l'application** :
- Application principale : http://localhost:8050
- Dashboard Analytics : http://localhost:8050/dashboard
- Recherche IA : http://localhost:8050/viewer
- Interface Admin : http://localhost:8050/admin

### Option 2 : Installation locale pour développement

1. **Créer un environnement virtuel** :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. **Installer les dépendances** :
```bash
pip install -r requirements.txt
```

3. **Configurer la base de données** :
```bash
# Créer le fichier .env avec vos configurations
cp .env.example .env

# Initialiser la base de données
flask init-db
```

4. **Créer les utilisateurs de démonstration** :
```bash
flask create-demo-users
```

5. **Lancer l'application** :
```bash
python run.py
```

L'application sera accessible sur http://localhost:8050

## ⚙️ Configuration

### Variables d'environnement essentielles

Créer un fichier `.env` à la racine du projet :

```env
# ========== BASE DE DONNÉES ==========
DATABASE_URL=postgresql://user:password@host:5432/database?sslmode=require

# Exemple Neon :
# DATABASE_URL=postgresql://neondb_owner:password@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require

# ========== SÉCURITÉ ==========
SECRET_KEY=votre-secret-key-ultra-securise-changez-absolument
JWT_SECRET_KEY=votre-jwt-secret-key-ultra-securise-changez-absolument

# ========== FLASK ==========
FLASK_ENV=production  # ou 'development'
FLASK_DEBUG=False     # True en développement
PORT=8050

# ========== REDIS (Optionnel) ==========
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# ========== SESSION ==========
SESSION_TYPE=filesystem
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=604800  # 7 jours

# ========== JWT ==========
JWT_ACCESS_TOKEN_EXPIRES=3600      # 1 heure
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 jours

# ========== MAPBOX (pour la carte) ==========
MAPBOX_ACCESS_TOKEN=votre_token_mapbox

# ========== LOGGING ==========
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### Configuration avancée

Dans `app/config.py`, vous pouvez personnaliser :
- Connexions poolées à PostgreSQL
- Rate limiting par route
- CORS origins autorisés
- Upload file limits
- Cache expiration times

## 📖 Utilisation

### Comptes de démonstration

Des comptes sont automatiquement créés au premier lancement :

| Rôle | Username | Password | Accès |
|------|----------|----------|-------|
| 👑 **Administrateur** | `admin` | `admin123` | Tous les dashboards + Gestion utilisateurs + Configuration système |
| 📊 **Analyste** | `analyst` | `analyst123` | Dashboard principal + Analytics + Carte + Recherche IA |
| 👁️ **Viewer** | `viewer` | `viewer123` | Recherche IA uniquement |

### Navigation par rôle

#### 👁️ **Viewer** voit :
```
🏠 Accueil
├── 🔍 Recherche IA (chatbot)
├── 👤 Mon Profil
├── ⚙️ Paramètres
└── 🚪 Déconnexion
```

#### 📊 **Analyste** voit :
```
🏠 Accueil
├── 📊 Dashboard Principal
├── 📈 Analytics Avancés
├── 🗺️ Vue Cartographique
├── 🔍 Recherche IA (chatbot)
├── 👤 Mon Profil
├── ⚙️ Paramètres
└── 🚪 Déconnexion
```

#### 👑 **Admin** voit :
```
🏠 Accueil
├── 📊 Dashboard Principal
├── 📈 Analytics Avancés
├── 🗺️ Vue Cartographique
├── 🔍 Recherche IA (chatbot)
├── 👑 Panneau Admin
│   ├── Gestion utilisateurs
│   ├── Logs d'audit
│   ├── Statistiques système
│   └── Configuration
├── 👤 Mon Profil
├── ⚙️ Paramètres
└── 🚪 Déconnexion
```

### Fonctionnalités détaillées

#### 🤖 Recherche IA
```python
# Exemples de requêtes naturelles :
"Je cherche un appartement à Dakar entre 50 et 100 millions"
"Maison avec piscine à Almadies"
"Terrain de 500m² pour moins de 30M"
"Villa 4 chambres à louer à Mermoz"
```

Le chatbot comprend :
- **Budget** : "50 millions", "entre 100k et 200k", "moins de 80M"
- **Localisation** : Villes, quartiers, communes
- **Type** : Appartement, maison, villa, terrain, studio
- **Caractéristiques** : Chambres, surface, équipements
- **Transaction** : Vente ou location (détection auto)

#### 📊 Dashboard Principal
- Vue d'ensemble avec KPIs
- Top 10 quartiers les plus chers
- Distribution des prix
- Évolution temporelle
- Comparaison par source

#### 📈 Analytics Avancés
- Analyse approfondie par critères multiples
- Graphiques personnalisables
- Export de données filtrées
- Statistiques descriptives

#### 🗺️ Carte Interactive
- Clustering intelligent
- Filtres géographiques
- Heat map des prix
- Itinéraires et distances

## 🔒 Sécurité

### Mesures implémentées

✅ **Authentification**
- Hashage bcrypt (12 rounds)
- JWT avec refresh tokens
- Sessions sécurisées Flask-Login
- Rate limiting sur login (5 tentatives / 15 min)

✅ **Autorisation**
- Système de rôles granulaire
- Permissions par endpoint
- Redirections intelligentes
- Middleware de vérification

✅ **Protection**
- CSRF tokens sur tous les formulaires
- XSS prevention (escaping automatique)
- SQL injection prevention (ORM)
- Secure cookies (httponly, secure, samesite)
- Headers de sécurité (CSP, HSTS)

✅ **Audit**
- Logging de toutes les actions sensibles
- Traçabilité par utilisateur
- IP tracking
- User agent logging

✅ **Données**
- Chiffrement des données sensibles
- Validation stricte des inputs
- Sanitization des données utilisateur

## 📊 API REST

### Endpoints principaux

#### Authentification
```bash
POST /auth/login
POST /auth/register
GET /auth/logout
GET /auth/profile
PUT /auth/change-password
```

#### Propriétés
```bash
GET /api/properties?city=Dakar&type=Appartement
GET /api/properties/{id}
GET /api/stats
POST /api/search
```

#### Utilisateurs (Admin)
```bash
GET /api/users
GET /api/users/{id}
POST /api/users
PUT /api/users/{id}
DELETE /api/users/{id}
```

### Exemple de requête

```bash
# Recherche de propriétés
curl -X GET "http://localhost:8050/api/properties?city=Dakar&min_price=50000000&max_price=100000000" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Statistiques
curl -X GET "http://localhost:8050/api/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## ⚡ Performance & Optimisation

### Optimisations implémentées

✅ **Backend**
- Connexions poolées PostgreSQL (min: 5, max: 20)
- Indexes sur colonnes critiques (prix, ville, type)
- Requêtes SQL optimisées avec JOINs efficaces
- Caching Redis pour données fréquentes (TTL: 5 min)
- Pagination des résultats (100 items max)

✅ **Frontend**
- Lazy loading des images
- Code splitting Dash
- Minification CSS/JS en production
- Compression Gzip
- CDN pour librairies (Bootstrap, Font Awesome)

✅ **Dashboards**
- Chargement asynchrone des graphiques
- Debouncing sur les filtres (500ms)
- Virtual scrolling pour grandes listes
- Memoization des callbacks Dash

### Métriques de performance

| Métrique | Valeur cible |
|----------|--------------|
| Page load | < 2s |
| API response | < 500ms |
| Dashboard render | < 1s |
| Search latency | < 300ms |
| Database query | < 100ms |

## 🐳 Déploiement

### Production avec Docker

1. **Build de l'image** :
```bash
docker build -t immoanalytics:latest .
```

2. **Configuration production** :
```bash
# docker-compose.prod.yml
version: '3.8'
services:
  web:
    image: immoanalytics:latest
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=False
    ports:
      - "80:8050"
    restart: always
```

3. **Lancement** :
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Déploiement sur cloud providers

#### Railway
```bash
railway login
railway init
railway up
```

#### Heroku
```bash
heroku create immoanalytics
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev
git push heroku main
```

#### AWS / GCP / Azure
Suivre les guides de déploiement Docker dans la documentation respective.

### Surveillance et maintenance

#### Health checks
```bash
# Endpoint de santé
GET /health

# Métriques Prometheus
GET /metrics
```

#### Logs
```bash
# Docker logs
docker logs -f immoanalytics_web

# Fichier logs
tail -f logs/app.log
```

#### Monitoring
- **Uptime** : UptimeRobot / Pingdom
- **Errors** : Sentry
- **Performance** : New Relic / DataDog
- **Database** : PgHero

## 🧪 Tests

### Lancer les tests

```bash
# Tests unitaires
pytest tests/

# Tests avec couverture
pytest --cov=app tests/

# Tests d'intégration
pytest tests/integration/

# Tests E2E
pytest tests/e2e/
```

### Structure des tests

```
tests/
├── test_auth.py          # Authentification
├── test_api.py           # Endpoints API
├── test_dashboards.py    # Dashboards Dash
├── test_models.py        # Modèles SQLAlchemy
└── test_utils.py         # Fonctions utilitaires
```

## 🤝 Contribution

### Workflow de contribution

1. **Fork** le projet
2. **Clone** votre fork :
```bash
git clone https://github.com/votre-username/immoanalytics.git
cd immoanalytics
```

3. **Créer une branche** pour votre fonctionnalité :
```bash
git checkout -b feature/AmazingFeature
```

4. **Développer** et **tester** vos modifications

5. **Commit** vos changements :
```bash
git commit -m 'feat: Add some AmazingFeature'
```

6. **Push** vers votre fork :
```bash
git push origin feature/AmazingFeature
```

7. **Ouvrir une Pull Request** sur GitHub

### Standards de code

- **Python** : PEP 8, type hints, docstrings
- **JavaScript** : ESLint, Prettier
- **Commits** : Conventional Commits
- **Tests** : Couverture > 80%

### Checklist PR

- [ ] Tests unitaires ajoutés
- [ ] Documentation mise à jour
- [ ] Pas de conflits avec main
- [ ] Code review passée
- [ ] CI/CD vert

## 📚 Documentation complète

### Guides disponibles

1. **AUTHENTICATION_README.md** : Système d'authentification détaillé
2. **INSTALLATION.md** : Guide d'installation approfondi
3. **SIDEBAR_INTEGRATION_GUIDE.md** : Intégration de la sidebar
4. **API_DOCUMENTATION.md** : Documentation API complète
5. **DEPLOYMENT_GUIDE.md** : Guide de déploiement

### Documentation technique

- Architecture système
- Diagrammes UML
- Schéma de base de données
- Flow charts utilisateur

## 🐛 Dépannage

### Problèmes courants

#### Base de données ne se connecte pas
```bash
# Vérifier la connexion
psql $DATABASE_URL

# Réinitialiser la DB
flask db-drop
flask init-db
```

#### Redis non accessible
```bash
# Vérifier Redis
redis-cli ping

# Désactiver le cache (mode dégradé)
export REDIS_ENABLED=False
```

#### Dashboards ne chargent pas
```bash
# Vérifier les logs
tail -f logs/app.log

# Nettoyer le cache
rm -rf __pycache__
rm -rf .dash_cache
```

#### Sidebar ne s'affiche pas
```bash
# Vérifier l'import
grep "dash_sidebar_component" app/dashboards/*.py

# Vérifier Font Awesome
curl -I https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css
```

## 📊 Statistiques du projet

- **Lignes de code** : ~15,000
- **Fichiers Python** : 45+
- **Templates HTML** : 15+
- **Dashboards** : 5
- **API Endpoints** : 25+
- **Tests** : 100+
- **Documentation** : 10+ guides

## 🗺️ Roadmap

### Version actuelle : 1.0.0

### Prochaines fonctionnalités (v1.1.0)
- [ ] Export PDF des rapports
- [ ] Notifications push
- [ ] Comparateur de biens
- [ ] Alertes prix personnalisées
- [ ] API publique avec clés

### Futur (v2.0.0)
- [ ] Machine Learning pour prédiction de prix
- [ ] Recommandations personnalisées
- [ ] Application mobile (React Native)
- [ ] Module de gestion locative
- [ ] Intégration paiement en ligne

## 📄 Licence

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👥 Équipe

- **Développement** : Cos Diallo
- **Design UI/UX** : ImmoAnalytics Team
- **Data Science** : ImmoAnalytics Team

## 📞 Support et Contact

### Obtenir de l'aide

- 📧 **Email** : support@immoanalytics.sn
- 💬 **Discord** : [Rejoindre notre serveur](https://discord.gg/immoanalytics)
- 🐛 **Issues GitHub** : [Signaler un bug](https://github.com/votreusername/immoanalytics/issues)
- 📖 **Documentation** : [docs.immoanalytics.sn](https://docs.immoanalytics.sn)

### Réseaux sociaux

- 🐦 **Twitter** : [@ImmoAnalytics](https://twitter.com/immoanalytics)
- 💼 **LinkedIn** : [ImmoAnalytics](https://linkedin.com/company/immoanalytics)
- 📸 **Instagram** : [@immoanalytics.sn](https://instagram.com/immoanalytics.sn)

## 🌟 Remerciements

Merci à tous les contributeurs et aux technologies open-source qui rendent ce projet possible :
- Flask & Dash teams
- Plotly community
- PostgreSQL & Neon
- Bootstrap & Font Awesome
- Tous nos beta-testeurs

---

<div align="center">

**ImmoAnalytics** - Décryptez le marché immobilier sénégalais avec intelligence et simplicité.

Made with ❤️ in Senegal 🇸🇳

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com)
[![Dash](https://img.shields.io/badge/Dash-2.14-purple.svg)](https://dash.plotly.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[🏠 Site Web](https://immoanalytics.sn) · [📖 Documentation](https://docs.immoanalytics.sn) · [🐛 Report Bug](https://github.com/votreusername/immoanalytics/issues) · [✨ Request Feature](https://github.com/votreusername/immoanalytics/issues)

</div>