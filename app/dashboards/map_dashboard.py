"""
🗺️ MAP DASHBOARD - VERSION COMPLÈTE ENRICHIE
Dashboard cartographique avec heatmap, clusters et analyses géospatiales
Auteur: Cos - ENSAE Dakar
Version: 2.0 - Enhanced
"""

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
import logging
import traceback
import base64
from sqlalchemy.exc import SQLAlchemyError, OperationalError

# Import du détecteur de statut
try:
    from .status_detector import detect_listing_status
except ImportError:
    try:
        from status_detector import detect_listing_status
    except ImportError:
        # Fallback si module non disponible
        def detect_listing_status(title=None, price=None, property_type=None, source=None, native_status=None):
            if price and price < 1_500_000:
                return 'Location'
            return 'Vente'

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PremiumMapDashboard:
    """Dashboard cartographique premium avec analyses géospatiales"""
    
    COLORS = {
        'primary': '#1E40AF',
        'secondary': '#EC4899',
        'success': '#10B981',
        'warning': '#F59E0B',
        'danger': '#EF4444',
        'info': '#06B6D4',
        'purple': '#8B5CF6',
        'teal': '#14B8A6',
        'bg_dark': '#0f172a',
        'bg_card': '#1e293b',
        'text_primary': '#f1f5f9',
        'text_secondary': '#94a3b8',
        'border': '#334155'
    }
    
    # Coordonnées précises des villes sénégalaises
    CITY_COORDINATES = {
        "dakar": {"lat": 14.6928, "lon": -17.4467, "region": "Cap-Vert", "population": 1030594},
        "pikine": {"lat": 14.7640, "lon": -17.3900, "region": "Cap-Vert", "population": 874062},
        "guédiawaye": {"lat": 14.7739, "lon": -17.3367, "region": "Cap-Vert", "population": 280353},
        "rufisque": {"lat": 14.7167, "lon": -17.2667, "region": "Cap-Vert", "population": 179797},
        "thiès": {"lat": 14.7956, "lon": -16.9981, "region": "Thiès", "population": 320000},
        "mbour": {"lat": 14.4167, "lon": -16.9667, "region": "Thiès", "population": 232777},
        "saint-louis": {"lat": 16.0179, "lon": -16.4896, "region": "Saint-Louis", "population": 258592},
        "kaolack": {"lat": 14.1500, "lon": -16.0833, "region": "Kaolack", "population": 260000},
        "ziguinchor": {"lat": 12.5833, "lon": -16.2667, "region": "Ziguinchor", "population": 205294},
        "tambacounda": {"lat": 13.7667, "lon": -13.6833, "region": "Tambacounda", "population": 107000},
        "kolda": {"lat": 12.8833, "lon": -14.9500, "region": "Kolda", "population": 68000},
        "louga": {"lat": 15.6181, "lon": -16.2244, "region": "Louga", "population": 90000},
        "diourbel": {"lat": 14.6500, "lon": -16.2333, "region": "Diourbel", "population": 140000},
        "fatick": {"lat": 14.3389, "lon": -16.4111, "region": "Fatick", "population": 30000},
        "kaffrine": {"lat": 14.1053, "lon": -15.5508, "region": "Kaffrine", "population": 55000},
        "kédougou": {"lat": 12.5579, "lon": -12.1784, "region": "Kédougou", "population": 25000},
        "sédhiou": {"lat": 12.7081, "lon": -15.5569, "region": "Sédhiou", "population": 25000},
        "matam": {"lat": 15.6556, "lon": -13.2553, "region": "Matam", "population": 40000},
        "bambey": {"lat": 14.6984, "lon": -16.2738, "region": "Diourbel", "population": 30000},
        "richard-toll": {"lat": 16.4625, "lon": -15.7008, "region": "Saint-Louis", "population": 60000},
        "touba": {"lat": 14.8500, "lon": -15.8833, "region": "Diourbel", "population": 529000},
    }
    
    def __init__(self, server=None, routes_pathname_prefix="/map/", requests_pathname_prefix="/map/"):
        # CSS personnalisé
        self.custom_css = """
        * { font-family: 'Outfit', sans-serif; }
        body { background: #0f172a; margin: 0; padding: 0; color: #f1f5f9; }
        .map-container { border-radius: 20px; overflow: hidden; }
        .stat-card { transition: all 0.3s ease; }
        .stat-card:hover { transform: translateY(-4px); box-shadow: 0 12px 28px rgba(0,0,0,0.3); }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        """
        
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[
                'https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap',
                dbc.themes.BOOTSTRAP
            ],
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix,
            suppress_callback_exceptions=True,
            meta_tags=[{
                "name": "viewport",
                "content": "width=device-width, initial-scale=1, maximum-scale=1"
            }]
        )
        
        if server:
            with server.app_context():
                self.setup_layout()
                self.setup_callbacks()
        else:
            self.setup_layout()
            self.setup_callbacks()
    
    # ==================== DATA LOADING ====================
    
    def safe_import_models(self):
        """Import sécurisé des modèles"""
        try:
            from database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
            return db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
        except ImportError:
            try:
                from app.database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
                return db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
            except Exception as e:
                logger.error(f"Erreur import models: {e}")
                return None, None, None, None
    
    def clean_city_name(self, city):
        """
        Nettoyer et normaliser les noms de ville
        Applique: lowercase, split par virgule, suppression espaces
        """
        if not city or not isinstance(city, str):
            return None
        
        # Nettoyer: lowercase, prendre première partie avant virgule, strip
        cleaned = city.lower().split(',')[0].strip()
        
        # Normaliser quelques variantes communes
        replacements = {
            'saint louis': 'saint-louis',
            'st louis': 'saint-louis',
            'richard toll': 'richard-toll',
            'guediawaye': 'guédiawaye',
            'thies': 'thiès',
            'kedougou': 'kédougou',
            'sedhiou': 'sédhiou',
        }
        
        for old, new in replacements.items():
            if cleaned == old:
                cleaned = new
                break
        
        return cleaned
    
    def get_enhanced_map_data(self, sources=None):
        """
        Récupération enrichie des données cartographiques
        Avec nettoyage des villes et calculs avancés
        """
        try:
            db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty = self.safe_import_models()
            
            if not db:
                logger.error("DB non disponible")
                return pd.DataFrame()
            
            all_data = []
            
            # Définir les sources à interroger
            models_to_query = []
            if not sources or 'CoinAfrique' in sources:
                models_to_query.append((CoinAfrique, 'CoinAfrique'))
            if not sources or 'ExpatDakar' in sources:
                models_to_query.append((ExpatDakarProperty, 'ExpatDakar'))
            if not sources or 'LogerDakar' in sources:
                models_to_query.append((LogerDakarProperty, 'LogerDakar'))
            
            for model, source_name in models_to_query:
                try:
                    properties = db.session.query(
                        model.city,
                        model.property_type,
                        model.price,
                        model.surface_area,
                        model.bedrooms,
                        model.bathrooms,
                        model.scraped_at
                    ).filter(
                        model.city.isnot(None),
                        model.price.isnot(None),
                        model.price > 10000,
                        model.price < 1e10
                    ).limit(3000).all()
                    
                    logger.info(f"{source_name}: {len(properties)} propriétés trouvées")
                    
                    for prop in properties:
                        try:
                            # Nettoyer le nom de la ville - CRITIQUE
                            city_raw = str(prop.city) if prop.city else None
                            city_clean = self.clean_city_name(city_raw)
                            
                            # Vérifier si la ville est dans nos coordonnées
                            if not city_clean or city_clean not in self.CITY_COORDINATES:
                                continue
                            
                            coords = self.CITY_COORDINATES[city_clean]
                            
                            # Extraire les données de base
                            price = float(prop.price) if prop.price else 0
                            surface = float(prop.surface_area) if prop.surface_area and prop.surface_area > 0 else None
                            title = str(prop.title) if hasattr(prop, 'title') and prop.title else None
                            prop_type = str(prop.property_type) if prop.property_type else 'Autre'
                            
                            # NOUVEAU: Détecter le statut (Vente/Location)
                            # Vérifier d'abord si la source a un champ 'status' natif
                            native_status = str(prop.status) if hasattr(prop, 'status') and prop.status else None
                            
                            # Utiliser le module StatusDetector
                            status = detect_listing_status(
                                title=title,
                                price=price,
                                property_type=prop_type,
                                source=source_name,
                                native_status=native_status
                            )
                            
                            # Calculer prix/m²
                            price_per_m2 = price / surface if surface and surface > 0 and price > 0 else None
                            
                            # Calculer l'âge de l'annonce
                            age_days = None
                            if prop.scraped_at:
                                age_days = (datetime.utcnow() - prop.scraped_at).days
                            
                            all_data.append({
                                'city': city_clean,
                                'city_display': city_clean.title(),
                                'region': coords['region'],
                                'population': coords['population'],
                                'lat': coords['lat'],
                                'lon': coords['lon'],
                                'property_type': prop_type,
                                'status': status,  # NOUVEAU: Vente ou Location
                                'title': title[:100] if title else None,
                                'price': price,
                                'surface_area': surface,
                                'price_per_m2': price_per_m2,
                                'bedrooms': int(prop.bedrooms) if prop.bedrooms else None,
                                'bathrooms': int(prop.bathrooms) if prop.bathrooms else None,
                                'age_days': age_days,
                                'source': source_name
                            })
                            
                        except Exception as e:
                            logger.warning(f"Erreur traitement propriété: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Erreur requête {source_name}: {e}")
                    continue
            
            if not all_data:
                logger.warning("Aucune donnée récupérée")
                return pd.DataFrame()
            
            df = pd.DataFrame(all_data)
            df['city'] = df['city'].apply(lambda x: x.lower().split(',')[0] if isinstance(x, str) else x)
            # Enrichissement des données
            if not df.empty:
                # Score de densité par ville (nombre d'annonces / population)
                city_counts = df.groupby('city').size()
                df['city_density_score'] = df['city'].map(
                    lambda c: (city_counts.get(c, 0) / self.CITY_COORDINATES[c]['population'] * 100000)
                    if c in self.CITY_COORDINATES else 0
                )
                
                # Score d'accessibilité (basé sur prix médian de la ville)
                city_median_price = df.groupby('city')['price'].median()
                overall_median = df['price'].median()
                df['affordability_score'] = df['city'].map(
                    lambda c: 100 - min(100, (city_median_price.get(c, overall_median) / overall_median * 100))
                )
                
                # Catégoriser les prix
                df['price_category'] = pd.cut(
                    df['price'],
                    bins=[0, 50_000_000, 100_000_000, 200_000_000, float('inf')],
                    labels=['Économique', 'Moyen', 'Élevé', 'Premium']
                )
                
                # Score de fraîcheur (basé sur age_days)
                df['freshness_score'] = df['age_days'].apply(
                    lambda x: 100 - min(100, x * 2) if pd.notna(x) and x >= 0 else 50
                )
            
            logger.info(f"DataFrame final: {len(df)} enregistrements, {df['city'].nunique()} villes")
            
            return df
            
        except Exception as e:
            logger.error(f"Erreur critique get_enhanced_map_data: {e}")
            traceback.print_exc()
            return pd.DataFrame()
    
    # ==================== VISUALISATIONS ====================
    
    def create_interactive_map(self, df, color_by='price'):
        """Carte interactive avec markers colorés"""
        if df.empty:
            return self.create_empty_figure("Aucune donnée disponible")
        
        try:
            # Préparer les données pour la carte
            df_map = df.copy()
            
            # Définir la colonne de couleur
            if color_by == 'price':
                color_col = 'price'
                color_label = 'Prix (FCFA)'
            elif color_by == 'price_per_m2':
                df_map = df_map[df_map['price_per_m2'].notna()]
                color_col = 'price_per_m2'
                color_label = 'Prix/m² (FCFA)'
            elif color_by == 'affordability':
                color_col = 'affordability_score'
                color_label = 'Score Accessibilité'
            else:
                color_col = 'city_density_score'
                color_label = 'Densité Annonces'
            
            if df_map.empty:
                return self.create_empty_figure("Pas de données pour ce critère")
            
            # Agréger par ville pour la carte
            city_agg = df_map.groupby(['city', 'city_display', 'lat', 'lon', 'region']).agg({
                'price': ['count', 'median', 'mean'],
                'price_per_m2': 'median',
                color_col: 'mean'
            }).reset_index()
            
            city_agg.columns = ['city', 'city_display', 'lat', 'lon', 'region', 
                               'count', 'median_price', 'mean_price', 'median_price_m2', 'color_value']
            
            # Créer le hover text
            city_agg['hover_text'] = city_agg.apply(
                lambda x: f"<b>{x['city_display']}</b><br>" +
                         f"Région: {x['region']}<br>" +
                         f"Annonces: {int(x['count'])}<br>" +
                         f"Prix médian: {x['median_price']/1_000_000:.1f}M FCFA<br>" +
                         f"Prix/m²: {x['median_price_m2']:.0f} FCFA" if pd.notna(x['median_price_m2']) else "",
                axis=1
            )
            
            # Créer la carte
            fig = go.Figure()
            
            fig.add_trace(go.Scattermapbox(
                lat=city_agg['lat'],
                lon=city_agg['lon'],
                mode='markers',
                marker=dict(
                    size=city_agg['count'].apply(lambda x: min(50, 10 + x/10)),
                    color=city_agg['color_value'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(
                        title=color_label,
                        x=1.02
                    ),
                    opacity=0.8,
                    line=dict(width=2, color='white')
                ),
                text=city_agg['hover_text'],
                hovertemplate='%{text}<extra></extra>',
                name='Villes'
            ))
            
            # Configuration de la carte
            fig.update_layout(
                mapbox=dict(
                    style='open-street-map',
                    center=dict(lat=14.5, lon=-14.5),
                    zoom=6
                ),
                height=700,
                margin=dict(l=0, r=0, t=40, b=0),
                title=dict(
                    text=f'🗺️ Carte Interactive - Colorée par {color_label}',
                    font=dict(size=20, family='Outfit, sans-serif', color=self.COLORS['text_primary']),
                    x=0.5,
                    xanchor='center'
                ),
                paper_bgcolor=self.COLORS['bg_card'],
                plot_bgcolor=self.COLORS['bg_card'],
                font=dict(color=self.COLORS['text_primary'])
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Erreur création carte: {e}")
            return self.create_empty_figure(f"Erreur: {str(e)}")
    
    def create_heatmap_density(self, df):
        """Heatmap de densité des annonces"""
        if df.empty:
            return self.create_empty_figure("Aucune donnée disponible")
        
        try:
            fig = go.Figure()
            
            fig.add_trace(go.Densitymapbox(
                lat=df['lat'],
                lon=df['lon'],
                z=df['price'],
                radius=30,
                colorscale='Hot',
                showscale=True,
                colorbar=dict(title="Intensité"),
                opacity=0.6
            ))
            
            fig.update_layout(
                mapbox=dict(
                    style='open-street-map',
                    center=dict(lat=14.5, lon=-14.5),
                    zoom=6
                ),
                height=700,
                margin=dict(l=0, r=0, t=40, b=0),
                title=dict(
                    text='🔥 Heatmap - Densité des Annonces',
                    font=dict(size=20, family='Outfit, sans-serif', color=self.COLORS['text_primary']),
                    x=0.5,
                    xanchor='center'
                ),
                paper_bgcolor=self.COLORS['bg_card'],
                plot_bgcolor=self.COLORS['bg_card'],
                font=dict(color=self.COLORS['text_primary'])
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Erreur heatmap: {e}")
            return self.create_empty_figure(f"Erreur: {str(e)}")
    
    def create_city_comparison_chart(self, df):
        """Comparaison des villes - Top 10"""
        if df.empty:
            return go.Figure()
        
        try:
            # Top 10 villes par nombre d'annonces
            city_stats = df.groupby('city_display').agg({
                'price': ['count', 'median'],
                'price_per_m2': 'median',
                'affordability_score': 'mean'
            }).reset_index()
            
            city_stats.columns = ['city', 'count', 'median_price', 'median_price_m2', 'affordability']
            city_stats = city_stats.sort_values('count', ascending=False).head(10)
            
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Nombre d\'Annonces', 'Prix Médian'),
                specs=[[{'type': 'bar'}, {'type': 'bar'}]]
            )
            
            # Graphique 1: Nombre d'annonces
            fig.add_trace(
                go.Bar(
                    x=city_stats['city'],
                    y=city_stats['count'],
                    marker=dict(color=self.COLORS['primary']),
                    text=city_stats['count'],
                    textposition='outside',
                    name='Annonces'
                ),
                row=1, col=1
            )
            
            # Graphique 2: Prix médian
            fig.add_trace(
                go.Bar(
                    x=city_stats['city'],
                    y=city_stats['median_price'],
                    marker=dict(
                        color=city_stats['median_price'],
                        colorscale='Viridis',
                        showscale=True
                    ),
                    text=city_stats['median_price'].apply(lambda x: f"{x/1_000_000:.1f}M"),
                    textposition='outside',
                    name='Prix'
                ),
                row=1, col=2
            )
            
            fig.update_layout(
                title=dict(
                    text='📊 Top 10 Villes - Comparaison',
                    font=dict(size=20, family='Outfit, sans-serif', color=self.COLORS['text_primary']),
                    x=0.5,
                    xanchor='center'
                ),
                showlegend=False,
                height=450,
                paper_bgcolor=self.COLORS['bg_card'],
                plot_bgcolor=self.COLORS['bg_card'],
                font=dict(color=self.COLORS['text_primary'])
            )
            
            fig.update_xaxes(tickangle=-45)
            
            return fig
            
        except Exception as e:
            logger.error(f"Erreur city comparison: {e}")
            return go.Figure()
    
    def create_status_distribution(self, df):
        """Distribution Vente vs Location avec insights"""
        if df.empty or 'status' not in df.columns:
            return go.Figure()
        
        try:
            # Statistiques par statut
            status_stats = df.groupby('status').agg({
                'price': ['count', 'median', 'mean'],
                'price_per_m2': 'median'
            }).reset_index()
            
            status_stats.columns = ['status', 'count', 'median_price', 'mean_price', 'median_price_m2']
            
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Répartition des Annonces', 'Prix Médian par Statut'),
                specs=[[{'type': 'pie'}, {'type': 'bar'}]]
            )
            
            # Graphique 1: Pie chart
            colors = [self.COLORS['success'], self.COLORS['warning']]
            fig.add_trace(
                go.Pie(
                    labels=status_stats['status'],
                    values=status_stats['count'],
                    marker=dict(colors=colors),
                    hole=0.4,
                    textinfo='label+percent',
                    textfont=dict(size=14)
                ),
                row=1, col=1
            )
            
            # Graphique 2: Bar chart des prix
            fig.add_trace(
                go.Bar(
                    x=status_stats['status'],
                    y=status_stats['median_price'],
                    marker=dict(color=colors),
                    text=status_stats['median_price'].apply(lambda x: f"{x/1_000_000:.1f}M"),
                    textposition='outside',
                    name='Prix Médian'
                ),
                row=1, col=2
            )
            
            fig.update_layout(
                title=dict(
                    text='🏷️ Analyse Vente vs Location',
                    font=dict(size=20, family='Outfit, sans-serif', color=self.COLORS['text_primary']),
                    x=0.5,
                    xanchor='center'
                ),
                showlegend=False,
                height=450,
                paper_bgcolor=self.COLORS['bg_card'],
                plot_bgcolor=self.COLORS['bg_card'],
                font=dict(color=self.COLORS['text_primary'])
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Erreur status distribution: {e}")
            return go.Figure()
    
    def create_regional_analysis(self, df):
        """Analyse par région"""
        if df.empty:
            return go.Figure()
        
        try:
            regional_stats = df.groupby('region').agg({
                'price': ['count', 'mean', 'median'],
                'affordability_score': 'mean',
                'city_density_score': 'mean'
            }).reset_index()
            
            regional_stats.columns = ['region', 'count', 'mean_price', 'median_price', 
                                     'affordability', 'density']
            
            regional_stats = regional_stats.sort_values('count', ascending=True)
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                y=regional_stats['region'],
                x=regional_stats['count'],
                orientation='h',
                marker=dict(
                    color=regional_stats['mean_price'],
                    colorscale='Plasma',
                    showscale=True,
                    colorbar=dict(title="Prix Moyen")
                ),
                text=regional_stats['count'],
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Annonces: %{x}<br>Prix moyen: %{marker.color:.0f}<extra></extra>'
            ))
            
            fig.update_layout(
                title=dict(
                    text='🌍 Analyse par Région',
                    font=dict(size=20, family='Outfit, sans-serif', color=self.COLORS['text_primary']),
                    x=0
                ),
                xaxis_title="Nombre d'annonces",
                height=500,
                paper_bgcolor=self.COLORS['bg_card'],
                plot_bgcolor=self.COLORS['bg_card'],
                font=dict(color=self.COLORS['text_primary']),
                margin=dict(l=150)
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Erreur regional analysis: {e}")
            return go.Figure()
    
    def create_empty_figure(self, message):
        """Figure vide avec message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color=self.COLORS['text_secondary'])
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            paper_bgcolor=self.COLORS['bg_card'],
            plot_bgcolor=self.COLORS['bg_card'],
            height=400
        )
        return fig
    
    # ==================== LAYOUT ====================
    
    def setup_layout(self):
        """Configuration du layout"""
        
        # Injection CSS
        css_b64 = base64.b64encode(self.custom_css.encode()).decode()
        
        self.app.layout = html.Div([
            # CSS
            html.Link(rel='stylesheet', href=f'data:text/css;base64,{css_b64}'),
            
            # Location
            dcc.Location(id='map-url', refresh=False),
            
            # Store pour les données
            dcc.Store(id='map-data-store', data=[]),
            
            # Header
            html.Div([
                html.Div([
                    html.Div([
                        DashIconify(icon="mdi:map-marker-radius", width=40, color="white"),
                        html.Div([
                            html.H1("Carte Immobilière Interactive", style={
                                'fontSize': '32px',
                                'fontWeight': '800',
                                'color': 'white',
                                'margin': '0'
                            }),
                            html.P("Visualisation géospatiale du marché sénégalais", style={
                                'fontSize': '14px',
                                'color': 'rgba(255,255,255,0.9)',
                                'margin': '4px 0 0 0'
                            })
                        ], style={'marginLeft': '16px'})
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                    
                    html.Div([
                        html.Div(style={
                            'width': '10px',
                            'height': '10px',
                            'background': '#10B981',
                            'borderRadius': '50%',
                            'marginRight': '8px',
                            'animation': 'pulse 2s infinite'
                        }),
                        html.Span("LIVE", style={
                            'fontSize': '12px',
                            'fontWeight': '700',
                            'color': 'white',
                            'letterSpacing': '1px'
                        })
                    ], style={
                        'display': 'flex',
                        'alignItems': 'center',
                        'background': 'rgba(255,255,255,0.15)',
                        'padding': '10px 18px',
                        'borderRadius': '24px',
                        'backdropFilter': 'blur(10px)'
                    })
                ], style={
                    'display': 'flex',
                    'justifyContent': 'space-between',
                    'alignItems': 'center',
                    'maxWidth': '1800px',
                    'margin': '0 auto',
                    'padding': '0 32px'
                })
            ], style={
                'background': f'linear-gradient(135deg, {self.COLORS["primary"]}, {self.COLORS["purple"]})',
                'padding': '32px 0',
                'boxShadow': '0 6px 24px rgba(99, 102, 241, 0.3)',
                'marginBottom': '32px'
            }),
            
            # Container principal
            html.Div([
                html.Div([
                    # Contrôles
                    html.Div([
                        html.Div([
                            DashIconify(icon="mdi:tune", width=20, color=self.COLORS['primary']),
                            html.Span("Contrôles de la Carte", style={
                                'fontSize': '16px',
                                'fontWeight': '700',
                                'color': self.COLORS['text_primary'],
                                'marginLeft': '8px'
                            })
                        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),
                        
                        html.Div([
                            html.Div([
                                html.Label("Colorier par", style={
                                    'fontSize': '13px',
                                    'fontWeight': '600',
                                    'color': self.COLORS['text_secondary'],
                                    'marginBottom': '8px',
                                    'display': 'block'
                                }),
                                dcc.Dropdown(
                                    id='map-color-by',
                                    options=[
                                        {'label': '💰 Prix', 'value': 'price'},
                                        {'label': '📐 Prix/m²', 'value': 'price_per_m2'},
                                        {'label': '🎯 Accessibilité', 'value': 'affordability'},
                                        {'label': '📊 Densité', 'value': 'density'}
                                    ],
                                    value='price',
                                    clearable=False,
                                    style={'borderRadius': '12px'}
                                )
                            ], style={'flex': '1', 'minWidth': '200px'}),
                            
                            html.Div([
                                html.Label("Statut", style={
                                    'fontSize': '13px',
                                    'fontWeight': '600',
                                    'color': self.COLORS['text_secondary'],
                                    'marginBottom': '8px',
                                    'display': 'block'
                                }),
                                dcc.Dropdown(
                                    id='map-status-filter',
                                    options=[
                                        {'label': '🏘️ Tous', 'value': 'Tous'},
                                        {'label': '💰 Vente', 'value': 'Vente'},
                                        {'label': '🏠 Location', 'value': 'Location'}
                                    ],
                                    value='Tous',
                                    clearable=False,
                                    style={'borderRadius': '12px'}
                                )
                            ], style={'flex': '1', 'minWidth': '200px'}),
                            
                            html.Div([
                                html.Label("Type de carte", style={
                                    'fontSize': '13px',
                                    'fontWeight': '600',
                                    'color': self.COLORS['text_secondary'],
                                    'marginBottom': '8px',
                                    'display': 'block'
                                }),
                                dcc.Dropdown(
                                    id='map-type',
                                    options=[
                                        {'label': '📍 Markers', 'value': 'markers'},
                                        {'label': '🔥 Heatmap', 'value': 'heatmap'}
                                    ],
                                    value='markers',
                                    clearable=False,
                                    style={'borderRadius': '12px'}
                                )
                            ], style={'flex': '1', 'minWidth': '200px'}),
                            
                            html.Div([
                                html.Label("Sources de données", style={
                                    'fontSize': '13px',
                                    'fontWeight': '600',
                                    'color': self.COLORS['text_secondary'],
                                    'marginBottom': '8px',
                                    'display': 'block'
                                }),
                                dcc.Dropdown(
                                    id='map-sources',
                                    options=[
                                        {'label': '🟦 CoinAfrique', 'value': 'CoinAfrique'},
                                        {'label': '🟨 ExpatDakar', 'value': 'ExpatDakar'},
                                        {'label': '🟩 LogerDakar', 'value': 'LogerDakar'}
                                    ],
                                    value=['CoinAfrique', 'ExpatDakar', 'LogerDakar'],
                                    multi=True,
                                    style={'borderRadius': '12px'}
                                )
                            ], style={'flex': '1.5', 'minWidth': '250px'}),
                            
                            html.Button([
                                DashIconify(icon="mdi:refresh", width=20, color="white"),
                                html.Span("Actualiser", style={'marginLeft': '8px'})
                            ], id='map-refresh-button', style={
                                'background': f'linear-gradient(135deg, {self.COLORS["primary"]}, {self.COLORS["purple"]})',
                                'color': 'white',
                                'border': 'none',
                                'borderRadius': '12px',
                                'padding': '12px 24px',
                                'fontSize': '14px',
                                'fontWeight': '600',
                                'cursor': 'pointer',
                                'display': 'flex',
                                'alignItems': 'center',
                                'alignSelf': 'flex-end',
                                'boxShadow': f'0 4px 12px {self.COLORS["primary"]}40'
                            })
                        ], style={
                            'display': 'flex',
                            'gap': '16px',
                            'flexWrap': 'wrap',
                            'alignItems': 'flex-end'
                        })
                    ], style={
                        'background': self.COLORS['bg_card'],
                        'padding': '24px',
                        'borderRadius': '20px',
                        'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
                        'border': f'1px solid {self.COLORS["border"]}',
                        'marginBottom': '32px'
                    }),
                    
                    # KPIs
                    html.Div(id='map-kpi-section', style={'marginBottom': '32px'}),
                    
                    # Carte principale
                    html.Div([
                        dcc.Graph(id='main-map', config={'displayModeBar': True})
                    ], style={
                        'background': self.COLORS['bg_card'],
                        'padding': '24px',
                        'borderRadius': '20px',
                        'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
                        'border': f'1px solid {self.COLORS["border"]}',
                        'marginBottom': '32px'
                    }),
                    
                    # Analyses
                    html.Div([
                        html.Div([
                            dcc.Graph(id='status-distribution', config={'displayModeBar': False})
                        ], style={
                            'background': self.COLORS['bg_card'],
                            'padding': '24px',
                            'borderRadius': '20px',
                            'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
                            'border': f'1px solid {self.COLORS["border"]}'
                        }),
                        
                        html.Div([
                            dcc.Graph(id='city-comparison', config={'displayModeBar': False})
                        ], style={
                            'background': self.COLORS['bg_card'],
                            'padding': '24px',
                            'borderRadius': '20px',
                            'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
                            'border': f'1px solid {self.COLORS["border"]}'
                        })
                    ], style={
                        'display': 'grid',
                        'gridTemplateColumns': 'repeat(auto-fit, minmax(600px, 1fr))',
                        'gap': '24px',
                        'marginBottom': '24px'
                    }),
                    
                    html.Div([
                        html.Div([
                            dcc.Graph(id='regional-analysis', config={'displayModeBar': False})
                        ], style={
                            'background': self.COLORS['bg_card'],
                            'padding': '24px',
                            'borderRadius': '20px',
                            'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
                            'border': f'1px solid {self.COLORS["border"]}'
                        })
                    ], style={
                        'marginBottom': '24px'
                    })
                    
                ], style={
                    'maxWidth': '1800px',
                    'margin': '0 auto',
                    'padding': '0 32px 60px 32px'
                })
            ], style={
                'background': self.COLORS['bg_dark'],
                'minHeight': '100vh'
            })
        ])
    
    # ==================== CALLBACKS ====================
    
    def setup_callbacks(self):
        """Configuration des callbacks"""
        
        @self.app.callback(
            Output('map-data-store', 'data'),
            [
                Input('map-url', 'pathname'),
                Input('map-refresh-button', 'n_clicks')
            ],
            State('map-sources', 'value')
        )
        def load_map_data(pathname, n_clicks, sources):
            """Charger les données cartographiques"""
            try:
                df = self.get_enhanced_map_data(sources)
                
                if df.empty:
                    return []
                
                # Convertir en dict pour le store
                return df.to_dict('records')
                
            except Exception as e:
                logger.error(f"Erreur load_map_data: {e}")
                return []
        
        @self.app.callback(
            Output('map-kpi-section', 'children'),
            Input('map-data-store', 'data')
        )
        def update_kpis(data):
            """Mettre à jour les KPIs avec statut"""
            try:
                if not data:
                    return html.Div("Aucune donnée", style={
                        'textAlign': 'center',
                        'padding': '40px',
                        'color': self.COLORS['text_secondary']
                    })
                
                df = pd.DataFrame(data)
                
                total_annonces = len(df)
                total_villes = df['city'].nunique()
                prix_median = df['price'].median()
                prix_m2_median = df['price_per_m2'].median() if 'price_per_m2' in df.columns else 0
                
                # Nouveaux KPIs basés sur le statut
                vente_count = len(df[df['status'] == 'Vente']) if 'status' in df.columns else 0
                location_count = len(df[df['status'] == 'Location']) if 'status' in df.columns else 0
                
                return html.Div([
                    self.create_kpi_card("🏠", "Annonces Totales", f"{total_annonces:,}".replace(',', ' ')),
                    self.create_kpi_card("💰", "À Vendre", f"{vente_count:,}".replace(',', ' ')),
                    self.create_kpi_card("🏘️", "À Louer", f"{location_count:,}".replace(',', ' ')),
                    self.create_kpi_card("🏙️", "Villes", str(total_villes)),
                    self.create_kpi_card("💵", "Prix Médian", f"{prix_median/1_000_000:.1f}M"),
                    self.create_kpi_card("📐", "Prix/m²", f"{prix_m2_median:,.0f}".replace(',', ' ')),
                ], style={
                    'display': 'grid',
                    'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))',
                    'gap': '20px'
                })
                
            except Exception as e:
                logger.error(f"Erreur update_kpis: {e}")
                return html.Div()
        
        @self.app.callback(
            [
                Output('main-map', 'figure'),
                Output('status-distribution', 'figure'),
                Output('city-comparison', 'figure'),
                Output('regional-analysis', 'figure')
            ],
            [
                Input('map-data-store', 'data'),
                Input('map-color-by', 'value'),
                Input('map-type', 'value'),
                Input('map-status-filter', 'value')
            ]
        )
        def update_visualizations(data, color_by, map_type, status_filter):
            """Mettre à jour toutes les visualisations avec filtre statut"""
            try:
                if not data:
                    empty = self.create_empty_figure("Chargement...")
                    return empty, go.Figure(), go.Figure(), go.Figure()
                
                df = pd.DataFrame(data)
                
                # Appliquer le filtre statut
                if status_filter and status_filter != 'Tous' and 'status' in df.columns:
                    df = df[df['status'] == status_filter]
                
                if df.empty:
                    empty = self.create_empty_figure(f"Aucune annonce pour: {status_filter}")
                    return empty, go.Figure(), go.Figure(), go.Figure()
                
                # Carte principale
                if map_type == 'heatmap':
                    main_map = self.create_heatmap_density(df)
                else:
                    main_map = self.create_interactive_map(df, color_by)
                
                # Distribution statut (utiliser toutes les données, pas filtrées)
                df_all = pd.DataFrame(data)
                status_dist = self.create_status_distribution(df_all)
                
                # Comparaison des villes (avec filtre)
                city_comp = self.create_city_comparison_chart(df)
                
                # Analyse régionale (avec filtre)
                regional = self.create_regional_analysis(df)
                
                return main_map, status_dist, city_comp, regional
                
            except Exception as e:
                logger.error(f"Erreur update_visualizations: {e}")
                traceback.print_exc()
                empty = self.create_empty_figure(f"Erreur: {str(e)}")
                return empty, go.Figure(), go.Figure(), go.Figure()
    
    def create_kpi_card(self, icon, title, value):
        """Carte KPI simple"""
        return html.Div([
            html.Div(icon, style={
                'fontSize': '32px',
                'marginBottom': '12px'
            }),
            html.Div(title, style={
                'fontSize': '13px',
                'fontWeight': '600',
                'color': self.COLORS['text_secondary'],
                'marginBottom': '8px'
            }),
            html.Div(value, style={
                'fontSize': '24px',
                'fontWeight': '700',
                'color': self.COLORS['text_primary']
            })
        ], style={
            'background': self.COLORS['bg_card'],
            'padding': '24px',
            'borderRadius': '20px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
            'border': f'1px solid {self.COLORS["border"]}',
            'textAlign': 'center'
        }, className='stat-card')


def create_premium_map_dashboard(server=None, routes_pathname_prefix="/map/", requests_pathname_prefix="/map/"):
    """Factory function pour créer le map dashboard"""
    try:
        dashboard = PremiumMapDashboard(
            server=server,
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix
        )
        logger.info("✅ Map Dashboard créé avec succès")
        return dashboard.app
    except Exception as e:
        logger.error(f"❌ ERREUR création Map Dashboard: {e}")
        traceback.print_exc()
        raise