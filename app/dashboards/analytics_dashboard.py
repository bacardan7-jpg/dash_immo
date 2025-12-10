import dash
from dash import html, dcc, Input, Output, callback, State, dash_table, ctx
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..database.models import db, LogerDakarProperty,  User, DashboardConfig
from ..auth.decorators import analyst_required
import json
import io
import base64

class AnalyticsDashboard:
    """Dashboard d'analytics premium avec modèle de données enrichi"""

    def __init__(self, server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix,
            suppress_callback_exceptions=True
        )
        
        # Cache pour les données filtrées
        self._data_cache = {}
        
        if server:
            with server.app_context():
                self.setup_layout()
                self.setup_callbacks()
        else:
            self._layout_setup_deferred = True

    # =================================================================
    #                       OPTIONS & FILTRAGE
    # =================================================================
    def get_filter_options(self):
        """Récupérer les options de filtrage depuis LogerDakarProperty"""
        try:
            # Utilisation de la table consolidée pour meilleur performance
            query = db.session.query(
                LogerDakarProperty.city,
                LogerDakarProperty.property_type,
                LogerDakarProperty.source
            ).distinct()
            
            cities = sorted([r.city for r in query.filter(LogerDakarProperty.city.isnot(None)).all() if r.city])
            property_types = sorted([r.property_type for r in query.filter(LogerDakarProperty.property_type.isnot(None)).all() if r.property_type])
            sources = sorted([r.source for r in query.filter(LogerDakarProperty.source.isnot(None)).all() if r.source])
            
            return {
                "cities": cities,
                "property_types": property_types,
                "sources": sources
            }
        except Exception as e:
            print(f"Erreur options: {e}")
            return {"cities": [], "property_types": [], "sources": []}

    def get_filtered_data(self, filters=None, limit=1000):
        """Récupération optimisée avec caching"""
        cache_key = str(sorted(filters.items())) if filters else "all"
        
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]
        
        try:
            query = db.session.query(LogerDakarProperty)
            
            if filters:
                if filters.get('city') and filters['city'] != 'all':
                    query = query.filter(LogerDakarProperty.city == filters['city'])
                
                if filters.get('property_type') and filters['property_type'] != 'all':
                    query = query.filter(LogerDakarProperty.property_type == filters['property_type'])
                
                if filters.get('source') and filters['source'] != 'all':
                    query = query.filter(LogerDakarProperty.source == filters['source'])
                
                if filters.get('bedrooms') and filters['bedrooms'] != 'all':
                    query = query.filter(LogerDakarProperty.bedrooms == int(filters['bedrooms']))
                
                # Filtres numériques
                if filters.get('min_price'):
                    query = query.filter(LogerDakarProperty.price >= filters['min_price'])
                if filters.get('max_price'):
                    query = query.filter(LogerDakarProperty.price <= filters['max_price'])
                
                if filters.get('min_surface'):
                    query = query.filter(LogerDakarProperty.surface_area >= filters['min_surface'])
                if filters.get('max_surface'):
                    query = query.filter(LogerDakarProperty.surface_area <= filters['max_surface'])
                
                # Filtres avancés
                if filters.get('min_quality'):
                    query = query.filter(LogerDakarProperty.quality_score >= filters['min_quality'])
                
                if filters.get('sentiment') and filters['sentiment'] != 'all':
                    if filters['sentiment'] == 'positive':
                        query = query.filter(LogerDakarProperty.description_sentiment > 0.2)
                    elif filters['sentiment'] == 'negative':
                        query = query.filter(LogerDakarProperty.description_sentiment < -0.2)
                    else:
                        query = query.filter(LogerDakarProperty.description_sentiment.between(-0.2, 0.2))
            
            # Optimisation: ne charger que les colonnes nécessaires
            data = query.limit(limit).all()
            
            result = [{
                'id': str(r.id),
                'title': r.title,
                'price': float(r.price) if r.price else None,
                'price_per_m2': float(r.price_per_m2) if r.price_per_m2 else None,
                'city': r.city,
                'property_type': r.property_type,
                'bedrooms': r.bedrooms,
                'surface_area': r.surface_area,
                'source': r.source,
                'quality_score': r.quality_score,
                'description_sentiment': r.description_sentiment,
                'scraped_at': r.scraped_at.isoformat() if r.scraped_at else None,
                'view_count': r.view_count
            } for r in data]
            
            # Cacher pour 60 secondes
            self._data_cache[cache_key] = result
            import threading
            threading.Timer(60.0, lambda: self._data_cache.pop(cache_key, None)).start()
            
            return result
        except Exception as e:
            print(f"Erreur filtrage: {e}")
            return []

    # =================================================================
    #                     KPIs PREMIUM
    # =================================================================
    def calculate_advanced_kpis(self, data):
        """Calculer les KPIs avancés depuis les données filtrées"""
        if not data:
            return {
                'count': 0,
                'avg_price': 0,
                'median_price': 0,
                'avg_price_per_m2': 0,
                'quality_score': 0,
                'sentiment': 0,
                'opportunities': [],
                'anomalies': []
            }
        
        df = pd.DataFrame(data)
        
        # KPIs de base
        count = len(df)
        avg_price = df['price'].mean() if 'price' in df else 0
        median_price = df['price'].median() if 'price' in df else 0
        
        # KPIs avancés
        avg_price_per_m2 = df['price_per_m2'].mean() if 'price_per_m2' in df else 0
        quality_score = df['quality_score'].mean() if 'quality_score' in df else 0
        sentiment = df['description_sentiment'].mean() if 'description_sentiment' in df else 0
        
        # Détection d'opportunités (bon rapport qualité-prix)
        opportunities = []
        if not df.empty and 'price_per_m2' in df and 'quality_score' in df:
            df['opportunity_score'] = (df['quality_score'] / 100) / (df['price_per_m2'] / 1_000_000)
            top_ops = df.nlargest(3, 'opportunity_score')
            opportunities = top_ops[['title', 'price', 'quality_score', 'city']].to_dict('records')
        
        # Détection d'anomalies (prix suspects)
        anomalies = []
        if 'price' in df and not df.empty:
            Q1 = df['price'].quantile(0.25)
            Q3 = df['price'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            anomaly_df = df[(df['price'] < lower_bound) | (df['price'] > upper_bound)]
            anomalies = anomaly_df[['title', 'price', 'city']].head(3).to_dict('records')
        
        return {
            'count': count,
            'avg_price': avg_price,
            'median_price': median_price,
            'avg_price_per_m2': avg_price_per_m2,
            'quality_score': quality_score,
            'sentiment': sentiment,
            'opportunities': opportunities,
            'anomalies': anomalies
        }

    # =================================================================
    #                     GRAPHIQUES PREMIUM
    # =================================================================
    def create_radar_chart(self, data):
        """Radar chart comparant les villes sur plusieurs axes"""
        try:
            df = pd.DataFrame(data)
            if df.empty or 'city' not in df:
                return go.Figure()
            
            # Agréger par ville
            city_stats = df.groupby('city').agg({
                'price': ['mean', 'std'],
                'surface_area': 'mean',
                'quality_score': 'mean',
                'view_count': 'mean'
            }).round(2)
            
            city_stats.columns = ['prix_moyen', 'volatilite', 'surface_moyenne', 'qualite', 'popularite']
            
            # Normaliser pour le radar (0-100)
            for col in city_stats.columns:
                max_val = city_stats[col].max()
                if max_val > 0:
                    city_stats[col] = (city_stats[col] / max_val) * 100
            
            fig = go.Figure()
            
            for city in city_stats.head(5).index:
                values = city_stats.loc[city].tolist()
                values += [values[0]]  # Fermer le radar
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=['Prix Moyen', 'Volatilité', 'Surface', 'Qualité', 'Popularité', 'Prix Moyen'],
                    fill='toself',
                    name=city,
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100]),
                    bgcolor='rgba(255,255,255,0.05)'
                ),
                height=450,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', family='Inter'),
                title=dict(text='Comparaison Villes', x=0.5, font=dict(size=18, color='white'))
            )
            
            return fig
        except Exception as e:
            print(f"Erreur radar: {e}")
            return go.Figure()
    
    def create_parallel_coordinates(self, data):
        """Parallel coordinates pour analyse multi-critères"""
        try:
            df = pd.DataFrame(data)
            if df.empty:
                return go.Figure()
            
            # Sélectionner les colonnes pertinentes
            cols = ['price', 'surface_area', 'bedrooms', 'quality_score']
            df_filtered = df[cols].dropna()
            
            # Normaliser pour l'affichage
            for col in cols:
                if df_filtered[col].max() > 0:
                    df_filtered[col] = (df_filtered[col] - df_filtered[col].min()) / (df_filtered[col].max() - df_filtered[col].min())
            
            fig = px.parallel_coordinates(
                df_filtered.head(200),
                color='price',
                title="Analyse Multi-critères",
                color_continuous_scale='Viridis'
            )
            
            fig.update_layout(
                height=450,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                title=dict(x=0.5, font=dict(size=18, color='white'))
            )
            
            return fig
        except Exception as e:
            print(f"Erreur parallel coordinates: {e}")
            return go.Figure()
    
    def create_treemap_advanced(self, data):
        """Treemap avec coloration par score"""
        try:
            df = pd.DataFrame(data)
            if df.empty:
                return go.Figure()
            
            # Préparer la hiérarchie
            df['value'] = df['price'] * (df['quality_score'] / 100)
            
            fig = px.treemap(
                df.head(100),
                path=['source', 'city', 'property_type'],
                values='value',
                color='price_per_m2' if 'price_per_m2' in df else 'price',
                color_continuous_scale='RdYlBu_r',
                title="Valeur Marché par Segment"
            )
            
            fig.update_layout(
                height=500,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', size=12),
                title=dict(x=0.5, font=dict(size=18, color='white'))
            )
            
            return fig
        except Exception as e:
            print(f"Erreur treemap: {e}")
            return go.Figure()

    # =================================================================
    #                         TABLE AVANCÉE
    # =================================================================
    def create_enhanced_table(self, data):
        """Table avec tri, formatage et cellules enrichies"""
        if not data:
            return dash_table.DataTable(data=[], columns=[])
        
        columns = [
            {"name": "Titre", "id": "title", "type": "text"},
            {"name": "Prix", "id": "price", "type": "numeric", "format": {"specifier": ",.0f"}},
            {"name": "Prix/m²", "id": "price_per_m2", "type": "numeric", "format": {"specifier": ",.0f"}},
            {"name": "Ville", "id": "city", "type": "text"},
            {"name": "Type", "id": "property_type", "type": "text"},
            {"name": "Surface", "id": "surface_area", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Chambres", "id": "bedrooms", "type": "numeric"},
            {"name": "Source", "id": "source", "type": "text"},
            {"name": "Qualité", "id": "quality_score", "type": "numeric", "format": {"specifier": ".0f"}},
            {"name": "Score", "id": "opportunity_score", "type": "numeric", "format": {"specifier": ".2f"}},
        ]
        
        # Calculer le score d'opportunité
        df = pd.DataFrame(data)
        if not df.empty and 'price_per_m2' in df and 'quality_score' in df:
            df['opportunity_score'] = (df['quality_score'] / 100) / (df['price_per_m2'] / 1_000_000)
        
        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=columns,
            page_size=15,
            sort_action='native',
            filter_action='native',
            style_table={
                'overflowX': 'auto',
                'borderRadius': '12px',
                'overflow': 'hidden'
            },
            style_cell={
                'backgroundColor': 'rgba(255,255,255,0.05)',
                'color': 'white',
                'border': '1px solid rgba(255,255,255,0.1)',
                'textAlign': 'left',
                'padding': '12px',
                'fontFamily': 'Inter'
            },
            style_header={
                'backgroundColor': 'rgba(255,255,255,0.15)',
                'fontWeight': '600',
                'borderBottom': '2px solid rgba(255,215,0,0.3)'
            },
            style_data_conditional=[
                {
                    'if': {'column_id': 'quality_score', 'filter_query': '{quality_score} >= 80'},
                    'color': '#28a745',
                    'fontWeight': '600'
                },
                {
                    'if': {'column_id': 'quality_score', 'filter_query': '{quality_score} < 50'},
                    'color': '#dc3545'
                },
                {
                    'if': {'column_id': 'opportunity_score', 'filter_query': '{opportunity_score} >= 1.5'},
                    'backgroundColor': 'rgba(40, 167, 69, 0.2)',
                    'borderLeft': '4px solid #28a745'
                }
            ],
            tooltip_data=[
                {
                    column: {'value': f"Prix/m²: {row.get('price_per_m2', 'N/A')}\nQualité: {row.get('quality_score', 'N/A')}/100", 
                            'type': 'markdown'}
                    for column in ['title', 'price']
                } for row in data
            ],
            tooltip_delay=0,
            tooltip_duration=None
        )

    # =================================================================
    #                         LAYOUT PREMIUM
    # =================================================================
    def setup_layout(self):
        options = self.get_filter_options()
        
        self.app.layout = html.Div([
            # Animated background
            html.Div(className='animated-bg'),
            
            # Loading overlay
            html.Div([
                html.Div(className='spinner-glow'),
                html.P('Analyse en cours...', className='loading-text')
            ], id='loading-overlay', className='loading-overlay'),
            
            # Navigation
            html.Nav([
                html.Div([
                    html.Div([
                        html.A([
                            html.I(className='fas fa-search'),
                            html.Span('Analytics Premium')
                        ], href='/', className='nav-brand'),
                        html.Button([
                            html.Span(className='hamburger')
                        ], className='nav-toggle', **{'aria-label': 'Menu'})
                    ], className='nav-wrapper'),
                    html.Div([
                        html.Ul([
                            html.Li(html.A('Dashboard', href='/dashboard', className='nav-link')),
                            html.Li(html.A('Analytics', href='/analytics', className='nav-link active')),
                            html.Li(html.A('Carte', href='/map', className='nav-link')),
                            html.Li(html.A('Admin', href='/admin', className='nav-link'))
                        ], className='nav-links'),
                        html.Div([
                            html.Button([
                                html.I(className='fas fa-save'),
                                ' Sauver Filtres'
                            ], id='save-filters-btn', className='glass-button btn-sm'),
                            html.Button([
                                html.I(className='fas fa-download'),
                                ' Exporter'
                            ], id='export-btn', className='glass-button btn-sm btn-success')
                        ], className='nav-actions')
                    ], className='nav-collapse')
                ], className='container-fluid')
            ], className='glass-nav'),
            
            # Main content
            html.Main([
                html.Div([
                    # Hero section
                    html.Section([
                        html.Div([
                            html.H1('Analyse Immobilière Avancée', className='hero-title'),
                            html.P('Explorez les données avec des outils professionnels', className='hero-subtitle'),
                            html.Div([
                                html.Span('Live Analytics', className='glass-badge'),
                                html.Button([
                                    html.I(className='fas fa-play'),
                                    ' Lancer Analyse'
                                ], id='run-analysis-btn', className='glass-button btn-primary')
                            ], className='hero-actions')
                        ], className='hero-content')
                    ], className='hero-section'),
                    
                    # Advanced filters
                    html.Section([
                        html.Div([
                            html.Div([
                                html.H3('Filtres Intelligents', className='filters-title'),
                                html.Div([
                                    html.Div([
                                        html.Label('Ville', className='filter-label'),
                                        dcc.Dropdown(
                                            id='filter-city',
                                            options=[{'label': 'Toutes', 'value': 'all'}] + 
                                                   [{'label': c, 'value': c} for c in options['cities']],
                                            value='all',
                                            className='modern-dropdown'
                                        ),
                                        html.Label('Type de bien', className='filter-label'),
                                        dcc.Dropdown(
                                            id='filter-property-type',
                                            options=[{'label': 'Tous', 'value': 'all'}] + 
                                                   [{'label': t, 'value': t} for t in options['property_types']],
                                            value='all',
                                            className='modern-dropdown'
                                        )
                                    ], className='filter-group'),
                                    
                                    html.Div([
                                        html.Label('Prix (FCFA)', className='filter-label'),
                                        dmc.RangeSlider(
                                            id='price-range',
                                            min=0,
                                            max=200_000_000,
                                            step=1_000_000,
                                            value=[0, 200_000_000],
                                            marks=[
                                                {"value": 0, "label": "0"},
                                                {"value": 50_000_000, "label": "50M"},
                                                {"value": 100_000_000, "label": "100M"},
                                                {"value": 200_000_000, "label": "200M+"}
                                            ],
                                        ),
                                        html.Label('Surface (m²)', className='filter-label'),
                                        dmc.RangeSlider(
                                            id='surface-range',
                                            min=0,
                                            max=1000,
                                            step=10,
                                            value=[0, 1000],
                                            marks=[
                                                {"value": 0, "label": "0"},
                                                {"value": 250, "label": "250"},
                                                {"value": 500, "label": "500"},
                                                {"value": 1000, "label": "1000+"}
                                            ],
                                        )
                                    ], className='filter-group'),
                                    
                                    html.Div([
                                        html.Label('Qualité minimale', className='filter-label'),
                                        dmc.Slider(
                                            id='quality-threshold',
                                            min=0,
                                            max=100,
                                            step=10,
                                            value=0,
                                            marks=[
                                                {"value": 0, "label": "Tous"},
                                                {"value": 50, "label": "Moyen"},
                                                {"value": 80, "label": "Haut"}
                                            ],
                                        ),
                                        html.Label('Sentiment', className='filter-label'),
                                        dcc.Dropdown(
                                            id='sentiment-filter',
                                            options=[
                                                {'label': 'Tous', 'value': 'all'},
                                                {'label': '😊 Positif', 'value': 'positive'},
                                                {'label': '😐 Neutre', 'value': 'neutral'},
                                                {'label': '😞 Négatif', 'value': 'negative'}
                                            ],
                                            value='all',
                                            className='modern-dropdown'
                                        )
                                    ], className='filter-group')
                                ], className='filters-grid'),
                                
                                html.Div([
                                    html.Button([
                                        html.I(className='fas fa-filter'),
                                        ' Appliquer Filtres'
                                    ], id='apply-filters-btn', className='glass-button'),
                                    html.Button([
                                        html.I(className='fas fa-undo'),
                                        ' Réinitialiser'
                                    ], id='reset-filters-btn', className='glass-button btn-secondary')
                                ], className='filters-actions')
                            ], className='glass-card filters-card')
                        ], className='container')
                    ], className='filters-section'),
                    
                    # KPIs premium
                    html.Section([
                        html.Div([
                            html.Div([
                                html.Div(id='kpi-cards', className='kpi-grid'),
                                html.Div(id='opportunities-panel', className='opportunities-panel')
                            ], className='analytics-header')
                        ], className='container')
                    ], className='kpis-section'),
                    
                    # Charts grid
                    html.Section([
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.Div([
                                        html.H3('Distribution & Corrélations', className='chart-section-title'),
                                        dcc.Graph(id='violin-plot', className='chart-figure'),
                                        dcc.Graph(id='correlation-heatmap', className='chart-figure'),
                                        dcc.Graph(id='radar-chart', className='chart-figure')
                                    ], className='col-lg-6'),
                                    
                                    html.Div([
                                        html.H3('Structure du Marché', className='chart-section-title'),
                                        dcc.Graph(id='treemap-chart', className='chart-figure'),
                                        dcc.Graph(id='parallel-coordinates', className='chart-figure'),
                                        html.Div(id='insights-panel', className='insights-glass-panel')
                                    ], className='col-lg-6')
                                ], className='row g-4')
                            ], className='container')
                        ], className='charts-section')
                    ], className='analytics-section'),
                    
                    # Data table
                    html.Section([
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.H3('Données Détaillées', className='table-title'),
                                    html.Div([
                                        html.Span('Affichage: ', className='table-info'),
                                        html.Span(id='table-row-count', className='table-count'),
                                        html.Span(' lignes')
                                    ], className='table-stats'),
                                    html.Div([
                                        dcc.Dropdown(
                                            id='columns-selector',
                                            options=[
                                                {'label': 'Titre', 'value': 'title'},
                                                {'label': 'Prix', 'value': 'price'},
                                                {'label': 'Prix/m²', 'value': 'price_per_m2'},
                                                {'label': 'Ville', 'value': 'city'},
                                                {'label': 'Type', 'value': 'property_type'},
                                                {'label': 'Surface', 'value': 'surface_area'},
                                                {'label': 'Chambres', 'value': 'bedrooms'},
                                                {'label': 'Qualité', 'value': 'quality_score'},
                                                {'label': 'Sentiment', 'value': 'description_sentiment'},
                                                {'label': 'Vues', 'value': 'view_count'}
                                            ],
                                            value=['title', 'price', 'city', 'property_type', 'quality_score'],
                                            multi=True,
                                            className='columns-selector'
                                        )
                                    ], className='table-controls')
                                ], className='table-header'),
                                html.Div(id='data-table-container')
                            ], className='glass-card table-card')
                        ], className='container')
                    ], className='table-section')
                ], className='analytics-wrapper')
            ], className='has-sidebar'),
            
            # Hidden stores
            dcc.Store(id='filters-store', storage_type='local'),
            dcc.Store(id='data-store'),
            dcc.Store(id='kpi-store'),
            
            # Scripts
            html.Script(src='https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js'),
            html.Script(src='https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js'),
            html.Script(src='/static/js/analytics-animations.js')
        ], className='dashboard-root')

    # =================================================================
    #                         CALLBACKS
    # =================================================================
    def setup_callbacks(self):
        """Callbacks interactifs avec debouncing"""
        
        # Appliquer filtres avec debouncing
        @callback(
            Output('data-store', 'data'),
            Output('loading-overlay', 'className', allow_duplicate=True),
            Input('apply-filters-btn', 'n_clicks'),
            Input('price-range', 'value'),
            Input('surface-range', 'value'),
            Input('quality-threshold', 'value'),
            State('filter-city', 'value'),
            State('filter-property-type', 'value'),
            State('sentiment-filter', 'value'),
            prevent_initial_call=True
        )
        def apply_filters(n_clicks, price_range, surface_range, quality, city, prop_type, sentiment):
            if not ctx.triggered:
                raise dash.exceptions.PreventUpdate
            
            filters = {
                'min_price': price_range[0],
                'max_price': price_range[1],
                'min_surface': surface_range[0],
                'max_surface': surface_range[1],
                'min_quality': quality,
                'city': city,
                'property_type': prop_type,
                'sentiment': sentiment,
                'source': 'all'  # À adapter si filtre source ajouté
            }
            
            # Supprimer les filtres None
            filters = {k: v for k, v in filters.items() if v is not None and v != 'all'}
            
            data = self.get_filtered_data(filters)
            return data, 'loading-overlay show'
        
        # Calculer KPIs
        @callback(
            Output('kpi-cards', 'children'),
            Output('opportunities-panel', 'children'),
            Input('data-store', 'data'),
            prevent_initial_call=True
        )
        def update_kpis(data):
            if not data:
                return [], html.Div('Aucune donnée')
            
            kpis = self.calculate_advanced_kpis(data)
            
            # Créer les cartes KPI
            kpi_cards = [
                self.create_premium_kpi_card(
                    'Propriétés', f"{kpis['count']:,}",
                    'fa-database', '#667eea', 0
                ),
                self.create_premium_kpi_card(
                    'Prix Moyen', f"{kpis['avg_price']:,.0f} FCFA",
                    'fa-coins', '#28a745', 0
                ),
                self.create_premium_kpi_card(
                    'Prix/m²', f"{kpis['avg_price_per_m2']:,.0f}",
                    'fa-ruler-combined', '#ff6b6b', 0
                ),
                self.create_premium_kpi_card(
                    'Qualité', f"{kpis['quality_score']:.0f}/100",
                    'fa-shield-alt', '#4ecdc4', 0
                )
            ]
            
            # Panel opportunités
            opportunities_html = html.Div([
                html.H4('🎯 Top Opportunités', className='opportunities-title'),
                html.Div([
                    html.Div([
                        html.Strong(opp['title'][:30] + '...'),
                        html.Br(),
                        html.Span(f"{opp['price']:,.0f} FCFA"),
                        html.Span(f" | Score: {opp['quality_score']:.0f}"),
                        html.Span(f" | {opp['city']}")
                    ], className='opportunity-item') for opp in kpis['opportunities']
                ], className='opportunities-list')
            ], className='opportunities-panel') if kpis['opportunities'] else html.Div()
            
            return kpi_cards, opportunities_html
        
        # Mettre à jour les graphiques
        @callback(
            Output('violin-plot', 'figure'),
            Output('correlation-heatmap', 'figure'),
            Output('radar-chart', 'figure'),
            Output('treemap-chart', 'figure'),
            Output('parallel-coordinates', 'figure'),
            Output('loading-overlay', 'className', allow_duplicate=True),
            Input('data-store', 'data'),
            prevent_initial_call=True
        )
        def update_charts(data):
            if not data:
                figures = [go.Figure()] * 5
                return *figures, 'loading-overlay'
            
            return (
                self.create_price_violin_plot(data),
                self.get_price_correlation_heatmap(data),
                self.create_radar_chart(data),
                self.create_treemap_advanced(data),
                self.create_parallel_coordinates(data),
                'loading-overlay'
            )
        
        # Mettre à jour la table
        @callback(
            Output('data-table-container', 'children'),
            Output('table-row-count', 'children'),
            Input('data-store', 'data'),
            Input('columns-selector', 'value')
        )
        def update_table(data, selected_columns):
            if not data:
                return "Aucune donnée", 0
            
            # Filtrer les colonnes
            df = pd.DataFrame(data)
            df_filtered = df[selected_columns] if selected_columns else df
            
            table = self.create_enhanced_table(df_filtered.to_dict('records'))
            return table, len(df_filtered)
        
        # Sauvegarder les filtres
        @callback(
            Output('filters-store', 'data'),
            Input('apply-filters-btn', 'n_clicks'),
            State('filter-city', 'value'),
            State('filter-property-type', 'value'),
            State('price-range', 'value'),
            State('quality-threshold', 'value'),
            prevent_initial_call=True
        )
        def save_filters(n_clicks, city, prop_type, price_range, quality):
            if not n_clicks:
                raise dash.exceptions.PreventUpdate
            
            filters = {
                'city': city,
                'property_type': prop_type,
                'price_range': price_range,
                'quality_threshold': quality,
                'saved_at': datetime.utcnow().isoformat()
            }
            
            return filters
        
        # Exporter les données
        @callback(
            Output('export-notification', 'children'),
            Input('export-btn', 'n_clicks'),
            State('data-store', 'data'),
            State('columns-selector', 'value'),
            prevent_initial_call=True
        )
        def export_data(n_clicks, data, columns):
            if not n_clicks or not data:
                raise dash.exceptions.PreventUpdate
            
            df = pd.DataFrame(data)
            if columns:
                df = df[columns]
            
            # Générer CSV
            csv_string = df.to_csv(index=False, encoding='utf-8')
            b64 = base64.b64encode(csv_string.encode()).decode()
            
            # Créer notification avec lien de téléchargement
            return dmc.Notification(
                title="Export prêt",
                message="Votre fichier CSV est prêt à être téléchargé",
                color="green",
                autoClose=5000,
                action=html.A(
                    "Télécharger",
                    href=f"data:text/csv;base64,{b64}",
                    download="immo_analytics_export.csv",
                    className="export-link"
                )
            )

# Factory function
def create_premium_analytics_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    dashboard = AnalyticsDashboard(
        server=server,
        routes_pathname_prefix=routes_pathname_prefix,
        requests_pathname_prefix=requests_pathname_prefix
    )
    return dashboard.app