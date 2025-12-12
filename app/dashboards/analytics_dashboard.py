"""
 ANALYTICS DASHBOARD ULTRA-AVANCÉ - VERSION COMPLÈTE CORRIGÉE
Dashboard avec analyses statistiques avancées, ML et visualisations 3D
Auteur: Cos - ENSAE Dakar
Version: 2.0 - Fixed
"""

import dash
from dash import html, dcc, Input, Output, State, callback, dash_table, ctx
from app.components.dash_sidebar_component import create_sidebar_layout
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import func, and_, or_
import json
import base64
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
import traceback
import sys

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

warnings.filterwarnings('ignore')

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re
import pandas as pd
import traceback

def parse_french_datetime(date_str):
    """
    Parse les dates françaises variées en objets datetime.
    Retourne datetime.now() si null ou parsing échoue.
    """
    if pd.isna(date_str) or date_str is None or str(date_str).strip() == '':
        return datetime.now()
    
    text = str(date_str).strip().lower()
    now = datetime.now()
    
    # Mapping mois français
    months = {
        'janv': 1, 'jan': 1, 'janvier': 1,
        'févr': 2, 'fevr': 2, 'février': 2, 'fevrier': 2,
        'mars': 3, 'mar': 3,
        'avr': 4, 'avril': 4,
        'mai': 5,
        'juin': 6,
        'juil': 7, 'juillet': 7,
        'août': 8, 'aout': 8,
        'sept': 9, 'sep': 9, 'septembre': 9,
        'oct': 10, 'octobre': 10,
        'nov': 11, 'novembre': 11,
        'déc': 12, 'dec': 12, 'décembre': 12, 'decembre': 12
    }
    
    # Mapping jours français
    days = {
        'lundi': 0, 'mardi': 1, 'mercredi': 2, 'jeudi': 3, 
        'vendredi': 4, 'samedi': 5, 'dimanche': 6
    }
    
    try:
        # 1. "Il y a X ans/jours/heures/minutes"
        match = re.match(r'il y a (\d+) (an|mois|semaine|jour|heure|minute)s?', text)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            if unit == 'an':
                return now - relativedelta(years=amount)
            elif unit == 'mois':
                return now - relativedelta(months=amount)
            elif unit == 'semaine':
                return now - timedelta(weeks=amount)
            elif unit == 'jour':
                return now - timedelta(days=amount)
            elif unit == 'heure':
                return now - timedelta(hours=amount)
            elif unit == 'minute':
                return now - timedelta(minutes=amount)
        
        # 2. "Hier, 13:00"
        if 'hier' in text:
            time_match = re.search(r'(\d{1,2}):(\d{2})', text)
            hier = now - timedelta(days=1)
            if time_match:
                hour, minute = map(int, time_match.groups())
                return hier.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return hier
        
        # 3. "Aujourd'hui, 15:30"
        if "aujourd'hui" in text:
            time_match = re.search(r'(\d{1,2}):(\d{2})', text)
            if time_match:
                hour, minute = map(int, time_match.groups())
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return now
        
        # 4. "vendredi, 22:49"
        for day_name, day_num in days.items():
            if day_name in text:
                time_match = re.search(r'(\d{1,2}):(\d{2})', text)
                days_diff = (now.weekday() - day_num) % 7
                if days_diff == 0:
                    days_diff = 7
                target_date = now - timedelta(days=days_diff)
                if time_match:
                    hour, minute = map(int, time_match.groups())
                    return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                return target_date
        
        # 5. "27. oct."
        date_match = re.match(r'(\d{1,2})[\.\s]+(\w{3,})\.?', text)
        if date_match:
            day = int(date_match.group(1))
            month_str = date_match.group(2).lower()
            if month_str in months:
                try:
                    return now.replace(month=months[month_str], day=day, hour=0, minute=0, second=0, microsecond=0)
                except ValueError:
                    pass
        
        # 6. "10:07" (heure seule)
        time_match = re.match(r'(\d{1,2}):(\d{2})', text)
        if time_match:
            hour, minute = map(int, time_match.groups())
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # 7. Fallback standard
        return pd.to_datetime(date_str)
        
    except Exception as e:
        print(f"⚠️ Erreur parsing '{date_str}': {e}")
        return now



# ============================================================
#                    GESTIONNAIRE D'ERREURS
# ============================================================

class ErrorManager:
    """Centralise la gestion des erreurs et les notifications UI"""
    
    @staticmethod
    def notify_success(title, message):
        return dmc.Notification(
            id=f"notification-success-{datetime.now().timestamp()}",
            title=title,
            message=message,
            color="green",
            action="show",
            autoClose=4000,
            icon=DashIconify(icon="mdi:check-circle", width=24)
        )
    
    @staticmethod
    def notify_error(title, message, details=None):
        return html.Div([
            dmc.Notification(
                id=f"notification-error-{datetime.now().timestamp()}",
                title=title,
                message=message,
                color="red",
                autoClose=False,
                icon=DashIconify(icon="mdi:alert-circle", width=24),
                action="show"
            ),
            html.Details([
                html.Summary("Détails techniques", style={'cursor': 'pointer', 'color': '#dc3545'}),
                html.Pre(details, style={
                    'background': "#1a5692",
                    'padding': '12px',
                    'borderRadius': '8px',
                    'fontSize': '12px',
                    'overflow': 'auto',
                    'maxHeight': '200px'
                })
            ], style={'marginTop': '12px'}) if details else None
        ])
    
    @staticmethod
    def notify_warning(title, message):
        return dmc.Notification(
            id=f"notification-warning-{datetime.now().timestamp()}",
            title=title,
            message=message,
            color="yellow",
            action="show",
            autoClose=6000,
            icon=DashIconify(icon="mdi:alert", width=24)
        )
    
    @staticmethod
    def notify_info(title, message):
        return dmc.Notification(
            id=f"notification-info-{datetime.now().timestamp()}",
            title=title,
            message=message,
            color="blue",
            action="show",
            autoClose=3000,
            icon=DashIconify(icon="mdi:information", width=24)
        )


# ============================================================
#                    DASHBOARD ULTRA-AVANCÉ
# ============================================================

