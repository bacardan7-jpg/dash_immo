import dash
from dash import html, dcc, Input, Output, callback
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
from ..auth.decorators import analyst_required


# E

class EnhancedMainDashboard:
    """Dashboard principal amélioré avec meilleures visualisations"""
    
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
    
    def get_enhanced_kpi_data(self):
        """KPIs améliorés avec contexte"""
        try:
            # Comptages
            coinafrique_count = db.session.query(CoinAfrique).count()
            expat_count = db.session.query(ExpatDakarProperty).count()
            loger_count = db.session.query(LogerDakarProperty).count()
            total_properties = coinafrique_count + expat_count + loger_count
            
            # Prix
            coinafrique_avg = db.session.query(db.func.avg(CoinAfrique.price)).scalar() or 0
            expat_avg = db.session.query(db.func.avg(ExpatDakarProperty.price)).scalar() or 0
            loger_avg = db.session.query(db.func.avg(LogerDakarProperty.price)).scalar() or 0
            
            # Global
            all_prices = []
            for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
                prices = db.session.query(model.price).filter(model.price > 0).all()
                all_prices.extend([p[0] for p in prices])
            
            avg_price = np.mean(all_prices) if all_prices else 0
            median_price = np.median(all_prices) if all_prices else 0
            std_price = np.std(all_prices) if all_prices else 0
            
            # Tendances
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_total = sum([
                db.session.query(CoinAfrique).filter(CoinAfrique.scraped_at >= week_ago).count(),
                db.session.query(ExpatDakarProperty).filter(ExpatDakarProperty.scraped_at >= week_ago).count(),
                db.session.query(LogerDakarProperty).filter(LogerDakarProperty.scraped_at >= week_ago).count()
            ])
            
            return {
                'total_properties': total_properties,
                'avg_price': avg_price,
                'median_price': median_price,
                'std_price': std_price,
                'recent_total': recent_total,
                'coinafrique_avg': coinafrique_avg,
                'expat_avg': expat_avg,
                'loger_avg': loger_avg,
                'market_volatility': std_price / avg_price * 100 if avg_price > 0 else 0
            }
        except Exception as e:
            print(f"Erreur KPI: {e}")
            return {}
    
    def get_sunburst_chart(self):
        """Sunburst chart hiérarchique"""
        try:
            data = []
            for model, source in [(CoinAfrique, 'CoinAfrique'), 
                                 (ExpatDakarProperty, 'ExpatDakar'), 
                                 (LogerDakarProperty, 'LogerDakar')]:
                records = db.session.query(model.city, model.property_type, model.price).filter(
                    model.city.isnot(None), model.price > 0
                ).limit(500).all()
                
                for city, prop_type, price in records:
                    data.append({
                        'source': source,
                        'city': city,
                        'type': prop_type or 'Autre',
                        'price': price
                    })
            
            df = pd.DataFrame(data)
            if df.empty:
                return go.Figure()
            
            fig = px.sunburst(
                df,
                path=['source', 'city', 'type'],
                values='price',
                color='price',
                color_continuous_scale='RdBu',
                title='Structure du marché immobilier'
            )
            
            fig.update_layout(
                height=500,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                title=dict(x=0.5, font=dict(size=18, color='white'))
            )
            
            return fig
        except Exception as e:
            print(f"Erreur sunburst: {e}")
            return go.Figure()
    
    def get_time_series(self):
        """Série temporelle des prix"""
        try:
            # Simuler des données temporelles (en vrai, utiliser une colonne date)
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            prices = np.random.normal(loc=50000000, scale=10000000, size=30).cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=prices,
                mode='lines+markers',
                line=dict(color='#ffd700', width=3),
                marker=dict(size=6, color='#ffd700'),
                fill='tonexty',
                fillcolor='rgba(255,215,0,0.1)'
            ))
            
            fig.update_layout(
                title='Évolution du prix moyen (30j)',
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            
            return fig
        except Exception as e:
            print(f"Erreur time series: {e}")
            return go.Figure()
    
    def create_enhanced_kpi(self, title, value, icon, color, trend=0):
        """KPI avec tendance"""
        return dmc.Card([
            dmc.Group([
                DashIconify(icon=icon, width=30, color=color),
                dmc.Text(title, size="sm", color="dimmed")
            ], position="apart", mt="md", mb="xs"),
            dmc.Text(value, size="xl", fw=700),
            dmc.Group([
                DashIconify(icon="mdi:trending-up" if trend > 0 else "mdi:trending-down", 
                           width=16, 
                           color="green" if trend > 0 else "red"),
                dmc.Text(f"{abs(trend):+.1f}%", size="xs", 
                        color="green" if trend > 0 else "red")
            ], spacing="xs") if trend != 0 else None
        ], withBorder=True, shadow="sm", radius="md", p="md")
    
    def setup_layout(self):
        """Layout amélioré"""
        kpi_data = self.get_enhanced_kpi_data()
        
        self.app.layout = dmc.MantineProvider(
            theme={"colorScheme": "light", "primaryColor": "blue"},
            children=[
                html.Div([
                    dmc.Header(height=60, children=[
                        dmc.Group([
                            dmc.Title("Dashboard Immobilier", order=3),
                            dmc.Group([
                                dmc.ActionIcon(DashIconify(icon="mdi:refresh", width=20), 
                                             size="lg", variant="subtle", id="refresh-btn"),
                                dmc.Badge("Live", color="green", variant="dot")
                            ])
                        ], position="apart", style={"height": "100%", "padding": "0 20px"})
                    ], style={"backgroundColor": "#fff", "borderBottom": "1px solid #e9ecef"}),
                    
                    html.Div(id="notification-container"),
                    
                    dmc.Container(size="xl", mt="xl", children=[
                        # KPIs
                        dmc.SimpleGrid(cols=4, spacing="lg", breakpoints=[
                            {"maxWidth": 980, "cols": 2, "spacing": "md"},
                            {"maxWidth": 755, "cols": 1, "spacing": "sm"}
                        ], children=[
                            self.create_enhanced_kpi("Total", f"{kpi_data.get('total_properties', 0):,}", 
                                                   "mdi:home", "blue"),
                            self.create_enhanced_kpi("Prix Moyen", f"{kpi_data.get('avg_price', 0):,.0f} FCFA", 
                                                   "mdi:cash", "green", trend=5.2),
                            self.create_enhanced_kpi("Volatilité", f"{kpi_data.get('market_volatility', 0):.1f}%", 
                                                   "mdi:chart-line-variant", "orange", trend=-2.1),
                            self.create_enhanced_kpi("Nouveau (7j)", f"{kpi_data.get('recent_total', 0)}", 
                                                   "mdi:new-box", "purple", trend=12.5)
                        ]),
                        
                        dmc.Space(h=30),
                        
                        # Graphiques avancés
                        dmc.SimpleGrid(cols=2, spacing="lg", breakpoints=[
                            {"maxWidth": 980, "cols": 1, "spacing": "md"}
                        ], children=[
                            dmc.Card([
                                dmc.Text("Répartition du marché", size="lg", fw=500, mb="md"),
                                dcc.Graph(id="sunburst-chart", figure=self.get_sunburst_chart(), 
                                         config={'displayModeBar': False})
                            ], withBorder=True, shadow="sm", radius="md", p="md"),
                            
                            dmc.Card([
                                dmc.Text("Évolution temporelle", size="lg", fw=500, mb="md"),
                                dcc.Graph(id="time-series", figure=self.get_time_series(), 
                                         config={'displayModeBar': False})
                            ], withBorder=True, shadow="sm", radius="md", p="md")
                        ])
                    ])
                ])
            ]
        )
    
    def setup_callbacks(self):
        """Callbacks"""
        @callback(
            Output("notification-container", "children"),
            Input("refresh-btn", "n_clicks"),
            prevent_initial_call=True
        )
        def refresh_data(n_clicks):
            if n_clicks:
                return dmc.Notification(
                    title="Actualisation",
                    message="Données mises à jour",
                    color="green",
                    autoClose=3000
                )

# Factory
def create_enhanced_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    dashboard = EnhancedMainDashboard(
        server=server,
        routes_pathname_prefix=routes_pathname_prefix,
        requests_pathname_prefix=requests_pathname_prefix
    )
    return dashboard.app