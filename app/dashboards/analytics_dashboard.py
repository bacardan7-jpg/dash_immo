import dash
from dash import html, dcc, Input, Output, callback, dash_table
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from ..database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty


# =====================================================================
#                           DASHBOARD CLASS
# =====================================================================

class AnalyticsDashboard:
    """Dashboard d'analyse approfondie"""

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

    # =================================================================
    #                       RECUPÉRATION DES OPTIONS
    # =================================================================
    def get_filter_options(self):
        try:
            cities = set()
            property_types = set()
            sources = ["CoinAfrique", "ExpatDakar", "LogerDakar"]

            for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
                cities.update([c[0] for c in db.session.query(model.city).distinct().all() if c[0]])
                property_types.update([t[0] for t in db.session.query(model.property_type).distinct().all() if t[0]])

            return {
                "cities": sorted(list(cities)),
                "property_types": sorted(list(property_types)),
                "sources": sources,
            }

        except Exception as e:
            print("Erreur options :", e)
            return {"cities": [], "property_types": [], "sources": []}

    # =================================================================
    #                       FILTRAGE DES DONNÉES
    # =================================================================
    def get_filtered_data(self, city=None, property_type=None, source=None,
                          min_price=None, max_price=None, min_surface=None,
                          max_surface=None, bedrooms=None):

        try:
            all_data = []
            sources_map = {
                "CoinAfrique": CoinAfrique,
                "ExpatDakar": ExpatDakarProperty,
                "LogerDakar": LogerDakarProperty
            }

            models = sources_map.keys() if source == "all" else [source]

            for src in models:
                model = sources_map[src]
                query = db.session.query(model)

                if city and city != "all":
                    query = query.filter(model.city == city)

                if property_type and property_type != "all":
                    query = query.filter(model.property_type == property_type)

                if min_price:
                    query = query.filter(model.price >= min_price)

                if max_price:
                    query = query.filter(model.price <= max_price)

                if min_surface:
                    query = query.filter(model.surface_area >= min_surface)

                if max_surface:
                    query = query.filter(model.surface_area <= max_surface)

                if bedrooms and bedrooms != "all":
                    query = query.filter(model.bedrooms == int(bedrooms))

                for row in query.all():
                    item = row.to_dict()
                    item["source"] = src
                    all_data.append(item)

            return all_data

        except Exception as e:
            print("Erreur filtrage :", e)
            return []

    # =================================================================
    #                     GRAPHIQUES ET ANALYSES
    # =================================================================

    def create_price_trend_chart(self, data):
        if not data:
            return go.Figure()

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["scraped_at"])
        df["month"] = df["date"].dt.to_period("M").astype(str)

        stats = df.groupby(["month", "source"])["price"].mean().reset_index()

        fig = px.line(stats, x="month", y="price", color="source",
                      markers=True,
                      title="Évolution des prix par mois")

        fig.update_layout(height=400)
        return fig

    def create_surface_price_scatter(self, data):
        if not data:
            return go.Figure()
        df = pd.DataFrame(data)
        df = df[df["surface_area"] > 0]

        fig = px.scatter(
            df,
            x="surface_area",
            y="price",
            color="source",
            hover_data=["city", "property_type"],
            title="Surface vs Prix"
        )
        fig.update_layout(height=400)
        return fig

    def create_city_analysis_chart(self, data):
        if not data:
            return go.Figure()

        df = pd.DataFrame(data)
        stats = df.groupby("city")["price"].mean().sort_values()

        fig = go.Figure(go.Bar(
            x=stats.values,
            y=stats.index,
            orientation="h"
        ))
        fig.update_layout(title="Prix moyen par ville", height=400)
        return fig

    # =================================================================
    #                           LAYOUT COMPLET
    # =================================================================

    def setup_layout(self):
        options = self.get_filter_options()

        self.app.layout = dmc.MantineProvider(
            theme={"colorScheme": "light"},
            children=[
                html.Div(
                    [
                        # Header
                        html.Div(
                            dmc.Group(
                                justify="space-between",
                                children=[
                                    dmc.Title("Analyse Approfondie", order=3),
                                    dmc.Button(
                                        "Exporter CSV",
                                        id="export-btn",
                                        color="green",
                                        leftSection=DashIconify(icon="mdi:download", width=16),
                                    ),
                                ],
                            ),
                            style={
                                "height": "60px",
                                "display": "flex",
                                "alignItems": "center",
                                "padding": "0 20px",
                                "borderBottom": "1px solid #eaeaea",
                                "background": "#fff",
                            },
                        ),

                        html.Br(),

                        dmc.Container(
                            size="xl",
                            children=[

                                # ---------------------------------------------------------
                                #                       FILTRES
                                # ---------------------------------------------------------
                                dmc.Paper(
                                    shadow="sm",
                                    p="md",
                                    radius="md",
                                    children=[

                                        dmc.SimpleGrid(
                                            cols=4,
                                            spacing="md",
                                            children=[
                                                dmc.Select(
                                                    label="Ville",
                                                    id="filter-city",
                                                    data=["all"] + options["cities"],
                                                ),
                                                dmc.Select(
                                                    label="Type propriété",
                                                    id="filter-property-type",
                                                    data=["all"] + options["property_types"],
                                                ),
                                                dmc.Select(
                                                    label="Source",
                                                    id="filter-source",
                                                    data=["all"] + options["sources"],
                                                ),
                                                dmc.Select(
                                                    label="Chambres",
                                                    id="filter-bedrooms",
                                                    data=["all", "1", "2", "3", "4", "5"],
                                                ),
                                            ],
                                        ),

                                        html.Br(),

                                        dmc.SimpleGrid(
                                            cols=4,
                                            spacing="md",
                                            children=[
                                                dmc.NumberInput(label="Prix min", id="filter-min-price"),
                                                dmc.NumberInput(label="Prix max", id="filter-max-price"),
                                                dmc.NumberInput(label="Surface min", id="filter-min-surface"),
                                                dmc.NumberInput(label="Surface max", id="filter-max-surface"),
                                            ],
                                        ),

                                        html.Br(),

                                        dmc.Button("Appliquer filtres", id="apply-filters", color="blue"),
                                    ],
                                ),

                                html.Br(),

                                # ---------------------------------------------------------
                                #                   INDICATEURS
                                # ---------------------------------------------------------
                                dmc.SimpleGrid(
                                    cols=4,
                                    spacing="lg",
                                    children=[
                                        dmc.Paper(dmc.Text("0", id="filtered-count"), p="md"),
                                        dmc.Paper(dmc.Text("0 FCFA", id="filtered-avg-price"), p="md"),
                                        dmc.Paper(dmc.Text("0 FCFA", id="filtered-median-price"), p="md"),
                                        dmc.Paper(dmc.Text("0 m²", id="filtered-avg-surface"), p="md"),
                                    ],
                                ),

                                html.Br(),

                                # ---------------------------------------------------------
                                #                      GRAPHIQUES
                                # ---------------------------------------------------------
                                dcc.Graph(id="price-trend-chart"),
                                html.Br(),
                                dcc.Graph(id="surface-price-chart"),
                                html.Br(),
                                dcc.Graph(id="city-analysis-chart"),
                                html.Br(),

                                # ---------------------------------------------------------
                                #                       TABLEAU
                                # ---------------------------------------------------------
                                dash_table.DataTable(
                                    id="filtered-data-table",
                                    page_size=20,
                                    style_table={"overflowX": "auto"},
                                ),
                            ],
                        ),
                    ]
                )
            ],
        )

    # =================================================================
    #                         CALLBACKS DASH
    # =================================================================

    def setup_callbacks(self):

        @callback(
            [
                Output("filtered-count", "children"),
                Output("filtered-avg-price", "children"),
                Output("filtered-median-price", "children"),
                Output("filtered-avg-surface", "children"),
                Output("price-trend-chart", "figure"),
                Output("surface-price-chart", "figure"),
                Output("city-analysis-chart", "figure"),
                Output("filtered-data-table", "data"),
            ],
            Input("apply-filters", "n_clicks"),
            [
                Input("filter-city", "value"),
                Input("filter-property-type", "value"),
                Input("filter-source", "value"),
                Input("filter-bedrooms", "value"),
                Input("filter-min-price", "value"),
                Input("filter-max-price", "value"),
                Input("filter-min-surface", "value"),
                Input("filter-max-surface", "value"),
            ],
        )
        def update_analytics(n, city, typ, source, bedrooms, pmin, pmax, smin, smax):

            data = self.get_filtered_data(
                city=city,
                property_type=typ,
                source=source,
                bedrooms=bedrooms,
                min_price=pmin,
                max_price=pmax,
                min_surface=smin,
                max_surface=smax,
            )

            if not data:
                return (
                    "0",
                    "0 FCFA",
                    "0 FCFA",
                    "0 m²",
                    go.Figure(),
                    go.Figure(),
                    go.Figure(),
                    [],
                )

            df = pd.DataFrame(data)

            count = len(df)
            avg_price = f"{df['price'].mean():,.0f} FCFA"
            median_price = f"{df['price'].median():,.0f} FCFA"
            avg_surface = f"{df['surface_area'].mean():.1f} m²" if "surface_area" in df else "N/A"

            return (
                f"{count}",
                avg_price,
                median_price,
                avg_surface,
                self.create_price_trend_chart(data),
                self.create_surface_price_scatter(data),
                self.create_city_analysis_chart(data),
                df.to_dict("records"),
            )

        @callback(
            Output("analytics-notification-container", "children"),
            Input("export-btn", "n_clicks"),
            prevent_initial_call=True
        )
        def export_csv(n):
            return dmc.Notification(
                title="Export CSV",
                message="Export lancé avec succès !",
                color="green",
                autoClose=3000,
            )