class AnalyticsDashboard:
    """Dashboard Analytics avec gestion d'erreurs complète"""
    
    COLORS = {
        'primary': '#1E40AF', 'secondary': '#EC4899', 'success': '#10B981',
        'warning': '#F59E0B', 'danger': '#EF4444', 'info': '#06B6D4',
        'purple': '#8B5CF6', 'teal': '#14B8A6',
        'gradient_1': ['#667EEA', '#764BA2'], 'gradient_2': ['#F093FB', '#F5576C'],
        'gradient_3': ['#4FACFE', '#00F2FE'], 'gradient_4': ['#43E97B', '#38F9D7'],
        'bg_light': '#F8FAFC', 'bg_card': '#FFFFFF',
        'text_primary': '#1E293B', 'text_secondary': '#64748B', 'border': '#E2E8F0'
    }
    
    def __init__(self, server=None, routes_pathname_prefix="/analytics/", requests_pathname_prefix="/analytics/"):
        # CSS personnalisé
        self.custom_css = """
        * { font-family: 'Outfit', sans-serif; }
        body { background: #F8FAFC; margin: 0; padding: 0; }
        .graph-container { transition: all 0.3s ease; }
        .graph-container:hover { transform: translateY(-4px); box-shadow: 0 12px 28px rgba(0,0,0,0.12); }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .fade-in { animation: fadeIn 0.6s ease-out; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .loading-spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #1E40AF;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        """
        
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[
                'https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap',
                'https://unpkg.com/@tabler/icons-webfont@latest/tabler-icons.min.css',
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
        
        self._data_cache = {}
        self._debug_mode = True
        
        # CRITIQUE: Configuration du layout AVANT les callbacks
        self.setup_layout()
        
        if server:
            with server.app_context():
                self.setup_callbacks()
        else:
            self.setup_callbacks()
    
    # ========================================================
    #              DATA LOADING AVEC GESTION D'ERREURS
    # ========================================================
    
    def check_database_connection(self):
        """Vérifie la connexion DB et retourne statut + message"""
        try:
            # Essayer plusieurs chemins d'import
            try:
                from app.database.models import db,  ExpatDakarProperty, LogerDakarProperty
            except ImportError:
                from database.models import db,  ExpatDakarProperty, LogerDakarProperty
            
            # Test simple
            db.session.execute(db.text("SELECT 1"))
            
            # Compter les enregistrements
            sources_count = {
                'ExpatDakar': db.session.query(ExpatDakarProperty).count(),
                'LogerDakar': db.session.query(LogerDakarProperty).count()
            }
            
            total_sources = sum(sources_count.values())
            
            if total_sources > 0:
                return True, "✅ Base de données OK", {
                    'sources': sources_count,
                    'message': f"{total_sources} enregistrements disponibles"
                }
            else:
                return False, "❌ Aucune donnée disponible", {
                    'sources': sources_count,
                    'message': "Toutes les tables sont vides"
                }
                
        except ImportError as e:
            return False, "❌ Erreur d'import des modèles", {
                'error': str(e),
                'message': "Vérifiez les chemins d'import"
            }
        except Exception as e:
            return False, "❌ Erreur de connexion DB", {
                'error': str(e),
                'message': traceback.format_exc()
            }
    
    def get_enriched_data(self, filters=None, limit=5000):
        """
        Récupération enrichie des données avec filtres avancés
        
        Args:
            filters: dict avec 'cities', 'property_types', 'price_range'
            limit: nombre max d'enregistrements
        
        Returns:
            DataFrame avec colonnes enrichies
        """
        try:
            # Import sécurisé
            try:
                from app.database.models import db,  ExpatDakarProperty, LogerDakarProperty
            except ImportError:
                from database.models import db,  ExpatDakarProperty, LogerDakarProperty
            
            all_data = []
            
            for model in [ ExpatDakarProperty, LogerDakarProperty]:
                try:
                    query = db.session.query(
                        model.city,
                        model.property_type,
                        model.price,
                        model.surface_area,
                        model.bedrooms,
                        model.bathrooms,
                        model.posted_time,
                    ).filter(
                        model.price.isnot(None),
                        model.price > 10000,
                        model.price < 1e10
                    )
                    
                    # Appliquer les filtres
                    if filters:
                        if filters.get('cities') and len(filters['cities']) > 0:
                            query = query.filter(model.city.in_(filters['cities']))
                        
                        if filters.get('property_types') and len(filters['property_types']) > 0:
                            query = query.filter(model.property_type.in_(filters['property_types']))
                        
                        if filters.get('price_range'):
                            min_price, max_price = filters['price_range']
                            query = query.filter(
                                model.price >= min_price,
                                model.price <= max_price
                            )
                    
                    records = query.limit(limit).all()
                    
                    for r in records:
                        try:
                            age_days = None
                            if r.posted_time:
                                age_days = (datetime.utcnow() - parse_french_datetime(r.posted_time)).days
                                print(age_days)
                            
                            price = float(r.price) if r.price else 0
                            surface = float(r.surface_area) if r.surface_area and r.surface_area > 0 else None
                            title = str(r.title) if hasattr(r, 'title') and r.title else None
                            prop_type = str(r.property_type) if r.property_type else 'Autre'
                            
                            # Détection du statut (Vente/Location)
                            native_status = str(r.status) if hasattr(r, 'status') and r.status else None
                            status = detect_listing_status(
                                title=title,
                                price=price,
                                property_type=prop_type,
                                source=model.__name__,
                                native_status=native_status
                            )
                            
                            record_dict = {
                                'city': str(r.city) if r.city else 'Non spécifié',
                                'property_type': prop_type,
                                'status': status,  # NOUVEAU
                                'price': price,
                                'surface_area': surface,
                                'bedrooms': int(r.bedrooms) if r.bedrooms else None,
                                'bathrooms': int(r.bathrooms) if r.bathrooms else None,
                                'age_days': age_days,
                                'price_per_m2': price / surface if surface and surface > 0 and price > 0 else None
                            }
                            
                            all_data.append(record_dict)
                            
                        except Exception:
                            continue
                            
                except Exception as e:
                    print(f"Erreur requête {model.__name__}: {e}")
                    continue
            
            if not all_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_data)
            df['city'] = df['city'].apply(lambda x: x.lower().split(',')[0] if isinstance(x, str) else x)
            if 'posted_time' in df.columns:
                df['posted_time'] = df['posted_time'].apply(parse_french_datetime)            
            
            # Enrichissement des données
            if not df.empty:
                # Catégoriser les prix
                df['price_category'] = pd.cut(
                    df['price'],
                    bins=[0, 50_000_000, 100_000_000, 200_000_000, float('inf')],
                    labels=['Économique', 'Moyen', 'Élevé', 'Premium']
                )
                
                # Catégoriser les surfaces
                if 'surface_area' in df.columns:
                    df['surface_category'] = pd.cut(
                        df['surface_area'],
                        bins=[0, 50, 100, 200, float('inf')],
                        labels=['Petit', 'Moyen', 'Grand', 'Très Grand']
                    )
            
            return df
            
        except Exception as e:
            print(f"Erreur globale chargement enrichi: {e}")
            traceback.print_exc()
            return pd.DataFrame()
    
    def calculate_ultra_kpis(self, data):
        """Calcule des KPIs ultra-avancés"""
        if data is None or len(data) == 0:
            return {
                'total': 0, 'median_price': 0, 'avg_price_m2': 0,
                'price_volatility': 0, 'market_liquidity': 0, 'growth_rate': 0
            }
        
        df = pd.DataFrame(data) if isinstance(data, list) else data
        
        kpis = {}
        
        try:
            kpis['total'] = len(df)
            kpis['median_price'] = float(df['price'].median()) if 'price' in df.columns else 0
            kpis['avg_price_m2'] = float(df['price_per_m2'].mean()) if 'price_per_m2' in df.columns and df['price_per_m2'].notna().sum() > 0 else 0
            
            # Volatilité (coefficient de variation)
            if 'price' in df.columns and df['price'].std() > 0:
                kpis['price_volatility'] = float((df['price'].std() / df['price'].mean()) * 100)
            else:
                kpis['price_volatility'] = 0
            
            # Liquidité du marché (nombre d'annonces récentes)
            if 'age_days' in df.columns:
                recent = df[df['age_days'] <= 30] if df['age_days'].notna().sum() > 0 else df
                kpis['market_liquidity'] = float(len(recent) / len(df) * 100) if len(df) > 0 else 0
            else:
                kpis['market_liquidity'] = 100.0
            
            # Taux de croissance simulé (basé sur quartiles)
            if 'price' in df.columns and df['price'].notna().sum() > 0:
                q1 = df['price'].quantile(0.25)
                q3 = df['price'].quantile(0.75)
                kpis['growth_rate'] = float(((q3 - q1) / q1 * 100)) if q1 > 0 else 0
            else:
                kpis['growth_rate'] = 0
            
        except Exception as e:
            print(f"Erreur calcul KPIs: {e}")
            kpis = {
                'total': 0, 'median_price': 0, 'avg_price_m2': 0,
                'price_volatility': 0, 'market_liquidity': 0, 'growth_rate': 0
            }
        
        return kpis
    
    # ========================================================
    #              GRAPHIQUES AVANCÉS - HELPERS
    # ========================================================
    
    def _create_empty_graph(self, message, title=""):
        """Crée un graphique vide avec message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color=self.COLORS['text_secondary'])
        )
        fig.update_layout(
            title=title,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=400
        )
        return fig
    
    def _create_error_component(self, title, error, details):
        """Crée un composant d'erreur"""
        return html.Div([
            html.Div([
                DashIconify(icon="mdi:alert-circle", width=48, color=self.COLORS['danger']),
                html.H3(title, style={
                    'color': self.COLORS['danger'],
                    'marginTop': '16px',
                    'marginBottom': '8px'
                }),
                html.P(str(error), style={
                    'color': self.COLORS['text_secondary'],
                    'fontSize': '14px'
                })
            ], style={
                'textAlign': 'center',
                'padding': '40px',
                'background': 'white',
                'borderRadius': '20px',
                'border': f'2px solid {self.COLORS["danger"]}'
            })
        ])
    
    # ========================================================
    #              GRAPHIQUES ULTRA-AVANCÉS
    # ========================================================
    
    def create_superposed_violin_ridgeplot(self, data):
        """Violin plot superposé avec ridge plot"""
        try:
            if data is None or len(data) == 0:
                return self._create_empty_graph("Aucune donnée disponible", "🎻 Violin Plot Superposé")
            
            df = pd.DataFrame(data) if isinstance(data, list) else data
            
            if 'price' not in df.columns or 'property_type' not in df.columns:
                return self._create_empty_graph("Colonnes manquantes", "🎻 Violin Plot Superposé")
            
            # Filtrer les NaN et les valeurs invalides
            df_clean = df[df['price'].notna() & (df['price'] > 0)].copy()
            
            if df_clean.empty:
                return self._create_empty_graph("Pas de données valides", "🎻 Violin Plot Superposé")
            
            fig = go.Figure()
            
            property_types = df_clean['property_type'].unique()
            colors = [self.COLORS['primary'], self.COLORS['secondary'], 
                     self.COLORS['success'], self.COLORS['warning'], self.COLORS['info']]
            
            for i, ptype in enumerate(property_types):
                df_type = df_clean[df_clean['property_type'] == ptype]
                
                # S'assurer qu'il y a des données
                if len(df_type) > 0 and df_type['price'].notna().sum() > 0:
                    fig.add_trace(go.Violin(
                        y=df_type['price'].dropna(),
                        name=ptype,
                        box_visible=True,
                        meanline_visible=True,
                        fillcolor=colors[i % len(colors)],
                        opacity=0.6,
                        line_color=colors[i % len(colors)]
                    ))
            
            fig.update_layout(
                title=dict(
                    text='🎻 Distribution des Prix - Violin Plot',
                    font=dict(size=20, family='Outfit, sans-serif'),
                    x=0
                ),
                yaxis_title="Prix (FCFA)",
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=500,
                showlegend=True,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
            )
            
            return fig
            
        except Exception as e:
            print(f"Erreur violin plot: {e}")
            traceback.print_exc()
            return self._create_empty_graph(f"Erreur: {str(e)}", "🎻 Violin Plot Superposé")
    
    def create_stacked_3d_surface(self, data):
        """Surface 3D empilée prix/surface/localisation"""
        try:
            if data is None or len(data) == 0:
                return self._create_empty_graph("Aucune donnée disponible", " Surface 3D")
            
            df = pd.DataFrame(data) if isinstance(data, list) else data
            
            required_cols = ['price', 'surface_area', 'city']
            if not all(col in df.columns for col in required_cols):
                return self._create_empty_graph("Colonnes manquantes", " Surface 3D")
            
            df_clean = df[df['surface_area'].notna() & (df['surface_area'] > 0)].copy()
            
            if df_clean.empty:
                return self._create_empty_graph("Pas assez de données", " Surface 3D")
            
            # Agréger par ville et tranche de surface
            df_clean['surface_bin'] = pd.cut(df_clean['surface_area'], bins=10)
            pivot = df_clean.groupby(['city', 'surface_bin'])['price'].mean().reset_index()
            pivot_table = pivot.pivot(index='city', columns='surface_bin', values='price')
            
            fig = go.Figure(data=[go.Surface(
                z=pivot_table.values,
                x=list(range(len(pivot_table.columns))),
                y=list(range(len(pivot_table.index))),
                colorscale='Viridis',
                colorbar=dict(title="Prix Moyen")
            )])
            
            fig.update_layout(
                title=dict(
                    text=' Surface 3D: Prix × Surface × Ville',
                    font=dict(size=20, family='Outfit, sans-serif'),
                    x=0
                ),
                scene=dict(
                    xaxis_title='Surface',
                    yaxis_title='Ville',
                    zaxis_title='Prix Moyen',
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.3))
                ),
                height=600,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            return fig
            
        except Exception as e:
            print(f"Erreur 3D surface: {e}")
            return self._create_empty_graph(f"Erreur: {str(e)}", " Surface 3D")
    
    def create_multi_layer_heatmap(self, data):
        """Heatmap multi-couches corrélations avancées"""
        try:
            if data is None or len(data) == 0:
                return self._create_empty_graph("Aucune donnée disponible", "🔥 Heatmap Corrélations")
            
            df = pd.DataFrame(data) if isinstance(data, list) else data
            
            numeric_cols = ['price', 'surface_area', 'bedrooms', 'bathrooms', 'price_per_m2']
            available_cols = [col for col in numeric_cols if col in df.columns]
            
            if len(available_cols) < 2:
                return self._create_empty_graph("Pas assez de colonnes numériques", "🔥 Heatmap Corrélations")
            
            df_numeric = df[available_cols].dropna()
            
            if df_numeric.empty or len(df_numeric) < 2:
                return self._create_empty_graph("Pas assez de données", "🔥 Heatmap Corrélations")
            
            corr = df_numeric.corr()
            
            fig = go.Figure(data=go.Heatmap(
                z=corr.values,
                x=corr.columns,
                y=corr.columns,
                colorscale='RdBu',
                zmid=0,
                text=corr.values.round(2),
                texttemplate='%{text}',
                textfont={"size": 12},
                colorbar=dict(title="Corrélation", x=1.1)
            ))
            
            fig.update_layout(
                title=dict(
                    text='🔥 Matrice de Corrélation Multi-Variables',
                    font=dict(size=20, family='Outfit, sans-serif'),
                    x=0
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=500,
                xaxis=dict(tickangle=-45),
                margin=dict(l=100, r=100, t=80, b=100)
            )
            
            return fig
            
        except Exception as e:
            print(f"Erreur heatmap: {e}")
            return self._create_empty_graph(f"Erreur: {str(e)}", "🔥 Heatmap Corrélations")
    
    def create_stacked_area_trends(self, data):
        """Graphique en aires empilées - tendances temporelles"""
        try:
            if data is None or len(data) == 0:
                return self._create_empty_graph("Aucune donnée disponible", " Tendances Temporelles")
            
            df = pd.DataFrame(data) if isinstance(data, list) else data
            
            if 'posted_time' not in df.columns or 'property_type' not in df.columns:
                return self._create_empty_graph("Colonnes manquantes", " Tendances Temporelles")
            
            df_dated = df[df['posted_time'].notna()].copy()
            
            if df_dated.empty:
                return self._create_empty_graph("Pas de dates disponibles", " Tendances Temporelles")
            
            df_dated['date'] = pd.to_datetime(df_dated['posted_time']).dt.date
            
            # Compter par type et date
            trend = df_dated.groupby(['date', 'property_type']).size().reset_index(name='count')
            
            # Filtrer les types avec au moins quelques données
            trend = trend[trend['count'] > 0]
            
            if trend.empty:
                return self._create_empty_graph("Pas assez de données", " Tendances Temporelles")
            
            fig = go.Figure()
            
            colors = [self.COLORS['primary'], self.COLORS['secondary'], 
                     self.COLORS['success'], self.COLORS['warning'], self.COLORS['info']]
            
            for i, ptype in enumerate(trend['property_type'].unique()):
                df_type = trend[trend['property_type'] == ptype]
                fig.add_trace(go.Scatter(
                    x=df_type['date'],
                    y=df_type['count'],
                    mode='lines',
                    name=ptype,
                    stackgroup='one',
                    fillcolor=f'rgba({int(colors[i % len(colors)][1:3], 16)}, {int(colors[i % len(colors)][3:5], 16)}, {int(colors[i % len(colors)][5:7], 16)}, 0.6)'
                ))
            
            fig.update_layout(
                title=dict(
                    text=' Évolution Temporelle des Annonces',
                    font=dict(size=20, family='Outfit, sans-serif'),
                    x=0
                ),
                xaxis_title="Date",
                yaxis_title="Nombre d'annonces",
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=450,
                hovermode='x unified',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
            )
            
            return fig
            
        except Exception as e:
            print(f"Erreur stacked area: {e}")
            traceback.print_exc()
            return self._create_empty_graph(f"Erreur: {str(e)}", " Tendances Temporelles")
    
    def create_parallel_coords_advanced(self, data):
        """Coordonnées parallèles avancées"""
        try:
            if data is None or len(data) == 0:
                return self._create_empty_graph("Aucune donnée disponible", " Coordonnées Parallèles")
            
            df = pd.DataFrame(data) if isinstance(data, list) else data
            
            required_cols = ['price', 'surface_area', 'bedrooms', 'property_type']
            available_cols = [col for col in required_cols if col in df.columns]
            
            if len(available_cols) < 3:
                return self._create_empty_graph("Pas assez de variables", " Coordonnées Parallèles")
            
            df_clean = df[available_cols].dropna()
            
            if df_clean.empty or len(df_clean) < 10:
                return self._create_empty_graph("Pas assez de données", " Coordonnées Parallèles")
            
            # Échantillonner pour performance
            df_sample = df_clean.sample(min(500, len(df_clean)))
            
            # Créer le graphique
            dimensions = []
            
            for col in ['price', 'surface_area', 'bedrooms']:
                if col in df_sample.columns:
                    dimensions.append(dict(
                        label=col.replace('_', ' ').title(),
                        values=df_sample[col]
                    ))
            
            fig = go.Figure(data=go.Parcoords(
                line=dict(
                    color=df_sample['price'] if 'price' in df_sample.columns else None,
                    colorscale='Viridis',
                    showscale=True
                ),
                dimensions=dimensions
            ))
            
            fig.update_layout(
                title=dict(
                    text=' Coordonnées Parallèles Multi-Variables',
                    font=dict(size=20, family='Outfit, sans-serif'),
                    x=0
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=500
            )
            
            return fig
            
        except Exception as e:
            print(f"Erreur parallel coords: {e}")
            return self._create_empty_graph(f"Erreur: {str(e)}", " Coordonnées Parallèles")
    
    def create_treemap_sunburst_combo(self, data):
        """Combo Treemap + Sunburst hiérarchique"""
        try:
            if data is None or len(data) == 0:
                return self._create_empty_graph("Aucune donnée disponible", "🌳 Treemap Hiérarchique")
            
            df = pd.DataFrame(data) if isinstance(data, list) else data
            
            if 'city' not in df.columns or 'property_type' not in df.columns:
                return self._create_empty_graph("Colonnes manquantes", "🌳 Treemap Hiérarchique")
            
            # Filtrer les données invalides
            df_clean = df[
                df['city'].notna() & 
                df['property_type'].notna() & 
                df['price'].notna() & 
                (df['price'] > 0)
            ].copy()
            
            if df_clean.empty:
                return self._create_empty_graph("Pas de données valides", "🌳 Treemap Hiérarchique")
            
            # Agréger les données
            hierarchy = df_clean.groupby(['city', 'property_type']).agg({
                'price': ['count', 'mean']
            }).reset_index()
            
            hierarchy.columns = ['city', 'property_type', 'count', 'avg_price']
            
            # Filtrer les groupes avec au moins 1 enregistrement
            hierarchy = hierarchy[hierarchy['count'] > 0]
            
            if hierarchy.empty:
                return self._create_empty_graph("Pas de groupes valides", "🌳 Treemap Hiérarchique")
            
            fig = go.Figure(go.Treemap(
                labels=hierarchy['property_type'],
                parents=hierarchy['city'],
                values=hierarchy['count'],
                text=hierarchy['avg_price'].apply(lambda x: f"{x/1_000_000:.1f}M" if pd.notna(x) and x > 0 else "N/A"),
                textposition='middle center',
                marker=dict(
                    colorscale='Viridis',
                    colorbar=dict(title="Prix Moyen")
                )
            ))
            
            fig.update_layout(
                title=dict(
                    text='🌳 Treemap: Ville × Type × Volume',
                    font=dict(size=20, family='Outfit, sans-serif'),
                    x=0
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=600
            )
            
            return fig
            
        except Exception as e:
            print(f"Erreur treemap: {e}")
            traceback.print_exc()
            return self._create_empty_graph(f"Erreur: {str(e)}", "🌳 Treemap Hiérarchique")
    
    def create_bubble_matrix_4d(self, data):
        """Matrice de bulles 4D (X, Y, size, color)"""
        try:
            if data is None or len(data) == 0:
                return self._create_empty_graph("Aucune donnée disponible", "⚫ Matrice Bulles 4D")
            
            df = pd.DataFrame(data) if isinstance(data, list) else data
            
            required_cols = ['price', 'surface_area', 'bedrooms']
            if not all(col in df.columns for col in required_cols):
                return self._create_empty_graph("Colonnes manquantes", "⚫ Matrice Bulles 4D")
            
            df_clean = df[
                df['surface_area'].notna() & 
                (df['surface_area'] > 0) &
                df['bedrooms'].notna() &
                (df['bedrooms'] > 0)
            ].copy()
            
            if df_clean.empty or len(df_clean) < 10:
                return self._create_empty_graph("Pas assez de données", "⚫ Matrice Bulles 4D")
            
            # Échantillonner
            df_sample = df_clean.sample(min(300, len(df_clean)))
            
            # S'assurer qu'il n'y a pas de NaN dans les colonnes critiques
            df_sample = df_sample.dropna(subset=['surface_area', 'price', 'bedrooms'])
            
            if df_sample.empty:
                return self._create_empty_graph("Données incomplètes", "⚫ Matrice Bulles 4D")
            
            # Calculer la taille des bulles (avec fallback)
            bubble_sizes = df_sample['bedrooms'] * 10
            bubble_sizes = bubble_sizes.fillna(10).clip(lower=5, upper=50)
            
            fig = go.Figure(data=go.Scatter(
                x=df_sample['surface_area'],
                y=df_sample['price'],
                mode='markers',
                marker=dict(
                    size=bubble_sizes,
                    color=df_sample['price_per_m2'] if 'price_per_m2' in df_sample.columns else df_sample['price'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Prix/m²"),
                    line=dict(width=1, color='white'),
                    opacity=0.7
                ),
                text=df_sample.apply(
                    lambda x: f"Surface: {x['surface_area']:.0f}m²<br>Prix: {x['price']/1_000_000:.1f}M<br>Chambres: {int(x['bedrooms'])}",
                    axis=1
                ),
                hovertemplate='%{text}<extra></extra>'
            ))
            
            fig.update_layout(
                title=dict(
                    text='⚫ Matrice Bulles 4D: Surface × Prix × Chambres × Prix/m²',
                    font=dict(size=20, family='Outfit, sans-serif'),
                    x=0
                ),
                xaxis_title="Surface (m²)",
                yaxis_title="Prix (FCFA)",
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=600
            )
            
            return fig
            
        except Exception as e:
            print(f"Erreur bubble matrix: {e}")
            return self._create_empty_graph(f"Erreur: {str(e)}", "⚫ Matrice Bulles 4D")
    
    def create_clustering_3d(self, data):
        """Clustering K-Means 3D avec ML"""
        try:
            if data is None or len(data) == 0:
                return self._create_empty_graph("Aucune donnée disponible", " Clustering ML 3D")
            
            df = pd.DataFrame(data) if isinstance(data, list) else data
            
            required_cols = ['price', 'surface_area', 'bedrooms']
            available_cols = [col for col in required_cols if col in df.columns]
            
            if len(available_cols) < 3:
                return self._create_empty_graph("Pas assez de variables", " Clustering ML 3D")
            
            df_clean = df[available_cols].dropna()
            
            if df_clean.empty or len(df_clean) < 20:
                return self._create_empty_graph("Pas assez de données pour clustering", " Clustering ML 3D")
            
            # Préparer les données pour K-Means
            X = df_clean[available_cols].values
            
            # Normalisation
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # K-Means avec 4 clusters
            n_clusters = min(4, len(df_clean))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)
            
            df_clean['cluster'] = clusters
            
            # Graphique 3D
            fig = go.Figure(data=go.Scatter3d(
                x=df_clean['surface_area'],
                y=df_clean['price'],
                z=df_clean['bedrooms'],
                mode='markers',
                marker=dict(
                    size=6,
                    color=df_clean['cluster'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Cluster"),
                    line=dict(width=0.5, color='white'),
                    opacity=0.8
                ),
                text=df_clean.apply(
                    lambda x: f"Cluster {x['cluster']}<br>Surface: {x['surface_area']:.0f}m²<br>Prix: {x['price']/1_000_000:.1f}M<br>Chambres: {x['bedrooms']}",
                    axis=1
                ),
                hovertemplate='%{text}<extra></extra>'
            ))
            
            fig.update_layout(
                title=dict(
                    text=' Clustering K-Means 3D (ML)',
                    font=dict(size=20, family='Outfit, sans-serif'),
                    x=0
                ),
                scene=dict(
                    xaxis_title='Surface (m²)',
                    yaxis_title='Prix (FCFA)',
                    zaxis_title='Chambres',
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.3))
                ),
                height=650,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            return fig
            
        except Exception as e:
            print(f"Erreur clustering: {e}")
            traceback.print_exc()
            return self._create_empty_graph(f"Erreur: {str(e)}", " Clustering ML 3D")
    
    # ========================================================
    #              COMPOSANTS UI
    # ========================================================
    
    def create_kpi_card_gradient(self, title, value, icon, color, trend=None):
        """Carte KPI avec gradient"""
        return html.Div([
            html.Div([
                html.Div([
                    DashIconify(icon=icon, width=28, color="white")
                ], style={
                    'background': f'linear-gradient(135deg, {color}, {self.adjust_color_brightness(color, -20)})',
                    'borderRadius': '16px',
                    'padding': '14px',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'boxShadow': f'0 8px 16px {color}30',
                    'marginBottom': '16px'
                }),
                html.Div(title, style={
                    'fontSize': '13px',
                    'fontWeight': '500',
                    'color': self.COLORS['text_secondary'],
                    'marginBottom': '8px'
                }),
                html.Div(str(value), style={
                    'fontSize': '26px',
                    'fontWeight': '700',
                    'color': self.COLORS['text_primary'],
                    'marginBottom': '8px'
                }),
                html.Div([
                    DashIconify(
                        icon="mdi:trending-up" if trend and trend > 0 else "mdi:trending-neutral",
                        width=16,
                        color=self.COLORS['success'] if trend and trend > 0 else self.COLORS['text_secondary']
                    ),
                    html.Span(
                        f"+{trend}%" if trend and trend > 0 else "Stable",
                        style={
                            'fontSize': '12px',
                            'fontWeight': '600',
                            'color': self.COLORS['success'] if trend and trend > 0 else self.COLORS['text_secondary'],
                            'marginLeft': '4px'
                        }
                    )
                ], style={'display': 'flex', 'alignItems': 'center'}) if trend is not None else html.Div()
            ], style={
                'background': 'white',
                'borderRadius': '20px',
                'padding': '24px',
                'boxShadow': '0 4px 20px rgba(0,0,0,0.06)',
                'border': f'1px solid {self.COLORS["border"]}',
                'height': '100%'
            })
        ], style={'height': '100%'})
    
    def adjust_color_brightness(self, hex_color, percent):
        """Ajuste la luminosité d'une couleur"""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r = max(0, min(255, r + int(r * percent / 100)))
            g = max(0, min(255, g + int(g * percent / 100)))
            b = max(0, min(255, b + int(b * percent / 100)))
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return hex_color
    
    def format_number(self, num):
        """Formate un nombre"""
        if num == 0:
            return "0"
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        if num >= 1_000:
            return f"{num/1_000:.0f}K"
        return f"{int(num):,}".replace(',', ' ')
    
    # ========================================================
    #                      LAYOUT FINAL
    # ========================================================
    
    def setup_layout(self):
        """Layout avec gestion d'erreurs intégrée - CORRIGÉ"""
        
        # CORRECTION CRITIQUE: Injection CSS via base64 au lieu de % formatting
        css_b64 = base64.b64encode(self.custom_css.encode()).decode()
        
        self.app.layout = html.Div([
            # Injection CSS via base64
            html.Link(
                rel='stylesheet',
                href=f'data:text/css;base64,{css_b64}'
            ),
            
            # URL pour déclencher le chargement initial
            dcc.Location(id='analytics-url', refresh=False),
            
            # Store pour les données
            dcc.Store(id='analytics-data-store', data=[]),
            dcc.Store(id='debug-store', data={'status': 'initializing'}),
            
            # Header premium
            html.Div([
                html.Div([
                    html.Div([
                        DashIconify(icon="mdi:home-analytics", width=40, color="white"),
                        html.Div([
                            html.H1("Analytics Immobilier Ultra", style={
                                'fontSize': '32px', 'fontWeight': '800', 'color': 'white', 'margin': '0'
                            }),
                            html.P("Analyse multi-dimensionnelle en temps réel", style={
                                'fontSize': '14px', 'color': 'rgba(255,255,255,0.9)', 'margin': '4px 0 0 0'
                            })
                        ], style={'marginLeft': '16px'})
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                    
                    html.Div([
                        html.Div(style={
                            'width': '10px', 'height': '10px', 'background': '#10B981', 'borderRadius': '50%',
                            'animation': 'pulse 2s infinite', 'marginRight': '8px'
                        }),
                        html.Span("LIVE ANALYTICS", style={
                            'fontSize': '12px', 'fontWeight': '700', 'color': 'white', 'letterSpacing': '1px'
                        })
                    ], style={
                        'display': 'flex', 'alignItems': 'center',
                        'background': 'rgba(255,255,255,0.15)', 'padding': '10px 18px', 'borderRadius': '24px',
                        'backdropFilter': 'blur(10px)'
                    })
                ], style={
                    'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                    'maxWidth': '1800px', 'margin': '0 auto', 'padding': '0 32px'
                })
            ], style={
                'background': f'linear-gradient(135deg, {self.COLORS["primary"]}, {self.COLORS["purple"]})',
                'padding': '32px 0', 'boxShadow': '0 6px 24px rgba(99, 102, 241, 0.3)', 'marginBottom': '40px'
            }),
            
            # Zone de notification
            html.Div(id="notification-container", style={
                'position': 'fixed', 'top': '20px', 'right': '20px', 'zIndex': '9999'
            }),
            
            # Container principal
            html.Div([
                html.Div([
                    # Filtres avancés
                    html.Div([
                        html.Div([
                            DashIconify(icon="mdi:filter-variant", width=20, color=self.COLORS['primary']),
                            html.Span("Filtres Avancés", style={
                                'fontSize': '16px', 'fontWeight': '700',
                                'color': self.COLORS['text_primary'], 'marginLeft': '8px'
                            })
                        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),
                        
                        html.Div([
                            html.Div([
                                html.Label("Villes", style={
                                    'fontSize': '13px', 'fontWeight': '600',
                                    'color': self.COLORS['text_secondary'], 'marginBottom': '8px', 'display': 'block'
                                }),
                                dcc.Dropdown(
                                    id='filter-cities',
                                    options=[],
                                    value=[],
                                    multi=True,
                                    placeholder="Sélectionnez des villes",
                                    style={'borderRadius': '12px'}
                                )
                            ], style={'flex': '1', 'minWidth': '200px'}),
                            
                            html.Div([
                                html.Label("Types de biens", style={
                                    'fontSize': '13px', 'fontWeight': '600',
                                    'color': self.COLORS['text_secondary'], 'marginBottom': '8px', 'display': 'block'
                                }),
                                dcc.Dropdown(
                                    id='filter-properties',
                                    options=[],
                                    value=[],
                                    multi=True,
                                    placeholder="Sélectionnez des types",
                                    style={'borderRadius': '12px'}
                                )
                            ], style={'flex': '1', 'minWidth': '200px'}),
                            
                            html.Div([
                                html.Label("Statut (🔴 CRITIQUE)", style={
                                    'fontSize': '13px', 'fontWeight': '700',
                                    'color': self.COLORS['warning'], 'marginBottom': '8px', 'display': 'block'
                                }),
                                dcc.Dropdown(
                                    id='filter-status',
                                    options=[
                                        {'label': '🏘️ Tous', 'value': 'Tous'},
                                        {'label': '💰 Vente', 'value': 'Vente'},
                                        {'label': '🏠 Location', 'value': 'Location'}
                                    ],
                                    value='Tous',
                                    clearable=False,
                                    placeholder="Statut de l'annonce",
                                    style={'borderRadius': '12px'}
                                )
                            ], style={'flex': '1', 'minWidth': '200px'}),
                            
                            html.Div([
                                html.Label("Fourchette de prix", style={
                                    'fontSize': '13px', 'fontWeight': '600',
                                    'color': self.COLORS['text_secondary'], 'marginBottom': '8px', 'display': 'block'
                                }),
                                dcc.RangeSlider(
                                    id='filter-price-range',
                                    min=0,
                                    max=500_000_000,
                                    step=10_000_000,
                                    value=[0, 500_000_000],
                                    marks={
                                        0: '0',
                                        100_000_000: '100M',
                                        250_000_000: '250M',
                                        500_000_000: '500M'
                                    },
                                    tooltip={"placement": "bottom", "always_visible": False}
                                )
                            ], style={'flex': '1.5', 'minWidth': '250px'}),
                            
                            html.Button([
                                DashIconify(icon="mdi:refresh", width=20, color="white"),
                                html.Span("Actualiser", style={'marginLeft': '8px'})
                            ], id='btn-load-filtered', style={
                                'background': f'linear-gradient(135deg, {self.COLORS["primary"]}, {self.COLORS["purple"]})',
                                'color': 'white', 'border': 'none', 'borderRadius': '12px',
                                'padding': '12px 24px', 'fontSize': '14px', 'fontWeight': '600',
                                'cursor': 'pointer', 'display': 'flex', 'alignItems': 'center',
                                'alignSelf': 'flex-end', 'boxShadow': f'0 4px 12px {self.COLORS["primary"]}40'
                            })
                        ], style={
                            'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap', 'alignItems': 'flex-end'
                        })
                    ], style={
                        'background': 'white', 'padding': '24px', 'borderRadius': '20px',
                        'boxShadow': '0 4px 20px rgba(0,0,0,0.06)',
                        'border': f'1px solid {self.COLORS["border"]}', 'marginBottom': '32px'
                    }),
                    
                    # KPI Section
                    html.Div(id='kpi-section', children=[
                        html.Div("Chargement des KPIs...", style={'textAlign': 'center', 'padding': '20px'})
                    ], style={'marginBottom': '32px'}),
                    
                    # Graphiques Grid
                    html.Div([
                        html.Div(id='graph-violin', className='graph-container'),
                        html.Div(id='graph-heatmap', className='graph-container'),
                    ], style={
                        'display': 'grid',
                        'gridTemplateColumns': 'repeat(auto-fit, minmax(600px, 1fr))',
                        'gap': '24px',
                        'marginBottom': '24px'
                    }),
                    
                    html.Div([
                        html.Div(id='graph-3d-surface', className='graph-container'),
                        html.Div(id='graph-stacked-area', className='graph-container'),
                    ], style={
                        'display': 'grid',
                        'gridTemplateColumns': 'repeat(auto-fit, minmax(600px, 1fr))',
                        'gap': '24px',
                        'marginBottom': '24px'
                    }),
                    
                    html.Div([
                        html.Div(id='graph-parallel', className='graph-container'),
                        html.Div(id='graph-treemap', className='graph-container'),
                    ], style={
                        'display': 'grid',
                        'gridTemplateColumns': 'repeat(auto-fit, minmax(600px, 1fr))',
                        'gap': '24px',
                        'marginBottom': '24px'
                    }),
                    
                    html.Div([
                        html.Div(id='graph-bubble', className='graph-container'),
                        html.Div(id='graph-clustering', className='graph-container'),
                    ], style={
                        'display': 'grid',
                        'gridTemplateColumns': 'repeat(auto-fit, minmax(600px, 1fr))',
                        'gap': '24px',
                        'marginBottom': '24px'
                    })
                    
                ], style={
                    'maxWidth': '1800px',
                    'margin': '0 auto',
                    'padding': '0 32px 60px 32px'
                })
            ])
        ], style={
            'minHeight': '100vh',
            'background': '#F8FAFC'
        })
    
    @property
    def graph_style(self):
        """Style pour les graphiques"""
        return {
            'background': 'white',
            'padding': '24px',
            'borderRadius': '20px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.06)',
            'border': f'1px solid {self.COLORS["border"]}'
        }
    
    # ========================================================
    #                      CALLBACKS
    # ========================================================
    
    def setup_callbacks(self):
        """Configuration des callbacks"""
        
        @self.app.callback(
            [
                Output('notification-container', 'children'),
                Output('debug-store', 'data')
            ],
            Input('analytics-url', 'pathname')
        )
        def check_system_on_load(path):
            """Vérifier le système au chargement"""
            try:
                status, message, details = self.check_database_connection()
                
                if status:
                    notification = ErrorManager.notify_success("Système OK", message)
                else:
                    notification = ErrorManager.notify_warning("Attention", message)
                
                return notification, {'status': 'ready', 'db_status': status, 'details': details}
                
            except Exception as e:
                notification = ErrorManager.notify_error(
                    "Erreur Système",
                    str(e),
                    traceback.format_exc()
                )
                return notification, {'status': 'error', 'error': str(e)}
        
        @self.app.callback(
            [
                Output('filter-cities', 'options'),
                Output('filter-properties', 'options')
            ],
            Input('analytics-url', 'pathname')
        )
        def load_filter_options(path):
            """Charger les options de filtres"""
            try:
                df = self.get_enriched_data(limit=10000)
                
                if df.empty:
                    return [], []
                
                cities = sorted(df['city'].dropna().unique().tolist())
                property_types = sorted(df['property_type'].dropna().unique().tolist())
                
                city_options = [{'label': f'📍 {city}', 'value': city} for city in cities]
                type_options = [{'label': f'🏠 {ptype}', 'value': ptype} for ptype in property_types]
                
                return city_options, type_options
                
            except Exception as e:
                print(f"Erreur chargement options: {e}")
                return [], []
        
        @self.app.callback(
            Output('analytics-data-store', 'data'),
            [
                Input('btn-load-filtered', 'n_clicks'),
                Input('analytics-url', 'pathname')
            ],
            [
                State('filter-cities', 'value'),
                State('filter-properties', 'value'),
                State('filter-price-range', 'value'),
                State('filter-status', 'value')
            ]
        )
        def load_with_filters(n_clicks, path, cities, properties, price_range, status):
            """Charger les données avec filtres + FILTRE STATUT CRITIQUE"""
            try:
                filters = {}
                
                if cities and len(cities) > 0:
                    filters['cities'] = cities
                
                if properties and len(properties) > 0:
                    filters['property_types'] = properties
                
                if price_range:
                    filters['price_range'] = price_range
                
                df = self.get_enriched_data(filters=filters if filters else None, limit=5000)
                
                if df.empty:
                    return []
                
                # 🔴 CRITIQUE: FILTRER PAR STATUT AVANT TOUTE ANALYSE
                if status and status != 'Tous' and 'status' in df.columns:
                    df = df[df['status'] == status].copy()
                    print(f"✅ Données filtrées par statut: {status} -> {len(df)} enregistrements")
                
                if df.empty:
                    print(f"⚠️ Aucune donnée après filtre statut: {status}")
                    return []
                
                # Convertir en dict pour le store
                data = df.to_dict('records')
                
                return data
                
            except Exception as e:
                print(f"Erreur chargement données: {e}")
                traceback.print_exc()
                return []
        
        @self.app.callback(
            Output('kpi-section', 'children'),
            Input('analytics-data-store', 'data')
        )
        def update_kpis(data):
            """Mettre à jour les KPIs"""
            try:
                if not data or len(data) == 0:
                    return html.Div("Aucune donnée disponible", style={
                        'textAlign': 'center',
                        'padding': '40px',
                        'color': self.COLORS['text_secondary']
                    })
                
                kpis = self.calculate_ultra_kpis(data)
                
                return html.Div([
                    html.Div([
                        self.create_kpi_card_gradient(
                            "Annonces Totales",
                            f"{kpis['total']:,}".replace(',', ' '),
                            "mdi:file-document-multiple",
                            self.COLORS['primary']
                        ),
                        self.create_kpi_card_gradient(
                            "Prix Médian",
                            f"{self.format_number(kpis['median_price'])} FCFA",
                            "mdi:currency-usd",
                            self.COLORS['success'],
                            kpis.get('growth_rate', 0)
                        ),
                        self.create_kpi_card_gradient(
                            "Prix Moyen/m²",
                            f"{self.format_number(kpis['avg_price_m2'])} FCFA",
                            "mdi:ruler-square",
                            self.COLORS['info']
                        ),
                        self.create_kpi_card_gradient(
                            "Volatilité",
                            f"{kpis['price_volatility']:.1f}%",
                            "mdi:chart-line-variant",
                            self.COLORS['warning']
                        ),
                        self.create_kpi_card_gradient(
                            "Liquidité Marché",
                            f"{kpis['market_liquidity']:.0f}%",
                            "mdi:water-percent",
                            self.COLORS['teal']
                        )
                    ], style={
                        'display': 'grid',
                        'gridTemplateColumns': 'repeat(auto-fit, minmax(220px, 1fr))',
                        'gap': '20px'
                    })
                ])
                
            except Exception as e:
                print(f"Erreur update KPIs: {e}")
                return self._create_error_component("Erreur KPIs", e, traceback.format_exc())
        
        @self.app.callback(
            [
                Output('graph-violin', 'children'),
                Output('graph-heatmap', 'children'),
                Output('graph-3d-surface', 'children'),
                Output('graph-stacked-area', 'children'),
                Output('graph-parallel', 'children'),
                Output('graph-treemap', 'children'),
                Output('graph-bubble', 'children'),
                Output('graph-clustering', 'children')
            ],
            Input('analytics-data-store', 'data')
        )
        def update_all_graphs(data):
            """Mettre à jour tous les graphiques - DONNÉES DÉJÀ FILTRÉES PAR STATUT"""
            try:
                if not data or len(data) == 0:
                    empty = html.Div("Aucune donnée - Vérifiez les filtres (notamment le STATUT)", style={
                        'textAlign': 'center', 'padding': '40px',
                        'background': 'white', 'borderRadius': '20px',
                        'boxShadow': '0 4px 20px rgba(0,0,0,0.06)',
                        'color': self.COLORS['warning']
                    })
                    return [empty] * 8
                
                # Vérifier que les données ont bien le champ status
                df_check = pd.DataFrame(data)
                if 'status' in df_check.columns:
                    status_counts = df_check['status'].value_counts().to_dict()
                    print(f"✅ Graphiques avec données filtrées: {status_counts}")
                else:
                    print("⚠️ Champ 'status' manquant dans les données")
                
                graphs = [
                    html.Div([
                        dcc.Graph(figure=self.create_superposed_violin_ridgeplot(data), config={'displayModeBar': False})
                    ], style=self.graph_style),
                    
                    html.Div([
                        dcc.Graph(figure=self.create_multi_layer_heatmap(data), config={'displayModeBar': False})
                    ], style=self.graph_style),
                    
                    html.Div([
                        dcc.Graph(figure=self.create_stacked_3d_surface(data), config={'displayModeBar': False})
                    ], style=self.graph_style),
                    
                    html.Div([
                        dcc.Graph(figure=self.create_stacked_area_trends(data), config={'displayModeBar': False})
                    ], style=self.graph_style),
                    
                    html.Div([
                        dcc.Graph(figure=self.create_parallel_coords_advanced(data), config={'displayModeBar': False})
                    ], style=self.graph_style),
                    
                    html.Div([
                        dcc.Graph(figure=self.create_treemap_sunburst_combo(data), config={'displayModeBar': False})
                    ], style=self.graph_style),
                    
                    html.Div([
                        dcc.Graph(figure=self.create_bubble_matrix_4d(data), config={'displayModeBar': False})
                    ], style=self.graph_style),
                    
                    html.Div([
                        dcc.Graph(figure=self.create_clustering_3d(data), config={'displayModeBar': False})
                    ], style=self.graph_style)
                ]
                
                return graphs
                
            except Exception as e:
                print(f"Erreur update graphs: {e}")
                traceback.print_exc()
                error = self._create_error_component("Erreur Graphiques", e, traceback.format_exc())
                return [error] * 8


# analytics_dashboard.py - FIN DU FICHIER

def create_ultra_dashboard(server=None, routes_pathname_prefix="/analytics/", requests_pathname_prefix="/analytics/"):
    """Factory function pour créer le dashboard analytics avec sidebar"""
    try:
        dashboard = AnalyticsDashboard(
            server=server,
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix
        )
        print("✅ Analytics Dashboard créé avec sidebar cohérent")
        return dashboard.app
        
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE création dashboard: {e}")
        import traceback
        traceback.print_exc()
        raise