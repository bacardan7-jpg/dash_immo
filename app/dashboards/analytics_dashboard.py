import dash
from dash import html, dcc, Input, Output, callback, State, dash_table, ctx
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
warnings.filterwarnings('ignore')

# ============================================================
#                    DASHBOARD ULTRA-AVANCÉ
# ============================================================

class AnalyticsDashboard:
    """Dashboard immobilier avec visualisations maximales"""
    
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
        if server:
            with server.app_context():
                self.setup_layout()
                self.setup_callbacks()
    
    # ========================================================
    #                DATA LOADING & CACHING
    # ========================================================
    
    def get_enriched_data(self, filters=None, limit=5000):
        """
        Charge CoinAfrique, ExpatDakar, LogerDakar et renvoie un dataset
        NORMALISÉ avec les mêmes colonnes que ProprietesConsolidees.
        Si une colonne n'existe pas → None.
        """

        from datetime import datetime
        from app.database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty

        # ------------ CACHE -------------
        cache_key = hash(str(sorted(filters.items())) if filters else "all")
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        try:
            # ------------ CHARGEMENT DES TABLES -------------
            ca_rows = db.session.query(CoinAfrique).limit(limit).all()
            ed_rows = db.session.query(ExpatDakarProperty).limit(limit).all()
            ld_rows = db.session.query(LogerDakarProperty).limit(limit).all()

            data = []

            # ------------ FONCTION DE NORMALISATION -------------
            def normalize(item, source_name):
                """Transforme un objet d'une table → format ProprietesConsolidees."""

                d = item.to_dict()

                return {
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "price": d.get("price"),

                    # surface_area existe partout, price_per_m2 doit être calculé
                    "surface_area": d.get("surface_area"),
                    "price_per_m2": (d["price"] / d["surface_area"]) if d.get("price") and d.get("surface_area") else None,

                    "city": d.get("city"),
                    "district": d.get("region") or None,  # CoinAfrique n'a pas "region"

                    "property_type": d.get("property_type"),
                    "bedrooms": d.get("bedrooms"),
                    "bathrooms": d.get("bathrooms"),

                    "land_area": None,     # n'existe dans aucune table
                    "source": source_name, # forcé

                    # Valeurs avancées inexistantes → None
                    "quality_score": None,
                    "sentiment": None,

                    "scraped_at": d.get("scraped_at"),
                    "posted_time": d.get("posted_time"),

                    # counters inexistants
                    "view_count": None,
                    "favorite_count": None,
                    "contact_count": None,

                    "latitude": d.get("latitude"),
                    "longitude": d.get("longitude"),

                    "furnishing": None,
                    "condition": None,

                    # calcul âge si possible
                    "age_days": (datetime.utcnow() - d["scraped_at"]).days 
                                if d.get("scraped_at") else None
                }

            # ------------ NORMALISATION + FUSION -------------

            for r in ca_rows:
                data.append(normalize(r, "CoinAfrique"))

            for r in ed_rows:
                data.append(normalize(r, "ExpatDakar"))

            for r in ld_rows:
                data.append(normalize(r, "LogerDakar"))

            # ------------ FILTRES -------------
            def match_filters(row):
                if not filters:
                    return True

                # city
                if filters.get("city") not in [None, "all"]:
                    if row["city"] != filters["city"]:
                        return False

                # source
                if filters.get("source") not in [None, "all"]:
                    if row["source"] != filters["source"]:
                        return False

                # property_type
                if filters.get("property_type") not in [None, "all"]:
                    if row["property_type"] != filters["property_type"]:
                        return False

                # price
                if filters.get("min_price") and row["price"]:
                    if row["price"] < filters["min_price"]:
                        return False

                if filters.get("max_price") and row["price"]:
                    if row["price"] > filters["max_price"]:
                        return False

                # surface
                if filters.get("min_surface") and row["surface_area"]:
                    if row["surface_area"] < filters["min_surface"]:
                        return False

                if filters.get("max_surface") and row["surface_area"]:
                    if row["surface_area"] > filters["max_surface"]:
                        return False

                # bedrooms
                if filters.get("bedrooms") not in [None, "all"]:
                    if row["bedrooms"] != int(filters["bedrooms"]):
                        return False

                return True

            filtered = [r for r in data if match_filters(r)]
            filtered = filtered[:limit]

            # ------------ CACHE 90s -------------
            self._data_cache[cache_key] = filtered
            import threading
            threading.Timer(90, lambda: self._data_cache.pop(cache_key, None)).start()

            return filtered

        except Exception as e:
            print("❌ Erreur dans get_enriched_data():", e)
            return []

    
    # ========================================================
    #              CALCULS STATISTIQUES AVANCÉS
    # ========================================================
    
    def calculate_ultra_kpis(self, data):
        """KPIs avec analyses statistiques avancées"""
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        
        # KPIs de base
        kpis = {
            'count': len(df),
            'avg_price': df['price'].mean(),
            'median_price': df['price'].median(),
            'std_price': df['price'].std(),
            'avg_price_per_m2': df['price_per_m2'].mean(),
            'avg_quality': df['quality_score'].mean(),
            'avg_sentiment': df['sentiment'].mean(),
        }
        
        # Variations et tendances (simulées avec percentiles)
        q10, q90 = df['price'].quantile([0.1, 0.9])
        kpis['price_volatility'] = ((q90 - q10) / kpis['median_price']) * 100
        
        # Score d'opportunité multi-dimensionnel
        if 'price_per_m2' in df and 'quality_score' in df:
            df['opportunity_score'] = (
                (df['quality_score'] / 100) * 0.4 + 
                (1 / (df['price_per_m2'] / df['price_per_m2'].median())) * 0.3 +
                (df['view_count'] / df['view_count'].max()) * 0.2 +
                (1 - df['age_days'] / df['age_days'].max()).fillna(0) * 0.1
            )
            top_ops = df.nlargest(5, 'opportunity_score')
            kpis['opportunities'] = top_ops.to_dict('records')
        
        # Anomalies avec Z-score
        if 'price_per_m2' in df:
            z_scores = np.abs(stats.zscore(df['price_per_m2'].dropna()))
            anomalies = df.loc[df['price_per_m2'].dropna().index[z_scores > 3]]
            kpis['anomalies'] = anomalies.head(3).to_dict('records')
            kpis['anomaly_count'] = len(anomalies)
        
        # Tendances par ville (top 5)
        city_trends = df.groupby('city').agg({
            'price': ['median', 'count'],
            'price_per_m2': 'mean'
        }).round(2)
        city_trends.columns = ['median_price', 'count', 'avg_price_m2']
        city_trends = city_trends.sort_values('median_price', ascending=False).head(5)
        kpis['city_trends'] = city_trends.reset_index().to_dict('records')
        
        return kpis
    
    # ========================================================
    #              GRAPHIQUES SUPERPOSÉS & AVANCÉS
    # ========================================================
    
    def create_superposed_violin_ridgeplot(self, data):
        """Violin plot superposé (ridge plot) - Distribution par ville"""
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        cities = df['city'].value_counts().head(8).index
        
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
    
    def create_stacked_3d_surface(self, data):
        """Surface 3D empilée - Prix, Surface, Qualité"""
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
    
    def create_multi_layer_heatmap(self, data):
        """Heatmap multi-couches : Corrélations + Densité"""
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        numeric_cols = ['price', 'surface_area', 'bedrooms', 'bathrooms', 
                       'quality_score', 'sentiment', 'view_count']
        df_numeric = df[numeric_cols].dropna()
        
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
    
    def create_stacked_area_trends(self, data):
        """Aires empilées - Tendances temporelles par source"""
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
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
    
    def create_parallel_coords_advanced(self, data):
        """Parallel coordinates avec coloration multi-dimensionnelle"""
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        cols = ['price', 'surface_area', 'bedrooms', 'quality_score', 'sentiment']
        df_filtered = df[cols].dropna().head(300)  # Limiter pour performance
        
        if df_filtered.empty:
            return go.Figure()
        
        # Normalisation
        df_norm = (df_filtered - df_filtered.min()) / (df_filtered.max() - df_filtered.min())
        
        # Score composite pour coloration
        df_norm['composite'] = (
            df_norm['price'] * 0.3 + 
            df_norm['quality_score'] * 0.3 + 
            df_norm['sentiment'] * 0.2 +
            df_norm['surface_area'] * 0.2
        )
        
        fig = px.parallel_coordinates(
            df_norm,
            color='composite',
            dimensions=cols,
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
    
    def create_treemap_sunburst_combo(self, data):
        """Treemap + Sunburst combinés - Structure hiérarchique"""
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        
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
    
    def create_bubble_matrix_4d(self, data):
        """Bubble chart 4D : Prix, Surface, Qualité, Taille = Volume"""
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        df = df.dropna(subset=['price', 'surface_area', 'quality_score', 'view_count'])
        
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
    
    def create_candlestick_advanced(self, data):
        """Candlestick chart - Prix OHLC par district"""
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
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
    
    def create_polar_scatter_multi(self, data):
        """Scatter plot polaire multi-dimensionnel"""
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        df = df.dropna(subset=['quality_score', 'sentiment', 'view_count'])
        
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
    
    def create_funnel_advanced(self, data):
        """Funnel chart - Conversion qualité"""
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        
        # Créer segments de qualité
        quality_bins = pd.cut(df['quality_score'], 
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
    
    def create_waterfall_advanced(self, data):
        """Waterfall chart - Impact des facteurs sur prix"""
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        
        # Calculer l'impact moyen de chaque caractéristique
        baseline = df['price'].min()
        
        impacts = {
            'Prix de base': baseline,
            '+ Surface moyenne': df['surface_area'].mean() * 100000,  # prix/m² simulé
            '+ Chambres': df['bedrooms'].mean() * 5000000,
            '+ Qualité': df['quality_score'].mean() * 50000,
            '+ Sentiment': (df['sentiment'].mean() + 1) * 1000000,
        }
        
        # Calculer les valeurs cumulées
        values = list(impacts.values())
        cumulative = np.cumsum(values)
        
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
    
    def create_clustering_3d(self, data):
        """Clustering K-means en 3D"""
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        features = ['price', 'surface_area', 'quality_score']
        df_cluster = df[features].dropna()
        
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
            y='surface_area',
            z='quality_score',
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
    
    def create_animation_timeseries(self, data):
        """Animation temporelle des prix par ville"""
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
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
    
    def create_dual_axis_advanced(self, data):
        """Graphe à double axe Y avancé"""
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        
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
    
    # ========================================================
    #                    COMPOSANTS UI PREMIUM
    # ========================================================
    
    def create_kpi_card_gradient(self, title, value, icon, color, trend=None):
        """Carte KPI avec gradient animé"""
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
                html.Div(value, style={
                    'fontSize': '28px',
                    'fontWeight': '800',
                    'color': '#1E293B',
                    'marginTop': '8px'
                }),
                html.Div(trend, style={
                    'fontSize': '12px',
                    'color': self.COLORS['success'] if trend and '+' in trend else self.COLORS['danger'],
                    'fontWeight': '600',
                    'marginTop': '4px'
                }) if trend else None
            ], style={
                'background': 'white',
                'borderRadius': '20px',
                'padding': '24px',
                'boxShadow': '0 4px 20px rgba(0,0,0,0.08)',
                'border': '1px solid #E2E8F0',
                'transition': 'all 0.3s ease',
                'cursor': 'pointer'
            })
        ])
    
    def adjust_color_brightness(self, hex_color, percent):
        """Ajuster luminosité couleur"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = max(0, min(255, r + int(r * percent / 100)))
        g = max(0, min(255, g + int(g * percent / 100)))
        b = max(0, min(255, b + int(b * percent / 100)))
        return f'#{r:02x}{g:02x}{b:02x}'
    
    # ========================================================
    #                      LAYOUT FINAL
    # ========================================================
    
    def setup_layout(self):
        """Layout ultra-complet avec toutes les visualisations"""
        
        self.app.layout = html.Div([
            # CSS personnalisé
            
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
            
            # Filtres avancés
            html.Div([
                html.Div([
                    html.Div([
                        dmc.MultiSelect(
                            label="Villes (Multi-sélection)",
                            id="filter-cities",
                            data=[],  # Rempli par callback
                            style={'marginBottom': '16px'}
                        ),
                        dmc.MultiSelect(
                            label="Types de biens",
                            id="filter-properties",
                            data=[],  # Rempli par callback
                        )
                    ], style={'flex': '1'}),
                    
                    dmc.RangeSlider(
                        id="price-range-slider",
                        value=[100000, 900000],
                        min=0,
                        max=1000000,
                        step=10000,
                        marks=[
                            {"value": 0, "label": "0"},
                            {"value": 500000, "label": "500k"},
                            {"value": 1000000, "label": "1M"},
                        ],
                        className="fade-in",
                    ),
                                
                    html.Button([
                        DashIconify(icon="mdi:filter-check", width=20, color="white"),
                        html.Span("Appliquer", style={'marginLeft': '8px'})
                    ], id="apply-filters", style={
                        'background': f'linear-gradient(135deg, {self.COLORS["success"]}, {self.adjust_color_brightness(self.COLORS["success"], -30)})',
                        'color': 'white', 'border': 'none', 'borderRadius': '12px',
                        'padding': '12px 24px', 'fontWeight': '600', 'cursor': 'pointer',
                        'marginLeft': '24px', 'alignSelf': 'flex-end'
                    })
                ], style={
                    'display': 'flex', 'gap': '24px', 'alignItems': 'flex-end',
                    'maxWidth': '1800px', 'margin': '0 auto', 'padding': '0 32px'
                })
            ], style={'marginBottom': '40px'}),
            
            # KPIs Section
            html.Div([
                html.Div(id="kpi-grid", style={
                    'display': 'grid',
                    'gridTemplateColumns': 'repeat(auto-fit, minmax(280px, 1fr))',
                    'gap': '24px',
                    'maxWidth': '1800px', 'margin': '0 auto', 'padding': '0 32px'
                })
            ], style={'marginBottom': '40px'}),
            
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
            ], style={'maxWidth': '1800px', 'margin': '0 auto', 'padding': '0 32px'}),
            
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
            ], style={'maxWidth': '1800px', 'margin': '0 auto', 'padding': '0 32px'}),
            
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
            
            # Notification
            html.Div(id="notification-container")
            
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
        """Configuration des callbacks interactifs"""
        
        @callback(
            [
                Output('filter-cities', 'data'),
                Output('filter-properties', 'data')
            ],
            Input('apply-filters', 'n_clicks')
        )
        def load_filter_options(n_clicks):
            """Charger les options de filtres"""
            try:
                from app.database.models import db, ProprietesConsolidees
                
                cities = db.session.query(ProprietesConsolidees.city).distinct().order_by(ProprietesConsolidees.city).all()
                properties = db.session.query(ProprietesConsolidees.property_type).distinct().order_by(ProprietesConsolidees.property_type).all()
                
                city_options = [{"value": c[0], "label": f"📍 {c[0]}"} for c in cities if c[0]]
                property_options = [{"value": p[0], "label": f"🏠 {p[0]}"} for p in properties if p[0]]
                
                return city_options, property_options
                
            except Exception as e:
                print(f"Erreur chargement filtres: {e}")
                return [], []
        
        @callback(
            [
                Output('data-store', 'data'),
                Output('notification-container', 'children')
            ],
            [
                Input('apply-filters', 'n_clicks')
            ],
            [
                State('filter-cities', 'value'),
                State('filter-properties', 'value'),
                State('price-range-slider', 'value')
            ],
            prevent_initial_call=False
        )
        def apply_filters_and_load(n_clicks, cities, properties, price_range):
            """Appliquer filtres et charger les données"""
            try:
                filters = {
                    'cities': cities or [],
                    'properties': properties or [],
                    'min_price': price_range[0],
                    'max_price': price_range[1]
                }
                
                data = self.get_enriched_data(filters)
                
                notification = dmc.Notification(
                    title="✅ Filtres appliqués",
                    message=f"{len(data)} propriétés chargées",
                    color="green",
                    autoClose=3000
                )
                
                return data, notification
                
            except Exception as e:
                error_notification = dmc.Notification(
                    title="❌ Erreur",
                    message=str(e),
                    color="red",
                    autoClose=5000
                )
                return [], error_notification
        
        @callback(
            Output('kpi-grid', 'children'),
            Input('data-store', 'data')
        )
        def update_kpis(data):
            """Mettre à jour les KPIs"""
            if not data:
                return []
            
            kpis = self.calculate_ultra_kpis(data)
            
            cards = [
                self.create_kpi_card_gradient("🏠 Total", f"{kpis.get('count', 0):,}", "mdi:home", self.COLORS['primary']),
                self.create_kpi_card_gradient("💰 Prix Moyen", f"{kpis.get('avg_price', 0):,.0f} FCFA", "mdi:currency-usd", self.COLORS['success']),
                self.create_kpi_card_gradient("📊 Prix/m²", f"{kpis.get('avg_price_per_m2', 0):,.0f}", "mdi:ruler-square", self.COLORS['info']),
                self.create_kpi_card_gradient("⭐ Qualité", f"{kpis.get('avg_quality', 0):.0f}/100", "mdi:shield-check", self.COLORS['warning']),
                self.create_kpi_card_gradient("😊 Sentiment", f"{kpis.get('avg_sentiment', 0):.2f}", "mdi:emoticon-happy", self.COLORS['purple']),
                self.create_kpi_card_gradient("⚠️ Anomalies", f"{kpis.get('anomaly_count', 0)}", "mdi:alert", self.COLORS['danger']),
            ]
            
            return cards
        
        # Callbacks pour tous les graphiques
        graph_callbacks = [
            ('graph-ridge', self.create_superposed_violin_ridgeplot),
            ('graph-3d-surface', self.create_stacked_3d_surface),
            ('graph-heatmap', self.create_multi_layer_heatmap),
            ('graph-stacked-area', self.create_stacked_area_trends),
            ('graph-parallel', self.create_parallel_coords_advanced),
            ('graph-treemap-sunburst', self.create_treemap_sunburst_combo),
            ('graph-bubble-4d', self.create_bubble_matrix_4d),
            ('graph-clustering-3d', self.create_clustering_3d),
            ('graph-animation', self.create_animation_timeseries),
            ('graph-dual-axis', self.create_dual_axis_advanced),
            ('graph-candlestick', self.create_candlestick_advanced),
            ('graph-polar', self.create_polar_scatter_multi),
            ('graph-funnel', self.create_funnel_advanced),
            ('graph-waterfall', self.create_waterfall_advanced),
        ]
        
        for graph_id, func in graph_callbacks:
            @callback(
                Output(graph_id, 'children'),
                Input('data-store', 'data')
            )
            def update_graph(data, func=func):
                if not data:
                    return dcc.Graph(figure=go.Figure(), config={'displayModeBar': False})
                
                fig = func(data)
                return dcc.Graph(figure=fig, config={'displayModeBar': True, 'displaylogo': False})
        
        @callback(
            Output('detailed-table', 'data'),
            Output('detailed-table', 'columns'),
            Input('data-store', 'data')
        )
        def update_table(data):
            """Mettre à jour le tableau détaillé"""
            if not data:
                return [], []
            
            df = pd.DataFrame(data)
            columns = [{"name": col, "id": col} for col in df.columns]
            
            return df.to_dict('records'), columns

# ========================================================
#                    FACTORY FUNCTION
# ========================================================

def create_ultra_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    dashboard = AnalyticsDashboard(
        server=server,
        routes_pathname_prefix=routes_pathname_prefix,
        requests_pathname_prefix=requests_pathname_prefix
    )
    return dashboard.app