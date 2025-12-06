import dash
from dash import html, dcc, Input, Output, callback
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
from ..database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty


class MapDashboard:
    """Dashboard avec visualisation cartographique Mapbox"""

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

    def get_map_data(self):
        """Récupérer les données pour la carte"""
        try:
            map_data = []

            # Coordonnées approximatives pour les villes principales du Sénégal
            city_coordinates = {
                "Dakar": {"lat": 14.6928, "lon": -17.4467},
                "Pikine": {"lat": 14.7640, "lon": -17.3900},
                "Guédiawaye": {"lat": 14.7739, "lon": -17.3367},
                "Rufisque": {"lat": 14.7167, "lon": -17.2667},
                "Thiès": {"lat": 14.7956, "lon": -16.9981},
                "Mbour": {"lat": 14.4167, "lon": -16.9667},
                "Saint-Louis": {"lat": 16.0179, "lon": -16.4896},
                "Kaolack": {"lat": 14.1500, "lon": -16.0833},
                "Ziguinchor": {"lat": 12.5833, "lon": -16.2667},
                "Tambacounda": {"lat": 13.7667, "lon": -13.6833},
            }

            # Collecter les données de chaque source
            for model, source_name in [
                (CoinAfrique, "CoinAfrique"),
                (ExpatDakarProperty, "ExpatDakar"),
                (LogerDakarProperty, "LogerDakar"),
            ]:
                properties = db.session.query(model).all()

                for prop in properties:
                    city_raw = getattr(prop, "city", None) or ""
                    city = city_raw.strip()
                    if not city:
                        continue
                    if city in city_coordinates:
                        description = getattr(prop, "description", None)
                        map_data.append(
                            {
                                "id": getattr(prop, "id", None),
                                "title": getattr(prop, "title", "") or "",
                                "price": getattr(prop, "price", None),
                                "city": city,
                                "property_type": getattr(prop, "property_type", "") or "",
                                "bedrooms": getattr(prop, "bedrooms", None),
                                "surface_area": getattr(prop, "surface_area", None),
                                "source": source_name,
                                "lat": city_coordinates[city]["lat"],
                                "lon": city_coordinates[city]["lon"],
                                "description": (description[:200] + "...") if description else "Pas de description",
                            }
                        )

            return map_data

        except Exception as e:
            print(f"Erreur lors de la récupération des données de carte: {e}")
            return []

    def create_map_figure(self, map_data, color_by="source"):
        """Créer la figure de la carte"""
        if not map_data:
            return go.Figure()

        df = pd.DataFrame(map_data)

        color_map = {
            "CoinAfrique": "#1f77b4",
            "ExpatDakar": "#ff7f0e",
            "LogerDakar": "#2ca02c",
        }

        if color_by == "price":
            fig = px.scatter_mapbox(
                df,
                lat="lat",
                lon="lon",
                color="price",
                size="surface_area" if "surface_area" in df.columns else None,
                hover_name="title",
                hover_data={
                    "price": True,
                    "city": True,
                    "property_type": True,
                    "bedrooms": True,
                    "source": True,
                },
                color_continuous_scale="Viridis",
                size_max=15,
                zoom=6,
                center=dict(lat=14.6928, lon=-17.4467),
                mapbox_style="open-street-map",
                title="Carte des propriétés - Coloration par prix",
            )
        else:
            fig = px.scatter_mapbox(
                df,
                lat="lat",
                lon="lon",
                color="source",
                size="price" if "price" in df.columns else None,
                hover_name="title",
                hover_data={
                    "price": True,
                    "city": True,
                    "property_type": True,
                    "bedrooms": True,
                },
                color_discrete_map=color_map,
                size_max=15,
                zoom=6,
                center=dict(lat=14.6928, lon=-17.4467),
                mapbox_style="open-street-map",
                title="Carte des propriétés - Coloration par source",
            )

        fig.update_layout(height=600, margin=dict(l=0, r=0, t=30, b=0))
        return fig

    def create_city_stats_chart(self, map_data):
        """Créer le graphique de statistiques par ville"""
        if not map_data:
            return go.Figure()

        df = pd.DataFrame(map_data)
        if df.empty or "city" not in df.columns:
            return go.Figure()

        city_stats = (
            df.groupby("city")
            .agg(
                price_count=("price", "count"),
                prix_moyen=("price", "mean"),
                prix_median=("price", "median"),
                prix_min=("price", "min"),
                prix_max=("price", "max"),
                surface_moyenne=("surface_area", "mean"),
            )
            .round(0)
        )

        city_stats = city_stats.sort_values("price_count", ascending=False).head(10)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(x=city_stats.index, y=city_stats["price_count"], name="Nombre de propriétés", marker_color="lightblue")
        )
        fig.add_trace(
            go.Scatter(
                x=city_stats.index,
                y=city_stats["prix_moyen"],
                mode="lines+markers",
                name="Prix moyen",
                line=dict(color="red", width=3),
                marker=dict(size=8),
                yaxis="y2",
            )
        )

        fig.update_layout(
            title="Top 10 des villes par nombre de propriétés",
            xaxis_title="Ville",
            yaxis=dict(title="Nombre de propriétés", side="left"),
            yaxis2=dict(title="Prix moyen (FCFA)", side="right", overlaying="y"),
            height=400,
            plot_bgcolor="white",
            paper_bgcolor="white",
        )

        return fig

    def create_property_type_map(self, map_data):
        """Créer une carte filtrée par type de propriété (subplots statiques)"""
        if not map_data:
            return go.Figure()

        df = pd.DataFrame(map_data)
        if df.empty or "property_type" not in df.columns:
            return go.Figure()

        property_types = df["property_type"].dropna().unique()
        from plotly.subplots import make_subplots

        n = min(4, len(property_types))
        rows = 2
        cols = 2

        fig = make_subplots(rows=rows, cols=cols, subplot_titles=list(property_types[:n]))
        colors = ["blue", "red", "green", "orange"]

        for i, prop_type in enumerate(property_types[:n]):
            row = (i // cols) + 1
            col = (i % cols) + 1
            type_data = df[df["property_type"] == prop_type]
            fig.add_trace(
                go.Scatter(
                    x=type_data["lon"],
                    y=type_data["lat"],
                    mode="markers",
                    name=prop_type,
                    marker=dict(size=8, color=colors[i % len(colors)], opacity=0.7),
                    text=type_data["title"],
                    hovertemplate="<b>%{text}</b><br>Lat: %{y}<br>Lon: %{x}<extra></extra>",
                ),
                row=row,
                col=col,
            )

        fig.update_layout(title="Répartition des types de propriétés", height=600, showlegend=False)
        return fig

    def setup_layout(self):
        """Configurer la mise en page"""
        map_data = self.get_map_data()

        # En-tête : utilisation de Paper au lieu de Header
        header = dmc.Paper(
            shadow="xs",
            p="sm",
            radius=0,
            withBorder=True,
            children=dmc.Group(
                justify="space-between",
                align="center",
                style={"height": "60px", "padding": "0 20px"},
                children=[
                    dmc.Title("Carte Interactive", order=3),
                    dmc.Group(
                        children=[
                            dmc.Select(
                                label="Colorer par",
                                id="map-color-by",
                                data=[{"value": "source", "label": "Source"}, {"value": "price", "label": "Prix"}],
                                value="source",
                                size="sm",
                            ),
                            dmc.Button(
                                "Vue satellite",
                                leftSection=DashIconify(icon="mdi:satellite", width=16),
                                id="satellite-toggle",
                                size="sm",
                                variant="outline",
                            ),
                        ]
                    ),
                ],
            ),
        )

        # Container principal
        self.app.layout = dmc.MantineProvider(
            theme={"colorScheme": "light", "primaryColor": "blue", "fontFamily": "Inter, sans-serif"},
            children=[
                html.Div(
                    [
                        header,
                        html.Div(id="map-notification-container"),
                        dmc.Container(
                            size="xl",
                            mt="xl",
                            children=[
                                dmc.Card(
                                    children=[
                                        dmc.Group(
                                            justify="space-between",
                                            children=[
                                                dmc.Text("Carte des propriétés", size="lg", fw=500),
                                                dmc.Badge(f"{len(map_data)} propriétés", color="blue", variant="light"),
                                            ],
                                        ),
                                        dcc.Graph(
                                            id="main-map",
                                            figure=self.create_map_figure(map_data),
                                            config={
                                                "displayModeBar": True,
                                                "displaylogo": False,
                                                "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
                                            },
                                        ),
                                    ],
                                    withBorder=True,
                                    shadow="sm",
                                    radius="md",
                                    p="md",
                                    mb="xl",
                                ),
                                dmc.SimpleGrid(
                                    cols=2,
                                    spacing="lg",
                                    children=[
                                        dmc.Card(
                                            children=[
                                                dmc.Text("Statistiques par ville", size="lg", fw=500, mb="md"),
                                                dcc.Graph(
                                                    id="city-stats-chart",
                                                    figure=self.create_city_stats_chart(map_data),
                                                    config={"displayModeBar": False},
                                                ),
                                            ],
                                            withBorder=True,
                                            shadow="sm",
                                            radius="md",
                                            p="md",
                                        ),
                                        dmc.Card(
                                            children=[
                                                dmc.Text("Répartition par type", size="lg", fw=500, mb="md"),
                                                dcc.Graph(
                                                    id="property-type-map",
                                                    figure=self.create_property_type_map(map_data),
                                                    config={"displayModeBar": False},
                                                ),
                                            ],
                                            withBorder=True,
                                            shadow="sm",
                                            radius="md",
                                            p="md",
                                        ),
                                    ],
                                ),
                                dmc.Space(h=30),
                                dmc.Card(
                                    children=[
                                        dmc.Group(
                                            justify="space-between",
                                            children=[
                                                dmc.Text("Détails des propriétés", size="lg", fw=500),
                                                dmc.Button(
                                                    "Afficher sur la carte",
                                                    id="show-on-map",
                                                    size="sm",
                                                    variant="outline",
                                                ),
                                            ],
                                            mb="md",
                                        ),
                                        # Table HTML (plus compatible que dmc.Table selon versions)
                                        html.Div(
                                            style={"overflowX": "auto"},
                                            children=[
                                                html.Table(
                                                    style={"width": "100%", "borderCollapse": "collapse"},
                                                    children=[
                                                        html.Thead(
                                                            html.Tr(
                                                                [
                                                                    html.Th("Titre"),
                                                                    html.Th("Prix"),
                                                                    html.Th("Ville"),
                                                                    html.Th("Type"),
                                                                    html.Th("Chambres"),
                                                                    html.Th("Surface"),
                                                                    html.Th("Source"),
                                                                ],
                                                                style={"textAlign": "left", "borderBottom": "1px solid #ddd", "padding": "8px"},
                                                            )
                                                        ),
                                                        html.Tbody(
                                                            [
                                                                html.Tr(
                                                                    [
                                                                        html.Td(
                                                                            (p["title"][:50] + "...") if len(p["title"]) > 50 else p["title"]
                                                                        ),
                                                                        html.Td(f"{p['price']:,} FCFA" if p.get("price") else "N/A"),
                                                                        html.Td(p.get("city", "N/A")),
                                                                        html.Td(p.get("property_type", "N/A")),
                                                                        html.Td(str(p.get("bedrooms", "N/A"))),
                                                                        html.Td(f"{p['surface_area']} m²" if p.get("surface_area") else "N/A"),
                                                                        html.Td(p.get("source", "N/A")),
                                                                    ],
                                                                    key=idx,
                                                                )
                                                                for idx, p in enumerate(map_data[:50])
                                                            ]
                                                        ),
                                                    ],
                                                )
                                            ],
                                        ),
                                    ],
                                    withBorder=True,
                                    shadow="sm",
                                    radius="md",
                                    p="md",
                                ),
                            ],
                        ),
                    ]
                )
            ],
        )

    def setup_callbacks(self):
        """Configurer les callbacks"""
        @callback(Output("main-map", "figure"), Input("map-color-by", "value"))
        def update_map_color(color_by):
            map_data = self.get_map_data()
            return self.create_map_figure(map_data, color_by)

        @callback(Output("map-notification-container", "children"), Input("satellite-toggle", "n_clicks"), prevent_initial_call=True)
        def toggle_satellite_view(n_clicks):
            if n_clicks:
                return dmc.Notification(
                    title="Vue satellite",
                    message="Fonctionnalité en cours de développement",
                    color="blue",
                    autoClose=3000,
                )
            return ""

        @callback(Output("map-notification-container", "children"), Input("show-on-map", "n_clicks"), prevent_initial_call=True)
        def highlight_on_map(n_clicks):
            if n_clicks:
                return dmc.Notification(
                    title="Sélection",
                    message="Sélectionnez une propriété dans le tableau pour la voir sur la carte",
                    color="green",
                    autoClose=3000,
                )
            return ""

