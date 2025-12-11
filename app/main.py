# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user, logout_user
from flask_caching import Cache
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from sqlalchemy.pool import NullPool
from sqlalchemy import or_
import redis
import os
from datetime import datetime

# Importer les modèles et composants
from .database.models import db, User, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
from .auth.auth import auth_bp, login_manager, hash_password
from .auth.decorators import admin_required, analyst_required

# Configuration Flask
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Configuration de la base de données (Neon)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'votre-secret-key-tres-securise')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://neondb_owner:npg_9vrYBWUeT7js@ep-raspy-dust-a4a9f62f-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': NullPool,
    'connect_args': {'connect_timeout': 10, 'sslmode': 'require'}
}
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-tres-securise')

# Initialiser les extensions
CORS(app)
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
jwt = JWTManager(app)

# Configuration Redis/cache
try:
    redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    cache = Cache(app, config={
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': 'redis://redis:6379/0'
    })
except Exception:
    cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Enregistrer les blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')

# Importer et créer les dashboards Dash
from .dashboards.modern_main_dashboard import create_observatoire_dashboard
from .dashboards.analytics_dashboard import create_ultra_dashboard
from .dashboards.map_dashboard import PremiumMapDashboard
from .dashboards.viewer_dashboard import create_viewer_dashboard
from .components.admin_panel import AdminPanel

# Initialiser les applications Dash
dash_app1 = create_observatoire_dashboard(
    server=app,
    routes_pathname_prefix="/dashboard/",
    requests_pathname_prefix="/dashboard/"
)
dash_app2 = create_ultra_dashboard(
    server=app,
    routes_pathname_prefix="/analytics/",
    requests_pathname_prefix="/analytics/"
)
map_dashboard = PremiumMapDashboard(
    server=app,
    routes_pathname_prefix="/map/",
    requests_pathname_prefix="/map/"
)
dash_app3 = map_dashboard.app
dash_app5 = create_viewer_dashboard(
    server=app,
    routes_pathname_prefix="/viewer/",
    requests_pathname_prefix="/viewer/"
)
admin_panel = AdminPanel(
    server=app,
    routes_pathname_prefix="/admin/",
    requests_pathname_prefix="/admin/"
)
dash_app4 = admin_panel.app

# Configurer les exceptions des callbacks
for dash_app in [dash_app1, dash_app2, dash_app3, dash_app4, dash_app5]:
    if dash_app:
        dash_app.css.append_css({
            'external_url': '/static/css/sidebar.css'
        })
        dash_app.config.suppress_callback_exceptions = True



# =============================================================================
# CONTEXT PROCESSORS - Variables globales pour les templates
# =============================================================================

@app.context_processor
def inject_navigation():
    """Injecte les URLs de navigation dans tous les templates"""
    return {
        'home_url': url_for('index'),
        'logout_url': url_for('logout') if current_user.is_authenticated else None
    }


@app.context_processor
def inject_user_capabilities():
    """Injecte les capacités utilisateur dans tous les templates"""
    
    class UserCapabilities:
        def __init__(self, user):
            self.user = user
            
        @property
        def can_view_dashboard(self):
            """Peut voir les dashboards principaux"""
            if not self.user or not self.user.is_authenticated:
                return False
            return self.user.role in ['analyst', 'admin']
            
        @property
        def can_manage_users(self):
            """Peut gérer les utilisateurs (admin)"""
            if not self.user or not self.user.is_authenticated:
                return False
            return self.user.role == 'admin'
            
        @property
        def can_view_analytics(self):
            """Peut voir l'analytics avancé"""
            if not self.user or not self.user.is_authenticated:
                return False
            return self.user.role in ['analyst', 'admin']
            
        @property
        def can_view_map(self):
            """Peut voir la carte interactive"""
            if not self.user or not self.user.is_authenticated:
                return False
            return self.user.role in ['analyst', 'admin']
            
        @property
        def can_view_viewer(self):
            """Peut voir l'interface viewer"""
            if not self.user or not self.user.is_authenticated:
                return False
            return True  # Tous les utilisateurs connectés peuvent accéder au viewer
            
        @property
        def can_export_data(self):
            """Peut exporter les données"""
            if not self.user or not self.user.is_authenticated:
                return False
            return self.user.role in ['analyst', 'admin']
    
    return {
        'user_capabilities': UserCapabilities(current_user),
        'current_user': current_user
    }


