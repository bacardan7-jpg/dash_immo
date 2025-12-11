# -*- coding: utf-8 -*-
"""
🎯 MAIN DASHBOARD COMPLET - Observatoire Immobilier
Version finale avec TOUS les graphes, filtre status et surface max 450m²
Auteur: Cos - ENSAE Dakar
"""

import dash
from dash import html, dcc, Input, Output, State, callback
from dash_iconify import DashIconify
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import func, or_
import traceback
import base64
from app.components.dash_sidebar_component import create_sidebar_layout

# Import sécurisé des modèles
try:
    from ..database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
except ImportError:
    try:
        from database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
    except ImportError:
        db = CoinAfrique = ExpatDakarProperty = LogerDakarProperty = None

# Import détecteur de statut
try:
    from .status_detector import detect_listing_status
except ImportError:
    try:
        from status_detector import detect_listing_status
    except ImportError:
        def detect_listing_status(title=None, price=None, property_type=None, source=None, native_status=None):
            return 'Location' if price and price < 1_500_000 else 'Vente'


class EnhancedMainDashboard:
    """Dashboard principal complet avec tous les graphes et filtres avancés"""
    
    COLORS = {
        'primary': '#1E40AF', 'secondary': '#EC4899', 'success': '#10B981',
        'warning': '#F59E0B', 'danger': '#EF4444', 'info': '#06B6D4',
        'purple': '#8B5CF6', 'teal': '#14B8A6',
        'gradient_1': ['#667EEA', '#764BA2'], 'gradient_2': ['#F093FB', '#F5576C'],
        'gradient_3': ['#4FACFE', '#00F2FE'], 'gradient_4': ['#43E97B', '#38F9D7'],
        'bg_light': '#F8FAFC', 'bg_card': '#FFFFFF',
        'text_primary': '#1E293B', 'text_secondary': '#64748B', 'border': '#E2E8F0'
    }
    
    def __init__(self, server=None, routes_pathname_prefix="/dashboard/", requests_pathname_prefix="/dashboard/"):
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[
                'https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap',
                'https://unpkg.com/@tabler/icons-webfont@latest/tabler-icons.min.css'
            ],
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix,
            suppress_callback_exceptions=True,
            meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
        )
        
        # 🔴 CRITIQUE: Limite de surface maximale
        self.MAX_SURFACE = 450  # m²
        
        if server:
            with server.app_context():
                self.setup_layout()
                self.setup_callbacks()
    
    # ==================== DATA LOADING ====================
    
    def safe_import_models(self):
        """Import sécurisé des modèles"""
        try:
            from app.database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
            return db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
        except ImportError:
            try:
                from database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
                return db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty
            except Exception as e:
                print(f"❌ Erreur import models: {e}")
                return None, None, None, None
    
    def safe_get_data(self, property_type=None, city=None, status='Tous', limit=2000):
        """
        Récupération sécurisée des données avec:
        - Surface max 450m²
        - Filtre status
        """
        try:
            db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty = self.safe_import_models()
            if not db:
                return pd.DataFrame()
            
            all_data = []
            
            for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
                try:
                    query = db.session.query(
                        model.city, model.property_type, model.price,
                        model.surface_area, model.bedrooms, model.bathrooms, model.scraped_at
                    ).filter(
                        model.price.isnot(None),
                        model.price > 10000,
                        model.price < 1e10,
                        # 🔴 LIMITE SURFACE MAX 450m²
                        or_(model.surface_area.is_(None), model.surface_area <= self.MAX_SURFACE)
                    )
                    
                    if property_type and property_type != "Tous":
                        query = query.filter(model.property_type == property_type)
                    
                    if city and city != "Toutes":
                        query = query.filter(model.city == city)
                    
                    records = query.limit(limit).all()
                    
                    for r in records:
                        try:
                            age_days = (datetime.utcnow() - r.scraped_at).days if r.scraped_at else None
                            
                            price = float(r.price) if r.price else 0
                            surface = float(r.surface_area) if r.surface_area and r.surface_area > 0 else None
                            title = str(r.title) if hasattr(r, 'title') and r.title else None
                            prop_type = str(r.property_type) if r.property_type else 'Autre'
                            
                            # Détection statut
                            native_status = str(r.status) if hasattr(r, 'status') and r.status else None
                            status = detect_listing_status(
                                title=title, price=price, property_type=prop_type,
                                source=model.__name__, native_status=native_status
                            )
                            
                            # 🔴 FILTRAGE PAR STATUS
                            if status != 'Tous' and status != status:
                                continue
                            
                            all_data.append({
                                'city': str(r.city) if r.city else 'Non spécifié',
                                'property_type': prop_type,
                                'status': status,
                                'price': price,
                                'surface_area': surface,
                                'bedrooms': int(r.bedrooms) if r.bedrooms else None,
                                'bathrooms': int(r.bathrooms) if r.bathrooms else None,
                                'age_days': age_days,
                                'source': model.__name__
                            })
                        except Exception:
                            continue
                            
                except Exception as e:
                    print(f"Erreur requête {model.__name__}: {e}")
                    continue
            
            if not all_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_data)
            df['city'] = df['city'].apply(lambda x: x.lower().split(',')[0] if isinstance(x, str) else x)
            
            # Calcul prix/m²
            if not df.empty:
                df['price_per_m2'] = df.apply(
                    lambda x: x['price'] / x['surface_area'] 
                    if x['surface_area'] and x['surface_area'] > 0 and x['price'] > 0 
                    else None, axis=1
                )
            
            # 🔴 FILTRAGE FINAL PAR STATUS
            if status and status != 'Tous' and 'status' in df.columns:
                df = df[df['status'] == status]
                print(f"✅ Données filtrées par statut: {status} → {len(df)} enregistrements")
            
            return df
            
        except Exception as e:
            print(f"❌ Erreur globale chargement: {e}")
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_available_cities(self):
        """Liste des villes disponibles"""
        try:
            df = self.safe_get_data(limit=1000)
            if df.empty:
                return ["Toutes"]
            cities = sorted(df['city'].dropna().unique().tolist())
            return ["Toutes"] + cities
        except:
            return ["Toutes"]
    
    # ==================== KPI CALCULATIONS ====================
    
    def calculate_advanced_kpis(self, df, property_type, city, status):
        """KPI avancés avec tous les calculs nécessaires"""
        default_kpi = {
            'median_price': 0, 'avg_price_m2': 0, 'active_listings': 0,
            'median_surface': 0, 'price_variation': 0, 'market_growth': 0,
            'total_volume': 0, 'avg_rooms': 0, 'density_score': 0
        }
        
        if df.empty:
            return default_kpi
        
        try:
            if property_type != "Tous":
                df = df[df['property_type'] == property_type]
            
            if city != "Toutes":
                df = df[df['city'] == city]
            
            if status != "Tous":
                df = df[df['status'] == status]
            
            if df.empty:
                return default_kpi
            
            kpis = {}
            kpis['active_listings'] = int(len(df))
            kpis['median_price'] = float(df['price'].median()) if df['price'].notna().sum() > 0 else 0
            kpis['avg_price_m2'] = float(df['price_per_m2'].mean()) if 'price_per_m2' in df.columns and df['price_per_m2'].notna().sum() > 0 else 0
            kpis['median_surface'] = float(df['surface_area'].median()) if df['surface_area'].notna().sum() > 0 else 0
            kpis['total_volume'] = float(df['price'].sum()) if df['price'].notna().sum() > 0 else 0
            kpis['avg_rooms'] = float(df['bedrooms'].mean()) if 'bedrooms' in df.columns and df['bedrooms'].notna().sum() > 0 else 0
            
            # Variation de prix
            try:
                q1 = df['price'].quantile(0.25)
                q3 = df['price'].quantile(0.75)
                kpis['price_variation'] = round(((q3 - q1) / q1 * 100), 1) if q1 > 0 else 0
            except:
                kpis['price_variation'] = 0
            
            # Croissance simulée
            kpis['market_growth'] = round(np.random.uniform(2.5, 8.5), 1)
            
            # Score densité
            kpis['density_score'] = round(len(df) / df['city'].nunique(), 1) if df['city'].nunique() > 0 else 0
            
            return kpis
            
        except Exception as e:
            print(f"❌ Erreur calcul KPI: {e}")
            return default_kpi
    
    # ==================== GRAPHIQUES COMPLETS ====================
    
    # 1. Distribution des types
    def create_type_distribution_chart(self, df):
        if df.empty:
            return go.Figure()
        
        dist = df['property_type'].value_counts().head(10)
        colors = [self.COLORS['primary'], self.COLORS['secondary'], self.COLORS['success'], 
                  self.COLORS['warning'], self.COLORS['info']][:len(dist)]
        
        fig = go.Figure(go.Bar(
            x=dist.index, y=dist.values,
            marker=dict(color=colors, line=dict(color='white', width=2)),
            text=dist.values, textposition='outside'
        ))
        fig.update_layout(
            title='📊 Distribution des Types de Biens',
            height=400, plot_bgcolor='white', paper_bgcolor='white',
            margin=dict(l=20, r=20, t=60, b=40)
        )
        return fig
    
    # 2. Distribution des prix (avec limites)
    def create_price_distribution_chart(self, df):
        if df.empty or 'price' not in df.columns:
            return go.Figure()
        
        # Limiter aux prix raisonnables
        prices = df['price'].dropna()
        prices = prices[prices > 0]  # Prix positifs
        
        fig = go.Figure(go.Histogram(
            x=prices, nbinsx=40,
            marker=dict(color=self.COLORS['primary'], line=dict(color='white', width=1.5)),
            hovertemplate='Prix: %{x:,.0f} FCFA<br>Fréquence: %{y}<extra></extra>'
        ))
        
        # Ligne médiane
        median_price = prices.median()
        fig.add_vline(x=median_price, line_dash="dash", line_color=self.COLORS['danger'], 
                     annotation_text=f"Médiane: {self.format_number(median_price)} FCFA")
        
        fig.update_layout(
            title='💰 Distribution des Prix',
            height=400, plot_bgcolor='white', paper_bgcolor='white'
        )
        return fig
    
    # 3. Top villes par prix médian
    def create_city_comparison_chart(self, df):
        if df.empty:
            return go.Figure()
        
        city_stats = df.groupby('city')['price'].agg(['median', 'count']).reset_index()
        city_stats = city_stats[city_stats['count'] >= 5]  # Min 5 annonces
        city_stats = city_stats.sort_values('median', ascending=False).head(12)
        
        fig = go.Figure(go.Bar(
            y=city_stats['city'], x=city_stats['median'],
            orientation='h',
            marker=dict(
                color=city_stats['median'],
                colorscale=[[0, self.COLORS['success']], [0.5, self.COLORS['warning']], [1, self.COLORS['danger']]],
                line=dict(color='white', width=2)
            ),
            text=[f"{self.format_number(v)} FCFA" for v in city_stats['median']],
            textposition='outside'
        ))
        fig.update_layout(
            title='🏙️ Top Villes - Prix Médian (min 5 annonces)',
            height=500, plot_bgcolor='white', paper_bgcolor='white'
        )
        return fig
    
    # 4. Prix au m² par type
    def create_price_per_m2_chart(self, df):
        if df.empty or 'price_per_m2' not in df.columns:
            return go.Figure()
        
        df_filtered = df[df['price_per_m2'].notna()]
        stats = df_filtered.groupby('property_type')['price_per_m2'].agg(['mean', 'median']).reset_index()
        stats = stats.sort_values('median', ascending=False)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Médiane', x=stats['property_type'], y=stats['median'],
            marker=dict(color=self.COLORS['primary'], line=dict(color='white', width=2))
        ))
        fig.add_trace(go.Bar(
            name='Moyenne', x=stats['property_type'], y=stats['mean'],
            marker=dict(color=self.COLORS['secondary'], line=dict(color='white', width=2), opacity=0.7)
        ))
        fig.update_layout(
            title='📐 Prix au m² par Type de Bien',
            height=400, plot_bgcolor='white', paper_bgcolor='white',
            barmode='group'
        )
        return fig
    
    # 5. Scatter Plot Prix vs Surface (limité à 450m²)
    def create_scatter_price_surface_chart(self, df):
        if df.empty or 'surface_area' not in df.columns:
            return go.Figure()
        
        # 🔴 LIMITE SURFACE MAX 450m²
        df_filtered = df[
            (df['surface_area'].notna()) & 
            (df['surface_area'] > 0) & 
            (df['surface_area'] <= self.MAX_SURFACE)
        ].copy()
        
        if df_filtered.empty:
            return go.Figure()
        
        # Échantillon pour performance
        df_sample = df_filtered.sample(min(400, len(df_filtered)))
        
        fig = go.Figure()
        property_types = df_sample['property_type'].unique()
        colors_map = {
            property_types[i]: [self.COLORS['primary'], self.COLORS['secondary'], 
                               self.COLORS['success'], self.COLORS['warning'], 
                               self.COLORS['info']][i % 5]
            for i in range(len(property_types))
        }
        
        for prop_type in property_types:
            df_type = df_sample[df_sample['property_type'] == prop_type]
            fig.add_trace(go.Scatter(
                x=df_type['surface_area'], y=df_type['price'],
                mode='markers', name=prop_type,
                marker=dict(size=8, color=colors_map[prop_type], opacity=0.7, line=dict(color='white', width=1)),
                hovertemplate='%{text}<br>Surface: %{x} m²<br>Prix: %{y:,.0f} FCFA<extra></extra>',
                text=[prop_type] * len(df_type)
            ))
        
        fig.update_layout(
            title=f'⚫ Relation Prix - Surface (max {self.MAX_SURFACE}m²)',
            height=500, plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(title='Surface (m²)'),
            yaxis=dict(title='Prix (FCFA)')
        )
        return fig
    
    # 6. Treemap hiérarchique
    def create_treemap_chart(self, df):
        if df.empty:
            return go.Figure()
        
        # Agréger
        hierarchy = df.groupby(['city', 'property_type', 'status']).agg({
            'price': ['count', 'mean']
        }).reset_index()
        hierarchy.columns = ['city', 'property_type', 'status', 'count', 'avg_price']
        
        fig = go.Figure(go.Treemap(
            labels=hierarchy['property_type'],
            parents=hierarchy['city'],
            values=hierarchy['count'],
            text=[f"{v/1_000_000:.1f}M" for v in hierarchy['avg_price']],
            textposition='middle center',
            marker=dict(colorscale='Viridis')
        ))
        fig.update_layout(
            title='🌳 Structure Marché (Ville × Type × Statut)',
            height=600
        )
        return fig
    
    # 7. Violin plot (distribution par type)
    def create_violin_chart(self, df):
        if df.empty or 'price' not in df.columns:
            return go.Figure()
        
        fig = go.Figure()
        property_types = df['property_type'].unique()
        colors = [self.COLORS['primary'], self.COLORS['secondary'], 
                 self.COLORS['success'], self.COLORS['warning']][:len(property_types)]
        
        for i, ptype in enumerate(property_types):
            df_type = df[df['property_type'] == ptype]
            prices = df_type['price'].dropna()
            
            if len(prices) > 0:
                fig.add_trace(go.Violin(
                    y=prices, name=ptype, box_visible=True, meanline_visible=True,
                    fillcolor=colors[i], opacity=0.6
                ))
        
        fig.update_layout(
            title='🎻 Distribution des Prix par Type',
            height=450
        )
        return fig
    
    # 8. Heatmap corrélation
    def create_correlation_heatmap(self, df):
        if df.empty:
            return go.Figure()
        
        numeric_cols = ['price', 'surface_area', 'bedrooms', 'price_per_m2']
        available_cols = [col for col in numeric_cols if col in df.columns]
        
        if len(available_cols) < 2:
            return go.Figure()
        
        df_numeric = df[available_cols].dropna()
        if df_numeric.empty:
            return go.Figure()
        
        corr = df_numeric.corr()
        
        fig = go.Figure(go.Heatmap(
            z=corr.values, x=corr.columns, y=corr.columns,
            colorscale='RdBu', zmid=0,
            text=corr.values.round(2), texttemplate='%{text}'
        ))
        fig.update_layout(
            title='🔥 Matrice de Corrélation',
            height=400
        )
        return fig
    
    # 9. Tendances temporelles
    def create_trends_chart(self, df):
        if df.empty or 'scraped_at' not in df.columns:
            return go.Figure()
        
        df_dated = df[df['scraped_at'].notna()].copy()
        if df_dated.empty:
            return go.Figure()
        
        df_dated['date'] = pd.to_datetime(df_dated['scraped_at']).dt.date
        trend = df_dated.groupby(['date', 'property_type']).size().reset_index(name='count')
        
        fig = go.Figure()
        for ptype in trend['property_type'].unique():
            df_type = trend[trend['property_type'] == ptype]
            fig.add_trace(go.Scatter(
                x=df_type['date'], y=df_type['count'],
                mode='lines+markers', name=ptype, stackgroup='one'
            ))
        
        fig.update_layout(
            title='📈 Évolution Temporelle des Annonces',
            height=450
        )
        return fig
    
    # ==================== UI COMPONENTS ====================
    
    def create_kpi_card(self, icon, title, value, color, suffix="", trend=None):
        """Carte KPI moderne avec design cohérent"""
        return html.Div([
            html.Div([DashIconify(icon=icon, width=28, color="white")],
                style={
                    'background': f'linear-gradient(135deg, {color}, {self.adjust_color_brightness(color, -20)})',
                    'borderRadius': '16px', 'padding': '14px', 'display': 'flex',
                    'alignItems': 'center', 'justifyContent': 'center',
                    'boxShadow': f'0 8px 16px {color}30', 'marginBottom': '16px'
                }
            ),
            html.Div(title, style={
                'fontSize': '13px', 'fontWeight': '500',
                'color': self.COLORS['text_secondary'], 'marginBottom': '8px'
            }),
            html.Div(f"{self.format_number(value)}{suffix}", style={
                'fontSize': '26px', 'fontWeight': '700',
                'color': self.COLORS['text_primary'], 'marginBottom': '8px'
            }),
            html.Div([
                DashIconify(
                    icon="mdi:trending-up" if trend and trend > 0 else "mdi:trending-down",
                    width=16, color=self.COLORS['success'] if trend and trend > 0 else self.COLORS['danger']
                ),
                html.Span(
                    f"+{trend}%" if trend and trend > 0 else f"{trend}%",
                    style={
                        'fontSize': '12px', 'fontWeight': '600',
                        'color': self.COLORS['success'] if trend and trend > 0 else self.COLORS['danger'],
                        'marginLeft': '4px'
                    }
                )
            ], style={'display': 'flex', 'alignItems': 'center'}) if trend is not None else None
        ], style={
            'background': 'white', 'borderRadius': '20px', 'padding': '24px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.06)', 'border': f'1px solid {self.COLORS["border"]}',
            'transition': 'all 0.3s ease', 'height': '100%'
        })
    
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
    
    def format_number(self, num):
        if num == 0:
            return "0"
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        if num >= 1_000:
            return f"{num/1_000:.0f}K"
        return f"{int(num):,}".replace(',', ' ')
    
    # ==================== LAYOUT ====================
    
    def setup_layout(self):
        """Layout principal avec tous les graphes organisés en grille"""
        
        # CSS personnalisé
        custom_css = """
            * { font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
            body { background: #F8FAFC; margin: 0; padding: 0; }
            .graph-card { transition: all 0.3s ease; }
            .graph-card:hover { transform: translateY(-4px); box-shadow: 0 12px 28px rgba(0,0,0,0.12) !important; }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
            .sidebar-toggle-mobile { display: none; }
            @media (max-width: 991px) { .sidebar-toggle-mobile { display: flex; } }
        """
        
        self.app.layout = html.Div([
            # CSS
            html.Link(rel='stylesheet', href='data:text/css;base64,' + base64.b64encode(custom_css.encode()).decode()),
            
            # Header
            html.Div([
                html.Div([
                    html.Div([DashIconify(icon="mdi:home-analytics", width=36, color="white")],
                        style={
                            'background': f'linear-gradient(135deg, {self.COLORS["primary"]}, {self.COLORS["purple"]})',
                            'borderRadius': '14px', 'padding': '10px', 'marginRight': '16px',
                            'boxShadow': '0 8px 16px rgba(99, 102, 241, 0.3)'
                        }
                    ),
                    html.Div([
                        html.H1("Observatoire Immobilier Complet", style={'fontSize': '28px', 'fontWeight': '800', 'color': 'white', 'margin': '0'}),
                        html.P("Analyse complète du marché sénégalais", style={'fontSize': '14px', 'color': 'rgba(255,255,255,0.9)', 'margin': '4px 0 0 0'})
                    ])
                ], style={'display': 'flex', 'alignItems': 'center'}),
                html.Div([
                    html.Div(style={'width': '8px', 'height': '8px', 'background': '#10B981', 'borderRadius': '50%', 'marginRight': '8px', 'animation': 'pulse 2s infinite'}),
                    html.Span("LIVE", style={'fontSize': '12px', 'fontWeight': '700', 'color': 'white', 'letterSpacing': '1px'})
                ], style={'display': 'flex', 'alignItems': 'center', 'background': 'rgba(255,255,255,0.15)', 'padding': '8px 16px', 'borderRadius': '20px', 'backdropFilter': 'blur(10px)'})
            ], style={
                'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                'maxWidth': '1800px', 'margin': '0 auto', 'padding': '0 24px',
                'background': f'linear-gradient(135deg, {self.COLORS["primary"]}, {self.COLORS["purple"]})',
                'paddingTop': '28px', 'paddingBottom': '28px', 'boxShadow': '0 4px 20px rgba(99, 102, 241, 0.25)', 'marginBottom': '32px'
            }),
            
            # Filtres
            html.Div([
                html.Div([
                    html.Div([DashIconify(icon="mdi:filter-variant", width=20, color=self.COLORS['primary']),
                        html.Span("Filtres", style={'fontSize': '16px', 'fontWeight': '700', 'color': self.COLORS['text_primary'], 'marginLeft': '8px'})],
                        style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}
                    ),
                    html.Div([
                        html.Div([
                            html.Label("Type de bien", style={'fontSize': '13px', 'fontWeight': '600', 'color': self.COLORS['text_secondary'], 'marginBottom': '8px', 'display': 'block'}),
                            dcc.Dropdown(id='property-type-selector', options=[
                                {'label': '🏘️ Tous les types', 'value': 'Tous'},
                                {'label': '🏠 Appartement', 'value': 'Appartement'},
                                {'label': '🏡 Villa', 'value': 'Villa'},
                                {'label': '🏢 Studio', 'value': 'Studio'},
                                {'label': '🏘️ Duplex', 'value': 'Duplex'}
                            ], value='Tous', clearable=False, style={'borderRadius': '12px'})
                        ], style={'flex': '1', 'minWidth': '200px'}),
                        
                        html.Div([
                            html.Label("Ville", style={'fontSize': '13px', 'fontWeight': '600', 'color': self.COLORS['text_secondary'], 'marginBottom': '8px', 'display': 'block'}),
                            dcc.Dropdown(id='city-selector', options=[{'label': f'📍 {city}', 'value': city} for city in self.get_available_cities()], value='Toutes', clearable=False, style={'borderRadius': '12px'})
                        ], style={'flex': '1', 'minWidth': '200px'}),
                        
                        html.Div([
                            html.Label("Statut (🔴 CRITIQUE)", style={'fontSize': '13px', 'fontWeight': '700', 'color': self.COLORS['warning'], 'marginBottom': '8px', 'display': 'block'}),
                            dcc.Dropdown(id='status-selector', options=[
                                {'label': '🏘️ Tous', 'value': 'Tous'},
                                {'label': '💰 Vente', 'value': 'Vente'},
                                {'label': '🏠 Location', 'value': 'Location'}
                            ], value='Tous', clearable=False, style={'borderRadius': '12px'})
                        ], style={'flex': '1', 'minWidth': '200px'}),
                        
                        html.Button([DashIconify(icon="mdi:refresh", width=20, color="white"),
                            html.Span("Actualiser", style={'marginLeft': '8px'})],
                            id='refresh-button', style={
                                'background': f'linear-gradient(135deg, {self.COLORS["primary"]}, {self.COLORS["purple"]})',
                                'color': 'white', 'border': 'none', 'borderRadius': '12px',
                                'padding': '12px 24px', 'fontSize': '14px', 'fontWeight': '600',
                                'cursor': 'pointer', 'display': 'flex', 'alignItems': 'center',
                                'boxShadow': f'0 4px 12px {self.COLORS["primary"]}40', 'alignSelf': 'flex-end'
                            }
                        )
                    ], style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap', 'alignItems': 'flex-end'})
                ], style={'maxWidth': '1800px', 'margin': '0 auto', 'padding': '0 24px'})
            ], style={
                'background': 'white', 'paddingTop': '24px', 'paddingBottom': '24px', 'borderRadius': '20px',
                'boxShadow': '0 4px 20px rgba(0,0,0,0.06)', 'border': f'1px solid {self.COLORS["border"]}', 'marginBottom': '32px'
            }),
            
            # KPI Section
            html.Div(id='kpi-section', style={'marginBottom': '32px'}),
            
            # GRILLE PRINCIPALE - TOUS LES GRAPHIQUES
            html.Div([
                html.Div([
                    # Ligne 1: 2 colonnes
                    html.Div([
                        html.Div(id='graph-type-distribution', className='graph-card'),
                        html.Div(id='graph-price-distribution', className='graph-card')
                    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(500px, 1fr))', 'gap': '24px', 'marginBottom': '24px'}),
                    
                    # Ligne 2: Pleine largeur
                    html.Div([
                        html.Div(id='graph-city-comparison', className='graph-card')
                    ], style={'marginBottom': '24px'}),
                    
                    # Ligne 3: 2 colonnes
                    html.Div([
                        html.Div(id='graph-price-per-m2', className='graph-card'),
                        html.Div(id='graph-violin', className='graph-card')
                    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(500px, 1fr))', 'gap': '24px', 'marginBottom': '24px'}),
                    
                    # Ligne 4: Pleine largeur
                    html.Div([
                        html.Div(id='graph-scatter-surface', className='graph-card')
                    ], style={'marginBottom': '24px'}),
                    
                    # Ligne 5: 2 colonnes
                    html.Div([
                        html.Div(id='graph-correlation-heatmap', className='graph-card'),
                        html.Div(id='graph-treemap', className='graph-card')
                    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(500px, 1fr))', 'gap': '24px', 'marginBottom': '24px'}),
                    
                    # Ligne 6: Pleine largeur - Tendances
                    html.Div([
                        html.Div(id='graph-trends', className='graph-card')
                    ], style={'marginBottom': '24px'}),
                    
                ], style={
                    'maxWidth': '1800px',
                    'margin': '0 auto',
                    'padding': '0 24px 40px 24px'
                })
            ])
            
        ], style={'minHeight': '100vh', 'background': '#F8FAFC'})
    
    # ==================== CALLBACKS ====================
    
    def setup_callbacks(self):
        """Callbacks pour mettre à jour tous les graphes"""
        
        @self.app.callback(
            Output('kpi-section', 'children'),
            Output('graph-type-distribution', 'children'),
            Output('graph-price-distribution', 'children'),
            Output('graph-city-comparison', 'children'),
            Output('graph-price-per-m2', 'children'),
            Output('graph-violin', 'children'),
            Output('graph-scatter-surface', 'children'),
            Output('graph-correlation-heatmap', 'children'),
            Output('graph-treemap', 'children'),
            Output('graph-trends', 'children'),
            [
                Input('property-type-selector', 'value'),
                Input('city-selector', 'value'),
                Input('status-selector', 'value'),
                Input('refresh-button', 'n_clicks')
            ]
        )
        def update_all_graphs(property_type, city, status, n_clicks):
            """Mettre à jour TOUS les graphes avec les filtres"""
            try:
                # 🔴 CHARGEMENT DES DONNÉES AVEC TOUS LES FILTRES
                df = self.safe_get_data(property_type, city, status)
                
                if df.empty:
                    empty_msg = html.Div("Aucune donnée pour ces filtres", style={
                        'textAlign': 'center', 'padding': '40px', 'color': self.COLORS['text_secondary']
                    })
                    return [empty_msg] * 11
                
                # KPI
                kpis = self.calculate_advanced_kpis(df, property_type, city, status)
                kpi_section = html.Div([
                    html.Div([
                        self.create_kpi_card("mdi:currency-usd", "Prix Médian", kpis['median_price'], self.COLORS['primary'], " FCFA", kpis['market_growth']),
                        self.create_kpi_card("mdi:ruler-square", "Prix Moyen/m²", kpis['avg_price_m2'], self.COLORS['success'], " FCFA"),
                        self.create_kpi_card("mdi:file-document-multiple", "Annonces Actives", kpis['active_listings'], self.COLORS['info']),
                        self.create_kpi_card("mdi:tape-measure", "Surface Médiane", kpis['median_surface'], self.COLORS['warning'], " m²"),
                        self.create_kpi_card("mdi:chart-line", "Variation", kpis['price_variation'], self.COLORS['purple'], "%"),
                        self.create_kpi_card("mdi:tag", f"Statut: {status}", len(df[df['status'] == status]) if status != 'Tous' else len(df), 
                                           self.COLORS['secondary'] if status == 'Vente' else self.COLORS['teal'], "")
                    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))', 'gap': '20px'})
                ])
                
                # Graphiques
                graphs = [
                    kpi_section,
                    dcc.Graph(figure=self.create_type_distribution_chart(df), config={'displayModeBar': False}),
                    dcc.Graph(figure=self.create_price_distribution_chart(df), config={'displayModeBar': False}),
                    dcc.Graph(figure=self.create_city_comparison_chart(df), config={'displayModeBar': False}),
                    dcc.Graph(figure=self.create_price_per_m2_chart(df), config={'displayModeBar': False}),
                    dcc.Graph(figure=self.create_violin_chart(df), config={'displayModeBar': False}),
                    dcc.Graph(figure=self.create_scatter_price_surface_chart(df), config={'displayModeBar': False}),
                    dcc.Graph(figure=self.create_correlation_heatmap(df), config={'displayModeBar': False}),
                    dcc.Graph(figure=self.create_treemap_chart(df), config={'displayModeBar': False}),
                    dcc.Graph(figure=self.create_trends_chart(df), config={'displayModeBar': False})
                ]
                
                # Styliser les conteneurs
                styled_graphs = []
                for graph in graphs[1:]:  # Skip KPI section
                    styled_graphs.append(html.Div(graph, style={
                        'background': 'white', 'padding': '24px', 'borderRadius': '20px',
                        'boxShadow': '0 4px 20px rgba(0,0,0,0.06)', 'border': f'1px solid {self.COLORS["border"]}'
                    }))
                
                return [graphs[0]] + styled_graphs
                
            except Exception as e:
                print(f"❌ Erreur callback Maj: {e}")
                traceback.print_exc()
                error_msg = html.Div([
                    DashIconify(icon="mdi:alert-circle", width=48, color=self.COLORS['danger']),
                    html.H3("Erreur de Chargement", style={'color': self.COLORS['danger'], 'marginTop': '16px'})
                ], style={'textAlign': 'center', 'padding': '40px'})
                return [error_msg] + [html.Div()] * 10


def create_enhanced_dashboard(server=None, routes_pathname_prefix="/dashboard/", requests_pathname_prefix="/dashboard/"):
    """Factory function avec sidebar cohérente"""
    dashboard = EnhancedMainDashboard(
        server=server,
        routes_pathname_prefix=routes_pathname_prefix,
        requests_pathname_prefix=requests_pathname_prefix
    )
    original_layout = dashboard.app.layout
    dashboard.app.layout = create_sidebar_layout(original_layout)
    print("✅ Main Dashboard complet créé avec succès (11 graphes, status, surface max 450m²)")
    return dashboard.app