# ImmoAnalytics - Plateforme d'Analyse Immobilière

## Description

ImmoAnalytics est une plateforme moderne et intuitive d'analyse immobilière développée pour le marché sénégalais. Elle permet de visualiser, explorer et analyser les données immobilières provenant de plusieurs sources.

## Fonctionnalités principales

### 🏠 Tableaux de bord interactifs
- KPIs en temps réel (prix moyen, médian, nombre de propriétés)
- Graphiques dynamiques et visualisations
- Distribution des prix par source
- Tendances temporelles

### 🔍 Explorateur de données avancé
- Filtres multi-critères (ville, type, prix, surface)
- Recherche full-text
- Analyse par quartier et commune
- Export CSV/Excel

### 🗺️ Carte interactive
- Visualisation Mapbox avec clustering
- Localisation des propriétés
- Infobulles détaillées
- Filtres géographiques

### 🔐 Sécurité et authentification
- Système d'authentification sécurisé
- Gestion des rôles (Admin, Analyste, Visiteur)
- Journalisation des actions
- Sessions sécurisées

### ⚙️ Administration
- Gestion des utilisateurs
- Configuration des dashboards
- Surveillance du système
- Export des données

## Architecture technique

### Stack technologique
- **Backend**: Python 3.11, Flask, Dash
- **Frontend**: Bootstrap 5, Dash Mantine Components
- **Base de données**: PostgreSQL (Neon)
- **Cache**: Redis
- **Conteneurisation**: Docker
- **Visualisations**: Plotly.js

### Structure du projet
```
app/
├── auth/                 # Système d'authentification
├── dashboards/           # Applications Dash
├── database/             # Modèles SQLAlchemy
├── components/           # Composants réutilisables
├── templates/            # Templates HTML
├── static/               # Fichiers statiques
└── utils/                # Utilitaires
```

## Installation et démarrage

### Prérequis
- Docker et Docker Compose
- Python 3.11+ (pour développement local)
- Accès à une base de données PostgreSQL

### Installation rapide avec Docker

1. Cloner le dépôt :
```bash
git clone https://github.com/votreusername/immoanalytics.git
cd immoanalytics
```

2. Configurer les variables d'environnement :
```bash
cp .env.example .env
# Éditer .env avec vos configurations
```

3. Lancer avec Docker Compose :
```bash
docker-compose up -d
```

4. Accéder à l'application :
- Application principale : http://localhost:8050
- Interface d'administration : http://localhost:8050/admin

### Installation locale pour développement

1. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurer la base de données :
```bash
# La base de données sera créée automatiquement au premier démarrage
```

4. Lancer l'application :
```bash
python app/main.py
```

## Configuration

### Variables d'environnement

Créer un fichier `.env` avec les variables suivantes :

```env
# Configuration de la base de données
DATABASE_URL=postgresql://neondb_owner:votre_mot_de_passe@ep-frosty-wind-a4aoph5q-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# Clés secrètes
SECRET_KEY=votre-secret-key-tres-securise-ici-changez-moi
JWT_SECRET_KEY=votre-jwt-secret-key-tres-securise-ici-changez-moi

# Configuration Redis
REDIS_URL=redis://redis:6379/0

# Configuration Flask
FLASK_ENV=production
FLASK_DEBUG=False
```

## Utilisation

### Comptes de démonstration

Des comptes de démonstration sont créés automatiquement :

- **Administrateur** : `admin` / `admin123`
  - Accès complet à toutes les fonctionnalités
  - Gestion des utilisateurs et des configurations
  
- **Analyste** : `analyst` / `analyst123`
  - Accès aux dashboards et à l'explorateur de données
  - Vue sur la carte interactive
  
- **Visiteur** : `viewer` / `viewer123`
  - Accès limité aux dashboards principaux
  - Pas d'accès aux fonctionnalités d'administration

### Navigation

1. **Page d'accueil** : Présentation de la plateforme
2. **Dashboard** : Vue d'ensemble des KPIs
3. **Analyse** : Explorateur de données avec filtres
4. **Carte** : Visualisation géographique des propriétés
5. **Admin** : Gestion des utilisateurs (administrateurs uniquement)

## API REST

L'application expose plusieurs endpoints API :

### Propriétés
- `GET /api/properties` - Récupérer les propriétés filtrées
- `GET /api/stats` - Statistiques générales
- `GET /api/search` - Recherche full-text

### Authentification
- `POST /auth/login` - Connexion
- `POST /auth/register` - Inscription
- `GET /auth/logout` - Déconnexion

## Sécurité

- Mots de passe hachés avec bcrypt
- Sessions sécurisées avec Flask-Login
- Protection CSRF
- Journalisation des actions sensibles
- Gestion des rôles et permissions

## Performance

- Caching Redis pour les données fréquemment accédées
- Connexions poolées à la base de données
- Optimisation des requêtes SQL
- Chargement asynchrone des graphiques

## Déploiement

### Production avec Docker

```bash
# Construire l'image
docker build -t immoanalytics .

# Lancer avec docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Surveillance et maintenance

- Logs accessibles via `docker logs`
- Health check sur `/health`
- Métriques de performance intégrées

## Contribution

1. Fork le projet
2. Créer une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Support

Pour toute question ou problème :
- Créer une issue sur GitHub
- Contacter l'équipe de développement
- Consulter la documentation technique

---

**ImmoAnalytics** - Décryptez le marché immobilier sénégalais avec intelligence et simplicité.# dash_immo