# =============================================================================
# ROUTES PRINCIPALES - Navigation vers l'accueil
# =============================================================================

@app.route('/')
@app.route('/accueil')
def index():
    """
    PAGE D'ACCUEIL UNIQUE - accessible à tous les utilisateurs
    """
    return render_template('index.html', user=current_user if current_user.is_authenticated else None)


@app.route('/mon-espace')
@login_required
def mon_espace():
    """
    Redirection intelligente vers l'espace utilisateur selon le rôle
    """
    try:
        if current_user.role == 'viewer':
            return redirect(url_for('viewer'))
        elif current_user.role in ['analyst', 'admin']:
            return redirect(url_for('dashboard'))
        else:
            flash("Rôle non reconnu.", "error")
            return redirect(url_for('index'))
    except Exception as e:
        flash(f"Erreur de redirection : {str(e)}", "error")
        return redirect(url_for('index'))


@app.route('/logout')
@login_required
def logout():
    """
    Déconnexion utilisateur et retour à l'accueil
    """
    try:
        logout_user()
        session.clear()
        flash("Déconnexion réussie. À bientôt !", "success")
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Erreur lors de la déconnexion : {str(e)}", "error")
        return redirect(url_for('index'))


# =============================================================================
# ROUTES DES DASHBOARDS
# =============================================================================

@app.route('/dashboard')
@login_required
@analyst_required
def dashboard():
    """Dashboard principal - réservé aux analystes et admin"""
    return dash_app1.index()


@app.route('/analytics')
@login_required
@analyst_required
def analytics():
    """Dashboard d'analyse avancée - réservé aux analystes et admin"""
    return dash_app2.index()


@app.route('/map')
@login_required
@analyst_required
def map_view():
    """Vue cartographique - réservée aux analystes et admin"""
    return dash_app3.index()


@app.route('/viewer')
@login_required
def viewer():
    """Interface viewer - accessible à tous les utilisateurs connectés"""
    return dash_app5.index()


@app.route('/admin')
@login_required
@admin_required
def admin():
    """Panneau d'administration - réservé aux admin"""
    return dash_app4.index()


# =============================================================================
# GESTION DES ERREURS
# =============================================================================

@app.errorhandler(403)
def forbidden(error):
    """Gestion des accès interdits avec redirection intelligente"""
    if current_user.is_authenticated:
        if current_user.role == 'viewer':
            flash("Accès réservé aux analystes et administrateurs.", "warning")
            return redirect(url_for('viewer'))
    
    flash("Permissions insuffisantes pour accéder à cette ressource.", "error")
    return redirect(url_for('index'))


@app.errorhandler(404)
def not_found(error):
    """Gestion des pages non trouvées"""
    flash("La page demandée n'existe pas.", "info")
    return redirect(url_for('index'))


@app.errorhandler(500)
def internal_error(error):
    """Gestion des erreurs serveur"""
    db.session.rollback()
    flash("Une erreur interne est survenue. Veuillez réessayer.", "error")
    return redirect(url_for('index'))


# =============================================================================
# APIS - Données et statistiques
# =============================================================================

