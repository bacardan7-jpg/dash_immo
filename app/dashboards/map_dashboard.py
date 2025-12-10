import dash
from dash import html, dcc, Input, Output, callback, State
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
from sqlalchemy.exc import SQLAlchemyError, OperationalError

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gestion des imports avec fallback
try:
    from ..database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
except ImportError:
    logger.warning("Import relatif échoué, tentative d'import absolu")
    try:
        from database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
    except ImportError as e:
        logger.error(f"Impossible d'importer les modèles : {e}")
        # Création de classes factices pour le développement
        class DummyDB:
            def session(self):
                pass
        db = DummyDB()
        class CoinAfrique: pass
        class ExpatDakarProperty: pass
        class LogerDakarProperty: pass

class PremiumMapDashboard:
    """Dashboard cartographique premium avec clusters et heatmap"""
    
    def __init__(self, server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[
                dbc.themes.BOOTSTRAP,
                "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
                # Styles CSS de secours en cas de problème avec les fichiers statiques
                "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
            ],
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix,
            suppress_callback_exceptions=True
        )
        
        # Ajout des styles CSS inline de secours
        self._add_fallback_styles()
        
        if server:
            try:
                with server.app_context():
                    self.setup_layout()
                    self.setup_callbacks()
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation avec contexte serveur: {e}")
                self.setup_layout()
                self.setup_callbacks()
        else:
            self._layout_setup_deferred = True
    
    def _add_fallback_styles(self):
        """Ajout de styles CSS de secours si les fichiers statiques ne sont pas disponibles"""
        self.app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>{%title%}</title>
                {%favicon%}
                {%css%}
                <style>
                    /* Styles de secours */
                    .dashboard-root {
                        font-family: 'Inter', sans-serif;
                        background: #0f172a;
                        color: #e2e8f0;
                        min-height: 100vh;
                    }
                    .glass-nav {
                        backdrop-filter: blur(10px);
                        background: rgba(15, 23, 42, 0.8);
                        padding: 1rem;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    }
                    .hero-section {
                        padding: 3rem 1rem;
                        text-align: center;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }
                    .map-container {
                        background: rgba(30, 41, 59, 0.5);
                        border-radius: 12px;
                        padding: 1rem;
                        margin: 1rem 0;
                        border: 1px solid rgba(148, 163, 184, 0.2);
                    }
                    .controls-section {
                        padding: 2rem 1rem;
                        background: rgba(15, 23, 42, 0.5);
                    }
                    .stats-section {
                        padding: 2rem 1rem;
                        background: rgba(15, 23, 42, 0.3);
                    }
                    .error-message {
                        background: rgba(220, 38, 38, 0.2);
                        border: 1px solid #dc2626;
                        color: #fecaca;
                        padding: 1rem;
                        border-radius: 8px;
                        margin: 1rem 0;
                    }
                    .loading-message {
                        background: rgba(59, 130, 246, 0.2);
                        border: 1px solid #3b82f6;
                        color: #bfdbfe;
                        padding: 1rem;
                        border-radius: 8px;
                        margin: 1rem 0;
                        text-align: center;
                    }
                    .empty-data-message {
                        background: rgba(245, 158, 11, 0.2);
                        border: 1px solid #f59e0b;
                        color: #fde68a;
                        padding: 2rem;
                        border-radius: 8px;
                        text-align: center;
                        margin: 2rem 0;
                    }
                    .control-group {
                        margin-bottom: 1rem;
                    }
                    .control-label {
                        display: block;
                        margin-bottom: 0.5rem;
                        font-weight: 500;
                    }
                    .modern-dropdown, .modern-checklist {
                        width: 100%;
                    }
                    .city-analysis {
                        background: rgba(30, 41, 59, 0.7);
                        padding: 1.5rem;
                        border-radius: 12px;
                        border: 1px solid rgba(148, 163, 184, 0.2);
                    }
                    .stat-item {
                        display: flex;
                        justify-content: space-between;
                        padding: 0.5rem 0;
                        border-bottom: 1px solid rgba(148, 163, 184, 0.1);
                    }
                </style>
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
        '''
    
    def safe_db_query(self, query_func):
        """Exécute une requête DB en toute sécurité avec gestion des erreurs"""
        try:
            if not hasattr(db, 'session'):
                logger.error("Base de données non initialisée")
                return None, "Base de données non disponible"
            
            with db.session.begin_nested():
                result = query_func()
            return result, None
        except OperationalError as e:
            logger.error(f"Erreur de connexion DB: {e}")
            return None, "Impossible de se connecter à la base de données"
        except SQLAlchemyError as e:
            logger.error(f"Erreur SQL: {e}")
            return None, f"Erreur de requête: {str(e)}"
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
            return None, f"Erreur système: {str(e)}"
    
    def get_enhanced_map_data(self):
        """Données enrichies avec scores et tendances - version robuste"""
        try:
            # Vérification préalable de la connexion DB
            if not hasattr(db, 'session') or db.session is None:
                logger.error("Session DB non disponible")
                return []
            
            map_data = []
            city_scores = {}
            
            # Scores par ville avec gestion d'erreurs
            try:
                city_stats_query = db.session.query(
                    LogerDakarProperty.city,
                    db.func.count(LogerDakarProperty.id),
                    db.func.avg(LogerDakarProperty.price),
                    db.func.stddev(LogerDakarProperty.price)
                ).filter(
                    LogerDakarProperty.city.isnot(None),
                    LogerDakarProperty.price > 1000,
                ).group_by(LogerDakarProperty.city)
                
                city_stats, error = self.safe_db_query(lambda: city_stats_query.all())
                if error:
                    logger.warning(f"Erreur lors de la récupération des stats villes: {error}")
                    city_stats = []
                
                logger.info(f"Stats villes récupérées : {len(city_stats)} villes")
                
                for city, count, avg, std in city_stats:
                    try:
                        score = min(100, (count / 50) * 20 + (avg / 1000000) * 30)
                        city_scores[city] = {
                            'score': score,
                            'count': count,
                            'avg_price': float(avg) if avg else 0,
                            'volatility': float(std) if std else 0
                        }
                    except Exception as e:
                        logger.warning(f"Erreur calcul score pour {city}: {e}")
                        city_scores[city] = {'score': 0, 'count': 0, 'avg_price': 0, 'volatility': 0}
                        
            except Exception as e:
                logger.error(f"Erreur lors du calcul des scores villes: {e}")
            
            # Coordonnées précises des villes
            city_coordinates = {
                "Dakar": {"lat": 14.6928, "lon": -17.4467, "region": "Cap-Vert"},
                "Pikine": {"lat": 14.7640, "lon": -17.3900, "region": "Cap-Vert"},
                "Guédiawaye": {"lat": 14.7739, "lon": -17.3367, "region": "Cap-Vert"},
                "Rufisque": {"lat": 14.7167, "lon": -17.2667, "region": "Cap-Vert"},
                "Thiès": {"lat": 14.7956, "lon": -16.9981, "region": "Thiès"},
                "Mbour": {"lat": 14.4167, "lon": -16.9667, "region": "Thiès"},
                "Saint-Louis": {"lat": 16.0179, "lon": -16.4896, "region": "Saint-Louis"},
                "Kaolack": {"lat": 14.1500, "lon": -16.0833, "region": "Kaolack"},
                "Ziguinchor": {"lat": 12.5833, "lon": -16.2667, "region": "Ziguinchor"},
                "Tambacounda": {"lat": 13.7667, "lon": -13.6833, "region": "Tambacounda"},
                "Kolda": {"lat": 12.8833, "lon": -14.9500, "region": "Kolda"},
                "Dagana": {"lat": 16.4833, "lon": -15.6000, "region": "Saint-Louis"},
                "Richard-Toll": {"lat": 16.4625, "lon": -15.7008, "region": "Saint-Louis"},
                "Louga": {"lat": 15.6181, "lon": -16.2244, "region": "Louga"},
                "Diourbel": {"lat": 14.6500, "lon": -16.2333, "region": "Diourbel"},
                "Bambey": {"lat": 14.6984, "lon": -16.2738, "region": "Diourbel"},
                "Fatick": {"lat": 14.3389, "lon": -16.4111, "region": "Fatick"},
                "Foundiougne": {"lat": 14.1333, "lon": -16.4667, "region": "Fatick"},
                "Kaffrine": {"lat": 14.1053, "lon": -15.5508, "region": "Kaffrine"},
                "Birkelane": {"lat": 14.2044, "lon": -15.5914, "region": "Kaffrine"},
                "Kédougou": {"lat": 12.5579, "lon": -12.1784, "region": "Kédougou"},
                "Sédhiou": {"lat": 12.7081, "lon": -15.5569, "region": "Sédhiou"},
                "Goudomp": {"lat": 12.5944, "lon": -15.7322, "region": "Sédhiou"},
                "Matam": {"lat": 15.6556, "lon": -13.2553, "region": "Matam"},
                "Ranérou": {"lat": 15.3000, "lon": -13.9500, "region": "Matam"},
            }
            
            # Collecter les propriétés avec enrichissement
            models_to_query = [
                (CoinAfrique, 'CoinAfrique'),
                (ExpatDakarProperty, 'ExpatDakar'),
                (LogerDakarProperty, 'LogerDakar')
            ]
            
            for model, source in models_to_query:
                try:
                    if not hasattr(model, 'query'):
                        logger.warning(f"Modèle {model} non initialisé")
                        continue
                    
                    properties, error = self.safe_db_query(lambda: db.session.query(model).all())
                    if error:
                        logger.warning(f"Erreur récupération {source}: {error}")
                        continue
                    
                    logger.info(f"{source}: {len(properties) if properties else 0} propriétés trouvées")
                    
                    if not properties:
                        continue
                    
                    for prop in properties:
                        try:
                            city = getattr(prop, 'city', None)
                            if city and city in city_coordinates:
                                coords = city_coordinates[city]
                                score = city_scores.get(city, {}).get('score', 0)
                                
                                # Vérification des coordonnées valides
                                if not (-90 <= coords['lat'] <= 90 and -180 <= coords['lon'] <= 180):
                                    logger.warning(f"Coordonnées invalides pour {city}: {coords}")
                                    continue
                                
                                map_data.append({
                                    'id': getattr(prop, 'id', str(prop)),
                                    'title': getattr(prop, 'title', '')[:50] if hasattr(prop, 'title') else 'N/A',
                                    'price': getattr(prop, 'price', 0) or 0,
                                    'city': city,
                                    'region': coords['region'],
                                    'property_type': getattr(prop, 'property_type', 'Autre') or 'Autre',
                                    'bedrooms': getattr(prop, 'bedrooms', 0) or 0,
                                    'surface_area': getattr(prop, 'surface_area', 0) or 0,
                                    'source': source,
                                    'lat': coords['lat'],
                                    'lon': coords['lon'],
                                    'score': float(score),
                                    'volatility': float(city_scores.get(city, {}).get('volatility', 0)),
                                    'color': '#ffd700' if score > 70 else '#ff6b6b' if score < 30 else '#667eea'
                                })
                        except Exception as e:
                            logger.warning(f"Erreur traitement propriété {prop}: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Erreur lors du traitement du modèle {source}: {e}")
                    continue
            
            logger.info(f"Données cartographiques finalisées : {len(map_data)} points")
            return map_data
            
        except Exception as e:
            logger.error(f"Erreur critique get_enhanced_map_data: {e}", exc_info=True)
            return []
    
    def create_heatmap(self, map_data):
        """Heatmap de densité des prix avec gestion d'erreurs"""
        try:
            if not map_data:
                logger.warning("Aucune donnée pour la heatmap")
                return self.create_empty_figure("Aucune donnée disponible pour la heatmap")
            
            df = pd.DataFrame(map_data)
            if df.empty:
                return self.create_empty_figure("Données insuffisantes")
            
            # Vérification des colonnes requises
            required_cols = ['lat', 'lon', 'price']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Colonnes manquantes dans DataFrame: {df.columns}")
                return self.create_empty_figure("Données corrompues")
            
            fig = px.density_mapbox(
                df, 
                lat='lat', 
                lon='lon', 
                z='price',
                radius=30,
                center=dict(lat=14.6928, lon=-17.4467),
                zoom=6,
                mapbox_style='open-street-map',
                color_continuous_scale='Viridis',
                title='Densité des prix par zone'
            )
            
            fig.update_layout(
                height=600,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', family='Inter'),
                title=dict(font=dict(size=18, color='white'), x=0.5),
                coloraxis_colorbar=dict(
                    title='Prix moyen',
                    titlefont=dict(color='white'),
                    tickfont=dict(color='white')
                )
            )
            
            return fig
        except Exception as e:
            logger.error(f"Erreur création heatmap: {e}", exc_info=True)
            return self.create_error_figure(f"Erreur heatmap: {str(e)}")
    
    def create_cluster_map(self, map_data):
        """Carte avec clusters - version robuste"""
        try:
            if not map_data:
                logger.warning("Aucune donnée pour la carte cluster")
                return self.create_empty_figure("Aucune donnée disponible pour la carte")
            
            df = pd.DataFrame(map_data)
            if df.empty:
                return self.create_empty_figure("Données insuffisantes")
            
            required_cols = ['lat', 'lon', 'source', 'price']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Colonnes manquantes: {df.columns}")
                return self.create_empty_figure("Données corrompues")
            
            fig = px.scatter_mapbox(
                df, 
                lat='lat', 
                lon='lon',
                color='source',
                size='price',
                hover_name='title',
                hover_data={
                    'price': True,
                    'city': True,
                    'property_type': True,
                    'score': True,
                    'volatility': True
                },
                color_discrete_map={
                    'CoinAfrique': '#667eea',
                    'ExpatDakar': '#764ba2',
                    'LogerDakar': '#ffd700'
                },
                size_max=25,
                zoom=6,
                center=dict(lat=14.6928, lon=-17.4467),
                title='Clusters de propriétés'
            )
            
            # Configuration cohérente de la carte
            fig.update_layout(
                height=600,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', family='Inter'),
                title=dict(font=dict(size=18, color='white'), x=0.5),
                mapbox=dict(
                    style="open-street-map",
                    zoom=6,
                    center=dict(lat=14.6928, lon=-17.4467)
                )
            )
            
            return fig
        except Exception as e:
            logger.error(f"Erreur création cluster map: {e}", exc_info=True)
            return self.create_error_figure(f"Erreur carte: {str(e)}")
    
    def create_empty_figure(self, message="Aucune donnée"):
        """Crée une figure vide avec message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="#94a3b8")
        )
        fig.update_layout(
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    def create_error_figure(self, error_message):
        """Crée une figure affichant un message d'erreur"""
        fig = go.Figure()
        fig.add_annotation(
            text=f"❌ Erreur: {error_message}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=14, color="#fecaca")
        )
        fig.update_layout(
            height=400,
            paper_bgcolor='rgba(220, 38, 38, 0.1)',
            plot_bgcolor='rgba(220, 38, 38, 0.1)'
        )
        return fig
    
    def generate_city_analysis(self, city):
        """Générer l'analyse détaillée d'une ville - VERSION CORRIGÉE (méthode de classe)"""
        try:
            if not city or not hasattr(db, 'session'):
                return html.Div([
                    html.H4("Sélectionnez une ville", className='insights-title'),
                    html.P("Cliquez sur un point de la carte pour voir les détails")
                ], className='city-analysis')
            
            # Requête sécurisée
            stats_query = db.session.query(
                db.func.count(LogerDakarProperty.id),
                db.func.avg(LogerDakarProperty.price),
                db.func.stddev(LogerDakarProperty.price),
                db.func.avg(LogerDakarProperty.surface_area)
            ).filter(LogerDakarProperty.city == city)
            
            stats, error = self.safe_db_query(lambda: stats_query.first())
            
            if error or not stats:
                return html.Div([
                    html.H4(f"Analyse: {city}", className='insights-title'),
                    html.P(f"Impossible de récupérer les données: {error or 'Aucune donnée'}")
                ], className='city-analysis')
            
            count, avg_price, volatility, avg_surface = stats
            avg_price = avg_price or 0
            volatility = volatility or 0
            avg_surface = avg_surface or 0
            
            # Calcul du prix au m²
            price_per_m2 = (avg_price / avg_surface) if avg_surface > 0 else 0
            
            return html.Div([
                html.H4(f'Analyse: {city}', className='insights-title'),
                html.Div([
                    html.Div([
                        html.Span('Propriétés:'),
                        html.Strong(f'{int(count) if count else 0:,}')
                    ], className='stat-item'),
                    html.Div([
                        html.Span('Prix moyen:'),
                        html.Strong(f'{avg_price:,.0f} FCFA' if avg_price > 0 else 'N/A')
                    ], className='stat-item'),
                    html.Div([
                        html.Span('Volatilité:'),
                        html.Strong(f'{volatility:,.0f} FCFA' if volatility > 0 else 'N/A')
                    ], className='stat-item'),
                    html.Div([
                        html.Span('Surface moyenne:'),
                        html.Strong(f'{avg_surface:,.0f} m²' if avg_surface > 0 else 'N/A')
                    ], className='stat-item'),
                    html.Div([
                        html.Span('Prix/m²:'),
                        html.Strong(f'{price_per_m2:,.0f} FCFA/m²' if price_per_m2 > 0 else 'N/A')
                    ], className='stat-item')
                ], className='city-stats')
            ], className='city-analysis')
            
        except Exception as e:
            logger.error(f"Erreur génération analyse ville {city}: {e}", exc_info=True)
            return html.Div([
                html.H4(f"Erreur analyse {city}", className='insights-title'),
                html.P(f"Détails: {str(e)}")
            ], className='city-analysis error')
    
    def setup_layout(self):
        """Layout premium pour la carte avec états de chargement"""
        try:
            # Message de chargement initial
            loading_message = html.Div([
                html.I(className="fas fa-spinner fa-spin", style={"marginRight": "8px"}),
                "Chargement des données cartographiques..."
            ], className="loading-message")
            
            self.app.layout = html.Div([
                html.Div(id='hidden-trigger', style={'display': 'none'}),
                
                # Message d'erreur global
                dcc.Store(id='error-store', data=None),
                
                # Navigation
                html.Nav([
                    html.Div([
                        html.Div([
                            html.A([
                                html.I(className='fas fa-map-marked-alt'),
                                html.Span(' Map Premium')
                            ], href='/', className='nav-brand'),
                        ], className='nav-wrapper')
                    ], className='container-fluid')
                ], className='glass-nav'),
                
                # Zone d'erreur affichée
                html.Div(id='global-error-display'),
                
                # Contenu principal
                html.Main([
                    html.Div([
                        # Hero
                        html.Section([
                            html.Div([
                                html.H1('Carte Interactive Premium', className='hero-title'),
                                html.P('Visualisation géospatiale intelligente', className='hero-subtitle'),
                                html.Div([
                                    html.Span(id='property-count', children='0 propriétés', className='glass-badge'),
                                    html.Button([
                                        html.I(className='fas fa-cog'),
                                        ' Filtres'
                                    ], id='filter-btn', className='glass-button')
                                ], className='hero-actions')
                            ], className='hero-content')
                        ], className='hero-section'),
                        
                        # Contrôles
                        html.Section([
                            html.Div([
                                html.Div([
                                    html.Div([
                                        html.Label('Coloration', className='control-label'),
                                        dcc.Dropdown(
                                            id='map-color-by',
                                            options=[
                                                {'label': 'Par Source', 'value': 'source'},
                                                {'label': 'Par Prix', 'value': 'price'},
                                                {'label': 'Par Score', 'value': 'score'},
                                                {'label': 'Par Volatilité', 'value': 'volatility'}
                                            ],
                                            value='source',
                                            className='modern-dropdown',
                                            clearable=False
                                        )
                                    ], className='control-group'),
                                    html.Div([
                                        html.Label('Type de vue', className='control-label'),
                                        dcc.Dropdown(
                                            id='map-type',
                                            options=[
                                                {'label': 'Clusters', 'value': 'cluster'},
                                                {'label': 'Heatmap', 'value': 'heatmap'},
                                                {'label': 'Points', 'value': 'points'}
                                            ],
                                            value='cluster',
                                            className='modern-dropdown',
                                            clearable=False
                                        )
                                    ], className='control-group'),
                                    html.Div([
                                        html.Label('Sources', className='control-label'),
                                        dcc.Checklist(
                                            id='map-sources',
                                            options=[
                                                {'label': ' CoinAfrique', 'value': 'CoinAfrique'},
                                                {'label': ' ExpatDakar', 'value': 'ExpatDakar'},
                                                {'label': ' LogerDakar', 'value': 'LogerDakar'}
                                            ],
                                            value=['CoinAfrique', 'ExpatDakar', 'LogerDakar'],
                                            className='modern-checklist'
                                        )
                                    ], className='control-group')
                                ], className='map-controls')
                            ], className='container')
                        ], className='controls-section'),
                        
                        # Map avec état de chargement
                        html.Section([
                            html.Div([
                                html.Div([
                                    dcc.Loading(
                                        id="loading-map",
                                        type="circle",
                                        color="#667eea",
                                        children=[
                                            dcc.Graph(
                                                id='premium-map',
                                                figure=self.create_empty_figure("Chargement en cours..."),
                                                config={
                                                    'displayModeBar': True,
                                                    'displaylogo': False,
                                                    'modeBarButtonsToRemove': ['select2d', 'lasso2d']
                                                },
                                                className='map-figure'
                                            )
                                        ]
                                    )
                                ], className='map-container')
                            ], className='container')
                        ], className='map-section'),
                        
                        # Stats panel
                        html.Section([
                            html.Div([
                                html.Div([
                                    html.Div(id='city-insights'),
                                    html.Div(id='market-analysis')
                                ], className='stats-grid')
                            ], className='container')
                        ], className='stats-section')
                    ], className='main-wrapper')
                ], className='has-sidebar'),
                
                # Scripts GSAP (chargement asynchrone)
            ], className='dashboard-root')
            
        except Exception as e:
            logger.error(f"Erreur setup_layout: {e}", exc_info=True)
            # Layout minimal de secours
            self.app.layout = html.Div([
                html.H1("Erreur d'initialisation", style={'color': 'red'}),
                html.P(f"Détails: {str(e)}"),
                html.P("Vérifiez les logs et la configuration de la base de données.")
            ])
    
    def setup_callbacks(self):
        """Callbacks interactifs avec gestion d'erreurs"""
        
        @callback(
            Output('premium-map', 'figure'),
            Output('property-count', 'children'),
            Output('global-error-display', 'children'),
            Input('map-color-by', 'value'),
            Input('map-type', 'value'),
            Input('map-sources', 'value'),
            Input('hidden-trigger', 'n_intervals'),  # Déclencheur initial
            prevent_initial_call=False
        )
        def update_map(color_by, map_type, sources, n_intervals=None):
            """Callback principal de mise à jour de la carte"""
            try:
                logger.info(f"Mise à jour carte: color={color_by}, type={map_type}, sources={sources}")
                
                # Récupération des données
                all_data = self.get_enhanced_map_data()
                
                if not all_data:
                    logger.warning("Aucune donnée récupérée")
                    empty_fig = self.create_empty_figure(
                        "📊 Aucune donnée à afficher\n\n"
                        "Vérifiez que:\n"
                        "- La base de données est connectée\n"
                        "- Des propriétés existent dans la base\n"
                        "- Les villes ont des coordonnées définies"
                    )
                    return empty_fig, "0 propriétés", self._create_error_alert(
                        "Aucune donnée disponible. Vérifiez la connexion à la base de données."
                    )
                
                # Filtrage par source
                filtered_data = [d for d in all_data if d.get('source') in sources]
                
                if not filtered_data:
                    logger.warning("Aucune donnée après filtrage")
                    empty_fig = self.create_empty_figure(
                        "📝 Aucune propriété ne correspond aux filtres sélectionnés"
                    )
                    return empty_fig, "0 propriétés", self._create_error_alert(
                        "Ajustez les filtres (Sources) pour voir des données."
                    )
                
                # Sélection du type de visualisation
                if map_type == 'heatmap':
                    figure = self.create_heatmap(filtered_data)
                else:  # cluster et points utilisent la même base
                    figure = self.create_cluster_map(filtered_data)
                
                # Mise à jour du compteur
                count_message = f"📍 {len(filtered_data)} propriété{'s' if len(filtered_data) > 1 else ''}"
                
                # Pas d'erreur
                return figure, count_message, None
                
            except Exception as e:
                logger.error(f"Erreur callback update_map: {e}", exc_info=True)
                error_fig = self.create_error_figure(f"Erreur de chargement: {str(e)}")
                return error_fig, "Erreur", self._create_error_alert(
                    f"Erreur lors du chargement des données: {str(e)}"
                )
        
        @callback(
            Output('city-insights', 'children'),
            Input('premium-map', 'clickData'),
            prevent_initial_call=True
        )
        def show_city_insights(click_data):
            """Affiche les insights d'une ville au clic"""
            try:
                if not click_data:
                    return html.Div([
                        html.H4('💡 Cliquez sur une propriété', className='insights-title'),
                        html.P('Sélectionnez un point sur la carte pour voir les détails de la ville')
                    ], className='city-analysis placeholder')
                
                # Extraction de la ville depuis les données cliquées
                points = click_data.get('points', [])
                if not points:
                    return self.generate_city_analysis(None)
                
                point_data = points[0]
                customdata = point_data.get('customdata', {})
                
                if isinstance(customdata, dict):
                    city = customdata.get('city')
                else:
                    # Fallback si customdata n'est pas un dict
                    city = point_data.get('location') or point_data.get('city')
                
                if not city:
                    logger.warning("Ville non trouvée dans clickData")
                    return self.generate_city_analysis(None)
                
                return self.generate_city_analysis(city)
                
            except Exception as e:
                logger.error(f"Erreur callback city_insights: {e}", exc_info=True)
                return html.Div([
                    html.H4('❌ Erreur', className='insights-title'),
                    html.P(f"Impossible d'afficher les détails: {str(e)}")
                ], className='city-analysis error')
        
        # Callback pour masquer l'erreur après un certain temps
        @callback(
            Output('global-error-display', 'style'),
            Input('global-error-display', 'children'),
            prevent_initial_call=True
        )
        def hide_error_after_timeout(error_children):
            """Masque le message d'erreur après 5 secondes"""
            if error_children:
                import time
                time.sleep(5)
                return {'display': 'none'}
            return {}
    
    def _create_error_alert(self, message):
        """Crée un composant alerte d'erreur"""
        if not message:
            return None
        return dbc.Alert(
            message,
            color="danger",
            dismissable=True,
            className="error-message",
            style={'margin': '1rem', 'position': 'fixed', 'top': '10px', 'right': '10px', 'zIndex': 9999}
        )

# Factory function
def create_premium_map_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    """Factory function avec gestion d'erreurs"""
    try:
        dashboard = PremiumMapDashboard(
            server=server,
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix
        )
        logger.info("Dashboard PremiumMap créé avec succès")
        return dashboard.app
    except Exception as e:
        logger.error(f"Erreur création dashboard: {e}", exc_info=True)
        raise