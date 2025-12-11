from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import os
from app.dashboards.main_dashboard import create_enhanced_dashboard
import dash
from dash import html, dcc
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
from flask_login import LoginManager, login_required, current_user, logout_user
from flask_caching import Cache
from flask_jwt_extended import JWTManager
from sqlalchemy.pool import NullPool
import redis
from datetime import datetime, timedelta
from flask_cors import CORS

# Importer les composants
from .database.models import db, User, CoinAfrique, ExpatDakarProperty, LogerDakarProperty, ProprietesConsolidees, AuditLog, DashboardConfig, MarketIndex
from .auth.auth import auth_bp, login_manager, hash_password, log_audit_action
from .auth.decorators import admin_required, analyst_required

# Configuration Flask
app = Flask(__name__)

# Database configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'votre-secret-key-tres-securise')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://neondb_owner:npg_9vrYBWUeT7js@ep-raspy-dust-a4a9f62f-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': NullPool,
    'connect_args': {
        'connect_timeout': 10,
        'sslmode': 'require'
    }
}
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-tres-securise')

CORS(app)

# Initialiser la base de données
db.init_app(app)

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
from .dashboards.modern_main_dashboard import create_observatoire_dashboard
from .dashboards.analytics_dashboard import create_ultra_dashboard
from .dashboards.map_dashboard import PremiumMapDashboard
from .dashboards.viewer_dashboard import create_viewer_dashboard
from .components.admin_panel import AdminPanel

# Initialize Dash apps
dash_app1 = create_observatoire_dashboard(server=app, routes_pathname_prefix="/dashboard/", requests_pathname_prefix="/dashboard/")
dash_app2 = create_ultra_dashboard(server=app, routes_pathname_prefix="/analytics/", requests_pathname_prefix="/analytics/")
map_dashboard = PremiumMapDashboard(server=app, routes_pathname_prefix="/map/", requests_pathname_prefix="/map/")
dash_app3 = map_dashboard.app
dash_app5 = create_viewer_dashboard(server=app, routes_pathname_prefix="/viewer/", requests_pathname_prefix="/viewer/")
admin_panel = AdminPanel(server=app, routes_pathname_prefix="/admin/", requests_pathname_prefix="/admin/")
dash_app4 = admin_panel.app

# Ensure callback exceptions allowed
for dash_app in [dash_app1, dash_app2, dash_app3, dash_app4, dash_app5]:
    dash_app.config.suppress_callback_exceptions = True

# ============================================
# NOUVELLE STRUCTURE DE ROUTES POUR NAVIGATION
# ============================================

@app.context_processor
def inject_navigation():
    """Rend la navigation disponible dans tous les templates"""
    return {
        'home_url': url_for('home'),
        'logout_url': url_for('logout') if current_user.is_authenticated else None
    }

@app.route('/')
@app.route('/accueil')
def home():
    """PAGE D'ACCUEIL UNIQUE - accessible à tous"""
    if current_user.is_authenticated:
        # Affiche un accueil personnalisé avec accès rapide
        return render_template('index.html', user=current_user)
    return render_template('index.html')

@app.route('/mon-espace')
@login_required
def mon_espace():
    """Redirection intelligente vers l'espace utilisateur"""
    if current_user.role == 'viewer':
        return redirect(url_for('viewer'))
    elif current_user.role in ['analyst', 'admin']:
        return redirect(url_for('dashboard'))
    else:
        flash("Rôle non reconnu.", "error")
        return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
    """Déconnexion et retour à l'accueil"""
    logout_user()
    flash("Déconnexion réussie.", "success")
    return redirect(url_for('home'))

@app.errorhandler(403)
def forbidden(error):
    """Gestion des accès interdits avec redirection"""
    if current_user.is_authenticated and current_user.role == 'viewer':
        flash("Accès réservé aux analystes et administrateurs.", "warning")
        return redirect(url_for('viewer'))
    flash("Permissions insuffisantes.", "error")
    return redirect(url_for('home'))