@app.route('/api/properties')
@login_required
def api_properties():
    """API pour récupérer les propriétés filtrées"""
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
            if min_price is not None:
                query = query.filter(model.price >= min_price)
            if max_price is not None:
                query = query.filter(model.price <= max_price)
            
            results = query.all()
            
            for result in results:
                prop_data = result.to_dict() if hasattr(result, 'to_dict') else {}
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
    """API pour récupérer les statistiques globales"""
    try:
        coinafrique_count = CoinAfrique.query.count() if hasattr(CoinAfrique, 'query') else 0
        expat_count = ExpatDakarProperty.query.count() if hasattr(ExpatDakarProperty, 'query') else 0
        loger_count = LogerDakarProperty.query.count() if hasattr(LogerDakarProperty, 'query') else 0
        total_properties = coinafrique_count + expat_count + loger_count
        
        all_prices = []
        for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
            if hasattr(model, 'query'):
                prices = db.session.query(model.price).filter(model.price > 0).all()
                all_prices.extend([p[0] for p in prices if p[0]])
        
        avg_price = sum(all_prices) / len(all_prices) if all_prices else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_properties': total_properties,
                'coinafrique_count': coinafrique_count,
                'expat_count': expat_count,
                'loger_count': loger_count,
                'average_price': round(avg_price, 2)
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
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Paramètre de recherche manquant'
            }), 400
        
        results = []
        
        for model, source_name in [
            (CoinAfrique, 'coinafrique'),
            (ExpatDakarProperty, 'expatdakar'),
            (LogerDakarProperty, 'logerdakar')
        ]:
            if not hasattr(model, 'query'):
                continue
                
            # Recherche dans les champs texte
            search_filters = []
            
            if hasattr(model, 'title'):
                search_filters.append(model.title.ilike(f'%{query}%'))
            
            if hasattr(model, 'description'):
                search_filters.append(model.description.ilike(f'%{query}%'))
            
            if hasattr(model, 'city'):
                search_filters.append(model.city.ilike(f'%{query}%'))
            
            if hasattr(model, 'district'):
                search_filters.append(model.district.ilike(f'%{query}%'))
            
            # Combiner les filtres avec OR
            all_results = model.query.filter(or_(*search_filters)).limit(50).all()
            
            for result in all_results:
                result_data = result.to_dict() if hasattr(result, 'to_dict') else {}
                result_data['source'] = source_name
                results.append(result_data)
        
        # Dédoublonner les résultats
        unique_results = {r.get('id', f"{r.get('source')}_{i}"): r 
                         for i, r in enumerate(results)}
        
        return jsonify({
            'success': True,
            'count': len(unique_results),
            'query': query,
            'results': list(unique_results.values())
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health_check():
    """Endpoint de vérification de santé"""
    try:
        # Tester la connexion DB
        db.session.execute('SELECT 1').scalar()
        db_status = 'connected'
    except Exception:
        db_status = 'disconnected'
    
    return jsonify({
        'status': 'healthy' if db_status == 'connected' else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status
    }), 200 if db_status == 'connected' else 503


# =============================================================================
# INITIALISATION
# =============================================================================

def create_tables_and_default_users():
    """Créer la table users et les utilisateurs par défaut"""
    try:
        # Créer seulement la table users
        if not hasattr(User, '__table__'):
            print("⚠️  Table User non définie")
            return
            
        User.__table__.create(db.engine, checkfirst=True)
        print("✅ Table 'users' vérifiée/créée")
        
        # Créer les utilisateurs par défaut
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
        
        users_created = 0
        
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
                print(f"✅ Utilisateur '{user_data['username']}' créé ({user_data['role']})")
                users_created += 1
        
        if users_created == 0:
            print("ℹ️  Aucun nouvel utilisateur créé (existent déjà)")
            
    except Exception as e:
        print(f"❌ Erreur initialisation : {e}")
        db.session.rollback()


# Initialisation avec contexte d'application
with app.app_context():
    create_tables_and_default_users()


# =============================================================================
# EXPOSITION POUR GUNICORN
# =============================================================================

server = app

if __name__ == '__main__':
    # Mode développement
    print("🚀 Démarrage en mode développement...")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 8050)))