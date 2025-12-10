import dash
from dash import html, dcc, Input, Output, State, callback, dash_table, ctx
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

warnings.filterwarnings('ignore')

# ============================================================
#                    GESTIONNAIRE D'ERREURS
# ============================================================

class ErrorManager:
    """Centralise la gestion des erreurs et les notifications UI"""
    
    @staticmethod
    def notify_success(title, message):
        return dmc.Notification(
            title=title,
            message=message,
            color="green",
            autoClose=4000,
            icon=DashIconify(icon="mdi:check-circle", width=24)
        )
    
    @staticmethod
    def notify_error(title, message, details=None):
        return html.Div([
            dmc.Notification(
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
                    'background': '#f8f9fa',
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
            title=title,
            message=message,
            color="yellow",
            autoClose=6000,
            icon=DashIconify(icon="mdi:alert", width=24)
        )
    
    @staticmethod
    def notify_info(title, message):
        return dmc.Notification(
            title=title,
            message=message,
            color="blue",
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
        'gradient_3': ['#4FACFE', '#00F2FE'], 'gradient_4': ['#43E97B', '#38F9D7']
    }
    
    def __init__(self, server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
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
            suppress_callback_exceptions=True
        )
        
        self._data_cache = {}
        self._debug_mode = True  # Activez/Désactivez le mode debug ici
        
        if server:
            with server.app_context():
                self.setup_layout()
                self.setup_callbacks()
    
    # ========================================================
    #              DATA LOADING AVEC GESTION D'ERREURS
    # ========================================================
    
    def check_database_connection(self):
        """Vérifie la connexion DB et retourne statut + message"""
        try:
            from app.database.models import db
            
            # Test simple
            db.session.execute("SELECT 1")
            
            # Vérifier quelles tables contiennent des données
            from app.database.models import ProprietesConsolidees, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
            
            consolidated_count = db.session.query(ProprietesConsolidees).count()
            sources_count = {
                'CoinAfrique': db.session.query(CoinAfrique).count(),
                'ExpatDakar': db.session.query(ExpatDakarProperty).count(),
                'LogerDakar': db.session.query(LogerDakarProperty).count()
            }
            
            total_sources = sum(sources_count.values())
            
            if consolidated_count > 0:
                return True, "✅ Base de données OK", {
                    'consolidated': consolidated_count,
                    'sources': sources_count,
                    'message': f"{consolidated_count} propriétés consolidées chargées"
                }
            elif total_sources > 0:
                return False, "⚠️ Table consolidée vide, utilisation des sources", {
                    'consolidated': 0,
                    'sources': sources_count,
                    'message': f"Utilisation des tables sources ({total_sources} enregistrements)"
                }
            else:
                return False, "❌ Aucune donnée disponible", {
                    'consolidated': 0,
                    'sources': sources_count,
                    'message': "Toutes les tables sont vides"
                }
                
        except ImportError as e:
            return False, "❌ Erreur d'import des modèles", {
                'error': str(e),
                'message': "Vérifiez app.database.models"
            }
        except Exception as e:
            return False, "❌ Erreur de connexion DB", {
                'error': str(e),
                'message': traceback.format_exc()
            }
    
    def get_enriched_data(self, filters=None, limit=5000):
        """Charge et normalise les données avec fallback intelligent"""
        cache_key = hash(str(sorted(filters.items())) if filters else "all")
        if cache_key in self._data_cache:
            return self._data_cache[cache_key], None  # (data, error)
        
        try:
            from app.database.models import db, ProprietesConsolidees, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
            
            # Vérification DB
            db_ok, message, details = self.check_database_connection()
            
            if not db_ok and details['consolidated'] == 0:
                # Fallback sur les tables sources
                print(f"⚠️ {message}")
                return self._load_from_sources(filters, limit), details
            
            # Chargement depuis table consolidée
            query = db.session.query(ProprietesConsolidees)
            
            # Application des filtres
            if filters:
                conditions = []
                if filters.get('cities'):
                    conditions.append(ProprietesConsolidees.city.in_(filters['cities']))
                if filters.get('properties'):
                    conditions.append(ProprietesConsolidees.property_type.in_(filters['properties']))
                
                # Filtres numériques
                if filters.get('min_price'):
                    conditions.append(ProprietesConsolidees.price >= filters['min_price'])
                if filters.get('max_price'):
                    conditions.append(ProprietesConsolidees.price <= filters['max_price'])
                
                if conditions:
                    query = query.filter(and_(*conditions))
            
            # Exécuter la requête
            records = query.limit(limit).all()
            
            if not records:
                return [], {'message': 'Aucune donnée ne correspond aux filtres'}
            
            # Normalisation
            data = self._normalize_records(records, 'ProprietesConsolidees')
            
            # Mise en cache
            self._data_cache[cache_key] = data
            import threading
            threading.Timer(90.0, lambda: self._data_cache.pop(cache_key, None)).start()
            
            return data, None
            
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"❌ ERREUR CRITIQUE dans get_enriched_data: {error_details}")
            return [], {'error': str(e), 'details': error_details}
    
    def _load_from_sources(self, filters, limit):
        """Fallback: charge depuis les tables sources directement"""
        try:
            from app.database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
            
            all_data = []
            
            # Chargement et normalisation de chaque source
            for model, source_name in [(CoinAfrique, 'CoinAfrique'), 
                                     (ExpatDakarProperty, 'ExpatDakar'), 
                                     (LogerDakarProperty, 'LogerDakar')]:
                try:
                    query = db.session.query(model)
                    
                    # Application des filtres basiques
                    if filters:
                        if filters.get('cities'):
                            query = query.filter(model.city.in_(filters['cities']))
                        if filters.get('min_price'):
                            query = query.filter(model.price >= filters['min_price'])
                    
                    records = query.limit(limit // 3).all()
                    all_data.extend(self._normalize_records(records, source_name))
                    
                except Exception as e:
                    print(f"⚠️ Erreur chargement {source_name}: {e}")
                    continue
            
            return all_data
            
        except Exception as e:
            print(f"❌ Erreur fallback sources: {e}")
            return []
    
    def _normalize_records(self, records, source_name):
        """Normalise les records en format uniforme"""
        try:
            normalized = []
            for r in records:
                # Convertit en dict si nécessaire
                data = r.to_dict() if hasattr(r, 'to_dict') else self._record_to_dict(r)
                
                # Normalisation des champs
                normalized.append({
                    'id': str(data.get('id', '')),
                    'title': data.get('title', 'Sans titre'),
                    'price': float(data['price']) if data.get('price') else None,
                    'price_per_m2': self._calculate_price_per_m2(data),
                    'city': data.get('city', 'Non spécifié'),
                    'district': data.get('region', data.get('district')),
                    'property_type': data.get('property_type', 'Autre'),
                    'bedrooms': data.get('bedrooms'),
                    'bathrooms': data.get('bathrooms'),
                    'surface_area': data.get('surface_area'),
                    'source': source_name,
                    'quality_score': data.get('quality_score'),
                    'sentiment': data.get('description_sentiment'),
                    'scraped_at': data.get('scraped_at'),
                    'view_count': data.get('view_count', 0),
                    'age_days': self._calculate_age(data.get('scraped_at'))
                })
            return normalized
        except Exception as e:
            print(f"❌ Erreur normalisation: {e}")
            return []
    
    def _record_to_dict(self, record):
        """Convertit un record SQLAlchemy en dict (fallback)"""
        try:
            return {c.name: getattr(record, c.name) for c in record.__table__.columns}
        except:
            return {}
    
    def _calculate_price_per_m2(self, data):
        """Calcule prix/m² si possible"""
        try:
            price = data.get('price')
            surface = data.get('surface_area')
            if price and surface and surface > 0:
                return float(price) / float(surface)
            return None
        except:
            return None
    
    def _calculate_age(self, scraped_at):
        """Calcule l'âge en jours"""
        try:
            if scraped_at:
                return (datetime.utcnow() - scraped_at).days
            return None
        except:
            return None
    
    # ========================================================
    #              CALCULS STATISTIQUES AVANCÉS
    # ========================================================
    
    def calculate_ultra_kpis(self, data):
        """KPIs avec analyses statistiques avancées ET gestion d'erreurs"""
        if not data or not isinstance(data, list) or len(data) == 0:
            return {'error': 'Aucune donnée à analyser'}
        
        try:
            df = pd.DataFrame(data)
            
            # Vérification des colonnes nécessaires
            required_cols = ['price']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {'error': f'Colonnes manquantes: {missing_cols}'}
            
            # KPIs de base
            kpis = {
                'count': len(df),
                'avg_price': df['price'].mean(),
                'median_price': df['price'].median(),
                'std_price': df['price'].std(),
                'avg_price_per_m2': df['price_per_m2'].mean() if 'price_per_m2' in df else 0,
                'avg_quality': df['quality_score'].mean() if 'quality_score' in df else 0,
                'avg_sentiment': df['sentiment'].mean() if 'sentiment' in df else 0,
            }
            
            # Variations et tendances
            try:
                q10, q90 = df['price'].quantile([0.1, 0.9])
                kpis['price_volatility'] = ((q90 - q10) / kpis['median_price']) * 100 if kpis['median_price'] > 0 else 0
            except:
                kpis['price_volatility'] = 0
            
            # Score d'opportunité
            try:
                if 'price_per_m2' in df and 'quality_score' in df:
                    df['opportunity_score'] = (
                        (df['quality_score'].fillna(50) / 100) * 0.4 + 
                        (1 / (df['price_per_m2'].fillna(1) / df['price_per_m2'].median())) * 0.3 +
                        (df['view_count'].fillna(0) / max(df['view_count'].max(), 1)) * 0.2 +
                        (1 - df['age_days'].fillna(0) / max(df['age_days'].max(), 1)) * 0.1
                    )
                    top_ops = df.nlargest(5, 'opportunity_score')
                    kpis['opportunities'] = top_ops.to_dict('records')
            except Exception as e:
                print(f"⚠️ Erreur calcul opportunités: {e}")
                kpis['opportunities'] = []
            
            # Anomalies
            try:
                if 'price_per_m2' in df:
                    clean_prices = df['price_per_m2'].dropna()
                    if len(clean_prices) > 10:
                        z_scores = np.abs(stats.zscore(clean_prices))
                        anomalies = df.loc[clean_prices.index[z_scores > 3]]
                        kpis['anomalies'] = anomalies.head(3).to_dict('records')
                        kpis['anomaly_count'] = len(anomalies)
            except:
                kpis['anomalies'] = []
                kpis['anomaly_count'] = 0
            
            # Tendances par ville
            try:
                if 'city' in df:
                    city_trends = df.groupby('city').agg({
                        'price': ['median', 'count'],
                        'price_per_m2': 'mean'
                    }).round(2)
                    city_trends.columns = ['median_price', 'count', 'avg_price_m2']
                    kpis['city_trends'] = city_trends.reset_index().to_dict('records')
            except:
                kpis['city_trends'] = []
            
            return kpis
            
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"❌ Erreur calcul KPIs: {error_details}")
            return {'error': f'Calcul KPIs échoué: {str(e)}', 'details': error_details}
    
    # ========================================================
    #              GRAPHIQUES AVEC GESTION D'ERREURS
    # ========================================================
    
    def _create_empty_graph(self, message, title):
        """Crée un graphe vide avec message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor="center", yanchor="middle",
            showarrow=False,
            font=dict(size=16, color="#64748B")
        )
        fig.update_layout(
            title=title,
            paper_bgcolor='white',
            plot_bgcolor='white',
            height=400
        )
        return dcc.Graph(figure=fig, config={'displayModeBar': False})
    
    def _create_error_component(self, title, error, details):
        """Crée un composant d'erreur UI"""
        return html.Div([
            html.Div([
                DashIconify(icon="mdi:alert-circle", width=48, color="#EF4444"),
                html.H3(f"Erreur: {title}", style={'color': '#EF4444', 'marginTop': '12px'}),
                html.P(error, style={'color': '#64748B'}),
                html.Details([
                    html.Summary("Détails techniques"),
                    html.Pre(details, style={
                        'background': '#f8f9fa', 'padding': '12px', 'borderRadius': '8px',
                        'fontSize': '11px', 'maxHeight': '150px', 'overflow': 'auto'
                    })
                ], style={'marginTop': '12px'}) if self._debug_mode else None
            ], style={'textAlign': 'center', 'padding': '40px'})
        ], style={'background': 'white', 'borderRadius': '12px', 'border': '2px solid #fecaca'})
    
    def create_superposed_violin_ridgeplot(self, data):
        """Violin plot superposé (ridge plot) - Distribution par ville"""
        try:
            if not data:
                return go.Figure()
            
            df = pd.DataFrame(data)
            cities = df['city'].value_counts().head(8).index
            
            fig = go.Figure()
            for i, city in enumerate(cities):
                city_data = df[df['city'] == city]['price'].dropna()
                fig.add_trace(go.Violin(
                    y=city_data,
                    name=city,
                    side='positive',
                    spanmode='hard',
                    line_color=self.COLORS['primary'],
                    fillcolor=f'rgba(30, 64, 175, {0.6 - i*0.05})',
                    opacity=0.8,
                    meanline_visible=True,
                    width=2,
                    offsetgroup=i,
                    x0=i
                ))
            
            fig.update_layout(
                title="📈 Distribution Superposée des Prix par Ville (Ridge Plot)",
                xaxis_title="Ville",
                yaxis_title="Prix (FCFA)",
                height=600,
                showlegend=False,
                violingap=0,
                violingroupgap=0,
                violinmode='overlay',
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(family='Outfit', size=12),
                margin=dict(l=40, r=40, t=80, b=60)
            )
            return fig
        except Exception as e:
            print(f"❌ Erreur violins: {e}")
            return go.Figure()
    
    def create_stacked_3d_surface(self, data):
        """Surface 3D empilée - Prix, Surface, Qualité"""
        try:
            if not data:
                return go.Figure()
            
            df = pd.DataFrame(data)
            df = df.dropna(subset=['price', 'surface_area', 'quality_score'])
            
            if df.empty:
                return go.Figure()
            
            # Créer une grille pour la surface
            x_grid = np.linspace(df['surface_area'].min(), df['surface_area'].max(), 50)
            y_grid = np.linspace(df['quality_score'].min(), df['quality_score'].max(), 50)
            X, Y = np.meshgrid(x_grid, y_grid)
            
            # Interpolation des prix
            from scipy.interpolate import griddata
            Z = griddata(
                (df['surface_area'], df['quality_score']),
                df['price'],
                (X, Y),
                method='cubic'
            )
            
            fig = go.Figure(go.Surface(
                x=x_grid,
                y=y_grid,
                z=Z,
                colorscale='Viridis',
                colorbar=dict(title="Prix (FCFA)")
            ))
            
            fig.update_layout(
                title="🗻 Surface 3D Empilée : Prix = f(Surface, Qualité)",
                scene=dict(
                    xaxis_title="Surface (m²)",
                    yaxis_title="Score de Qualité",
                    zaxis_title="Prix (FCFA)",
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
                ),
                height=700,
                paper_bgcolor='white',
                font=dict(family='Outfit', size=12)
            )
            return fig
        except Exception as e:
            print(f"❌ Erreur surface 3D: {e}")
            return go.Figure()
    
    def create_multi_layer_heatmap(self, data):
        """Heatmap multi-couches : Corrélations + Densité"""
        try:
            if not data:
                return go.Figure()
            
            df = pd.DataFrame(data)
            numeric_cols = ['price', 'surface_area', 'bedrooms', 'bathrooms', 
                           'quality_score', 'sentiment', 'view_count']
            df_numeric = df[[col for col in numeric_cols if col in df.columns]].dropna()
            
            if df_numeric.empty:
                return go.Figure()
            
            # Corrélations
            corr_matrix = df_numeric.corr()
            
            # Densité (inverse de la variance)
            density = 1 / df_numeric.var()
            density_matrix = np.outer(density, density)
            
            # Combinaison : corrélation * densité
            combined_matrix = corr_matrix * density_matrix
            
            fig = go.Figure()
            
            # Heatmap principale
            fig.add_trace(go.Heatmap(
                z=combined_matrix.values,
                x=combined_matrix.columns,
                y=combined_matrix.index,
                colorscale='RdBu_r',
                zmid=0,
                text=combined_matrix.round(2).values,
                texttemplate="%{text}",
                textfont={"size": 10, "family": "Outfit"},
                hoverongaps=False,
                hovertemplate='%{x} vs %{y}<br>Valeur: %{z:.2f}<extra></extra>'
            ))
            
            # Overlay : contours de haute corrélation
            fig.add_trace(go.Contour(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                contours=dict(start=0.7, end=1.0, size=0.1),
                line=dict(width=2, color='rgba(0,0,0,0.8)'),
                showscale=False,
                showlegend=False
            ))
            
            fig.update_layout(
                title="🔥 Heatmap Multi-Couches : Corrélations × Densité",
                height=500,
                paper_bgcolor='white',
                font=dict(family='Outfit', size=12),
                margin=dict(l=40, r=40, t=80, b=60)
            )
            return fig
        except Exception as e:
            print(f"❌ Erreur heatmap: {e}")
            return go.Figure()
    
    def create_stacked_area_trends(self, data):
        """Aires empilées - Tendances temporelles par source"""
        try:
            if not data:
                return go.Figure()
            
            df = pd.DataFrame(data)
            if 'scraped_at' not in df or 'source' not in df:
                return go.Figure()
            
            df['scraped_at'] = pd.to_datetime(df['scraped_at'])
            df = df.set_index('scraped_at')
            
            # Grouper par semaine et source
            weekly_counts = df.groupby([pd.Grouper(freq='W'), 'source']).size().unstack(fill_value=0)
            
            fig = go.Figure()
            sources = weekly_counts.columns
            colors = px.colors.qualitative.Set3
            
            for i, source in enumerate(sources):
                fig.add_trace(go.Scatter(
                    x=weekly_counts.index,
                    y=weekly_counts[source],
                    mode='lines',
                    stackgroup='one',
                    name=source,
                    line=dict(width=0),
                    fillcolor=colors[i % len(colors)],
                    hovertemplate=f'{source}<br>Date: %{{x}}<br>Annonces: %{{y}}<extra></extra>'
                ))
            
            fig.update_layout(
                title="📊 Aires Empilées - Volume d'Annonces par Source (Semaine)",
                xaxis_title="Date",
                yaxis_title="Nombre d'annonces",
                height=450,
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(family='Outfit', size=12),
                hovermode='x unified'
            )
            return fig
        except Exception as e:
            print(f"❌ Erreur stacked area: {e}")
            return go.Figure()
    
    def create_parallel_coords_advanced(self, data):
        """Parallel coordinates avec coloration multi-dimensionnelle"""
        try:
            if not data:
                return go.Figure()
            
            df = pd.DataFrame(data)
            available_cols = [col for col in ['price', 'surface_area', 'bedrooms', 'quality_score', 'sentiment'] if col in df.columns]
            
            if not available_cols:
                return go.Figure()
            
            df_filtered = df[available_cols].dropna().head(300)  # Limiter pour performance
            
            if df_filtered.empty:
                return go.Figure()
            
            # Normalisation
            df_norm = (df_filtered - df_filtered.min()) / (df_filtered.max() - df_filtered.min())
            
            # Score composite pour coloration
            if 'price' in df_norm and 'quality_score' in df_norm:
                df_norm['composite'] = (
                    df_norm['price'] * 0.3 + 
                    df_norm['quality_score'] * 0.3 + 
                    (df_norm['sentiment'] if 'sentiment' in df_norm else 0) * 0.2 +
                    (df_norm['surface_area'] if 'surface_area' in df_norm else 0) * 0.2
                )
            else:
                df_norm['composite'] = df_norm.iloc[:, 0]  # Fallback
            
            fig = px.parallel_coordinates(
                df_norm,
                color='composite',
                dimensions=df_norm.columns[:-1],  # Exclure composite
                color_continuous_scale='Rainbow',
                title="🌈 Parallel Coordinates Avancé (Coloration Composite)"
            )
            
            fig.update_layout(
                height=500,
                paper_bgcolor='white',
                font=dict(family='Outfit', size=10),
                margin=dict(l=60, r=60, t=100, b=40)
            )
            return fig
        except Exception as e:
            print(f"❌ Erreur parallel coords: {e}")
            return go.Figure()
    
    def create_treemap_sunburst_combo(self, data):
        """Treemap + Sunburst combinés - Structure hiérarchique"""
        try:
            if not data:
                return go.Figure()
            
            df = pd.DataFrame(data)
            if 'source' not in df or 'city' not in df or 'property_type' not in df:
                return go.Figure()
            
            # Préparer la hiérarchie
            hierarchy = df.groupby(['source', 'city', 'property_type']).agg({
                'price': 'mean',
                'id': 'count'
            }).reset_index()
            hierarchy = hierarchy.rename(columns={'id': 'count'})
            
            fig = make_subplots(
                rows=1, cols=2,
                specs=[{"type": "treemap"}, {"type": "sunburst"}],
                subplot_titles=("Treemap - Valeur Marché", "Sunburst - Distribution")
            )
            
            # Treemap
            fig.add_trace(go.Treemap(
                labels=hierarchy['property_type'],
                parents=hierarchy['city'],
                values=hierarchy['price'],
                textinfo="label+value+percent parent",
                name="Treemap"
            ), row=1, col=1)
            
            # Sunburst
            fig.add_trace(go.Sunburst(
                labels=hierarchy['property_type'],
                parents=hierarchy['city'],
                values=hierarchy['count'],
                branchvalues="total",
                name="Sunburst"
            ), row=1, col=2)
            
            fig.update_layout(
                title_text="🏘️ Visualisation Hiérarchique Double (Treemap + Sunburst)",
                height=500,
                paper_bgcolor='white',
                font=dict(family='Outfit', size=12)
            )
            return fig
        except Exception as e:
            print(f"❌ Erreur treemap/sunburst: {e}")
            return go.Figure()
    
    def create_bubble_matrix_4d(self, data):
        """Bubble chart 4D : Prix, Surface, Qualité, Taille = Volume"""
        try:
            if not data:
                return go.Figure()
            
            df = pd.DataFrame(data)
            required_cols = ['price', 'surface_area', 'quality_score', 'view_count']
            if not all(col in df.columns for col in required_cols):
                return go.Figure()
            
            df = df.dropna(subset=required_cols)
            
            if df.empty:
                return go.Figure()
            
            # Limiter pour performance
            df_sample = df.sample(min(200, len(df)))
            
            fig = px.scatter(
                df_sample,
                x='surface_area',
                y='price',
                size='view_count',
                color='quality_score',
                hover_name='title',
                hover_data=['city', 'property_type'],
                color_continuous_scale='Viridis',
                size_max=40,
                title="🎈 Bubble Chart 4D : Surface × Prix × Vues × Qualité"
            )
            
            fig.update_layout(
                height=550,
                paper_bgcolor='white',
                font=dict(family='Outfit', size=12),
                xaxis_title="Surface (m²)",
                yaxis_title="Prix (FCFA)",
                coloraxis_colorbar=dict(title="Score Qualité")
            )
            return fig
        except Exception as e:
            print(f"❌ Erreur bubble 4D: {e}")
            return go.Figure()
    
    def create_candlestick_advanced(self, data):
        """Candlestick chart - Prix OHLC par district"""
        try:
            if not data:
                return go.Figure()
            
            df = pd.DataFrame(data)
            if 'district' not in df or 'price' not in df:
                return go.Figure()
            
            df = df.dropna(subset=['district', 'price'])
            
            if df.empty:
                return go.Figure()
            
            # Calculer OHLC par district
            district_stats = df.groupby('district')['price'].agg([
                'min', 'max', 'mean', 'median'
            ]).reset_index()
            
            fig = go.Figure(data=go.Candlestick(
                x=district_stats['district'],
                open=district_stats['median'],
                high=district_stats['max'],
                low=district_stats['min'],
                close=district_stats['mean'],
                increasing_line_color=self.COLORS['success'],
                decreasing_line_color=self.COLORS['danger']
            ))
            
            fig.update_layout(
                title="📉 Candlestick Avancé - Prix OHLC par District",
                yaxis_title="Prix (FCFA)",
                xaxis_title="District",
                height=500,
                paper_bgcolor='white',
                font=dict(family='Outfit', size=12),
                xaxis_rangeslider_visible=False
            )
            return fig
        except Exception as e:
            print(f"❌ Erreur candlestick: {e}")
            return go.Figure()
    
    def create_polar_scatter_multi(self, data):
        """Scatter plot polaire multi-dimensionnel"""
        try:
            if not data:
                return go.Figure()
            
            df = pd.DataFrame(data)
            required_cols = ['quality_score', 'sentiment', 'view_count']
            if not all(col in df.columns for col in required_cols):
                return go.Figure()
            
            df = df.dropna(subset=required_cols)
            
            if df.empty:
                return go.Figure()
            
            fig = go.Figure()
            
            property_types = df['property_type'].unique()
            colors = px.colors.qualitative.Prism
            
            for i, prop_type in enumerate(property_types):
                df_type = df[df['property_type'] == prop_type]
                
                fig.add_trace(go.Scatterpolar(
                    r=df_type['quality_score'],
                    theta=df_type['sentiment'],
                    mode='markers',
                    marker=dict(
                        size=df_type['view_count'] / 10,
                        color=colors[i % len(colors)],
                        opacity=0.7,
                        line=dict(width=1, color='white')
                    ),
                    name=prop_type,
                    hovertemplate='<b>%{text}</b><br>Qualité: %{r}<br>Sentiment: %{theta}<extra></extra>',
                    text=df_type['city']
                ))
            
            fig.update_layout(
                title="🎯 Scatter Polaire Multi-dimensionnel : Qualité × Sentiment × Vues",
                polar=dict(
                    radialaxis=dict(title="Score Qualité", range=[0, 100]),
                    angularaxis=dict(title="Sentiment")
                ),
                height=600,
                paper_bgcolor='white',
                font=dict(family='Outfit', size=12)
            )
            return fig
        except Exception as e:
            print(f"❌ Erreur polar scatter: {e}")
            return go.Figure()
    
    def create_funnel_advanced(self, data):
        """Funnel chart - Conversion qualité"""
        try:
            if not data:
                return go.Figure()
            
            df = pd.DataFrame(data)
            if 'quality_score' not in df:
                return go.Figure()
            
            # Créer segments de qualité
            quality_bins = pd.cut(df['quality_score'].fillna(50), 
                                 bins=[0, 30, 50, 70, 85, 100],
                                 labels=['🚨 Basse', '⚠️ Moyenne-Basse', '✅ Moyenne', 
                                        '⭐ Haute', '💎 Premium'])
            df['quality_segment'] = quality_bins
            
            funnel_data = df['quality_segment'].value_counts()
            
            fig = go.Figure(go.Funnel(
                y=funnel_data.index,
                x=funnel_data.values,
                textinfo="value+percent initial",
                textfont=dict(family="Outfit", size=14),
                marker=dict(
                    color=[self.COLORS['danger'], self.COLORS['warning'], 
                           self.COLORS['info'], self.COLORS['success'], 
                           self.COLORS['primary']],
                    line=dict(width=2, color='white')
                )
            ))
            
            fig.update_layout(
                title="🔻 Funnel Avancé - Distribution par Niveau de Qualité",
                height=500,
                paper_bgcolor='white',
                font=dict(family='Outfit', size=12)
            )
            return fig
        except Exception as e:
            print(f"❌ Erreur funnel: {e}")
            return go.Figure()
    
    def create_waterfall_advanced(self, data):
        """Waterfall chart - Impact des facteurs sur prix"""
        try:
            if not data:
                return go.Figure()
            
            df = pd.DataFrame(data)
            if 'price' not in df:
                return go.Figure()
            
            # Calculer l'impact moyen de chaque caractéristique
            baseline = df['price'].min()
            
            impacts = {
                'Prix de base': baseline,
                '+ Surface moyenne': df['surface_area'].mean() * 100000 if 'surface_area' in df else 0,
                '+ Chambres': df['bedrooms'].mean() * 5000000 if 'bedrooms' in df else 0,
                '+ Qualité': df['quality_score'].mean() * 50000 if 'quality_score' in df else 0,
                '+ Sentiment': (df['sentiment'].mean() + 1) * 1000000 if 'sentiment' in df else 0,
            }
            
            # Calculer les valeurs cumulées
            values = list(impacts.values())
            
            fig = go.Figure(go.Waterfall(
                name="Prix",
                orientation="v",
                measure=["absolute"] + ["relative"] * (len(values)-1),
                x=list(impacts.keys()),
                textposition="outside",
                text=[f"{v:,.0f}" for v in values],
                y=values,
                connector={"line":{"color":"rgb(63, 63, 63)"}},
                increasing={"marker":{"color":self.COLORS['success']}},
                decreasing={"marker":{"color":self.COLORS['danger']}},
                totals={"marker":{"color":self.COLORS['primary']}}
            ))
            
            fig.update_layout(
                title="💧 Waterfall Avancé - Décomposition du Prix Moyen",
                yaxis_title="Prix (FCFA)",
                height=500,
                paper_bgcolor='white',
                font=dict(family='Outfit', size=12)
            )
            return fig
        except Exception as e:
            print(f"❌ Erreur waterfall: {e}")
            return go.Figure()
    
    def create_clustering_3d(self, data):
        """Clustering K-means en 3D"""
        try:
            if not data:
                return go.Figure()
            
            df = pd.DataFrame(data)
            features = ['price', 'surface_area', 'quality_score']
            available_features = [f for f in features if f in df.columns]
            
            if len(available_features) < 2:
                return go.Figure()
            
            df_cluster = df[available_features].dropna()
            
            if len(df_cluster) < 10:
                return go.Figure()
            
            # Standardisation et clustering
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(df_cluster)
            
            n_clusters = min(5, len(df_cluster) // 3)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(X_scaled)
            
            df_cluster['cluster'] = clusters
            
            fig = px.scatter_3d(
                df_cluster,
                x='price',
                y='surface_area' if 'surface_area' in df_cluster else df_cluster.columns[1],
                z='quality_score' if 'quality_score' in df_cluster else df_cluster.columns[2] if len(df_cluster.columns) > 2 else df_cluster.columns[1],
                color='cluster',
                size_max=15,
                opacity=0.8,
                color_discrete_sequence=px.colors.qualitative.Set3,
                title="🧬 Clustering 3D - Segmentation Automatique du Marché"
            )
            
            fig.update_layout(
                height=600,
                paper_bgcolor='white',
                font=dict(family='Outfit', size=12),
                scene=dict(
                    xaxis_title="Prix (FCFA)",
                    yaxis_title="Surface (m²)",
                    zaxis_title="Qualité"
                )
            )
            return fig
        except Exception as e:
            print(f"❌ Erreur clustering: {e}")
            return go.Figure()
    
    def create_animation_timeseries(self, data):
        """Animation temporelle des prix par ville"""
        try:
            if not data:
                return go.Figure()
            
            df = pd.DataFrame(data)
            if 'scraped_at' not in df or 'city' not in df:
                return go.Figure()
            
            df['scraped_at'] = pd.to_datetime(df['scraped_at'])
            
            # Créer une plage de dates complète
            date_range = pd.date_range(
                start=df['scraped_at'].min(),
                end=df['scraped_at'].max(),
                freq='W'
            )
            
            # Agréger par ville et date
            animation_data = []
            for date in date_range:
                week_data = df[df['scraped_at'] <= date]
                city_stats = week_data.groupby('city')['price'].median().reset_index()
                city_stats['date'] = date
                animation_data.append(city_stats)
            
            if not animation_data:
                return go.Figure()
            
            df_anim = pd.concat(animation_data, ignore_index=True)
            top_cities = df['city'].value_counts().head(5).index
            df_anim = df_anim[df_anim['city'].isin(top_cities)]
            
            fig = px.line(
                df_anim,
                x='date',
                y='price',
                color='city',
                animation_frame='date',
                animation_group='city',
                range_y=[0, df_anim['price'].max() * 1.1],
                markers=True,
                title="📽️ Évolution Temporelle Animée des Prix par Ville"
            )
            
            fig.update_layout(
                height=500,
                paper_bgcolor='white',
                font=dict(family='Outfit', size=12),
                xaxis_title="Date",
                yaxis_title="Prix Médian (FCFA)"
            )
            
            # Ajuster la vitesse de l'animation
            fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 500
            
            return fig
        except Exception as e:
            print(f"❌ Erreur animation: {e}")
            return go.Figure()
    
    def create_dual_axis_advanced(self, data):
        """Graphe à double axe Y avancé"""
        try:
            if not data:
                return go.Figure()
            
            df = pd.DataFrame(data)
            if 'scraped_at' not in df:
                return go.Figure()
            
            # Grouper par mois
            df['scraped_at'] = pd.to_datetime(df['scraped_at'])
            monthly = df.set_index('scraped_at').groupby([pd.Grouper(freq='M')]).agg({
                'price': 'median',
                'view_count': 'sum'
            }).reset_index()
            
            fig = make_subplots(
                rows=1, cols=1,
                specs=[[{"secondary_y": True}]]
            )
            
            # Axe Y1 : Prix
            fig.add_trace(
                go.Scatter(
                    x=monthly['scraped_at'],
                    y=monthly['price'],
                    mode='lines+markers',
                    name="Prix Médian",
                    line=dict(color=self.COLORS['primary'], width=3),
                    marker=dict(size=8)
                ),
                secondary_y=False
            )
            
            # Axe Y2 : Vues
            fig.add_trace(
                go.Bar(
                    x=monthly['scraped_at'],
                    y=monthly['view_count'],
                    name="Volume de Vues",
                    marker=dict(color=self.COLORS['secondary'], opacity=0.6)
                ),
                secondary_y=True
            )
            
            fig.update_xaxes(title_text="Date")
            fig.update_yaxes(title_text="Prix Médian (FCFA)", secondary_y=False)
            fig.update_yaxes(title_text="Nombre de Vues", secondary_y=True)
            
            fig.update_layout(
                title_text="📊 Double Axe - Prix vs Volume d'Intérêt",
                height=450,
                paper_bgcolor='white',
                font=dict(family='Outfit', size=12),
                hovermode='x unified'
            )
            return fig
        except Exception as e:
            print(f"❌ Erreur dual axis: {e}")
            return go.Figure()
    
    # ========================================================
    #                    COMPOSANTS UI PREMIUM
    # ========================================================
    
    def create_kpi_card_gradient(self, title, value, icon, color, trend=None):
        """Carte KPI avec gestion d'erreurs"""
        try:
            return html.Div([
                html.Div([
                    html.Div([
                        DashIconify(icon=icon, width=32, color="white")
                    ], style={
                        'background': f'linear-gradient(135deg, {color}, {self.adjust_color_brightness(color, -30)})',
                        'borderRadius': '16px',
                        'padding': '16px',
                        'boxShadow': f'0 8px 20px {color}40'
                    }),
                    html.Div(title, style={
                        'fontSize': '14px',
                        'fontWeight': '600',
                        'color': '#64748B',
                        'marginTop': '16px'
                    }),
                    html.Div(value if value is not None else "N/A", style={
                        'fontSize': '28px',
                        'fontWeight': '800',
                        'color': '#1E293B',
                        'marginTop': '8px'
                    }),
                    html.Div(trend, style={
                        'fontSize': '12px',
                        'color': self.COLORS['success'] if trend and '+' in str(trend) else self.COLORS['danger'],
                        'fontWeight': '600',
                        'marginTop': '4px'
                    }) if trend else None
                ], style={
                    'background': 'white',
                    'borderRadius': '20px',
                    'padding': '24px',
                    'boxShadow': '0 4px 20px rgba(0,0,0,0.08)',
                    'border': '1px solid #E2E8F0',
                    'transition': 'all 0.3s ease'
                })
            ])
        except Exception as e:
            print(f"❌ Erreur création KPI card: {e}")
            return html.Div("Erreur KPI", style={'color': 'red'})
    
    def adjust_color_brightness(self, hex_color, percent):
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r = max(0, min(255, r + int(r * percent / 100)))
            g = max(0, min(255, g + int(g * percent / 100)))
            b = max(0, min(255, b + int(b * percent / 100)))
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return hex_color
    
    # ========================================================
    #                      LAYOUT FINAL
    # ========================================================
    
    def setup_layout(self):
        """Layout avec gestion d'erreurs intégrée"""
        
        # CSS personnalisé
        custom_css = """
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
        
        self.app.layout = html.Div([
            # Injection CSS
            html.Style(custom_css),
            
            # URL pour déclencher le chargement initial
            dcc.Location(id='url', refresh=False),
            
            # Debug store (visible en mode debug)
            dcc.Store(id='debug-store', data={'status': 'initializing'}),
            
            # Header premium
            html.Div([
                html.Div([
                    html.Div([
                        DashIconify(icon="mdi:home-analytics", width=40, color="white"),
                        html.Div([
                            html.H1("Observatoire Immobilier Ultra", style={
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
            
            # Filtres avancés
            html.Div([
                html.Div([
                    html.Div([
                        dmc.MultiSelect(
                            label="Villes (Multi-sélection)",
                            id="filter-cities",
                            data=[],  # Rempli par callback
                            placeholder="Sélectionnez une ou plusieurs villes",
                            style={'marginBottom': '16px'}
                        ),
                        dmc.MultiSelect(
                            label="Types de biens",
                            id="filter-properties",
                            data=[],  # Rempli par callback
                            placeholder="Sélectionnez des types",
                        )
                    ], style={'flex': '1'}),
                    
                    dmc.RangeSlider(
                        label="Prix (FCFA)",
                        id="price-range-slider",
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
                        style={'flex': '1', 'marginLeft': '24px'}
                    ),
                    
                    html.Button([
                        DashIconify(icon="mdi:filter-check", width=20, color="white"),
                        html.Span("Appliquer Filtres", style={'marginLeft': '8px'})
                    ], id="apply-filters", style={
                        'background': f'linear-gradient(135deg, {self.COLORS["success"]}, {self.adjust_color_brightness(self.COLORS["success"], -30)})',
                        'color': 'white', 'border': 'none', 'borderRadius': '12px',
                        'padding': '12px 24px', 'fontWeight': '600', 'cursor': 'pointer',
                        'marginLeft': '24px', 'alignSelf': 'flex-end',
                        'boxShadow': f'0 4px 12px {self.COLORS["success"]}40'
                    })
                ], style={
                    'display': 'flex', 'gap': '24px', 'alignItems': 'flex-end',
                    'maxWidth': '1800px', 'margin': '0 auto', 'padding': '0 32px'
                })
            ], style={'marginBottom': '40px'}),
            
            # Zone de statut
            html.Div(id="loading-status", style={
                'textAlign': 'center', 'padding': '20px', 'fontSize': '16px'
            }),
            
            # KPIs Section (cachée pendant le chargement)
            html.Div([
                html.Div(id="kpi-grid", style={
                    'display': 'grid',
                    'gridTemplateColumns': 'repeat(auto-fit, minmax(280px, 1fr))',
                    'gap': '24px',
                    'maxWidth': '1800px', 'margin': '0 auto', 'padding': '0 32px'
                })
            ], style={'marginBottom': '40px'}, id="kpi-section"),
            
            # Graphiques principaux - Grille 2x3
            html.Div([
                html.Div([
                    html.Div(id="graph-ridge", className="graph-container fade-in", style={**self.graph_style}),
                    html.Div(id="graph-3d-surface", className="graph-container fade-in", style={**self.graph_style}),
                ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '24px', 'marginBottom': '24px'}),
                
                html.Div([
                    html.Div(id="graph-heatmap", className="graph-container fade-in", style={**self.graph_style}),
                    html.Div(id="graph-stacked-area", className="graph-container fade-in", style={**self.graph_style}),
                ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '24px', 'marginBottom': '24px'}),
                
                html.Div([
                    html.Div(id="graph-parallel", className="graph-container fade-in", style={**self.graph_style}),
                    html.Div(id="graph-treemap-sunburst", className="graph-container fade-in", style={**self.graph_style}),
                ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '24px', 'marginBottom': '24px'}),
            ], style={'maxWidth': '1800px', 'margin': '0 auto', 'padding': '0 32px'}, id="graphs-grid-1"),
            
            # Graphiques 3D et spéciaux - Pleine largeur
            html.Div([
                html.Div(id="graph-bubble-4d", className="graph-container fade-in", style={**self.graph_style_full}),
                html.Div(id="graph-clustering-3d", className="graph-container fade-in", style={**self.graph_style_full}),
                html.Div(id="graph-animation", className="graph-container fade-in", style={**self.graph_style_full}),
                html.Div(id="graph-dual-axis", className="graph-container fade-in", style={**self.graph_style_full}),
                html.Div(id="graph-candlestick", className="graph-container fade-in", style={**self.graph_style_full}),
                html.Div(id="graph-polar", className="graph-container fade-in", style={**self.graph_style_full}),
                html.Div(id="graph-funnel", className="graph-container fade-in", style={**self.graph_style_full}),
                html.Div(id="graph-waterfall", className="graph-container fade-in", style={**self.graph_style_full}),
            ], style={'maxWidth': '1800px', 'margin': '0 auto', 'padding': '0 32px'}, id="graphs-grid-2"),
            
            # Tableau de données détaillé
            html.Div([
                html.Div([
                    html.H2("📋 Données Détaillées", style={
                        'fontSize': '24px', 'fontWeight': '700', 'color': '#1E293B', 'marginBottom': '20px'
                    }),
                    dash_table.DataTable(
                        id='detailed-table',
                        page_size=20,
                        style_table={'overflowX': 'auto', 'borderRadius': '12px', 'overflow': 'hidden'},
                        style_cell={'backgroundColor': 'white', 'color': '#1E293B', 'border': '1px solid #E2E8F0'},
                        style_header={'backgroundColor': '#F1F5F9', 'fontWeight': '700', 'borderBottom': '2px solid #1E40AF'}
                    )
                ], style={**self.graph_style_full})
            ], style={'maxWidth': '1800px', 'margin': '40px auto', 'padding': '0 32px'}),
            
            # Stores
            dcc.Store(id='filters-store', data={}),
            dcc.Store(id='data-store', data=[]),
            
        ], style={'paddingBottom': '60px'})
    
    @property
    def graph_style(self):
        return {
            'background': 'white',
            'padding': '24px',
            'borderRadius': '20px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.08)',
            'border': '1px solid #E2E8F0'
        }
    
    @property
    def graph_style_full(self):
        return {
            **self.graph_style,
            'marginBottom': '24px'
        }
    
    # ========================================================
    #                      CALLBACKS
    # ========================================================
    
    def setup_callbacks(self):
        """Configuration des callbacks COMPLETE avec gestion d'erreurs"""
        
        # ------------------------------------------------------------------
        # 1. VÉRIFICATION DB AU DÉMARRAGE
        # ------------------------------------------------------------------
        @callback(
            Output('loading-status', 'children'),
            Output('notification-container', 'children'),
            Input('url', 'pathname')
        )
        def check_system_on_load(path):
            """Vérifie la base de données au chargement de la page"""
            try:
                db_ok, message, details = self.check_database_connection()
                
                if not db_ok:
                    if 'consolidated' in details and details['consolidated'] == 0:
                        # Fallback sur sources
                        notification = ErrorManager.notify_warning(
                            "Mode Fallback Activé",
                            "Utilisation des tables sources (CoinAfrique, ExpatDakar, LogerDakar)"
                        )
                    else:
                        notification = ErrorManager.notify_error(
                            "Problème de base de données",
                            message,
                            details.get('details')
                        )
                else:
                    notification = ErrorManager.notify_success(
                        "Système prêt",
                        details.get('message', 'Base de données connectée')
                    )
                
                status = html.Div([
                    html.Div(className="loading-spinner"),
                    html.P(message, style={'marginTop': '12px', 'color': '#64748B'})
                ]) if not db_ok else None
                
                return status, notification
                
            except Exception as e:
                return (
                    html.Div([
                        html.Div(className="loading-spinner"),
                        html.P("⏳ Chargement...", style={'marginTop': '12px'})
                    ]),
                    ErrorManager.notify_error(
                        "Erreur système",
                        "Impossible de vérifier la base de données",
                        traceback.format_exc()
                    )
                )
        
        # ------------------------------------------------------------------
        # 2. CHARGEMENT INITIAL AUTOMATIQUE DES DONNÉES
        # ------------------------------------------------------------------
        @callback(
            Output('data-store', 'data'),
            Output('notification-container', 'children', allow_duplicate=True),
            Input('url', 'pathname'),
            prevent_initial_call=False  # ⭐ ESSENTIEL - Permet le chargement auto
        )
        def load_initial_data(path):
            """Charge les données automatiquement au démarrage"""
            try:
                print("🚀 Chargement initial des données...")
                
                data, error = self.get_enriched_data()
                
                if error:
                    if 'consolidated' in error and error['consolidated'] == 0:
                        # Fallback déjà géré dans get_enriched_data
                        notification = ErrorManager.notify_info(
                            "Chargement",
                            f"{len(data)} propriétés chargées depuis les tables sources"
                        )
                    else:
                        notification = ErrorManager.notify_error(
                            "Erreur chargement",
                            error.get('message', 'Erreur inconnue'),
                            error.get('details')
                        )
                else:
                    notification = ErrorManager.notify_success(
                        "✅ Données chargées",
                        f"{len(data)} propriétés consolidées prêtes"
                    )
                
                print(f"✅ {len(data)} lignes chargées")
                return data, notification
                
            except Exception as e:
                error_details = traceback.format_exc()
                print(f"❌ ERREUR CRITIQUE chargement initial: {error_details}")
                return [], ErrorManager.notify_error(
                    "Erreur critique",
                    "Impossible de charger les données initiales",
                    error_details
                )
        
        # ------------------------------------------------------------------
        # 3. CHARGEMENT AVEC FILTRES (manuel)
        # ------------------------------------------------------------------
        @callback(
            Output('data-store', 'data', allow_duplicate=True),
            Output('notification-container', 'children', allow_duplicate=True),
            Input('apply-filters', 'n_clicks'),
            State('filter-cities', 'value'),
            State('filter-properties', 'value'),
            State('price-range-slider', 'value'),
            prevent_initial_call=True
        )
        def load_with_filters(n_clicks, cities, properties, price_range):
            """Charge les données quand l'utilisateur applique des filtres"""
            if not n_clicks:
                raise dash.exceptions.PreventUpdate
            
            try:
                print(f"🔍 Application des filtres: villes={cities}, types={properties}")
                
                filters = {
                    'cities': cities or [],
                    'properties': properties or [],
                    'min_price': price_range[0],
                    'max_price': price_range[1]
                }
                
                data, error = self.get_enriched_data(filters)
                
                if error:
                    notification = ErrorManager.notify_warning(
                        "⚠️ Filtres appliqués avec avertissement",
                        error.get('message', 'Problème lors du filtrage')
                    )
                else:
                    notification = ErrorManager.notify_success(
                        "✅ Filtres appliqués",
                        f"{len(data)} propriétés chargées"
                    )
                
                return data, notification
                
            except Exception as e:
                error_details = traceback.format_exc()
                print(f"❌ Erreur filtres: {error_details}")
                return [], ErrorManager.notify_error(
                    "❌ Erreur filtres",
                    "Impossible d'appliquer les filtres",
                    error_details
                )
        
        # ------------------------------------------------------------------
        # 4. MISE À JOUR DES OPTIONS DE FILTRES
        # ------------------------------------------------------------------
        @callback(
            Output('filter-cities', 'data'),
            Output('filter-properties', 'data'),
            Input('url', 'pathname')  # Charge au démarrage
        )
        def load_filter_options(path):
            """Charge les options pour les filtres (villes, types)"""
            try:
                from app.database.models import db, ProprietesConsolidees
                
                # Essaye la table consolidée d'abord
                consolidated_count = db.session.query(ProprietesConsolidees).count()
                
                if consolidated_count > 0:
                    cities = db.session.query(ProprietesConsolidees.city).distinct().order_by(ProprietesConsolidees.city).all()
                    properties = db.session.query(ProprietesConsolidees.property_type).distinct().order_by(ProprietesConsolidees.property_type).all()
                    
                    city_options = [{"value": c[0], "label": f"📍 {c[0]}"} for c in cities if c[0]]
                    property_options = [{"value": p[0], "label": f"🏠 {p[0]}"} for p in properties if p[0]]
                else:
                    # Fallback sur les sources
                    from app.database.models import CoinAfrique, ExpatDakarProperty, LogerDakarProperty
                    
                    cities = set()
                    properties = set()
                    
                    for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
                        try:
                            cities.update([c[0] for c in db.session.query(model.city).distinct().all() if c[0]])
                            properties.update([p[0] for p in db.session.query(model.property_type).distinct().all() if p[0]])
                        except:
                            continue
                    
                    city_options = [{"value": c, "label": f"📍 {c}"} for c in sorted(cities)]
                    property_options = [{"value": p, "label": f"🏠 {p}"} for p in sorted(properties)]
                
                return city_options, property_options
                
            except Exception as e:
                print(f"❌ Erreur chargement options: {e}")
                return [], []
        
        # ------------------------------------------------------------------
        # 5. MISE À JOUR DES KPIs
        # ------------------------------------------------------------------
        @callback(
            Output('kpi-grid', 'children'),
            Output('loading-status', 'children', allow_duplicate=True),
            Input('data-store', 'data'),
            prevent_initial_call=True
        )
        def update_kpis(data):
            """Met à jour les KPIs et cache le statut de chargement"""
            if data is None:
                return [], None
            
            try:
                if not data:
                    return [
                        html.Div([
                            DashIconify(icon="mdi:database-off", width=64, color="#64748B"),
                            html.H3("Aucune donnée à afficher", style={'color': '#64748B', 'marginTop': '16px'}),
                            html.P("Essayez de relancer le chargement ou de vérifier les filtres", style={'color': '#94A3B8'})
                        ], style={'textAlign': 'center', 'padding': '40px', 'gridColumn': '1/-1'})
                    ], None
                
                kpis = self.calculate_ultra_kpis(data)
                
                if 'error' in kpis:
                    return [
                        html.Div([
                            DashIconify(icon="mdi:chart-bar", width=64, color="#F59E0B"),
                            html.H3("Impossible de calculer les KPIs", style={'color': '#F59E0B', 'marginTop': '16px'}),
                            html.P(kpis['error'], style={'color': '#64748B'})
                        ], style={'textAlign': 'center', 'padding': '40px', 'gridColumn': '1/-1'})
                    ], None
                
                cards = []
                kpi_defs = [
                    ("🏠 Total", f"{kpis.get('count', 0):,}", "mdi:home", self.COLORS['primary']),
                    ("💰 Prix Moyen", f"{kpis.get('avg_price', 0):,.0f} FCFA", "mdi:currency-usd", self.COLORS['success']),
                    ("📊 Prix/m²", f"{kpis.get('avg_price_per_m2', 0):,.0f}", "mdi:ruler-square", self.COLORS['info']),
                    ("⭐ Qualité", f"{kpis.get('avg_quality', 0):.0f}/100", "mdi:shield-check", self.COLORS['warning']),
                    ("😊 Sentiment", f"{kpis.get('avg_sentiment', 0):.2f}", "mdi:emoticon-happy", self.COLORS['purple']),
                    ("⚠️ Anomalies", f"{kpis.get('anomaly_count', 0)}", "mdi:alert", self.COLORS['danger']),
                ]
                
                for title, value, icon, color in kpi_defs:
                    cards.append(self.create_kpi_card_gradient(title, value, icon, color))
                
                return cards, None  # Cache le statut de chargement
                
            except Exception as e:
                print(f"❌ Erreur mise à jour KPIs: {e}")
                return [
                    html.Div([
                        DashIconify(icon="mdi:bug", width=64, color="#EF4444"),
                        html.H3("Erreur KPIs", style={'color': '#EF4444'}),
                    ], style={'textAlign': 'center', 'padding': '40px', 'gridColumn': '1/-1'})
                ], None
        
        # ------------------------------------------------------------------
        # 6. MISE À JOUR DE TOUS LES GRAPHES
        # ------------------------------------------------------------------
        graph_callbacks = [
            ('graph-ridge', self.create_superposed_violin_ridgeplot, "Ridge Plot"),
            ('graph-3d-surface', self.create_stacked_3d_surface, "Surface 3D"),
            ('graph-heatmap', self.create_multi_layer_heatmap, "Heatmap Multi-couches"),
            ('graph-stacked-area', self.create_stacked_area_trends, "Aires Empilées"),
            ('graph-parallel', self.create_parallel_coords_advanced, "Parallel Coordinates"),
            ('graph-treemap-sunburst', self.create_treemap_sunburst_combo, "Treemap + Sunburst"),
            ('graph-bubble-4d', self.create_bubble_matrix_4d, "Bubble 4D"),
            ('graph-clustering-3d', self.create_clustering_3d, "Clustering 3D"),
            ('graph-animation', self.create_animation_timeseries, "Animation Temporelle"),
            ('graph-dual-axis', self.create_dual_axis_advanced, "Double Axe"),
            ('graph-candlestick', self.create_candlestick_advanced, "Candlestick"),
            ('graph-polar', self.create_polar_scatter_multi, "Scatter Polaire"),
            ('graph-funnel', self.create_funnel_advanced, "Funnel"),
            ('graph-waterfall', self.create_waterfall_advanced, "Waterfall"),
        ]
        
        for graph_id, func, title in graph_callbacks:
            @callback(
                Output(graph_id, 'children'),
                Input('data-store', 'data'),
                prevent_initial_call=True
            )
            def update_graph(data, func=func, title=title):
                if data is None:
                    return html.Div("⏳ Chargement...", style={'textAlign': 'center', 'padding': '40px'})
                
                if not data:
                    return self._create_empty_graph("Aucune donnée à afficher", title)
                
                try:
                    fig = func(data)
                    return dcc.Graph(figure=fig, config={'displayModeBar': True, 'displaylogo': False})
                except Exception as e:
                    return self._create_error_component(title, str(e), traceback.format_exc())
        
        # ------------------------------------------------------------------
        # 7. MISE À JOUR DU TABLEAU
        # ------------------------------------------------------------------
        @callback(
            Output('detailed-table', 'data'),
            Output('detailed-table', 'columns'),
            Input('data-store', 'data'),
            prevent_initial_call=True
        )
        def update_table(data):
            if data is None:
                return [], []
            
            try:
                if not data:
                    return [], []
                
                df = pd.DataFrame(data)
                
                # Sélectionner les colonnes à afficher
                cols_to_show = ['title', 'price', 'city', 'property_type', 'surface_area', 'source']
                df_display = df[[col for col in cols_to_show if col in df.columns]]
                
                columns = [{"name": col.replace('_', ' ').title(), "id": col} for col in df_display.columns]
                
                return df_display.to_dict('records'), columns
                
            except Exception as e:
                print(f"❌ Erreur mise à jour table: {e}")
                return [], []

# ========================================================
#                    FACTORY FUNCTION
# ========================================================

def create_ultra_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    """
    Factory pour créer le dashboard analytics
    Gère les erreurs globales de création
    """
    try:
        dashboard = AnalyticsDashboard(
            server=server,
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix
        )
        print("✅ Dashboard Analytics créé avec succès")
        return dashboard.app
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE création dashboard: {e}")
        traceback.print_exc()
        
        # Retourne une app minimale avec message d'erreur
        app = dash.Dash(__name__)
        app.layout = html.Div([
            html.H1("❌ Erreur Critique", style={'color': '#EF4444'}),
            html.P("Impossible de créer le dashboard"),
            html.Pre(traceback.format_exc(), style={'background': '#f8f9fa', 'padding': '20px'})
        ], style={'padding': '40px'})
        return app

