import os
import dash
from dash import html, dcc
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from flask_caching import Cache
from flask_jwt_extended import JWTManager
import redis
from datetime import datetime, timedelta

# Importer les composants
from .database.models import db, User, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
from .auth.auth import auth_bp, login_manager, hash_password, log_audit_action
from .auth.decorators import admin_required, analyst_required

# Configuration Flask
app = Flask(__name__)

# Database configuration - Neon requires SSL, use aggressive connection recycling
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'votre-secret-key-tres-securise')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://neondb_owner:npg_ciyfh8H9bZdj@ep-frosty-wind-a4aoph5q-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 1,  # Minimal pool for free tier
    'max_overflow': 2,  # Allow minimal overflow
    'pool_recycle': 30,  # Recycle every 30 seconds to prevent stale connections
    'pool_pre_ping': True,  # Test connection before using
    'connect_args': {
        'connect_timeout': 10,
    }
}
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-tres-securise')

# Initialiser la base de données
db.init_app(app)

# NullPool will create fresh connections for each query, avoiding stale SSL connections
# No need for pool event listeners with NullPool

# Configuration Flask-Login
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Configuration JWT
jwt = JWTManager(app)

# Configuration Redis pour le caching
try:
    redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': 'redis://redis:6379/0'})
except:
    cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Enregistrer les blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')

# Import dashboard creation functions
from .dashboards.modern_main_dashboard import create_modern_dashboard
from .dashboards.analytics_dashboard import AnalyticsDashboard
from .dashboards.map_dashboard import MapDashboard
from .components.admin_panel import AdminPanel

# Initialize Dash apps immediately (before first request)
# modern dashboard -> served at /dashboard/
dash_app1 = create_modern_dashboard(server=app,
                                    routes_pathname_prefix="/dashboard/",
                                    requests_pathname_prefix="/dashboard/")
# analytics -> served at /analytics/
analytics_dashboard = AnalyticsDashboard(server=app,
                                         routes_pathname_prefix="/analytics/",
                                         requests_pathname_prefix="/analytics/")
dash_app2 = analytics_dashboard.app
# map -> served at /map/
map_dashboard = MapDashboard(server=app,
                             routes_pathname_prefix="/map/",
                             requests_pathname_prefix="/map/")
dash_app3 = map_dashboard.app
# admin -> served at /admin/
admin_panel = AdminPanel(server=app,
                         routes_pathname_prefix="/admin/",
                         requests_pathname_prefix="/admin/")
dash_app4 = admin_panel.app

# Ensure callback exceptions allowed
dash_app1.config.suppress_callback_exceptions = True
dash_app2.config.suppress_callback_exceptions = True
dash_app3.config.suppress_callback_exceptions = True
dash_app4.config.suppress_callback_exceptions = True


# Routes Flask principales
@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/dashboard')
@login_required
@analyst_required
def dashboard():
    """Dashboard principal"""
    return dash_app1.index()

@app.route('/analytics')
@login_required
@analyst_required
def analytics():
    """Dashboard d'analyse"""
    return dash_app2.index()

@app.route('/map')
@login_required
@analyst_required
def map_view():
    """Vue cartographique"""
    return dash_app3.index()

@app.route('/admin')
@login_required
@admin_required
def admin():
    """Panneau d'administration"""
    return dash_app4.index()

