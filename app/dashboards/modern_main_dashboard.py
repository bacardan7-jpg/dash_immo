import dash
from dash import html, dcc, Input, Output, callback, State
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty, ProprietesConsolidees
from ..auth.decorators import analyst_required
from textblob import TextBlob
import json

class ModernMainDashboard:
    """Dashboard principal premium avec analytics avancées"""
    
    def __init__(self, server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix,
            suppress_callback_exceptions=True
        )
        
        if server:
            with server.app_context():
                self.setup_layout()
                self.setup_callbacks()
        else:
            self._layout_setup_deferred = True
    
    def get_advanced_kpi_data(self):
        """KPIs stratégiques avec tendances"""
        try:
            # Données de base
            coinafrique_count = db.session.query(CoinAfrique).count()
            expat_count = db.session.query(ExpatDakarProperty).count()
            loger_count = db.session.query(LogerDakarProperty).count()
            total_properties = coinafrique_count + expat_count + loger_count
            
            # Prix moyens
            coinafrique_avg = db.session.query(db.func.avg(CoinAfrique.price)).scalar() or 0
            expat_avg = db.session.query(db.func.avg(ExpatDakarProperty.price)).scalar() or 0
            loger_avg = db.session.query(db.func.avg(LogerDakarProperty.price)).scalar() or 0
            
            # Calcul du marché global
            all_prices = []
            for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
                prices = db.session.query(model.price).filter(model.price > 0).all()
                all_prices.extend([p[0] for p in prices])
            
            avg_price = np.mean(all_prices) if all_prices else 0
            median_price = np.median(all_prices) if all_prices else 0
            std_price = np.std(all_prices) if all_prices else 0
            
            # Tendances (comparaison 7 derniers jours vs 7 jours précédents)
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            two_weeks_ago = now - timedelta(days=14)
            
            recent_total = db.session.query(CoinAfrique).filter(CoinAfrique.scraped_at >= week_ago).count() + \
                          db.session.query(ExpatDakarProperty).filter(ExpatDakarProperty.scraped_at >= week_ago).count() + \
                          db.session.query(LogerDakarProperty).filter(LogerDakarProperty.scraped_at >= week_ago).count()
            
            previous_week = db.session.query(CoinAfrique).filter(
                CoinAfrique.scraped_at.between(two_weeks_ago, week_ago)
            ).count() + \
            db.session.query(ExpatDakarProperty).filter(
                ExpatDakarProperty.scraped_at.between(two_weeks_ago, week_ago)
            ).count() + \
            db.session.query(LogerDakarProperty).filter(
                LogerDakarProperty.scraped_at.between(two_weeks_ago, week_ago)
            ).count()
            
            growth_rate = ((recent_total - previous_week) / previous_week * 100) if previous_week > 0 else 0
            
            # Score du marché (indicateur composite)
            market_score = min(100, (total_properties / 1000) * 10 + (growth_rate / 2) + (len(all_prices) / 100))
            
            # Qualité des données (taux de remplissage)
            filled_fields = 0
            total_fields = 0
            
            for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
                records = db.session.query(model).limit(100).all()
                for record in records:
                    fields = ['price', 'city', 'property_type', 'surface_area', 'bedrooms']
                    for field in fields:
                        total_fields += 1
                        if getattr(record, field) is not None:
                            filled_fields += 1
            
            data_quality = (filled_fields / total_fields * 100) if total_fields > 0 else 0
            
            # Sentiment analysis sur les descriptions
            descriptions = []
            for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
                descs = db.session.query(model.description).filter(model.description.isnot(None)).limit(50).all()
                descriptions.extend([d[0] for d in descs])
            
            sentiment_score = 0
            if descriptions:
                sentiments = [TextBlob(desc).sentiment.polarity for desc in descriptions if desc]
                sentiment_score = np.mean(sentiments) * 100 if sentiments else 0
            
            # Ratio prix/surface
            price_per_m2 = []
            for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
                data = db.session.query(model.price, model.surface_area).filter(
                    model.price > 0, model.surface_area > 0
                ).limit(1000).all()
                price_per_m2.extend([p[0]/p[1] for p in data if p[1] > 0])
            
            avg_price_per_m2 = np.mean(price_per_m2) if price_per_m2 else 0
            
            return {
                'total_properties': total_properties,
                'avg_price': avg_price,
                'median_price': median_price,
                'std_price': std_price,
                'growth_rate': growth_rate,
                'recent_total': recent_total,
                'market_score': market_score,
                'data_quality': data_quality,
                'sentiment_score': sentiment_score,
                'avg_price_per_m2': avg_price_per_m2,
                'coinafrique_avg': coinafrique_avg,
                'expat_avg': expat_avg,
                'loger_avg': loger_avg,
                'price_volatility': std_price / avg_price * 100 if avg_price > 0 else 0
            }
        except Exception as e:
            print(f"Erreur KPI avancé: {e}")
            return {}
    
    def create_premium_kpi_card(self, title, value, icon, color="#ffd700", trend=0, subtitle=""):
        """Carte KPI premium avec tendance animée"""
        trend_icon = "fa-arrow-up" if trend > 0 else "fa-arrow-down" if trend < 0 else "fa-minus"
        trend_color = "#28a745" if trend > 0 else "#dc3545" if trend < 0 else "#6c757d"
        
        return html.Div([
            html.Div([
                html.Div([
                    html.I(className=f"fas {icon}", style={
                        "fontSize": "2.5rem",
                        "color": color,
                        "marginBottom": "1rem",
                        "filter": "drop-shadow(0 0 8px rgba(255,215,0,0.5))"
                    }),
                    html.H3(title, className="kpi-title")
                ], className="kpi-header"),
                
                html.Div([
                    html.Div(value, className="kpi-value", 
                            style={"color": color}),
                    html.Div([
                        html.I(className=f"fas {trend_icon}", style={
                            "color": trend_color,
                            "fontSize": "0.9rem"
                        }),
                        html.Span(f"{abs(trend):+.1f}%", style={
                            "color": trend_color,
                            "fontWeight": "600",
                            "marginLeft": "0.5rem"
                        })
                    ], className="kpi-trend", style={"marginTop": "0.5rem"}),
                    html.P(subtitle, className="kpi-subtitle")
                ], className="kpi-body")
            ], className="kpi-content")
        ], className="premium-kpi-card glass-card", 
        style={"borderLeft": f"4px solid {color}"})
    
    def get_market_treemap(self):
        """Treemap de la répartition du marché par valeur"""
        try:
            data = []
            for model, source in [(CoinAfrique, 'CoinAfrique'), 
                                 (ExpatDakarProperty, 'ExpatDakar'), 
                                 (LogerDakarProperty, 'LogerDakar')]:
                records = db.session.query(model.city, model.property_type, model.price).filter(
                    model.price > 0
                ).all()
                
                for city, prop_type, price in records:
                    data.append({
                        'source': source,
                        'city': city or 'Inconnu',
                        'type': prop_type or 'Autre',
                        'value': price
                    })
            
            df = pd.DataFrame(data)
            if df.empty:
                return go.Figure()
            
            fig = px.treemap(
                df, 
                path=['source', 'city', 'type'], 
                values='value',
                color='value',
                color_continuous_scale='Viridis',
                title="Répartition du marché par valeur"
            )
            
            fig.update_layout(
                height=500,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', family='Inter'),
                title=dict(
                    font=dict(size=18, color='white'),
                    x=0.5
                )
            )
            
            return fig
        except Exception as e:
            print(f"Erreur treemap: {e}")
            return go.Figure()
    
    def get_price_correlation_heatmap(self):
        """Heatmap de corrélation prix/caractéristiques"""
        try:
            data = []
            for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
                records = db.session.query(
                    model.price, model.surface_area, model.bedrooms, model.bathrooms
                ).filter(
                    model.price > 0, model.surface_area > 0
                ).limit(1000).all()
                
                for price, surface, beds, baths in records:
                    data.append({
                        'price': price,
                        'surface': surface or 0,
                        'bedrooms': beds or 0,
                        'bathrooms': baths or 0
                    })
            
            df = pd.DataFrame(data)
            if df.empty:
                return go.Figure()
            
            # Calculer les corrélations
            corr = df.corr()
            
            fig = px.imshow(
                corr, 
                text_auto=True, 
                aspect="auto",
                color_continuous_scale='RdBu_r',
                title="Corrélation entre les caractéristiques"
            )
            
            fig.update_layout(
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', family='Inter'),
                title=dict(font=dict(size=18, color='white'), x=0.5)
            )
            
            return fig
        except Exception as e:
            print(f"Erreur heatmap: {e}")
            return go.Figure()
    
    def get_3d_price_surface(self):
        """Graphique 3D prix × surface × source"""
        try:
            data = []
            for model, source in [(CoinAfrique, 'CoinAfrique'), 
                                 (ExpatDakarProperty, 'ExpatDakar'), 
                                 (LogerDakarProperty, 'LogerDakar')]:
                records = db.session.query(model.price, model.surface_area).filter(
                    model.price > 0, model.surface_area > 0
                ).limit(500).all()
                
                for price, surface in records:
                    data.append({
                        'price': price,
                        'surface': surface,
                        'source': source
                    })
            
            df = pd.DataFrame(data)
            if df.empty:
                return go.Figure()
            
            fig = px.scatter_3d(
                df, 
                x='surface', 
                y='price', 
                z='source',
                color='price',
                size='surface',
                hover_data=['source'],
                title="Prix en fonction de la surface (3D)",
                color_continuous_scale='Plasma'
            )
            
            fig.update_layout(
                height=600,
                paper_bgcolor='rgba(0,0,0,0)',
                scene=dict(
                    bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(title='Surface (m²)', color='white'),
                    yaxis=dict(title='Prix (FCFA)', color='white'),
                    zaxis=dict(title='Source', color='white')
                ),
                font=dict(color='white', family='Inter'),
                title=dict(font=dict(size=18, color='white'), x=0.5)
            )
            
            return fig
        except Exception as e:
            print(f"Erreur 3D plot: {e}")
            return go.Figure()
    
    def get_price_violin_plot(self):
        """Violin plot de la distribution des prix"""
        try:
            data = []
            for model, source in [(CoinAfrique, 'CoinAfrique'), 
                                 (ExpatDakarProperty, 'ExpatDakar'), 
                                 (LogerDakarProperty, 'LogerDakar')]:
                prices = db.session.query(model.price).filter(model.price > 0).limit(1000).all()
                data.extend([{
                    'price': p[0],
                    'source': source
                } for p in prices])
            
            df = pd.DataFrame(data)
            if df.empty:
                return go.Figure()
            
            fig = px.violin(
                df, 
                y='price', 
                x='source', 
                box=True,
                color='source',
                title="Distribution des prix par source",
                color_discrete_map={
                    'CoinAfrique': '#667eea',
                    'ExpatDakar': '#764ba2',
                    'LogerDakar': '#ffd700'
                }
            )
            
            fig.update_layout(
                height=450,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', family='Inter'),
                title=dict(font=dict(size=18, color='white'), x=0.5),
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    tickcolor='rgba(255,255,255,0.3)'
                ),
                yaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    tickcolor='rgba(255,255,255,0.3)'
                )
            )
            
            return fig
        except Exception as e:
            print(f"Erreur violin plot: {e}")
            return go.Figure()
    
    def setup_layout(self):
        """Layout premium avec animations"""
        kpi_data = self.get_advanced_kpi_data()
        
        self.app.layout = html.Div([
            # Animated background
            html.Div(className='animated-bg'),
            
            # Loading overlay
            html.Div([
                html.Div(className='spinner-glow'),
                html.P('Chargement des données...', className='loading-text')
            ], id='loading-overlay', className='loading-overlay'),
            
            # Navigation
            html.Nav([
                html.Div([
                    html.Div([
                        html.A([
                            html.I(className='fas fa-home'),
                            html.Span('ImmoAnalytics Premium')
                        ], href='/', className='nav-brand'),
                        html.Button([
                            html.Span(className='hamburger')
                        ], className='nav-toggle', **{'aria-label': 'Menu mobile'})
                    ], className='nav-wrapper'),
                    html.Div([
                        html.Ul([
                            html.Li(html.A('Dashboard', href='/dashboard', className='nav-link active')),
                            html.Li(html.A('Analyse', href='/analytics', className='nav-link')),
                            html.Li(html.A('Carte', href='/map', className='nav-link')),
                            html.Li(html.A('Admin', href='/admin', className='nav-link'))
                        ], className='nav-links'),
                        html.Div(id='nav-actions')
                    ], className='nav-collapse', id='navbarNav')
                ], className='container-fluid')
            ], className='glass-nav'),
            
            # Main content
            html.Main([
                html.Div([
                    # Hero section
                    html.Section([
                        html.Div([
                            html.H1('Analytics du Marché Immobilier', className='hero-title'),
                            html.P('Données en temps réel du marché sénégalais', className='hero-subtitle'),
                            html.Div([
                                html.Span('Live Data', className='glass-badge'),
                                html.Button([
                                    html.I(className='fas fa-sync-alt'),
                                    ' Actualiser'
                                ], id='refresh-btn', className='glass-button')
                            ], className='hero-actions')
                        ], className='hero-content')
                    ], className='hero-section'),
                    
                    # KPIs premium
                    html.Section([
                        html.Div([
                            self.create_premium_kpi_card(
                                'Score Marché', 
                                f"{kpi_data.get('market_score', 0):.0f}/100",
                                'fa-chart-pie',
                                '#ffd700',
                                kpi_data.get('growth_rate', 0),
                                'Performance globale'
                            ),
                            self.create_premium_kpi_card(
                                'Volatilité Prix',
                                f"{kpi_data.get('price_volatility', 0):.1f}%",
                                'fa-wave-square',
                                '#ff6b6b',
                                -kpi_data.get('price_volatility', 0),
                                'Indicateur risque'
                            ),
                            self.create_premium_kpi_card(
                                'Qualité Données',
                                f"{kpi_data.get('data_quality', 0):.0f}%",
                                'fa-shield-alt',
                                '#4ecdc4',
                                kpi_data.get('data_quality', 0),
                                'Taux de complétion'
                            ),
                            self.create_premium_kpi_card(
                                'Sentiment',
                                f"{kpi_data.get('sentiment_score', 0):+.0f}",
                                'fa-smile',
                                '#95e77e',
                                kpi_data.get('sentiment_score', 0),
                                'Analyse descriptions'
                            )
                        ], className='kpi-grid')
                    ], className='container'),
                    
                    # Advanced charts grid
                    html.Section([
                        html.Div([
                            # Treemap
                            html.Div([
                                html.Div([
                                    html.H3('Répartition du Marché', className='chart-title'),
                                    dcc.Graph(
                                        id='market-treemap',
                                        figure=self.get_market_treemap(),
                                        config={'displayModeBar': False},
                                        className='chart-figure'
                                    )
                                ], className='chart-container')
                            ], className='col-12 col-lg-8'),
                            
                            # 3D Surface
                            html.Div([
                                html.Div([
                                    html.H3('Analyse 3D Prix×Surface', className='chart-title'),
                                    dcc.Graph(
                                        id='price-3d',
                                        figure=self.get_3d_price_surface(),
                                        config={'displayModeBar': True},
                                        className='chart-figure'
                                    )
                                ], className='chart-container')
                            ], className='col-12 col-lg-4')
                        ], className='row mb-5'),
                        
                        # Violin + Heatmap
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.H3('Distribution des Prix', className='chart-title'),
                                    dcc.Graph(
                                        id='price-violin',
                                        figure=self.get_price_violin_plot(),
                                        config={'displayModeBar': False},
                                        className='chart-figure'
                                    )
                                ], className='chart-container')
                            ], className='col-12 col-lg-6'),
                            
                            html.Div([
                                html.Div([
                                    html.H3('Corrélation des Données', className='chart-title'),
                                    dcc.Graph(
                                        id='correlation-heatmap',
                                        figure=self.get_price_correlation_heatmap(),
                                        config={'displayModeBar': False},
                                        className='chart-figure'
                                    )
                                ], className='chart-container')
                            ], className='col-12 col-lg-6')
                        ], className='row mb-5')
                    ], className='container')
                ], className='main-wrapper')
            ], className='has-sidebar'),
            
            # Footer
            html.Footer([
                html.Div([
                    html.Div([
                        html.Div([
                            html.H5('ImmoAnalytics Premium'),
                            html.P('Plateforme d\'analytics immobilière leader au Sénégal')
                        ], className='footer-brand'),
                        html.Div([
                            html.A('À propos', href='#'),
                            html.A('Documentation', href='#'),
                            html.A('API', href='#'),
                            html.A('Support', href='#')
                        ], className='footer-links'),
                        html.Div([
                            html.P('© 2024 ImmoAnalytics. Tous droits réservés.'),
                            html.P('Propulsé par AI & Big Data')
                        ], className='footer-legal')
                    ], className='footer-content')
                ], className='container')
            ], className='glass-footer'),
            
            # GSAP & Scripts
            html.Script(src='https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js'),
            html.Script(src='https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js'),
            html.Script(src='/static/js/dashboard-animations.js')
            
        ], className='dashboard-root', 
        style={
            'background': 'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
            'minHeight': '100vh',
            'color': 'white'
        })
    
    def setup_callbacks(self):
        """Callbacks avec animations"""
        @callback(
            Output('loading-overlay', 'className'),
            Input('refresh-btn', 'n_clicks'),
            prevent_initial_call=True
        )
        def show_loading(n_clicks):
            if n_clicks:
                return 'loading-overlay show'
            return 'loading-overlay'
        
        @callback(
            Output('market-treemap', 'figure'),
            Output('price-violin', 'figure'),
            Output('loading-overlay', 'className'),
            Input('refresh-btn', 'n_clicks'),
            prevent_initial_call=True
        )
        def refresh_dashboard(n_clicks):
            if n_clicks:
                return self.get_market_treemap(), self.get_price_violin_plot(), 'loading-overlay'
            raise dash.exceptions.PreventUpdate

# Factory function
def create_modern_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    dashboard = ModernMainDashboard(
        server=server,
        routes_pathname_prefix=routes_pathname_prefix,
        requests_pathname_prefix=requests_pathname_prefix
    )
    return dashboard.app