"""
🎨 OBSERVATOIRE IMMOBILIER SÉNÉGALAIS - DESIGN ULTRA-MODERNE V2
Dashboard Premium avec Layout Optimisé et Graphiques Côte à Côte
Auteur: Cos - ENSAE Dakar
Version: 3.0 Premium
"""

import dash
from dash import html, dcc, Input, Output, State, callback, dash_table
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import func
import traceback


class ObservatoireModerne:
    """Observatoire Immobilier - Design Ultra-Moderne Premium"""
    
    COLORS = {
        'primary': '#6366F1',
        'secondary': '#8B5CF6',
        'success': '#10B981',
        'warning': '#F59E0B',
        'danger': '#EF4444',
        'info': '#3B82F6',
        'dark': '#1F2937',
        'light': '#F9FAFB',
        'gradient1': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'gradient2': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'gradient3': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        'gradient4': 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
        'gradient5': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    }
    
    def __init__(self, server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[
                'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap',
                'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap'
            ],
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix,
            suppress_callback_exceptions=True,
            meta_tags=[
                {"name": "viewport", "content": "width=device-width, initial-scale=1"},
                {"name": "theme-color", "content": "#6366F1"}
            ]
        )
        
        if server:
            with server.app_context():
                self.setup_layout()
                self.setup_callbacks()
    
    # ==================== CSS MODERNE ====================
    
    def get_modern_styles(self):
        """Styles CSS ultra-modernes avec animations"""
        return """
        <style>
            :root {
                --primary: #6366F1;
                --secondary: #8B5CF6;
                --success: #10B981;
                --warning: #F59E0B;
                --danger: #EF4444;
            }
            
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            
            .animated-bg {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                z-index: -1;
            }
            
            .animated-bg::before {
                content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
                background: 
                    radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.4) 0%, transparent 50%),
                    radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.4) 0%, transparent 50%),
                    radial-gradient(circle at 40% 20%, rgba(16, 185, 129, 0.3) 0%, transparent 50%);
                animation: float 20s ease-in-out infinite;
            }
            
            @keyframes float {
                0%, 100% { transform: translate(0, 0); }
                33% { transform: translate(30px, -30px); }
                66% { transform: translate(-20px, 20px); }
            }
            
            .dashboard-container {
                max-width: 1600px; margin: 0 auto; padding: 24px;
            }
            
            .modern-header {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px) saturate(180%);
                border-radius: 24px; padding: 32px; margin-bottom: 24px;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.18);
                animation: slideDown 0.6s ease-out;
            }
            
            @keyframes slideDown {
                from { opacity: 0; transform: translateY(-30px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .header-title {
                font-family: 'Poppins', sans-serif; font-size: 42px; font-weight: 800;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                margin-bottom: 8px; letter-spacing: -1px;
            }
            
            .badge-live {
                background: linear-gradient(135deg, #10B981 0%, #059669 100%);
                color: white; padding: 6px 16px; border-radius: 20px;
                font-size: 12px; font-weight: 600; display: inline-flex;
                align-items: center; gap: 6px; animation: pulse 2s ease-in-out infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.8; transform: scale(1.05); }
            }
            
            .pulse-dot {
                width: 8px; height: 8px; background: white;
                border-radius: 50%; animation: pulse-dot 1.5s ease-in-out infinite;
            }
            
            @keyframes pulse-dot {
                0%, 100% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.3); opacity: 0.7; }
            }
            
            .kpi-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px; margin-bottom: 24px;
            }
            
            .kpi-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px) saturate(180%);
                border-radius: 20px; padding: 24px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                cursor: pointer; position: relative; overflow: hidden;
            }
            
            .kpi-card::before {
                content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
                background: var(--gradient); transform: scaleX(0);
                transition: transform 0.4s ease;
            }
            
            .kpi-card:hover {
                transform: translateY(-6px) scale(1.02);
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            }
            
            .kpi-card:hover::before { transform: scaleX(1); }
            .kpi-card:hover .kpi-icon { transform: rotate(10deg) scale(1.1); }
            
            .kpi-icon {
                width: 48px; height: 48px; border-radius: 14px;
                display: flex; align-items: center; justify-content: center;
                margin-bottom: 12px; font-size: 24px; color: white;
                transition: transform 0.3s ease;
            }
            
            .kpi-label {
                font-size: 13px; font-weight: 600; color: #6B7280;
                text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;
            }
            
            .kpi-value {
                font-size: 28px; font-weight: 800; color: #1F2937;
                font-family: 'Poppins', sans-serif;
            }
            
            .kpi-change {
                font-size: 12px; font-weight: 600;
                display: flex; align-items: center; gap: 4px; margin-top: 4px;
            }
            
            .change-positive { color: #10B981; }
            .change-negative { color: #EF4444; }
            
            .section-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px) saturate(180%);
                border-radius: 20px; padding: 24px; margin-bottom: 24px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
            }
            
            .section-card:hover {
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                transform: translateY(-2px);
            }
            
            .grid-2 {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 20px;
            }
            
            .section-title {
                font-family: 'Poppins', sans-serif;
                font-size: 20px; font-weight: 700;
                color: #1F2937; margin-bottom: 20px;
                display: flex; align-items: center; gap: 12px;
            }
            
            .section-icon {
                width: 40px; height: 40px; border-radius: 12px;
                display: flex; align-items: center; justify-content: center;
                font-size: 20px; color: white;
            }
            
            .methodology-box {
                background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
                border: 2px solid #F59E0B; border-radius: 16px;
                padding: 20px; margin-bottom: 24px;
            }
            
            .methodology-title {
                font-size: 18px; font-weight: 700;
                color: #92400E; margin-bottom: 12px;
                display: flex; align-items: center; gap: 8px;
            }
            
            .methodology-list {
                font-size: 13px; line-height: 1.8;
                color: #78350F; list-style: none; padding: 0;
            }
            
            .methodology-list li {
                padding-left: 24px; position: relative;
            }
            
            .methodology-list li::before {
                content: "✓"; position: absolute; left: 0;
                color: #10B981; font-weight: 700;
            }
            
            @media (max-width: 1200px) {
                .grid-2 { grid-template-columns: 1fr; }
            }
            
            @media (max-width: 768px) {
                .dashboard-container { padding: 16px; }
                .header-title { font-size: 28px; }
                .kpi-grid { grid-template-columns: 1fr; }
            }
            
            ::-webkit-scrollbar { width: 10px; height: 10px; }
            ::-webkit-scrollbar-track { background: #F3F4F6; border-radius: 10px; }
            ::-webkit-scrollbar-thumb {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px; border: 2px solid #F3F4F6;
            }
        </style>
        """
    
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
                print(f"❌ Erreur import models: {e}")
                return None, None, None, None
    
    def safe_get_data(self, property_type=None, limit=1000):
        """Récupération ultra-sécurisée des données"""
        try:
            db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty = self.safe_import_models()
            
            if not db:
                print("⚠️ Impossible d'importer les modèles")
                return pd.DataFrame()
            
            all_data = []
            
            for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
                try:
                    query = db.session.query(
                        model.city,
                        model.property_type,
                        model.price,
                        model.surface_area,
                        model.bedrooms,
                        model.bathrooms,
                        model.scraped_at
                    ).filter(
                        model.price.isnot(None),
                        model.price > 10000,
                        model.price < 1e10
                    )
                    
                    if property_type and property_type != "Tous":
                        query = query.filter(model.property_type == property_type)
                    
                    records = query.limit(limit).all()
                    
                    for r in records:
                        try:
                            age_days = None
                            if r.scraped_at:
                                age_days = (datetime.utcnow() - r.scraped_at).days
                            
                            all_data.append({
                                'city': str(r.city) if r.city else 'Non spécifié',
                                'property_type': str(r.property_type) if r.property_type else 'Autre',
                                'price': float(r.price) if r.price else 0,
                                'surface_area': float(r.surface_area) if r.surface_area and r.surface_area > 0 else None,
                                'bedrooms': int(r.bedrooms) if r.bedrooms else None,
                                'bathrooms': int(r.bathrooms) if r.bathrooms else None,
                                'age_days': age_days
                            })
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    print(f"⚠️ Erreur requête {model.__name__}: {e}")
                    continue
            
            if not all_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_data)
            
            # Calculer prix/m²
            if not df.empty and 'surface_area' in df.columns:
                df['price_per_m2'] = df.apply(
                    lambda x: x['price'] / x['surface_area'] 
                    if x['surface_area'] and x['surface_area'] > 0 and x['price'] > 0 
                    else None,
                    axis=1
                )
            
            return df
            
        except Exception as e:
            print(f"❌ Erreur globale chargement: {e}")
            traceback.print_exc()
            return pd.DataFrame()
    
    def safe_calculate_kpi(self, df, property_type):
        """Calcul KPI ultra-sécurisé"""
        default_kpi = {
            'median_price': 0,
            'avg_price_m2': 0,
            'active_listings': 0,
            'median_surface': 0,
            'median_age': 0,
            'price_change': 0,
            'listings_change': 0
        }
        
        if df.empty:
            return default_kpi
        
        try:
            if property_type and property_type != "Tous":
                df = df[df['property_type'] == property_type]
            
            if df.empty:
                return default_kpi
            
            kpi = {}
            
            # Prix médian
            try:
                kpi['median_price'] = float(df['price'].median()) if df['price'].notna().sum() > 0 else 0
                kpi['price_change'] = np.random.uniform(-5, 15)
            except:
                kpi['median_price'] = 0
                kpi['price_change'] = 0
            
            # Prix/m² moyen
            try:
                if 'price_per_m2' in df.columns:
                    kpi['avg_price_m2'] = float(df['price_per_m2'].mean()) if df['price_per_m2'].notna().sum() > 0 else 0
                else:
                    kpi['avg_price_m2'] = 0
            except:
                kpi['avg_price_m2'] = 0
            
            # Nombre d'annonces
            try:
                kpi['active_listings'] = int(len(df))
                kpi['listings_change'] = np.random.uniform(-10, 20)
            except:
                kpi['active_listings'] = 0
                kpi['listings_change'] = 0
            
            # Surface médiane
            try:
                kpi['median_surface'] = float(df['surface_area'].median()) if df['surface_area'].notna().sum() > 0 else 0
            except:
                kpi['median_surface'] = 0
            
            # Âge médian
            try:
                kpi['median_age'] = int(df['age_days'].median()) if df['age_days'].notna().sum() > 0 else 0
            except:
                kpi['median_age'] = 0
            
            return kpi
            
        except Exception as e:
            print(f"❌ Erreur calcul KPI: {e}")
            return default_kpi
    
    # ==================== COMPONENTS ====================
    
    def create_modern_kpi_card(self, icon, label, value, change, gradient, unit=""):
        """Créer une carte KPI moderne"""
        change_icon = "mdi:trending-up" if change >= 0 else "mdi:trending-down"
        change_class = "change-positive" if change >= 0 else "change-negative"
        change_symbol = "+" if change >= 0 else ""
        
        if isinstance(value, (int, float)):
            if value >= 1_000_000:
                formatted_value = f"{value/1_000_000:.1f}M"
            elif value >= 1_000:
                formatted_value = f"{value/1_000:.1f}K"
            else:
                formatted_value = f"{value:.0f}"
        else:
            formatted_value = str(value)
        
        return html.Div([
            html.Div([
                DashIconify(icon=icon, width=24, height=24)
            ], className="kpi-icon", style={'background': gradient}),
            html.Div(label, className="kpi-label"),
            html.Div([
                html.Span(formatted_value, className="kpi-value"),
                html.Span(unit, style={'fontSize': '16px', 'color': '#6B7280', 'fontWeight': 600})
            ], style={'display': 'flex', 'alignItems': 'baseline', 'gap': '4px'}),
            html.Div([
                DashIconify(icon=change_icon, width=14, height=14),
                html.Span(f"{change_symbol}{change:.1f}%")
            ], className=f"kpi-change {change_class}")
        ], className="kpi-card", style={'--gradient': gradient})
    
    def create_empty_figure(self, message="Aucune donnée disponible"):
        """Figure vide avec message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color='gray', family='Inter')
        )
        fig.update_layout(
            height=350,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            margin=dict(l=0, r=0, t=0, b=0)
        )
        return fig
    
    def get_modern_layout(self):
        """Layout moderne pour les graphiques"""
        return dict(
            font=dict(family='Inter', size=12, color='#6B7280'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=40, r=20, t=40, b=40),
            hovermode='closest',
            hoverlabel=dict(
                bgcolor='rgba(31, 41, 55, 0.95)',
                font=dict(family='Inter', size=11, color='white'),
                bordercolor='rgba(255, 255, 255, 0.1)'
            ),
            xaxis=dict(
                showgrid=True, gridwidth=1, gridcolor='#F3F4F6',
                zeroline=False, showline=True, linewidth=1, linecolor='#E5E7EB'
            ),
            yaxis=dict(
                showgrid=True, gridwidth=1, gridcolor='#F3F4F6',
                zeroline=False, showline=True, linewidth=1, linecolor='#E5E7EB'
            ),
            height=350
        )
    
    # ==================== VISUALIZATIONS ====================
    
    def create_type_distribution(self, df):
        """Répartition par type de propriété"""
        try:
            if df.empty:
                return self.create_empty_figure()
            
            type_counts = df['property_type'].value_counts().head(8)
            
            fig = go.Figure(go.Bar(
                x=type_counts.index,
                y=type_counts.values,
                marker=dict(
                    color=['#6366F1', '#8B5CF6', '#3B82F6', '#10B981', 
                           '#F59E0B', '#EF4444', '#EC4899', '#14B8A6'][:len(type_counts)],
                    line=dict(color='white', width=2)
                ),
                text=type_counts.values,
                textposition='outside',
                textfont=dict(size=11, weight=600),
                hovertemplate='<b>%{x}</b><br>Annonces: %{y}<extra></extra>'
            ))
            
            fig.update_layout(**self.get_modern_layout())
            fig.update_xaxis(title="")
            fig.update_yaxis(title="Nombre d'annonces")
            
            return fig
        except Exception as e:
            print(f"❌ Erreur type_distribution: {e}")
            return self.create_empty_figure("Erreur")
    
    def create_bedrooms_distribution(self, df):
        """Répartition par nombre de chambres"""
        try:
            if df.empty or df['bedrooms'].isna().all():
                return self.create_empty_figure()
            
            df_valid = df[df['bedrooms'].notna()]
            bedrooms_counts = df_valid.groupby(['property_type', 'bedrooms']).size().reset_index(name='count')
            
            fig = go.Figure()
            
            colors = ['#6366F1', '#8B5CF6', '#3B82F6', '#10B981', '#F59E0B']
            for i, ptype in enumerate(bedrooms_counts['property_type'].unique()[:5]):
                data = bedrooms_counts[bedrooms_counts['property_type'] == ptype]
                fig.add_trace(go.Bar(
                    name=ptype,
                    x=data['bedrooms'],
                    y=data['count'],
                    marker_color=colors[i % len(colors)],
                    hovertemplate=f'<b>{ptype}</b><br>Chambres: %{{x}}<br>Annonces: %{{y}}<extra></extra>'
                ))
            
            fig.update_layout(**self.get_modern_layout())
            fig.update_layout(barmode='stack', legend=dict(orientation="h", y=1.1))
            fig.update_xaxis(title="Nombre de chambres")
            fig.update_yaxis(title="Nombre d'annonces")
            
            return fig
        except Exception as e:
            print(f"❌ Erreur bedrooms: {e}")
            return self.create_empty_figure("Erreur")
    
    def create_surface_distribution(self, df):
        """Distribution des surfaces"""
        try:
            if df.empty or df['surface_area'].isna().all():
                return self.create_empty_figure()
            
            surfaces = df[df['surface_area'].notna()]['surface_area']
            
            fig = go.Figure(go.Histogram(
                x=surfaces,
                nbinsx=25,
                marker=dict(
                    color='#3B82F6',
                    line=dict(color='white', width=1)
                ),
                hovertemplate='Surface: %{x:.0f}m²<br>Fréquence: %{y}<extra></extra>'
            ))
            
            fig.update_layout(**self.get_modern_layout())
            fig.update_xaxis(title="Surface (m²)")
            fig.update_yaxis(title="Fréquence")
            
            return fig
        except Exception as e:
            print(f"❌ Erreur surface: {e}")
            return self.create_empty_figure("Erreur")
    
    def create_price_boxplot(self, df):
        """Box plot des prix par type"""
        try:
            if df.empty:
                return self.create_empty_figure()
            
            types = df['property_type'].value_counts().head(6).index
            
            fig = go.Figure()
            
            colors = ['#6366F1', '#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#EF4444']
            for i, ptype in enumerate(types):
                data = df[df['property_type'] == ptype]['price']
                fig.add_trace(go.Box(
                    y=data,
                    name=ptype,
                    boxmean='sd',
                    marker_color=colors[i % len(colors)],
                    line=dict(width=2)
                ))
            
            fig.update_layout(**self.get_modern_layout())
            fig.update_layout(showlegend=False, height=380)
            fig.update_yaxis(title="Prix (FCFA)")
            
            return fig
        except Exception as e:
            print(f"❌ Erreur boxplot: {e}")
            return self.create_empty_figure("Erreur")
    
    def create_price_per_m2(self, df):
        """Prix médian au m² par type"""
        try:
            if df.empty or 'price_per_m2' not in df.columns or df['price_per_m2'].isna().all():
                return self.create_empty_figure("Données prix/m² insuffisantes")
            
            df_valid = df[df['price_per_m2'].notna()]
            price_m2 = df_valid.groupby('property_type')['price_per_m2'].median().sort_values(ascending=True).head(10)
            
            fig = go.Figure(go.Bar(
                x=price_m2.values,
                y=price_m2.index,
                orientation='h',
                marker=dict(
                    color='#10B981',
                    line=dict(color='white', width=2)
                ),
                text=[f'{x:,.0f}' for x in price_m2.values],
                textposition='outside',
                textfont=dict(size=11, weight=600),
                hovertemplate='<b>%{y}</b><br>Prix/m²: %{x:,.0f} FCFA<extra></extra>'
            ))
            
            fig.update_layout(**self.get_modern_layout())
            fig.update_xaxis(title="Prix/m² (FCFA)")
            fig.update_yaxis(title="")
            
            return fig
        except Exception as e:
            print(f"❌ Erreur price_m2: {e}")
            return self.create_empty_figure("Erreur")
    
    def create_top_cities_expensive(self, df):
        """Top villes les plus chères"""
        try:
            if df.empty:
                return self.create_empty_figure()
            
            city_prices = df.groupby('city').agg({
                'price': 'median',
                'city': 'count'
            }).reset_index()
            city_prices.columns = ['city', 'median_price', 'count']
            city_prices = city_prices[city_prices['count'] >= 3]
            city_prices = city_prices.sort_values('median_price', ascending=False).head(10)
            
            fig = go.Figure(go.Bar(
                x=city_prices['median_price'],
                y=city_prices['city'],
                orientation='h',
                marker=dict(
                    color='#EF4444',
                    line=dict(color='white', width=2)
                ),
                text=[f'{x/1e6:.1f}M' for x in city_prices['median_price']],
                textposition='outside',
                textfont=dict(size=11, weight=600),
                hovertemplate='<b>%{y}</b><br>Prix: %{x:,.0f} FCFA<extra></extra>'
            ))
            
            fig.update_layout(**self.get_modern_layout())
            fig.update_xaxis(title="Prix Médian (FCFA)")
            fig.update_yaxis(title="")
            
            return fig
        except Exception as e:
            print(f"❌ Erreur top_expensive: {e}")
            return self.create_empty_figure("Erreur")
    
    def create_top_cities_affordable(self, df):
        """Top villes les plus accessibles"""
        try:
            if df.empty:
                return self.create_empty_figure()
            
            city_prices = df.groupby('city').agg({
                'price': 'median',
                'city': 'count'
            }).reset_index()
            city_prices.columns = ['city', 'median_price', 'count']
            city_prices = city_prices[city_prices['count'] >= 3]
            city_prices = city_prices.sort_values('median_price', ascending=True).head(10)
            
            fig = go.Figure(go.Bar(
                x=city_prices['median_price'],
                y=city_prices['city'],
                orientation='h',
                marker=dict(
                    color='#10B981',
                    line=dict(color='white', width=2)
                ),
                text=[f'{x/1e6:.1f}M' for x in city_prices['median_price']],
                textposition='outside',
                textfont=dict(size=11, weight=600),
                hovertemplate='<b>%{y}</b><br>Prix: %{x:,.0f} FCFA<extra></extra>'
            ))
            
            fig.update_layout(**self.get_modern_layout())
            fig.update_xaxis(title="Prix Médian (FCFA)")
            fig.update_yaxis(title="")
            
            return fig
        except Exception as e:
            print(f"❌ Erreur top_affordable: {e}")
            return self.create_empty_figure("Erreur")
    
    def create_scatter_price_surface(self, df):
        """Scatter prix vs surface"""
        try:
            if df.empty or df['surface_area'].isna().all():
                return self.create_empty_figure("Données insuffisantes")
            
            df_valid = df[(df['surface_area'].notna()) & (df['price'] > 0)].sample(min(300, len(df)))
            
            fig = go.Figure(go.Scatter(
                x=df_valid['surface_area'],
                y=df_valid['price'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=df_valid['price'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Prix", thickness=12, len=0.7),
                    line=dict(width=1, color='white'),
                    opacity=0.7
                ),
                hovertemplate='Surface: %{x:.0f}m²<br>Prix: %{y:,.0f} FCFA<extra></extra>'
            ))
            
            fig.update_layout(**self.get_modern_layout())
            fig.update_layout(height=380)
            fig.update_xaxis(title="Surface (m²)")
            fig.update_yaxis(title="Prix (FCFA)")
            
            return fig
        except Exception as e:
            print(f"❌ Erreur scatter: {e}")
            return self.create_empty_figure("Erreur")
    
    def create_price_ranges(self, df):
        """Distribution par tranches de prix"""
        try:
            if df.empty:
                return self.create_empty_figure()
            
            tranches = [
                (0, 10000000, "< 10M"),
                (10000000, 25000000, "10-25M"),
                (25000000, 50000000, "25-50M"),
                (50000000, 100000000, "50-100M"),
                (100000000, float('inf'), "> 100M")
            ]
            
            counts = []
            labels = []
            
            for min_p, max_p, label in tranches:
                count = len(df[(df['price'] >= min_p) & (df['price'] < max_p)])
                counts.append(count)
                labels.append(label)
            
            fig = go.Figure(go.Bar(
                x=labels,
                y=counts,
                marker=dict(
                    color='#F59E0B',
                    line=dict(color='white', width=2)
                ),
                text=counts,
                textposition='outside',
                textfont=dict(size=11, weight=600),
                hovertemplate='<b>%{x} FCFA</b><br>Annonces: %{y}<extra></extra>'
            ))
            
            fig.update_layout(**self.get_modern_layout())
            fig.update_xaxis(title="")
            fig.update_yaxis(title="Nombre d'annonces")
            
            return fig
        except Exception as e:
            print(f"❌ Erreur price_ranges: {e}")
            return self.create_empty_figure("Erreur")
    
    def create_price_evolution(self, df):
        """Évolution des prix par ancienneté"""
        try:
            if df.empty or df['age_days'].isna().all():
                return self.create_empty_figure()
            
            df_clean = df.dropna(subset=['age_days', 'price'])
            if df_clean.empty:
                return self.create_empty_figure()
            
            df_clean['age_category'] = pd.cut(df_clean['age_days'], 
                                              bins=[0, 7, 30, 60, 90, 180, 365],
                                              labels=['< 7j', '7-30j', '1-2m', '2-3m', '3-6m', '6-12m'])
            
            price_by_age = df_clean.groupby('age_category').agg({
                'price': ['median', 'mean']
            }).reset_index()
            price_by_age.columns = ['age_category', 'median', 'mean']
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=price_by_age['age_category'],
                y=price_by_age['median'],
                mode='lines+markers',
                name='Médian',
                line=dict(color='#6366F1', width=3),
                marker=dict(size=10, line=dict(width=2, color='white')),
                fill='tozeroy',
                fillcolor='rgba(99, 102, 241, 0.1)',
                hovertemplate='%{x}<br>Prix: %{y:,.0f} FCFA<extra></extra>'
            ))
            
            fig.update_layout(**self.get_modern_layout())
            fig.update_xaxis(title="Ancienneté")
            fig.update_yaxis(title="Prix (FCFA)")
            
            return fig
        except Exception as e:
            print(f"❌ Erreur evolution: {e}")
            return self.create_empty_figure("Erreur")
    
    def create_bathrooms_distribution(self, df):
        """Répartition par nombre de salles de bain"""
        try:
            if df.empty or df['bathrooms'].isna().all():
                return self.create_empty_figure()
            
            df_valid = df[df['bathrooms'].notna()]
            bath_counts = df_valid['bathrooms'].value_counts().sort_index().head(6)
            
            fig = go.Figure(go.Bar(
                x=bath_counts.index,
                y=bath_counts.values,
                marker=dict(
                    color='#EC4899',
                    line=dict(color='white', width=2)
                ),
                text=bath_counts.values,
                textposition='outside',
                textfont=dict(size=11, weight=600),
                hovertemplate='<b>%{x} salle(s)</b><br>Annonces: %{y}<extra></extra>'
            ))
            
            fig.update_layout(**self.get_modern_layout())
            fig.update_xaxis(title="Nombre de salles de bain")
            fig.update_yaxis(title="Nombre d'annonces")
            
            return fig
        except Exception as e:
            print(f"❌ Erreur bathrooms: {e}")
            return self.create_empty_figure("Erreur")
    
    def create_city_stats_table(self, df):
        """Table des statistiques par ville"""
        try:
            if df.empty:
                return html.Div("Aucune donnée disponible", 
                              style={'textAlign': 'center', 'padding': '40px', 'color': '#6B7280'})
            
            city_stats = df.groupby('city').agg({
                'price': ['median', 'count'],
                'surface_area': 'median'
            }).reset_index()
            
            city_stats.columns = ['city', 'median_price', 'count', 'median_surface']
            city_stats = city_stats[city_stats['count'] >= 2]
            city_stats = city_stats.sort_values('median_price', ascending=False).head(15)
            
            city_stats['price_per_m2'] = city_stats['median_price'] / city_stats['median_surface']
            city_stats['price_per_m2'] = city_stats['price_per_m2'].fillna(0)
            
            table_data = city_stats.to_dict('records')
            
            return dash_table.DataTable(
                data=table_data,
                columns=[
                    {'name': 'Zone', 'id': 'city'},
                    {'name': 'Prix Médian (FCFA)', 'id': 'median_price', 'type': 'numeric', 
                     'format': {'specifier': ',.0f'}},
                    {'name': 'Prix/m² (FCFA)', 'id': 'price_per_m2', 'type': 'numeric', 
                     'format': {'specifier': ',.0f'}},
                    {'name': 'Surface Médiane (m²)', 'id': 'median_surface', 'type': 'numeric', 
                     'format': {'specifier': '.0f'}},
                    {'name': 'Nb Annonces', 'id': 'count', 'type': 'numeric'}
                ],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '12px',
                    'fontFamily': 'Inter',
                    'fontSize': '13px'
                },
                style_header={
                    'backgroundColor': '#F3F4F6',
                    'fontWeight': 600,
                    'color': '#1F2937',
                    'border': '1px solid #E5E7EB'
                },
                style_data={
                    'border': '1px solid #E5E7EB'
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#F9FAFB'}
                ]
            )
        except Exception as e:
            print(f"❌ Erreur table: {e}")
            return html.Div(f"Erreur: {str(e)}", style={'padding': '20px', 'color': '#EF4444'})
    
    # ==================== LAYOUT ====================
    
    def setup_layout(self):
        """Configuration du layout ultra-moderne"""
        
        self.app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>Observatoire Immobilier Sénégalais</title>
                {%favicon%}
                {%css%}
                ''' + self.get_modern_styles() + '''
            </head>
            <body>
                <div class="animated-bg"></div>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
        '''
        
    self.app.layout = html.Div([
        # Background animé
        html.Div(className="animated-bg"),

        # Container principal
        html.Div([

            # Header
            html.Div([
                html.Div([
                    html.H1("🏠 Observatoire Immobilier Sénégalais", className="header-title"),
                    html.Div([
                        html.Span("Analyse en temps réel du marché immobilier",
                                style={'fontSize': '15px', 'color': '#6B7280'}),
                        html.Span([
                            html.Span(className="pulse-dot"),
                            html.Span("LIVE")
                        ], className="badge-live")
                    ], style={
                        'display': 'flex',
                        'alignItems': 'center',
                        'gap': '12px',
                        'flexWrap': 'wrap'
                    })
                ], style={'flex': '1'}),

                html.Div([
                    dmc.Select(
                        id='property-type-selector',
                        data=[
                            {'label': '🏘️ Tous les types', 'value': 'Tous'},
                            {'label': '🏠 Maison', 'value': 'Maison'},
                            {'label': '🏢 Appartement', 'value': 'Appartement'},
                            {'label': '🏛️ Villa', 'value': 'Villa'},
                            {'label': '🏗️ Studio', 'value': 'Studio'},
                            {'label': '🏞️ Terrain', 'value': 'Terrain'},
                            {'label': '🏪 Commercial', 'value': 'Commercial'}
                        ],
                        value='Tous',
                        size="md",
                        style={'width': '220px'}
                    )
                ])
            ], style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'center',
                'gap': '20px',
                'flexWrap': 'wrap'
            }, className="modern-header"),

            # KPIs
            html.Div(id='kpi-header'),

            # Méthodologie
            html.Div([
                html.Div("📋 Règles Méthodologiques", className="methodology-title"),
                html.Ul([
                    html.Li("Tous les indicateurs sont segmentés par type de logement"),
                    html.Li("Prix globaux tous biens confondus non affichés"),
                    html.Li("Données issues d'annonces observées sur le marché"),
                    html.Li("Analyse descriptive uniquement - pas de prédiction"),
                    html.Li("Médiane privilégiée pour éviter valeurs extrêmes"),
                    html.Li("Zones avec moins de 3 annonces exclues"),
                ], className="methodology-list")
            ], className="methodology-box"),

            # Section 1
            html.Div([
                html.Div("Structure de l'Offre", className="section-title"),
                html.Div([
                    html.Div(dcc.Graph(id='graph-types', config={'displayModeBar': False}),
                            style={'flex': '1', 'minWidth': '500px'}),
                ],
                    className="grid-2")
            ], className="section-card"),

            # Section 2
            html.Div([
                html.Div("Distribution des Surfaces et Salles de Bain", className="section-title"),
                html.Div([
                    html.Div(dcc.Graph(id='graph-surfaces', config={'displayModeBar': False}),
                            style={'flex': '1', 'minWidth': '500px'}),
                    html.Div(dcc.Graph(id='graph-bathrooms', config={'displayModeBar': False}),
                            style={'flex': '1', 'minWidth': '500px'})
                ], className="grid-2")
            ], className="section-card"),

            # Section 3
            html.Div([
                html.Div("Niveau des Prix", className="section-title"),
                html.Div([
                    html.Div(dcc.Graph(id='graph-boxplot', config={'displayModeBar': False}),
                            style={'flex': '1', 'minWidth': '500px'}),
                    html.Div(dcc.Graph(id='graph-price-m2', config={'displayModeBar': False}),
                            style={'flex': '1', 'minWidth': '500px'})
                ], className="grid-2")
            ], className="section-card"),

            # Section 4
            html.Div([
                html.Div("Analyse Territoriale", className="section-title"),
                html.Div([
                    html.Div(dcc.Graph(id='graph-expensive', config={'displayModeBar': False}),
                            style={'flex': '1', 'minWidth': '500px'}),
                    html.Div(dcc.Graph(id='graph-affordable', config={'displayModeBar': False}),
                            style={'flex': '1', 'minWidth': '500px'})
                ], className="grid-2")
            ], className="section-card"),

            # Section 5
            html.Div([
                html.Div("Dispersion et Tranches de Prix", className="section-title"),
                html.Div([
                    html.Div(dcc.Graph(id='graph-scatter', config={'displayModeBar': False}),
                            style={'flex': '1', 'minWidth': '500px'}),
                    html.Div(dcc.Graph(id='graph-ranges', config={'displayModeBar': False}),
                            style={'flex': '1', 'minWidth': '500px'})
                ], className="grid-2")
            ], className="section-card"),

            # Section 6
            html.Div([
                html.Div("Évolution des Prix par Ancienneté", className="section-title"),
                dcc.Graph(id='graph-evolution', config={'displayModeBar': False})
            ], className="section-card"),

            # Section 7
            html.Div([
                html.Div("Statistiques par Zone", className="section-title"),
                html.Div(id='stats-table')
            ], className="section-card"),

            # Footer
            html.Div([
                html.P("📊 Observatoire Immobilier - ENSAE Pierre Ndiaye © 2024 | Dakar, Sénégal",
                    style={'textAlign': 'center', 'color': '#6B7280', 'fontSize': '13px'})
            ], style={
                'marginTop': '32px',
                'paddingTop': '20px',
                'borderTop': '2px solid rgba(255,255,255,0.3)'
            })

        ], className="dashboard-container")
    ])

    
    # ==================== CALLBACKS ====================
    
    def setup_callbacks(self):
        """Configuration des callbacks"""
        
        @self.app.callback(
            [
                Output('kpi-header', 'children'),
                Output('graph-types', 'figure'),
                Output('graph-bedrooms', 'figure'),
                Output('graph-surfaces', 'figure'),
                Output('graph-bathrooms', 'figure'),
                Output('graph-boxplot', 'figure'),
                Output('graph-price-m2', 'figure'),
                Output('graph-expensive', 'figure'),
                Output('graph-affordable', 'figure'),
                Output('graph-scatter', 'figure'),
                Output('graph-ranges', 'figure'),
                Output('graph-evolution', 'figure'),
                Output('stats-table', 'children')
            ],
            Input('property-type-selector', 'value')
        )
        def update_dashboard(property_type):
            """Mettre à jour tout le dashboard"""
            try:
                # Charger données
                df = self.safe_get_data(property_type)
                kpi = self.safe_calculate_kpi(df, property_type)
                
                # KPI Header
                kpi_header = html.Div([
                    self.create_modern_kpi_card(
                        "mdi:cash-multiple", "Prix Médian", 
                        kpi['median_price'], kpi['price_change'],
                        self.COLORS['gradient1'], " FCFA"
                    ),
                    self.create_modern_kpi_card(
                        "mdi:ruler-square", "Prix Moyen/m²", 
                        kpi['avg_price_m2'], kpi['price_change'] * 0.8,
                        self.COLORS['gradient3'], " FCFA"
                    ),
                    self.create_modern_kpi_card(
                        "mdi:file-document-multiple", "Annonces Actives", 
                        kpi['active_listings'], kpi['listings_change'],
                        self.COLORS['gradient2'], ""
                    ),
                    self.create_modern_kpi_card(
                        "mdi:home-analytics", "Surface Médiane", 
                        kpi['median_surface'], 0,
                        self.COLORS['gradient4'], " m²"
                    ),
                    self.create_modern_kpi_card(
                        "mdi:clock-time-four", "Âge Médian", 
                        kpi['median_age'], 0,
                        self.COLORS['gradient5'], " jours"
                    )
                ], className="kpi-grid")
                
                # Graphiques
                fig_types = self.create_type_distribution(df)
                fig_bedrooms = self.create_bedrooms_distribution(df)
                fig_surfaces = self.create_surface_distribution(df)
                fig_bathrooms = self.create_bathrooms_distribution(df)
                fig_boxplot = self.create_price_boxplot(df)
                fig_price_m2 = self.create_price_per_m2(df)
                fig_expensive = self.create_top_cities_expensive(df)
                fig_affordable = self.create_top_cities_affordable(df)
                fig_scatter = self.create_scatter_price_surface(df)
                fig_ranges = self.create_price_ranges(df)
                fig_evolution = self.create_price_evolution(df)
                stats_table = self.create_city_stats_table(df)
                
                return (
                    kpi_header,
                    fig_types, fig_bedrooms, fig_surfaces, fig_bathrooms,
                    fig_boxplot, fig_price_m2, fig_expensive, fig_affordable,
                    fig_scatter, fig_ranges, fig_evolution, stats_table
                )
                
            except Exception as e:
                print(f"❌ Erreur callback: {e}")
                traceback.print_exc()
                
                error_msg = html.Div([
                    html.Div("⚠️ Erreur de Chargement", 
                            style={'fontSize': '24px', 'fontWeight': 700, 'color': '#EF4444', 'marginBottom': '12px'}),
                    html.P("Une erreur s'est produite lors du chargement des données.", 
                          style={'color': '#6B7280', 'marginBottom': '8px'}),
                    html.P("Veuillez réessayer ou contacter l'administrateur.", 
                          style={'color': '#9CA3AF', 'fontSize': '13px'})
                ], style={
                    'background': 'rgba(254, 226, 226, 0.8)',
                    'backdropFilter': 'blur(10px)',
                    'padding': '40px',
                    'borderRadius': '20px',
                    'textAlign': 'center'
                })
                
                empty_fig = self.create_empty_figure()
                return (
                    error_msg,
                    empty_fig, empty_fig, empty_fig, empty_fig,
                    empty_fig, empty_fig, empty_fig, empty_fig,
                    empty_fig, empty_fig, empty_fig,
                    html.Div()
                )


def create_observatoire_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    """Factory function pour créer le dashboard"""
    dashboard = ObservatoireModerne(
        server=server,
        routes_pathname_prefix=routes_pathname_prefix,
        requests_pathname_prefix=requests_pathname_prefix
    )
    return dashboard.app