@app.route('/api/properties')
@login_required
def api_properties():
    """API pour récupérer les propriétés"""
    try:
        # Récupérer les paramètres de filtrage
        source = request.args.get('source', 'all')
        city = request.args.get('city')
        property_type = request.args.get('type')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        
        # Construire la requête
        properties = []
        
        models_to_query = []
        if source == 'all' or source == 'coinafrique':
            models_to_query.append((CoinAfrique, 'coinafrique'))
        if source == 'all' or source == 'expatdakar':
            models_to_query.append((ExpatDakarProperty, 'expatdakar'))
        if source == 'all' or source == 'logerdakar':
            models_to_query.append((LogerDakarProperty, 'logerdakar'))
        
        for model, source_name in models_to_query:
            query = db.session.query(model)
            
            if city:
                query = query.filter(model.city.ilike(f'%{city}%'))
            if property_type:
                query = query.filter(model.property_type.ilike(f'%{property_type}%'))
            if min_price:
                query = query.filter(model.price >= min_price)
            if max_price:
                query = query.filter(model.price <= max_price)
            
            results = query.all()
            
            for result in results:
                prop_data = result.to_dict()
                prop_data['source'] = source_name
                properties.append(prop_data)
        
        return jsonify({
            'success': True,
            'count': len(properties),
            'properties': properties
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats')
@login_required
def api_stats():
    """API pour récupérer les statistiques"""
    try:
        # Statistiques des propriétés
        coinafrique_count = CoinAfrique.query.count()
        expat_count = ExpatDakarProperty.query.count()
        loger_count = LogerDakarProperty.query.count()
        total_properties = coinafrique_count + expat_count + loger_count
        
        # Prix moyen
        all_prices = []
        for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
            prices = db.session.query(model.price).all()
            all_prices.extend([p[0] for p in prices])
        
        avg_price = sum(all_prices) / len(all_prices) if all_prices else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_properties': total_properties,
                'coinafrique_count': coinafrique_count,
                'expat_count': expat_count,
                'loger_count': loger_count,
                'average_price': avg_price
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search')
@login_required
def api_search():
    """API de recherche full-text"""
    try:
        query = request.args.get('q', '')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Paramètre de recherche manquant'
            }), 400
        
        results = []
        
        # Rechercher dans toutes les tables
        for model, source_name in [
            (CoinAfrique, 'coinafrique'),
            (ExpatDakarProperty, 'expatdakar'),
            (LogerDakarProperty, 'logerdakar')
        ]:
            # Recherche dans le titre et la description
            title_results = model.query.filter(
                model.title.ilike(f'%{query}%')
            ).all()
            
            desc_results = model.query.filter(
                model.description.ilike(f'%{query}%')
            ).all() if hasattr(model, 'description') else []
            
            city_results = model.query.filter(
                model.city.ilike(f'%{query}%')
            ).all()
            
            # Combiner et dédupliquer les résultats
            all_results = list(set(title_results + desc_results + city_results))
            
            for result in all_results:
                result_data = result.to_dict()
                result_data['source'] = source_name
                results.append(result_data)
        
        return jsonify({
            'success': True,
            'count': len(results),
            'query': query,
            'results': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health_check():
    """Endpoint de vérification de santé"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected' if db.session.execute('SELECT 1').scalar() else 'disconnected'
    })

# Créer les tables et l'utilisateur admin par défaut
def create_tables():
    """Créer les tables et l'utilisateur admin par défaut"""
    try:
        # Drop all existing tables to ensure clean state
        db.drop_all()
        # Create all tables
        db.create_all()
        
        # Vérifier si l'utilisateur admin existe déjà
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            # Créer l'utilisateur admin par défaut
            admin_password = hash_password('admin123')
            admin_user = User(
                username='admin',
                email='admin@immobilier.sn',
                password_hash=admin_password,
                first_name='Administrateur',
                last_name='Système',
                role='admin',
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            
            print("Utilisateur admin créé avec succès")
            print("Identifiants par défaut: admin / admin123")
        
        # Créer un utilisateur analyste de démonstration
        analyst_user = User.query.filter_by(username='analyst').first()
        if not analyst_user:
            analyst_password = hash_password('analyst123')
            analyst_user = User(
                username='analyst',
                email='analyst@immobilier.sn',
                password_hash=analyst_password,
                first_name='Analyste',
                last_name='Données',
                role='analyst',
                is_active=True
            )
            db.session.add(analyst_user)
            db.session.commit()
            
            print("Utilisateur analyste créé avec succès")
            print("Identifiants: analyst / analyst123")
        
        # Créer un utilisateur viewer de démonstration
        viewer_user = User.query.filter_by(username='viewer').first()
        if not viewer_user:
            viewer_password = hash_password('viewer123')
            viewer_user = User(
                username='viewer',
                email='viewer@immobilier.sn',
                password_hash=viewer_password,
                first_name='Visiteur',
                last_name='Plateforme',
                role='viewer',
                is_active=True
            )
            db.session.add(viewer_user)
            db.session.commit()
            
            print("Utilisateur viewer créé avec succès")
            print("Identifiants: viewer / viewer123")
    
    except Exception as e:
        print(f"Erreur lors de la création des tables: {e}")

# Initialiser les tables avec le contexte d'application
with app.app_context():
    create_tables()

# Exposer l'application pour Gunicorn
server = app

if __name__ == '__main__':
    # Mode développement
    with app.app_context():
        init_dashboards_lazy()
    app.run(debug=True, host='0.0.0.0', port=8050)