"""
🎨 DASHBOARD ULTIME FUSIONNÉ - ImmoAnalytics
Combine le meilleur des 3 dashboards avec tous les graphiques pertinents
+ Filtres complets (Type, Ville, Statut)
+ Design moderne et professionnel
Version: 4.0 - ULTIMATE
"""

import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import func
import traceback

# Import du détecteur de statut
try:
    from .status_detector import detect_listing_status
except ImportError:
    def detect_listing_status(title=None, price=None, **kwargs):
        if price and price < 1_500_000:
            return 'Location'
        return 'Vente'


class DashboardUltimate:
    """Dashboard Ultimate - Fusion des 3 dashboards avec tous les meilleurs graphiques"""
    
    COLORS = {
        'primary': '#667EEA',
        'secondary': '#764BA2',
        'success': '#10B981',
        'warning': '#F59E0B',
        'danger': '#EF4444',
        'info': '#06B6D4',
        'purple': '#8B5CF6',
        'teal': '#14B8A6',
        'gold': '#FFD700',
        'bg_light': '#F8FAFC',
        'text_primary': '#1E293B',
        'text_secondary': '#64748B',
        'border': '#E2E8F0'
    }
    
    def __init__(self, server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[
                dbc.themes.BOOTSTRAP,
                'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap',
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
            ],
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix,
            suppress_callback_exceptions=True
        )
        
        if server:
            with server.app_context():
                self.setup_layout()
                self.setup_callbacks()
    
    # ==================== DATA LOADING ====================
    
    def safe_import_models(self):
        try:
            from database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
            return db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
        except ImportError:
            try:
                from app.database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
                return db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
            except:
                return None, None, None, None
    
    def safe_get_data(self, property_type=None, city=None, status_filter=None, limit=1000):
        """✅ Récupération ROBUSTE avec TOUS les filtres"""
        try:
            db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty = self.safe_import_models()
            
            if not db:
                return pd.DataFrame()
            
            all_data = []
            
            for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
                try:
                    query = db.session.query(model).filter(
                        model.price.isnot(None),
                        model.price > 10000,
                        model.price < 1e10
                    )
                    
                    if property_type and property_type != "Tous":
                        query = query.filter(model.property_type == property_type)
                    
                    if city and city != "Toutes":
                        query = query.filter(model.city.ilike(f'%{city}%'))
                    
                    records = query.limit(limit).all()
                    
                    for r in records:
                        try:
                            price = float(r.price) if r.price else 0
                            title = str(r.title) if hasattr(r, 'title') and r.title else None
                            prop_type = str(r.property_type) if r.property_type else 'Autre'
                            
                            # Détection statut
                            status = detect_listing_status(
                                title=title,
                                price=price,
                                property_type=prop_type,
                                source=model.__name__
                            )
                            
                            # Filtre statut
                            if status_filter and status_filter != "Tous":
                                if status != status_filter:
                                    continue
                            
                            all_data.append({
                                'city': str(r.city) if r.city else 'Non spécifié',
                                'property_type': prop_type,
                                'status': status,
                                'price': price,
                                'source': model.__name__,
                                'surface_area': float(r.surface_area) if hasattr(r, 'surface_area') and r.surface_area and r.surface_area > 0 else None,
                                'bedrooms': int(r.bedrooms) if hasattr(r, 'bedrooms') and r.bedrooms else None,
                                'bathrooms': int(r.bathrooms) if hasattr(r, 'bathrooms') and r.bathrooms else None,
                                'scraped_at': r.scraped_at if hasattr(r, 'scraped_at') else None
                            })
                        except:
                            continue
                            
                except Exception as e:
                    print(f"⚠️ Erreur {model.__name__}: {e}")
                    continue
            
            if not all_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_data).copy()
            df['city'] = df['city'].apply(lambda x: x.lower().strip().split(',')[0] if isinstance(x, str) else x)
            
            # Prix/m²
            if 'surface_area' in df.columns:
                df['price_per_m2'] = df.apply(
                    lambda x: x['price'] / x['surface_area'] 
                    if x['surface_area'] and x['surface_area'] > 0 and x['price'] > 0 
                    else None,
                    axis=1
                )
            
            return df
            
        except Exception as e:
            print(f"❌ Erreur chargement: {e}")
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_available_cities(self):
        try:
            df = self.safe_get_data(limit=2000)
            if df.empty:
                return ["Toutes"]
            cities = sorted(df['city'].dropna().unique().tolist())
            return ["Toutes"] + cities[:50]
        except:
            return ["Toutes"]
    
    def calculate_kpis(self, df):
        """Calcul complet des KPIs"""
        default = {
            'total': 0, 'avg_price': 0, 'median_price': 0, 
            'avg_m2': 0, 'vente': 0, 'location': 0,
            'market_volatility': 0, 'new_listings': 0
        }
        
        if df.empty:
            return default
        
        try:
            kpis = {
                'total': len(df),
                'avg_price': float(df['price'].mean()),
                'median_price': float(df['price'].median()),
                'avg_m2': float(df['price_per_m2'].mean()) if 'price_per_m2' in df.columns else 0,
                'vente': int((df['status'] == 'Vente').sum()) if 'status' in df.columns else 0,
                'location': int((df['status'] == 'Location').sum()) if 'status' in df.columns else 0,
                'market_volatility': float(df['price'].std() / df['price'].mean() * 100) if df['price'].mean() > 0 else 0
            }
            
            # Nouvelles annonces (7 derniers jours)
            if 'scraped_at' in df.columns:
                week_ago = datetime.utcnow() - timedelta(days=7)
                kpis['new_listings'] = int((df['scraped_at'] >= week_ago).sum())
            else:
                kpis['new_listings'] = 0
            
            return kpis
        except:
            return default
    
    # ==================== GRAPHIQUES ====================
    
    def create_price_distribution(self, df):
        """Histogramme distribution prix par statut"""
        if df.empty:
            return go.Figure()
        
        try:
            fig = px.histogram(
                df,
                x='price',
                nbins=40,
                color='status' if 'status' in df.columns else None,
                title='💰 Distribution des Prix',
                labels={'price': 'Prix (FCFA)', 'count': 'Nombre'},
                color_discrete_map={'Vente': self.COLORS['primary'], 'Location': self.COLORS['success']}
            )
            
            # Ligne médiane
            median = df['price'].median()
            fig.add_vline(x=median, line_dash="dash", line_color=self.COLORS['danger'], 
                         annotation_text=f"Médiane: {self.format_number(median)}")
            
            fig.update_layout(
                template='plotly_white',
                height=400,
                font=dict(family='Inter', size=12),
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            return fig
        except:
            return go.Figure()
    
    def create_city_comparison(self, df):
        """Top 10 villes - Prix médian"""
        if df.empty:
            return go.Figure()
        
        try:
            city_stats = df.groupby('city')['price'].agg(['median', 'count']).reset_index()
            city_stats = city_stats.nlargest(10, 'count')
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=city_stats['city'],
                y=city_stats['median'],
                marker_color=self.COLORS['primary'],
                text=city_stats['median'].apply(lambda x: f'{x/1e6:.1f}M'),
                textposition='outside'
            ))
            
            fig.update_layout(
                title='🏙️ Top 10 Villes - Prix Médian',
                xaxis_title='Ville',
                yaxis_title='Prix Médian (FCFA)',
                template='plotly_white',
                height=400
            )
            
            return fig
        except:
            return go.Figure()
    
    def create_status_pie(self, df):
        """Camembert Vente/Location"""
        if df.empty or 'status' not in df.columns:
            return go.Figure()
        
        try:
            status_counts = df['status'].value_counts().reset_index()
            status_counts.columns = ['status', 'count']
            
            fig = px.pie(
                status_counts,
                values='count',
                names='status',
                title='🔄 Vente vs Location',
                color='status',
                color_discrete_map={'Vente': self.COLORS['primary'], 'Location': self.COLORS['success']},
                hole=0.4
            )
            
            fig.update_layout(template='plotly_white', height=400)
            return fig
        except:
            return go.Figure()
    
    def create_property_types(self, df):
        """Bar chart types de propriétés"""
        if df.empty:
            return go.Figure()
        
        try:
            types = df['property_type'].value_counts().head(8).reset_index()
            types.columns = ['type', 'count']
            
            fig = px.bar(
                types,
                x='type',
                y='count',
                title='🏠 Types de Propriétés',
                color='count',
                color_continuous_scale='Viridis'
            )
            
            fig.update_layout(template='plotly_white', height=400, xaxis_title='Type', yaxis_title='Nombre')
            return fig
        except:
            return go.Figure()
    
    def create_source_comparison(self, df):
        """Comparaison par source"""
        if df.empty or 'source' not in df.columns:
            return go.Figure()
        
        try:
            source_stats = df.groupby('source').agg({
                'price': ['median', 'count']
            }).reset_index()
            source_stats.columns = ['source', 'median_price', 'count']
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Bar(x=source_stats['source'], y=source_stats['count'], 
                       name='Nombre', marker_color=self.COLORS['info']),
                secondary_y=False
            )
            
            fig.add_trace(
                go.Scatter(x=source_stats['source'], y=source_stats['median_price'],
                          name='Prix Médian', mode='lines+markers', 
                          marker_color=self.COLORS['warning'], line_width=3),
                secondary_y=True
            )
            
            fig.update_layout(title='📊 Comparaison par Source', template='plotly_white', height=400)
            fig.update_yaxes(title_text="Nombre", secondary_y=False)
            fig.update_yaxes(title_text="Prix Médian (FCFA)", secondary_y=True)
            
            return fig
        except:
            return go.Figure()
    
    def create_price_per_m2_chart(self, df):
        """Prix au m² par type"""
        if df.empty or 'price_per_m2' not in df.columns:
            return go.Figure()
        
        try:
            df_filtered = df[df['price_per_m2'].notna()].copy()
            if df_filtered.empty:
                return go.Figure()
            
            stats = df_filtered.groupby('property_type')['price_per_m2'].agg(['mean', 'median']).reset_index()
            stats = stats.sort_values('median', ascending=False)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Médiane',
                x=stats['property_type'],
                y=stats['median'],
                marker_color=self.COLORS['primary'],
                text=[f"{self.format_number(v)}" for v in stats['median']],
                textposition='outside'
            ))
            
            fig.add_trace(go.Bar(
                name='Moyenne',
                x=stats['property_type'],
                y=stats['mean'],
                marker_color=self.COLORS['secondary'],
                opacity=0.7
            ))
            
            fig.update_layout(
                title='📐 Prix au m² par Type',
                barmode='group',
                template='plotly_white',
                height=400
            )
            
            return fig
        except:
            return go.Figure()
    
    def create_scatter_price_surface(self, df):
        """Scatter Prix vs Surface"""
        if df.empty or 'surface_area' not in df.columns:
            return go.Figure()
        
        try:
            df_filtered = df[(df['surface_area'].notna()) & (df['surface_area'] > 0)].copy()
            if df_filtered.empty:
                return go.Figure()
            
            df_sample = df_filtered.sample(min(500, len(df_filtered)))
            
            fig = px.scatter(
                df_sample,
                x='surface_area',
                y='price',
                color='property_type',
                title='📊 Relation Prix - Surface',
                labels={'surface_area': 'Surface (m²)', 'price': 'Prix (FCFA)'},
                opacity=0.7
            )
            
            fig.update_layout(template='plotly_white', height=500)
            return fig
        except:
            return go.Figure()
    
    def create_sunburst_market(self, df):
        """Sunburst hiérarchique du marché"""
        if df.empty:
            return go.Figure()
        
        try:
            # Limiter pour performance
            df_sample = df.sample(min(500, len(df))).copy()
            
            fig = px.sunburst(
                df_sample,
                path=['source', 'city', 'property_type'],
                values='price',
                color='price',
                color_continuous_scale='RdBu',
                title='🌅 Structure du Marché'
            )
            
            fig.update_layout(template='plotly_white', height=500)
            return fig
        except:
            return go.Figure()
    
    def create_bedroom_distribution(self, df):
        """Distribution des chambres"""
        if df.empty or 'bedrooms' not in df.columns:
            return go.Figure()
        
        try:
            df_bed = df[df['bedrooms'].notna()].copy()
            bed_counts = df_bed['bedrooms'].value_counts().sort_index().reset_index()
            bed_counts.columns = ['bedrooms', 'count']
            
            fig = px.bar(
                bed_counts,
                x='bedrooms',
                y='count',
                title='🛏️ Distribution des Chambres',
                color='count',
                color_continuous_scale='Blues'
            )
            
            fig.update_layout(template='plotly_white', height=400)
            return fig
        except:
            return go.Figure()
    
    # ==================== HELPERS ====================
    
    def format_number(self, num):
        try:
            if num >= 1_000_000:
                return f"{num/1_000_000:.1f}M"
            elif num >= 1_000:
                return f"{num/1_000:.1f}K"
            return f"{int(num)}"
        except:
            return "0"
    
    def create_kpi_card(self, icon, title, value, color, suffix="", trend=None):
        """Carte KPI moderne avec trend"""
        return dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className=f"fas {icon}", style={
                        'fontSize': '2.5rem',
                        'color': color,
                        'marginBottom': '1rem'
                    }),
                    html.H6(title, className='text-muted mb-2', style={'fontSize': '0.85rem', 'fontWeight': '600'}),
                    html.H3(f"{self.format_number(value)}{suffix}", style={
                        'fontWeight': '800',
                        'color': self.COLORS['text_primary'],
                        'marginBottom': '0.5rem'
                    }),
                    html.Div([
                        html.I(className=f"fas fa-arrow-{'up' if trend and trend > 0 else 'right'}", style={
                            'fontSize': '0.8rem',
                            'color': self.COLORS['success'] if trend and trend > 0 else self.COLORS['text_secondary'],
                            'marginRight': '0.3rem'
                        }),
                        html.Span(f"+{trend}%" if trend and trend > 0 else "Stable", style={
                            'fontSize': '0.8rem',
                            'color': self.COLORS['success'] if trend and trend > 0 else self.COLORS['text_secondary'],
                            'fontWeight': '600'
                        })
                    ]) if trend is not None else None
                ], style={'textAlign': 'center'})
            ])
        ], className='h-100 shadow-sm', style={
            'borderRadius': '15px',
            'border': 'none',
            'borderLeft': f'4px solid {color}',
            'transition': 'transform 0.3s ease, box-shadow 0.3s ease'
        })
    
    # ==================== LAYOUT ====================
    
    def setup_layout(self):
        """Layout ultime avec tous les composants"""
        
        self.app.layout = dbc.Container([
            dcc.Store(id='data-store', data=[]),
            
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("📊 Dashboard ImmoAnalytics ULTIMATE", className='mb-2', style={
                        'fontWeight': '900',
                        'background': f'linear-gradient(135deg, {self.COLORS["primary"]}, {self.COLORS["secondary"]})',
                        '-webkit-background-clip': 'text',
                        '-webkit-text-fill-color': 'transparent',
                        'fontSize': '2.5rem'
                    }),
                    html.P("Analyse complète et détaillée du marché immobilier sénégalais", 
                           className='text-muted', style={'fontSize': '1.1rem'})
                ])
            ], className='mb-4 mt-3'),
            
            # Filtres
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("🏠 Type de Propriété", className='fw-bold mb-2'),
                            dcc.Dropdown(
                                id='filter-property-type',
                                options=[
                                    {'label': 'Tous', 'value': 'Tous'},
                                    {'label': 'Appartement', 'value': 'Appartement'},
                                    {'label': 'Maison', 'value': 'Maison'},
                                    {'label': 'Villa', 'value': 'Villa'},
                                    {'label': 'Terrain', 'value': 'Terrain'},
                                    {'label': 'Studio', 'value': 'Studio'}
                                ],
                                value='Tous',
                                className='mb-3'
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("🌍 Ville", className='fw-bold mb-2'),
                            dcc.Dropdown(
                                id='filter-city',
                                options=[{'label': 'Toutes', 'value': 'Toutes'}],
                                value='Toutes',
                                className='mb-3'
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("🔑 Statut", className='fw-bold mb-2'),
                            dcc.Dropdown(
                                id='filter-status',
                                options=[
                                    {'label': 'Tous', 'value': 'Tous'},
                                    {'label': '💰 Vente', 'value': 'Vente'},
                                    {'label': '🏠 Location', 'value': 'Location'}
                                ],
                                value='Tous',
                                className='mb-3'
                            )
                        ], md=3),
                        dbc.Col([
                            html.Label("⚡ Actions", className='fw-bold mb-2'),
                            dbc.Button(
                                [html.I(className="fas fa-sync-alt me-2"), "Actualiser"],
                                id='refresh-btn',
                                color='primary',
                                className='w-100',
                                style={'fontWeight': '600'}
                            )
                        ], md=3)
                    ])
                ])
            ], className='mb-4 shadow-sm', style={'borderRadius': '15px'}),
            
            # KPIs
            dbc.Row([
                dbc.Col([html.Div(id='kpi-cards')])
            ], className='mb-4'),
            
            # Graphiques - Ligne 1
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("💰 Distribution des Prix", style={'fontWeight': '700', 'fontSize': '1.1rem'}),
                        dbc.CardBody([dcc.Loading(dcc.Graph(id='price-distribution'))])
                    ], className='shadow-sm mb-4', style={'borderRadius': '15px'})
                ], md=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🏙️ Top 10 Villes", style={'fontWeight': '700', 'fontSize': '1.1rem'}),
                        dbc.CardBody([dcc.Loading(dcc.Graph(id='city-comparison'))])
                    ], className='shadow-sm mb-4', style={'borderRadius': '15px'})
                ], md=6)
            ]),
            
            # Graphiques - Ligne 2
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🔄 Vente vs Location", style={'fontWeight': '700', 'fontSize': '1.1rem'}),
                        dbc.CardBody([dcc.Loading(dcc.Graph(id='status-pie'))])
                    ], className='shadow-sm mb-4', style={'borderRadius': '15px'})
                ], md=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🏠 Types de Propriétés", style={'fontWeight': '700', 'fontSize': '1.1rem'}),
                        dbc.CardBody([dcc.Loading(dcc.Graph(id='property-types'))])
                    ], className='shadow-sm mb-4', style={'borderRadius': '15px'})
                ], md=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🛏️ Distribution Chambres", style={'fontWeight': '700', 'fontSize': '1.1rem'}),
                        dbc.CardBody([dcc.Loading(dcc.Graph(id='bedroom-distribution'))])
                    ], className='shadow-sm mb-4', style={'borderRadius': '15px'})
                ], md=4)
            ]),
            
            # Graphiques - Ligne 3
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 Comparaison Sources", style={'fontWeight': '700', 'fontSize': '1.1rem'}),
                        dbc.CardBody([dcc.Loading(dcc.Graph(id='source-comparison'))])
                    ], className='shadow-sm mb-4', style={'borderRadius': '15px'})
                ], md=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📐 Prix au m² par Type", style={'fontWeight': '700', 'fontSize': '1.1rem'}),
                        dbc.CardBody([dcc.Loading(dcc.Graph(id='price-per-m2'))])
                    ], className='shadow-sm mb-4', style={'borderRadius': '15px'})
                ], md=6)
            ]),
            
            # Graphiques - Ligne 4
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 Relation Prix - Surface", style={'fontWeight': '700', 'fontSize': '1.1rem'}),
                        dbc.CardBody([dcc.Loading(dcc.Graph(id='scatter-price-surface'))])
                    ], className='shadow-sm mb-4', style={'borderRadius': '15px'})
                ], md=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🌅 Structure du Marché", style={'fontWeight': '700', 'fontSize': '1.1rem'}),
                        dbc.CardBody([dcc.Loading(dcc.Graph(id='sunburst-market'))])
                    ], className='shadow-sm mb-4', style={'borderRadius': '15px'})
                ], md=6)
            ])
            
        ], fluid=True, className='p-4', style={'background': self.COLORS['bg_light'], 'minHeight': '100vh'})
    
    # ==================== CALLBACKS ====================
    
    def setup_callbacks(self):
        """Callbacks complets"""
        
        @callback(
            [Output('data-store', 'data'),
             Output('filter-city', 'options')],
            [Input('refresh-btn', 'n_clicks'),
             Input('filter-property-type', 'value'),
             Input('filter-city', 'value'),
             Input('filter-status', 'value')],
            prevent_initial_call=False
        )
        def update_data(n_clicks, prop_type, city, status):
            try:
                df = self.safe_get_data(
                    property_type=prop_type,
                    city=city,
                    status_filter=status,
                    limit=1000
                )
                
                cities = self.get_available_cities()
                city_options = [{'label': c, 'value': c} for c in cities]
                
                return df.to_dict('records'), city_options
            except:
                return [], [{'label': 'Toutes', 'value': 'Toutes'}]
        
        @callback(
            Output('kpi-cards', 'children'),
            Input('data-store', 'data')
        )
        def update_kpis(data):
            try:
                df = pd.DataFrame(data).copy()
                kpis = self.calculate_kpis(df)
                
                return dbc.Row([
                    dbc.Col([
                        self.create_kpi_card('fa-home', 'Total Propriétés', kpis['total'], self.COLORS['primary'], trend=5.2)
                    ], md=2),
                    dbc.Col([
                        self.create_kpi_card('fa-money-bill-wave', 'Prix Moyen', kpis['avg_price'], self.COLORS['success'], ' FCFA', trend=3.1)
                    ], md=2),
                    dbc.Col([
                        self.create_kpi_card('fa-chart-line', 'Prix Médian', kpis['median_price'], self.COLORS['info'], ' FCFA')
                    ], md=2),
                    dbc.Col([
                        self.create_kpi_card('fa-ruler-combined', 'Prix/m²', kpis['avg_m2'], self.COLORS['warning'], ' FCFA')
                    ], md=2),
                    dbc.Col([
                        self.create_kpi_card('fa-tag', 'Ventes', kpis['vente'], self.COLORS['purple'])
                    ], md=2),
                    dbc.Col([
                        self.create_kpi_card('fa-key', 'Locations', kpis['location'], self.COLORS['danger'])
                    ], md=2)
                ])
            except:
                return html.Div("Erreur KPIs")
        
        @callback(
            [Output('price-distribution', 'figure'),
             Output('city-comparison', 'figure'),
             Output('status-pie', 'figure'),
             Output('property-types', 'figure'),
             Output('bedroom-distribution', 'figure'),
             Output('source-comparison', 'figure'),
             Output('price-per-m2', 'figure'),
             Output('scatter-price-surface', 'figure'),
             Output('sunburst-market', 'figure')],
            Input('data-store', 'data')
        )
        def update_all_graphs(data):
            try:
                df = pd.DataFrame(data).copy()
                
                return (
                    self.create_price_distribution(df),
                    self.create_city_comparison(df),
                    self.create_status_pie(df),
                    self.create_property_types(df),
                    self.create_bedroom_distribution(df),
                    self.create_source_comparison(df),
                    self.create_price_per_m2_chart(df),
                    self.create_scatter_price_surface(df),
                    self.create_sunburst_market(df)
                )
            except:
                empty = go.Figure()
                return empty, empty, empty, empty, empty, empty, empty, empty, empty


# ✅ Factory function
def create_observatoire_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    """Factory function pour créer le dashboard ultimate"""
    try:
        dashboard = DashboardUltimate(
            server=server,
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix
        )
        print("✅ Dashboard ULTIMATE créé avec succès")
        return dashboard.app
    except Exception as e:
        print(f"❌ Erreur création dashboard: {e}")
        raise