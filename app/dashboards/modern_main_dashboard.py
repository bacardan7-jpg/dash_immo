import dash
from dash import html, dcc, Input, Output, callback
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from ..database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
from ..auth.decorators import analyst_required
import json

class ModernMainDashboard:
    """Dashboard principal avec design moderne et animations GSAP"""
    
    def __init__(self, server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix
        )

        # If a Flask server is provided, build the layout inside its application context
        # to allow DB access (db.session / models) during layout construction.
        if server:
            with server.app_context():
                self.setup_layout()
                self.setup_callbacks()
        else:
            # Defer layout setup if no server is passed (e.g. standalone usage)
            self._layout_setup_deferred = True
    
    def get_kpi_data(self):
        """Récupérer les données KPI"""
        try:
            # Compter les propriétés par source
            coinafrique_count = db.session.query(CoinAfrique).count()
            expat_count = db.session.query(ExpatDakarProperty).count()
            loger_count = db.session.query(LogerDakarProperty).count()
            total_properties = coinafrique_count + expat_count + loger_count
            
            # Prix moyen par source
            coinafrique_avg = db.session.query(db.func.avg(CoinAfrique.price)).scalar() or 0
            expat_avg = db.session.query(db.func.avg(ExpatDakarProperty.price)).scalar() or 0
            loger_avg = db.session.query(db.func.avg(LogerDakarProperty.price)).scalar() or 0
            
            # Prix global
            all_prices = []
            for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
                prices = db.session.query(model.price).all()
                all_prices.extend([p[0] for p in prices])
            
            avg_price = sum(all_prices) / len(all_prices) if all_prices else 0
            median_price = sorted(all_prices)[len(all_prices)//2] if all_prices else 0
            
            # Propriétés ajoutées récemment (7 derniers jours)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_coinafrique = db.session.query(CoinAfrique).filter(
                CoinAfrique.scraped_at >= week_ago
            ).count()
            recent_expat = db.session.query(ExpatDakarProperty).filter(
                ExpatDakarProperty.scraped_at >= week_ago
            ).count()
            recent_loger = db.session.query(LogerDakarProperty).filter(
                LogerDakarProperty.scraped_at >= week_ago
            ).count()
            recent_total = recent_coinafrique + recent_expat + recent_loger
            
            return {
                'total_properties': total_properties,
                'coinafrique_count': coinafrique_count,
                'expat_count': expat_count,
                'loger_count': loger_count,
                'avg_price': avg_price,
                'median_price': median_price,
                'coinafrique_avg': coinafrique_avg,
                'expat_avg': expat_avg,
                'loger_avg': loger_avg,
                'recent_total': recent_total,
                'recent_coinafrique': recent_coinafrique,
                'recent_expat': recent_expat,
                'recent_loger': recent_loger
            }
        except Exception as e:
            print(f"Erreur lors de la récupération des KPIs: {e}")
            return {}
    
    def create_modern_kpi_card(self, title, value, icon, color="gold", trend="", description=""):
        """Créer une carte KPI moderne avec animation"""
        return html.Div([
            html.Div([
                html.Div([
                    html.I(className=f"fas {icon}", style={
                        "fontSize": "2.5rem",
                        "color": color,
                        "marginBottom": "1rem",
                        "animation": "pulse 2s infinite"
                    }),
                    html.H3(title, style={
                        "fontSize": "1.1rem",
                        "fontWeight": "600",
                        "color": "rgba(255, 255, 255, 0.8)",
                        "marginBottom": "0.5rem"
                    })
                ], style={"textAlign": "center"}),
                
                html.Div([
                    html.Div(value, className="kpi-value", style={
                        "fontSize": "2.5rem",
                        "fontWeight": "800",
                        "background": f"linear-gradient(45deg, {color}, #ffed4e)",
                        "WebkitBackgroundClip": "text",
                        "WebkitTextFillColor": "transparent",
                        "backgroundClip": "text",
                        "textAlign": "center",
                        "marginBottom": "0.5rem"
                    }),
                    html.P(trend, style={
                        "fontSize": "0.9rem",
                        "color": "rgba(255, 255, 255, 0.7)",
                        "textAlign": "center",
                        "marginBottom": "0.5rem"
                    }) if trend else None,
                    html.P(description, style={
                        "fontSize": "0.8rem",
                        "color": "rgba(255, 255, 255, 0.6)",
                        "textAlign": "center"
                    }) if description else None
                ])
            ], style={
                "padding": "2rem",
                "height": "100%",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "space-between"
            })
        ], style={
            "background": "rgba(255, 255, 255, 0.1)",
            "backdropFilter": "blur(20px)",
            "border": "1px solid rgba(255, 255, 255, 0.2)",
            "borderRadius": "16px",
            "boxShadow": "0 8px 32px 0 rgba(31, 38, 135, 0.37)",
            "height": "280px",
            "transition": "all 0.3s ease",
            "cursor": "pointer"
        }, className="kpi-card-hover")
    
    def get_price_distribution_chart(self):
        """Créer le graphique de distribution des prix moderne"""
        try:
            # Collecter toutes les données de prix
            price_data = []
            
            # CoinAfrique
            coinafrique_data = db.session.query(CoinAfrique.price, CoinAfrique.property_type, CoinAfrique.city).all()
            for price, prop_type, city in coinafrique_data:
                price_data.append({
                    'price': price,
                    'source': 'CoinAfrique',
                    'type': prop_type,
                    'city': city
                })
            
            # ExpatDakar
            expat_data = db.session.query(ExpatDakarProperty.price, ExpatDakarProperty.property_type, ExpatDakarProperty.city).all()
            for price, prop_type, city in expat_data:
                price_data.append({
                    'price': price,
                    'source': 'ExpatDakar',
                    'type': prop_type,
                    'city': city
                })
            
            # LogerDakar
            loger_data = db.session.query(LogerDakarProperty.price, LogerDakarProperty.property_type, LogerDakarProperty.city).all()
            for price, prop_type, city in loger_data:
                price_data.append({
                    'price': price,
                    'source': 'LogerDakar',
                    'type': prop_type,
                    'city': city
                })
            
            if not price_data:
                return go.Figure()
            
            df = pd.DataFrame(price_data)
            
            # Créer le graphique de distribution avec style moderne
            fig = px.histogram(
                df, 
                x='price', 
                color='source',
                nbins=50,
                title='Distribution des prix par plateforme',
                labels={'price': 'Prix (FCFA)', 'count': 'Nombre de propriétés'},
                color_discrete_map={
                    'CoinAfrique': '#667eea',
                    'ExpatDakar': '#764ba2',
                    'LogerDakar': '#ffd700'
                }
            )
            
            # Modern styling
            fig.update_layout(
                height=400,
                showlegend=True,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', family='Inter'),
                title=dict(
                    font=dict(size=18, color='white'),
                    x=0.5,
                    xanchor='center'
                ),
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    tickcolor='rgba(255,255,255,0.3)',
                    title_font=dict(color='white')
                ),
                yaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    tickcolor='rgba(255,255,255,0.3)',
                    title_font=dict(color='white')
                ),
                legend=dict(
                    bgcolor='rgba(255,255,255,0.1)',
                    bordercolor='rgba(255,255,255,0.2)',
                    borderwidth=1
                )
            )
            
            return fig
        
        except Exception as e:
            print(f"Erreur lors de la création du graphique de distribution: {e}")
            return go.Figure()
    
    def get_property_type_chart(self):
        """Créer le graphique des types de propriétés moderne"""
        try:
            type_counts = {}
            
            # Compter les types pour chaque source
            for model, source_name in [
                (CoinAfrique, 'CoinAfrique'),
                (ExpatDakarProperty, 'ExpatDakar'),
                (LogerDakarProperty, 'LogerDakar')
            ]:
                types = db.session.query(model.property_type, db.func.count(model.id)).group_by(model.property_type).all()
                for prop_type, count in types:
                    if prop_type not in type_counts:
                        type_counts[prop_type] = {}
                    type_counts[prop_type][source_name] = count
            
            if not type_counts:
                return go.Figure()
            
            # Préparer les données pour le graphique
            property_types = list(type_counts.keys())
            sources = ['CoinAfrique', 'ExpatDakar', 'LogerDakar']
            
            data = []
            colors = ['#667eea', '#764ba2', '#ffd700']
            
            for i, source in enumerate(sources):
                counts = [type_counts.get(pt, {}).get(source, 0) for pt in property_types]
                data.append(go.Bar(
                    name=source,
                    x=property_types,
                    y=counts,
                    marker_color=colors[i],
                    marker_line=dict(width=0),
                    hovertemplate='<b>%{x}</b><br>%{y} propriétés<extra></extra>'
                ))
            
            fig = go.Figure(data=data)
            fig.update_layout(
                title=dict(
                    text='Types de propriétés par plateforme',
                    font=dict(size=18, color='white'),
                    x=0.5,
                    xanchor='center'
                ),
                xaxis_title='Type de propriété',
                yaxis_title='Nombre de propriétés',
                barmode='group',
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', family='Inter'),
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    tickcolor='rgba(255,255,255,0.3)',
                    title_font=dict(color='white')
                ),
                yaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    tickcolor='rgba(255,255,255,0.3)',
                    title_font=dict(color='white')
                ),
                legend=dict(
                    bgcolor='rgba(255,255,255,0.1)',
                    bordercolor='rgba(255,255,255,0.2)',
                    borderwidth=1
                )
            )
            
            return fig
        
        except Exception as e:
            print(f"Erreur lors de la création du graphique des types: {e}")
            return go.Figure()
    
    def setup_layout(self):
        """Configurer la mise en page moderne du dashboard"""
        kpi_data = self.get_kpi_data()
        
        self.app.layout = html.Div([
            # Animated background
            html.Div(className='animated-bg'),
            
            # Navigation header
            html.Nav([
                html.Div([
                    html.Div([
                        html.A([
                            html.I(className="fas fa-home", style={"marginRight": "0.5rem"}),
                            "ImmoAnalytics"
                        ], href="/", className="nav-brand"),
                        
                        html.Ul([
                            html.Li(html.A("Dashboard", href="/dashboard", className="nav-link active")),
                            html.Li(html.A("Analyse", href="/analytics", className="nav-link")),
                            html.Li(html.A("Carte", href="/map", className="nav-link")),
                            html.Li(html.A("Admin", href="/admin", className="nav-link"))
                        ], className="nav-links")
                    ], style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "width": "100%"
                    })
                ], className="container")
            ], className="glass-nav"),
            
            # Notification container
            html.Div(id="notification-container"),
            
            # Main content
            html.Div([
                html.Div([
                    # Header section
                    html.Div([
                        html.H1("Tableau de Bord Immobilier", style={
                            "fontSize": "2.5rem",
                            "fontWeight": "700",
                            "marginBottom": "0.5rem",
                            "background": "linear-gradient(45deg, #ffd700, #ffed4e)",
                            "WebkitBackgroundClip": "text",
                            "WebkitTextFillColor": "transparent",
                            "backgroundClip": "text"
                        }),
                        html.Div([
                            html.Span("Live", className="badge bg-success"),
                            html.Button([
                                html.I(className="fas fa-sync-alt"),
                                " Actualiser"
                            ], id="refresh-btn", className="glass-button", style={"marginLeft": "1rem"})
                        ], style={"display": "flex", "alignItems": "center", "gap": "1rem"})
                    ], style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "marginBottom": "3rem",
                        "paddingTop": "2rem"
                    }),
                    
                    # KPI Cards Section
                    html.Div([
                        self.create_modern_kpi_card(
                            "Total Propriétés", 
                            f"{kpi_data.get('total_properties', 0):,}",
                            "fa-home",
                            "#ffd700",
                            f"+{kpi_data.get('recent_total', 0)} cette semaine",
                            "Propriétés répertoriées"
                        ),
                        self.create_modern_kpi_card(
                            "Prix Moyen",
                            f"{kpi_data.get('avg_price', 0):,.0f} FCFA",
                            "fa-chart-line",
                            "#667eea",
                            "Prix moyen du marché",
                            "Basé sur toutes les sources"
                        ),
                        self.create_modern_kpi_card(
                            "Prix Médian",
                            f"{kpi_data.get('median_price', 0):,.0f} FCFA",
                            "fa-balance-scale",
                            "#764ba2",
                            "Médiane du marché",
                            "Valeur centrale"
                        ),
                        self.create_modern_kpi_card(
                            "Nouveautés (7j)",
                            f"{kpi_data.get('recent_total', 0)}",
                            "fa-calendar-plus",
                            "#28a745",
                            "Cette semaine",
                            "Propriétés récentes"
                        )
                    ], className="kpi-grid"),
                    
                    # Charts Section
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H3("Distribution des Prix", style={
                                    "fontSize": "1.4rem",
                                    "fontWeight": "600",
                                    "color": "white",
                                    "marginBottom": "1rem"
                                }),
                                dcc.Graph(
                                    id="price-distribution-chart",
                                    figure=self.get_price_distribution_chart(),
                                    config={
                                        'displayModeBar': False,
                                        'responsive': True
                                    },
                                    style={"height": "400px"}
                                )
                            ], className="chart-container")
                        ], className="col-lg-6 mb-4"),
                        
                        html.Div([
                            html.Div([
                                html.H3("Types de Propriétés", style={
                                    "fontSize": "1.4rem",
                                    "fontWeight": "600",
                                    "color": "white",
                                    "marginBottom": "1rem"
                                }),
                                dcc.Graph(
                                    id="property-type-chart",
                                    figure=self.get_property_type_chart(),
                                    config={
                                        'displayModeBar': False,
                                        'responsive': True
                                    },
                                    style={"height": "400px"}
                                )
                            ], className="chart-container")
                        ], className="col-lg-6 mb-4")
                    ], className="row"),
                    
                    # Table Section
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H3("Vue d'ensemble par source", style={
                                    "fontSize": "1.6rem",
                                    "fontWeight": "700",
                                    "color": "white",
                                    "marginBottom": "2rem",
                                    "textAlign": "center"
                                }),
                                html.Div([
                                    html.Div([
                                        html.H4("CoinAfrique", style={
                                            "color": "#667eea",
                                            "fontSize": "1.2rem",
                                            "marginBottom": "0.5rem"
                                        }),
                                        html.P(f"{kpi_data.get('coinafrique_count', 0):,} propriétés", style={"fontSize": "2rem", "fontWeight": "700", "color": "#667eea", "marginBottom": "0.5rem"}),
                                        html.P(f"Prix moyen: {kpi_data.get('coinafrique_avg', 0):,.0f} FCFA", style={"color": "rgba(255,255,255,0.8)"}),
                                        html.P(f"Nouveau: {kpi_data.get('recent_coinafrique', 0)}", style={"color": "rgba(255,255,255,0.6)", "fontSize": "0.9rem"})
                                    ], style={
                                        "background": "rgba(102, 126, 234, 0.1)",
                                        "border": "1px solid rgba(102, 126, 234, 0.3)",
                                        "borderRadius": "12px",
                                        "padding": "1.5rem",
                                        "textAlign": "center"
                                    }),
                                    
                                    html.Div([
                                        html.H4("ExpatDakar", style={
                                            "color": "#764ba2",
                                            "fontSize": "1.2rem",
                                            "marginBottom": "0.5rem"
                                        }),
                                        html.P(f"{kpi_data.get('expat_count', 0):,} propriétés", style={"fontSize": "2rem", "fontWeight": "700", "color": "#764ba2", "marginBottom": "0.5rem"}),
                                        html.P(f"Prix moyen: {kpi_data.get('expat_avg', 0):,.0f} FCFA", style={"color": "rgba(255,255,255,0.8)"}),
                                        html.P(f"Nouveau: {kpi_data.get('recent_expat', 0)}", style={"color": "rgba(255,255,255,0.6)", "fontSize": "0.9rem"})
                                    ], style={
                                        "background": "rgba(118, 75, 162, 0.1)",
                                        "border": "1px solid rgba(118, 75, 162, 0.3)",
                                        "borderRadius": "12px",
                                        "padding": "1.5rem",
                                        "textAlign": "center"
                                    }),
                                    
                                    html.Div([
                                        html.H4("LogerDakar", style={
                                            "color": "#ffd700",
                                            "fontSize": "1.2rem",
                                            "marginBottom": "0.5rem"
                                        }),
                                        html.P(f"{kpi_data.get('loger_count', 0):,} propriétés", style={"fontSize": "2rem", "fontWeight": "700", "color": "#ffd700", "marginBottom": "0.5rem"}),
                                        html.P(f"Prix moyen: {kpi_data.get('loger_avg', 0):,.0f} FCFA", style={"color": "rgba(255,255,255,0.8)"}),
                                        html.P(f"Nouveau: {kpi_data.get('recent_loger', 0)}", style={"color": "rgba(255,255,255,0.6)", "fontSize": "0.9rem"})
                                    ], style={
                                        "background": "rgba(255, 215, 0, 0.1)",
                                        "border": "1px solid rgba(255, 215, 0, 0.3)",
                                        "borderRadius": "12px",
                                        "padding": "1.5rem",
                                        "textAlign": "center"
                                    })
                                ], style={
                                    "display": "grid",
                                    "gridTemplateColumns": "repeat(auto-fit, minmax(250px, 1fr))",
                                    "gap": "1.5rem",
                                    "marginTop": "2rem"
                                })
                            ], className="glass-card", style={"padding": "2rem"})
                        ], className="col-12")
                    ], className="row mb-5")
                ], className="container")
            ], style={"minHeight": "100vh", "paddingBottom": "4rem"})
        ], style={
            "background": "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)",
            "minHeight": "100vh",
            "color": "white",
            "fontFamily": "Inter, sans-serif"
        })
    
    def setup_callbacks(self):
        """Configurer les callbacks avec animations"""
        @callback(
            Output("notification-container", "children"),
            Input("refresh-btn", "n_clicks"),
            prevent_initial_call=True
        )
        def refresh_data(n_clicks):
            if n_clicks:
                # Actualiser les données
                return html.Div([
                    html.Div([
                        html.I(className="fas fa-check-circle", style={"color": "#28a745", "marginRight": "0.5rem"}),
                        "Données actualisées avec succès !"
                    ], className="notification-content")
                ], className="notification notification-success show")
            return ""
        
        # Hover animations for KPI cards
        @callback(
            Output({"type": "kpi-card", "index": "all"}, "style"),
            Input({"type": "kpi-card", "index": "all"}, "n_clicks")
        )
        def animate_kpi_card_hover(n_clicks):
            if n_clicks:
                return {
                    "background": "rgba(255, 255, 255, 0.15)",
                    "transform": "translateY(-5px) scale(1.02)",
                    "boxShadow": "0 15px 35px rgba(0, 0, 0, 0.3)"
                }
            return {
                "background": "rgba(255, 255, 255, 0.1)",
                "transform": "translateY(0) scale(1)",
                "boxShadow": "0 8px 32px 0 rgba(31, 38, 135, 0.37)"
            }

# Create and export the dashboard
def create_modern_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    """Factory function to create the modern dashboard"""
    dashboard = ModernMainDashboard(
        server=server,
        routes_pathname_prefix=routes_pathname_prefix,
        requests_pathname_prefix=requests_pathname_prefix
    )
    return dashboard.app

if __name__ == "__main__":
    dashboard = ModernMainDashboard()
    dashboard.app.run_server(debug=True, port=8050)