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

class MainDashboard:
    """Dashboard principal avec KPIs et aperçu des données"""
    
    def __init__(self, server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix
        )

        # Build layout inside Flask application context when server is provided
        if server:
            with server.app_context():
                self.setup_layout()
                self.setup_callbacks()
        else:
            # Defer layout setup if no server is passed
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
    
    def create_kpi_card(self, title, value, icon, color="blue", description=""):
        """Créer une carte KPI"""
        return dmc.Card(
            children=[
                dmc.CardSection(
                    dmc.Group(
                        children=[
                            DashIconify(icon=icon, width=30, color=color),
                            dmc.Text(title, size="sm", color="dimmed")
                        ],
                        position="apart",
                        mt="md",
                        mb="xs",
                    )
                ),
                dmc.Text(value, size="xl", fw=700),
                dmc.Text(description, size="xs", color="dimmed", mt=5)
            ],
            withBorder=True,
            shadow="sm",
            radius="md",
            p="md"
        )
    
    def get_price_distribution_chart(self):
        """Créer le graphique de distribution des prix"""
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
            
            # Créer le graphique de distribution
            fig = px.histogram(
                df, 
                x='price', 
                color='source',
                nbins=50,
                title='Distribution des prix par plateforme',
                labels={'price': 'Prix (FCFA)', 'count': 'Nombre de propriétés'},
                color_discrete_map={
                    'CoinAfrique': '#1f77b4',
                    'ExpatDakar': '#ff7f0e',
                    'LogerDakar': '#2ca02c'
                }
            )
            
            fig.update_layout(
                height=400,
                showlegend=True,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            return fig
        
        except Exception as e:
            print(f"Erreur lors de la création du graphique de distribution: {e}")
            return go.Figure()
    
    def get_property_type_chart(self):
        """Créer le graphique des types de propriétés"""
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
            for source in sources:
                counts = [type_counts.get(pt, {}).get(source, 0) for pt in property_types]
                data.append(go.Bar(name=source, x=property_types, y=counts))
            
            fig = go.Figure(data=data)
            fig.update_layout(
                title='Types de propriétés par plateforme',
                xaxis_title='Type de propriété',
                yaxis_title='Nombre de propriétés',
                barmode='group',
                height=400,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            return fig
        
        except Exception as e:
            print(f"Erreur lors de la création du graphique des types: {e}")
            return go.Figure()
    
    def setup_layout(self):
        """Configurer la mise en page du dashboard"""
        kpi_data = self.get_kpi_data()
        
        self.app.layout = dmc.MantineProvider(
            theme={
                "colorScheme": "light",
                "primaryColor": "blue",
                "fontFamily": "Inter, sans-serif"
            },
            children=[
                html.Div([
                    # En-tête
                    dmc.Header(
                        height=60,
                        children=[
                            dmc.Group(
                                children=[
                                    dmc.Title("Tableau de Bord Immobilier", order=3),
                                    dmc.Group([
                                        dmc.ActionIcon(
                                            DashIconify(icon="mdi:refresh", width=20),
                                            size="lg",
                                            variant="subtle",
                                            id="refresh-btn"
                                        ),
                                        dmc.Badge("Live", color="green", variant="dot")
                                    ])
                                ],
                                position="apart",
                                style={"height": "100%", "padding": "0 20px"}
                            )
                        ],
                        style={"backgroundColor": "#fff", "borderBottom": "1px solid #e9ecef"}
                    ),
                    
                    # Zone de notification
                    html.Div(id="notification-container"),
                    
                    # Contenu principal
                    dmc.Container(
                        size="xl",
                        mt="xl",
                        children=[
                            # Section KPIs
                            dmc.SimpleGrid(
                                cols=4,
                                spacing="lg",
                                breakpoints=[
                                    {"maxWidth": 980, "cols": 2, "spacing": "md"},
                                    {"maxWidth": 755, "cols": 1, "spacing": "sm"}
                                ],
                                children=[
                                    self.create_kpi_card(
                                        "Total Propriétés", 
                                        f"{kpi_data.get('total_properties', 0):,}",
                                        "mdi:home-city",
                                        "blue"
                                    ),
                                    self.create_kpi_card(
                                        "Prix Moyen",
                                        f"{kpi_data.get('avg_price', 0):,.0f} FCFA",
                                        "mdi:cash-multiple",
                                        "green"
                                    ),
                                    self.create_kpi_card(
                                        "Prix Médian",
                                        f"{kpi_data.get('median_price', 0):,.0f} FCFA",
                                        "mdi:chart-line",
                                        "orange"
                                    ),
                                    self.create_kpi_card(
                                        "Nouveau (7j)",
                                        f"{kpi_data.get('recent_total', 0)}",
                                        "mdi:new-box",
                                        "purple"
                                    )
                                ]
                            ),
                            
                            dmc.Space(h=30),
                            
                            # Graphiques
                            dmc.SimpleGrid(
                                cols=2,
                                spacing="lg",
                                breakpoints=[
                                    {"maxWidth": 980, "cols": 1, "spacing": "md"}
                                ],
                                children=[
                                    dmc.Card(
                                        children=[
                                            dmc.Text("Distribution des Prix", size="lg", fw=500, mb="md"),
                                            dcc.Graph(
                                                id="price-distribution-chart",
                                                figure=self.get_price_distribution_chart(),
                                                config={'displayModeBar': False}
                                            )
                                        ],
                                        withBorder=True,
                                        shadow="sm",
                                        radius="md",
                                        p="md"
                                    ),
                                    dmc.Card(
                                        children=[
                                            dmc.Text("Types de Propriétés", size="lg", fw=500, mb="md"),
                                            dcc.Graph(
                                                id="property-type-chart",
                                                figure=self.get_property_type_chart(),
                                                config={'displayModeBar': False}
                                            )
                                        ],
                                        withBorder=True,
                                        shadow="sm",
                                        radius="md",
                                        p="md"
                                    )
                                ]
                            ),
                            
                            dmc.Space(h=30),
                            
                            # Tableau récapitulatif par source
                            dmc.Card(
                                children=[
                                    dmc.Text("Répartition par Source", size="lg", fw=500, mb="md"),
                                    dmc.Table(
                                        children=[
                                            html.Thead(
                                                html.Tr([
                                                    html.Th("Source"),
                                                    html.Th("Nombre de propriétés"),
                                                    html.Th("Prix moyen"),
                                                    html.Th("Nouveautés (7j)")
                                                ])
                                            ),
                                            html.Tbody([
                                                html.Tr([
                                                    html.Td("CoinAfrique"),
                                                    html.Td(f"{kpi_data.get('coinafrique_count', 0):,}"),
                                                    html.Td(f"{kpi_data.get('coinafrique_avg', 0):,.0f} FCFA"),
                                                    html.Td(f"{kpi_data.get('recent_coinafrique', 0)}")
                                                ]),
                                                html.Tr([
                                                    html.Td("ExpatDakar"),
                                                    html.Td(f"{kpi_data.get('expat_count', 0):,}"),
                                                    html.Td(f"{kpi_data.get('expat_avg', 0):,.0f} FCFA"),
                                                    html.Td(f"{kpi_data.get('recent_expat', 0)}")
                                                ]),
                                                html.Tr([
                                                    html.Td("LogerDakar"),
                                                    html.Td(f"{kpi_data.get('loger_count', 0):,}"),
                                                    html.Td(f"{kpi_data.get('loger_avg', 0):,.0f} FCFA"),
                                                    html.Td(f"{kpi_data.get('recent_loger', 0)}")
                                                ])
                                            ])
                                        ]
                                    )
                                ],
                                withBorder=True,
                                shadow="sm",
                                radius="md",
                                p="md"
                            )
                        ]
                    )
                ])
            ]
        )
    
    def setup_callbacks(self):
        """Configurer les callbacks"""
        @callback(
            Output("notification-container", "children"),
            Input("refresh-btn", "n_clicks"),
            prevent_initial_call=True
        )
        def refresh_data(n_clicks):
            if n_clicks:
                # Actualiser les données
                return dmc.Notification(
                    title="Données actualisées",
                    message="Les données ont été mises à jour avec succès",
                    color="green",
                    action="show",
                    autoClose=3000
                )
            return ""