# ============================================
# ROUTES DES DASHBOARDS (inchangées)
# ============================================

@app.route('/dashboard')
@login_required
@analyst_required
def dashboard():
    """Dashboard principal avec lien vers accueil intégré dans le layout Dash"""
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

@app.route('/viewer')
@login_required
def viewer():
    """Interface viewer"""
    return dash_app5.index()

@app.route('/admin')
@login_required
@admin_required
def admin():
    """Panneau d'administration"""
    return dash_app4.index()

# ============================================
# API ROUTES (inchangées)
# ============================================

@app.route('/api/properties')
@login_required
def api_properties():
    """API pour récupérer les propriétés"""
    try:
        source = request.args.get('source', 'all')
        city = request.args.get('city')
        property_type = request.args.get('type')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        
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
        
        return jsonify({'success': True, 'count': len(properties), 'properties': properties})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats')
@login_required
def api_stats():
    """API pour récupérer les statistiques"""
    try:
        coinafrique_count = CoinAfrique.query.count()
        expat_count = ExpatDakarProperty.query.count()
        loger_count = LogerDakarProperty.query.count()
        total_properties = coinafrique_count + expat_count + loger_count
        
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
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/search')
@login_required
def api_search():
    """API de recherche full-text"""
    try:
        query = request.args.get('q', '')
        
        if not query:
            return jsonify({'success': False, 'error': 'Paramètre de recherche manquant'}), 400
        
        results = []
        
        for model, source_name in [
            (CoinAfrique, 'coinafrique'),
            (ExpatDakarProperty, 'expatdakar'),
            (LogerDakarProperty, 'logerdakar')
        ]:
            title_results = model.query.filter(model.title.ilike(f'%{query}%')).all()
            desc_results = model.query.filter(model.description.ilike(f'%{query}%')).all() if hasattr(model, 'description') else []
            city_results = model.query.filter(model.city.ilike(f'%{query}%')).all()
            
            all_results = list(set(title_results + desc_results + city_results))
            
            for result in all_results:
                result_data = result.to_dict()
                result_data['source'] = source_name
                results.append(result_data)
        
        return jsonify({'success': True, 'count': len(results), 'query': query, 'results': results})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Endpoint de vérification de santé"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected' if db.session.execute('SELECT 1').scalar() else 'disconnected'
    })

# ============================================
# INITIALISATION
# ============================================

def create_tables():
    """Créer les tables métier et utilisateurs par défaut"""
    try:
        tables_to_create = [(User, 'users')]
        
        for model, name in tables_to_create:
            try:
                model.__table__.create(db.engine, checkfirst=True)
                print(f"Table '{name}' vérifiée/créée")
            except Exception as e:
                print(f"Erreur table '{name}': {e}")
        
        # Création des utilisateurs par défaut
        default_users = [
            {
                'username': 'admin',
                'email': 'admin@immobilier.sn',
                'password': 'admin123',
                'first_name': 'Administrateur',
                'last_name': 'Système',
                'role': 'admin'
            },
            {
                'username': 'analyst',
                'email': 'analyst@immobilier.sn',
                'password': 'analyst123',
                'first_name': 'Analyste',
                'last_name': 'Données',
                'role': 'analyst'
            },
            {
                'username': 'viewer',
                'email': 'viewer@immobilier.sn',
                'password': 'viewer123',
                'first_name': 'Visiteur',
                'last_name': 'Plateforme',
                'role': 'viewer'
            }
        ]
        
        for user_data in default_users:
            if not User.query.filter_by(username=user_data['username']).first():
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password_hash=hash_password(user_data['password']),
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=user_data['role'],
                    is_active=True
                )
                db.session.add(user)
                db.session.commit()
                print(f"Utilisateur '{user_data['username']}' créé ({user_data['role']})")
        
    except Exception as e:
        print(f"Erreur initialisation: {e}")

# Initialisation avec contexte
with app.app_context():
    create_tables()

# Exposition pour Gunicorn
server = app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 8050)))