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
from ..database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty, ProprietesConsolidees

class PremiumMapDashboard:
    """Dashboard cartographique premium avec clusters et heatmap"""
    
    def __init__(self, server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix
        )
        
        if server:
            with server.app_context():
                self.setup_layout()
                self.setup_callbacks()
        else:
            self._layout_setup_deferred = True
    
    def get_enhanced_map_data(self):
        """Données enrichies avec scores et tendances"""
        try:
            map_data = []
            city_scores = {}
            
            # Scores par ville
            city_stats = db.session.query(
                ProprietesConsolidees.city,
                db.func.count(ProprietesConsolidees.id),
                db.func.avg(ProprietesConsolidees.price),
                db.func.stddev(ProprietesConsolidees.price)
            ).filter(
                ProprietesConsolidees.city.isnot(None),
                ProprietesConsolidees.price > 1000,
            ).group_by(ProprietesConsolidees.city).all()
            
            for city, count, avg, std in city_stats:
                score = min(100, (count / 50) * 20 + (avg / 1000000) * 30)
                city_scores[city] = {
                    'score': score,
                    'count': count,
                    'avg_price': avg or 0,
                    'volatility': std or 0
                }
            
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
            for model, source in [(CoinAfrique, 'CoinAfrique'), 
                                 (ExpatDakarProperty, 'ExpatDakar'), 
                                 (LogerDakarProperty, 'LogerDakar')]:
                properties = db.session.query(model).all()
                
                for prop in properties:
                    city = getattr(prop, 'city', None)
                    if city and city in city_coordinates:
                        coords = city_coordinates[city]
                        score = city_scores.get(city, {}).get('score', 0)
                        
                        map_data.append({
                            'id': getattr(prop, 'id', None),
                            'title': getattr(prop, 'title', '')[:50],
                            'price': getattr(prop, 'price', 0),
                            'city': city,
                            'region': coords['region'],
                            'property_type': getattr(prop, 'property_type', 'Autre'),
                            'bedrooms': getattr(prop, 'bedrooms', 0),
                            'surface_area': getattr(prop, 'surface_area', 0),
                            'source': source,
                            'lat': coords['lat'],
                            'lon': coords['lon'],
                            'score': score,
                            'volatility': city_scores.get(city, {}).get('volatility', 0),
                            'color': '#ffd700' if score > 70 else '#ff6b6b' if score < 30 else '#667eea'
                        })
            
            return map_data
        except Exception as e:
            print(f"Erreur données carte: {e}")
            return []
    
    def create_heatmap(self, map_data):
        """Heatmap de densité des prix"""
        try:
            df = pd.DataFrame(map_data)
            if df.empty:
                return go.Figure()
            
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
            print(f"Erreur heatmap: {e}")
            return go.Figure()
    
    def create_cluster_map(self, map_data):
        """Carte avec clusters"""
        try:
            df = pd.DataFrame(map_data)
            if df.empty:
                return go.Figure()
            
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
                mapbox_style='carto-darkmatter',
                title='Clusters de propriétés'
            )
            
            fig.update_layout(
                height=600,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', family='Inter'),
                title=dict(font=dict(size=18, color='white'), x=0.5),
                mapbox=dict(
                    style="open-street-map",
                    zoom=5
                )
            )

            
            return fig
        except Exception as e:
            print(f"Erreur cluster map: {e}")
            return go.Figure()
    
    def setup_layout(self):
        """Layout premium pour la carte"""
        map_data = self.get_enhanced_map_data()
        
        self.app.layout = html.Div([
            # Background animé
            html.Div(className='animated-bg'),
            
            # Navigation
            html.Nav([
                html.Div([
                    html.Div([
                        html.A([
                            html.I(className='fas fa-map-marked-alt'),
                            html.Span('Map Premium')
                        ], href='/', className='nav-brand'),
                        html.Button([
                            html.Span(className='hamburger')
                        ], className='nav-toggle', **{'aria-label': 'Menu'})
                    ], className='nav-wrapper'),
                    html.Div([
                        html.Ul([
                            html.Li(html.A('Dashboard', href='/dashboard', className='nav-link')),
                            html.Li(html.A('Carte', href='/map', className='nav-link active')),
                            html.Li(html.A('Analyse', href='/analytics', className='nav-link')),
                            html.Li(html.A('Admin', href='/admin', className='nav-link'))
                        ], className='nav-links')
                    ], className='nav-collapse')
                ], className='container-fluid')
            ], className='glass-nav'),
            
            # Main content
            html.Main([
                html.Div([
                    # Hero
                    html.Section([
                        html.Div([
                            html.H1('Carte Interactive Premium', className='hero-title'),
                            html.P('Visualisation géospatiale intelligente', className='hero-subtitle'),
                            html.Div([
                                html.Span(f'{len(map_data)} propriétés', className='glass-badge'),
                                html.Button([
                                    html.I(className='fas fa-cog'),
                                    ' Filtres'
                                ], id='filter-btn', className='glass-button')
                            ], className='hero-actions')
                        ], className='hero-content')
                    ], className='hero-section'),
                    
                    # Controls
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
                                        className='modern-dropdown'
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
                                        className='modern-dropdown'
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
                    
                    # Map
                    html.Section([
                        html.Div([
                            html.Div([
                                dcc.Graph(
                                    id='premium-map',
                                    figure=self.create_cluster_map(map_data),
                                    config={
                                        'displayModeBar': True,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['select2d', 'lasso2d']
                                    },
                                    className='map-figure'
                                )
                            ], className='map-container')
                        ], className='container')
                    ], className='map-section'),
                    
                    # Stats panel
                    html.Section([
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.Div(id='city-insights'),
                                    html.Div(id='market-analysis')
                                ], className='stats-grid')
                            ], className='container')
                        ], className='stats-section')
                    ], className='container')
                ], className='main-wrapper')
            ], className='has-sidebar'),
            
            # Scripts
            html.Script(src='https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js'),
            html.Script(src='https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js'),
            html.Script(src='/static/js/map-animations.js')
        ], className='dashboard-root')
    
    def setup_callbacks(self):
        """Callbacks interactifs"""
        @callback(
            Output('premium-map', 'figure'),
            Input('map-color-by', 'value'),
            Input('map-type', 'value'),
            Input('map-sources', 'value'),
            prevent_initial_call=True
        )
        def update_map(color_by, map_type, sources):
            filtered_data = [d for d in self.get_enhanced_map_data() if d['source'] in sources]
            
            if map_type == 'heatmap':
                return self.create_heatmap(filtered_data)
            elif map_type == 'cluster':
                return self.create_cluster_map(filtered_data)
            else:
                # Points simples
                return self.create_cluster_map(filtered_data)
        
        @callback(
            Output('city-insights', 'children'),
            Input('premium-map', 'clickData')
        )
        def show_city_insights(click_data):
            if not click_data:
                return html.Div([
                    html.H4('Cliquez sur une ville', className='insights-title'),
                    html.P('Sélectionnez une zone pour voir les insights détaillés')
                ], className='insights-placeholder')
            
            # Analyse détaillée de la ville
            city = click_data['points'][0].get('customdata', {}).get('city', 'Dakar')
            return self.generate_city_analysis(city)
        
        def generate_city_analysis(self, city):
            """Générer l'analyse détaillée d'une ville"""
            stats = db.session.query(
                db.func.count(ProprietesConsolidees.id),
                db.func.avg(ProprietesConsolidees.price),
                db.func.stddev(ProprietesConsolidees.price),
                db.func.avg(ProprietesConsolidees.surface_area)
            ).filter(ProprietesConsolidees.city == city).first()
            
            return html.Div([
                html.H4(f'Analyse {city}', className='city-title'),
                html.Div([
                    html.Div([
                        html.Span('Propriétés:'),
                        html.Strong(f'{stats[0] or 0}')
                    ], className='stat-item'),
                    html.Div([
                        html.Span('Prix moyen:'),
                        html.Strong(f'{stats[1] or 0:,.0f} FCFA')
                    ], className='stat-item'),
                    html.Div([
                        html.Span('Volatilité:'),
                        html.Strong(f'{stats[2] or 0:,.0f}')
                    ], className='stat-item'),
                    html.Div([
                        html.Span('Prix/m²:'),
                        html.Strong(f'{(stats[1] or 0) / (stats[3] or 1):,.0f}')
                    ], className='stat-item')
                ], className='city-stats')
            ], className='city-analysis')

# Factory function
def create_premium_map_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    dashboard = PremiumMapDashboard(
        server=server,
        routes_pathname_prefix=routes_pathname_prefix,
        requests_pathname_prefix=requests_pathname_prefix
    )
    return dashboard.app

# Backwards-compatible alias: existing code expects `MapDashboard` class
MapDashboard = PremiumMapDashboard