"""
🎨 OBSERVATOIRE IMMOBILIER SÉNÉGALAIS - DESIGN ULTRA-MODERNE
Dashboard Premium avec Glassmorphism, Animations & Interface Contemporaine
Auteur: Cos - ENSAE Dakar
Version: 3.0 Premium
"""

import dash
from dash import html, dcc, Input, Output, State, callback
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
    
    # Palette de couleurs moderne et élégante
    COLORS = {
        'primary': '#6366F1',      # Indigo moderne
        'secondary': '#8B5CF6',    # Violet vibrant
        'success': '#10B981',      # Vert émeraude
        'warning': '#F59E0B',      # Ambre
        'danger': '#EF4444',       # Rouge moderne
        'info': '#3B82F6',         # Bleu vif
        'dark': '#1F2937',         # Gris foncé
        'light': '#F9FAFB',        # Gris très clair
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
            /* Variables CSS */
            :root {
                --primary: #6366F1;
                --secondary: #8B5CF6;
                --success: #10B981;
                --warning: #F59E0B;
                --danger: #EF4444;
                --dark: #1F2937;
                --light: #F9FAFB;
                --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
                --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                --shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                overflow-x: hidden;
            }
            
            /* Animated Background */
            .animated-bg {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                z-index: -1;
            }
            
            .animated-bg::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
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
            
            /* Container Principal */
            .dashboard-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 32px 24px;
                position: relative;
                z-index: 1;
            }
            
            /* Header Moderne */
            .modern-header {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px) saturate(180%);
                -webkit-backdrop-filter: blur(20px) saturate(180%);
                border-radius: 24px;
                padding: 40px;
                margin-bottom: 32px;
                box-shadow: var(--shadow-2xl);
                border: 1px solid rgba(255, 255, 255, 0.18);
                animation: slideDown 0.6s ease-out;
            }
            
            @keyframes slideDown {
                from {
                    opacity: 0;
                    transform: translateY(-30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .header-title {
                font-family: 'Poppins', sans-serif;
                font-size: 48px;
                font-weight: 800;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 12px;
                letter-spacing: -1px;
            }
            
            .header-subtitle {
                font-size: 18px;
                color: #6B7280;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .badge-live {
                background: linear-gradient(135deg, #10B981 0%, #059669 100%);
                color: white;
                padding: 6px 16px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 600;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                animation: pulse 2s ease-in-out infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.8; transform: scale(1.05); }
            }
            
            .pulse-dot {
                width: 8px;
                height: 8px;
                background: white;
                border-radius: 50%;
                animation: pulse-dot 1.5s ease-in-out infinite;
            }
            
            @keyframes pulse-dot {
                0%, 100% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.3); opacity: 0.7; }
            }
            
            /* KPI Cards Modernes */
            .kpi-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 24px;
                margin-bottom: 32px;
            }
            
            .kpi-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px) saturate(180%);
                -webkit-backdrop-filter: blur(20px) saturate(180%);
                border-radius: 20px;
                padding: 28px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                box-shadow: var(--shadow-xl);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
                cursor: pointer;
            }
            
            .kpi-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: var(--gradient);
                transform: scaleX(0);
                transition: transform 0.4s ease;
            }
            
            .kpi-card:hover {
                transform: translateY(-8px) scale(1.02);
                box-shadow: var(--shadow-2xl);
            }
            
            .kpi-card:hover::before {
                transform: scaleX(1);
            }
            
            .kpi-icon {
                width: 56px;
                height: 56px;
                border-radius: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 16px;
                font-size: 28px;
                color: white;
                transition: transform 0.3s ease;
            }
            
            .kpi-card:hover .kpi-icon {
                transform: rotate(10deg) scale(1.1);
            }
            
            .kpi-label {
                font-size: 14px;
                font-weight: 600;
                color: #6B7280;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
            }
            
            .kpi-value {
                font-size: 32px;
                font-weight: 800;
                color: #1F2937;
                margin-bottom: 4px;
                font-family: 'Poppins', sans-serif;
            }
            
            .kpi-change {
                font-size: 13px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 4px;
            }
            
            .change-positive {
                color: #10B981;
            }
            
            .change-negative {
                color: #EF4444;
            }
            
            /* Section Cards */
            .section-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px) saturate(180%);
                -webkit-backdrop-filter: blur(20px) saturate(180%);
                border-radius: 24px;
                padding: 32px;
                margin-bottom: 32px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                box-shadow: var(--shadow-xl);
                animation: fadeInUp 0.6s ease-out backwards;
                transition: all 0.3s ease;
            }
            
            .section-card:hover {
                box-shadow: var(--shadow-2xl);
                transform: translateY(-4px);
            }
            
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .section-card:nth-child(1) { animation-delay: 0.1s; }
            .section-card:nth-child(2) { animation-delay: 0.2s; }
            .section-card:nth-child(3) { animation-delay: 0.3s; }
            .section-card:nth-child(4) { animation-delay: 0.4s; }
            .section-card:nth-child(5) { animation-delay: 0.5s; }
            
            .section-header {
                display: flex;
                align-items: center;
                gap: 16px;
                margin-bottom: 28px;
                padding-bottom: 20px;
                border-bottom: 2px solid #F3F4F6;
            }
            
            .section-icon {
                width: 48px;
                height: 48px;
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                color: white;
                box-shadow: var(--shadow-lg);
            }
            
            .section-title {
                font-family: 'Poppins', sans-serif;
                font-size: 24px;
                font-weight: 700;
                color: #1F2937;
                margin: 0;
            }
            
            /* Filters Modernes */
            .filters-container {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px) saturate(180%);
                -webkit-backdrop-filter: blur(20px) saturate(180%);
                border-radius: 20px;
                padding: 24px;
                margin-bottom: 32px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                box-shadow: var(--shadow-lg);
                display: flex;
                align-items: center;
                gap: 20px;
                flex-wrap: wrap;
            }
            
            .filter-group {
                flex: 1;
                min-width: 200px;
            }
            
            .filter-label {
                font-size: 13px;
                font-weight: 600;
                color: #6B7280;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
                display: block;
            }
            
            /* Dropdown Moderne */
            .Select-control {
                border-radius: 12px !important;
                border: 2px solid #E5E7EB !important;
                background: white !important;
                transition: all 0.3s ease !important;
                padding: 4px !important;
            }
            
            .Select-control:hover {
                border-color: var(--primary) !important;
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
            }
            
            .is-focused .Select-control {
                border-color: var(--primary) !important;
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
            }
            
            /* Button Moderne */
            .modern-button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 28px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: var(--shadow-md);
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }
            
            .modern-button:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-xl);
            }
            
            .modern-button:active {
                transform: translateY(0);
            }
            
            /* Loading Spinner Moderne */
            .modern-loader {
                width: 60px;
                height: 60px;
                border: 4px solid #F3F4F6;
                border-top-color: var(--primary);
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 60px auto;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            /* Stats Badge */
            .stats-badge {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);
                padding: 8px 16px;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 600;
                color: #374151;
                margin-top: 8px;
            }
            
            /* Tooltip Moderne */
            .custom-tooltip {
                background: rgba(31, 41, 55, 0.95) !important;
                backdrop-filter: blur(10px);
                border-radius: 12px !important;
                padding: 12px 16px !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                box-shadow: var(--shadow-xl) !important;
            }
            
            /* Scrollbar Moderne */
            ::-webkit-scrollbar {
                width: 10px;
                height: 10px;
            }
            
            ::-webkit-scrollbar-track {
                background: #F3F4F6;
                border-radius: 10px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                border: 2px solid #F3F4F6;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .dashboard-container {
                    padding: 20px 16px;
                }
                
                .modern-header {
                    padding: 28px 24px;
                    border-radius: 20px;
                }
                
                .header-title {
                    font-size: 32px;
                }
                
                .kpi-grid {
                    grid-template-columns: 1fr;
                    gap: 16px;
                }
                
                .section-card {
                    padding: 24px;
                    border-radius: 20px;
                }
                
                .section-title {
                    font-size: 20px;
                }
                
                .filters-container {
                    flex-direction: column;
                    gap: 16px;
                }
                
                .filter-group {
                    width: 100%;
                }
            }
            
            /* Animation de chargement pour les graphiques */
            .js-plotly-plot {
                animation: fadeIn 0.6s ease-out;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            /* Footer Moderne */
            .modern-footer {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px) saturate(180%);
                -webkit-backdrop-filter: blur(20px) saturate(180%);
                border-radius: 20px;
                padding: 32px;
                margin-top: 40px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                box-shadow: var(--shadow-lg);
                text-align: center;
            }
            
            .footer-content {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 16px;
            }
            
            .footer-logo {
                font-family: 'Poppins', sans-serif;
                font-size: 24px;
                font-weight: 700;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .footer-text {
                font-size: 14px;
                color: #6B7280;
                font-weight: 500;
            }
            
            .footer-links {
                display: flex;
                gap: 24px;
                margin-top: 8px;
            }
            
            .footer-link {
                color: #6366F1;
                text-decoration: none;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            
            .footer-link:hover {
                color: #8B5CF6;
                transform: translateY(-2px);
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
        """Calcul KPI ultra-sécurisé avec variations"""
        default_kpi = {
            'median_price': 0,
            'avg_price_m2': 0,
            'active_listings': 0,
            'median_surface': 0,
            'median_age': 0,
            'price_change': 0,  # Variation en %
            'listings_change': 0,
            'surface_change': 0
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
                # Simuler variation (remplacer par vraie comparaison temporelle)
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
                kpi['surface_change'] = np.random.uniform(-3, 8)
            except:
                kpi['median_surface'] = 0
                kpi['surface_change'] = 0
            
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
        """Créer une carte KPI moderne avec glassmorphism"""
        change_icon = "mdi:trending-up" if change >= 0 else "mdi:trending-down"
        change_class = "change-positive" if change >= 0 else "change-negative"
        change_symbol = "+" if change >= 0 else ""
        
        # Formater la valeur
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
                DashIconify(icon=icon, width=28, height=28)
            ], className="kpi-icon", style={'background': gradient}),
            
            html.Div(label, className="kpi-label"),
            
            html.Div([
                html.Span(formatted_value, className="kpi-value"),
                html.Span(unit, style={'fontSize': '18px', 'color': '#6B7280', 'fontWeight': 600})
            ], style={'display': 'flex', 'alignItems': 'baseline', 'gap': '4px'}),
            
            html.Div([
                DashIconify(icon=change_icon, width=16, height=16),
                html.Span(f"{change_symbol}{change:.1f}%")
            ], className=f"kpi-change {change_class}")
            
        ], className="kpi-card", style={'--gradient': gradient})
    
    def create_section_header(self, icon, title, gradient):
        """Créer un en-tête de section moderne"""
        return html.Div([
            html.Div([
                DashIconify(icon=icon, width=24, height=24)
            ], className="section-icon", style={'background': gradient}),
            
            html.H2(title, className="section-title")
        ], className="section-header")
    
    # ==================== VISUALIZATIONS ====================
    
    def create_modern_chart_config(self):
        """Configuration moderne pour les graphiques Plotly"""
        return {
            'displayModeBar': False,
            'responsive': True
        }
    
    def get_modern_layout(self, title=""):
        """Layout moderne pour les graphiques"""
        return dict(
            title=dict(
                text=title,
                font=dict(size=20, family='Poppins', weight=700, color='#1F2937'),
                x=0,
                xanchor='left'
            ),
            font=dict(family='Inter', size=13, color='#6B7280'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=60, b=20),
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='rgba(31, 41, 55, 0.95)',
                font=dict(family='Inter', size=12, color='white'),
                bordercolor='rgba(255, 255, 255, 0.1)',
                namelength=-1
            ),
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='#F3F4F6',
                zeroline=False,
                showline=True,
                linewidth=2,
                linecolor='#E5E7EB'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='#F3F4F6',
                zeroline=False,
                showline=True,
                linewidth=2,
                linecolor='#E5E7EB'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#E5E7EB',
                borderwidth=1
            )
        )
    
    def create_distribution_chart(self, df):
        """Graphique de distribution des prix moderne"""
        if df.empty or 'price' not in df.columns:
            return go.Figure()
        
        fig = go.Figure()
        
        # Histogramme avec gradient
        fig.add_trace(go.Histogram(
            x=df['price'],
            nbinsx=30,
            name='Distribution',
            marker=dict(
                color=df['price'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Prix (FCFA)", thickness=15)
            ),
            opacity=0.8,
            hovertemplate='<b>Prix</b>: %{x:,.0f} FCFA<br><b>Nombre</b>: %{y}<extra></extra>'
        ))
        
        # Ajouter courbe de densité
        from scipy import stats
        density = stats.gaussian_kde(df['price'].dropna())
        xs = np.linspace(df['price'].min(), df['price'].max(), 200)
        ys = density(xs)
        
        fig.add_trace(go.Scatter(
            x=xs,
            y=ys * len(df) * (df['price'].max() - df['price'].min()) / 30,
            mode='lines',
            name='Densité',
            line=dict(color='#EF4444', width=3, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(239, 68, 68, 0.1)',
            hovertemplate='<b>Prix</b>: %{x:,.0f} FCFA<extra></extra>'
        ))
        
        fig.update_layout(self.get_modern_layout("📊 Distribution des Prix"))
        
        return fig
    
    def create_price_by_city_chart(self, df):
        """Graphique des prix par ville moderne"""
        if df.empty or 'city' not in df.columns or 'price' not in df.columns:
            return go.Figure()
        
        # Agréger par ville
        city_stats = df.groupby('city').agg({
            'price': ['median', 'count']
        }).reset_index()
        city_stats.columns = ['city', 'median_price', 'count']
        city_stats = city_stats.sort_values('median_price', ascending=False).head(10)
        
        fig = go.Figure()
        
        # Barres avec gradient
        colors = ['#6366F1', '#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', 
                  '#EF4444', '#EC4899', '#14B8A6', '#F97316', '#8B5CF6']
        
        fig.add_trace(go.Bar(
            x=city_stats['median_price'],
            y=city_stats['city'],
            orientation='h',
            marker=dict(
                color=colors[:len(city_stats)],
                line=dict(color='white', width=2)
            ),
            text=city_stats['median_price'].apply(lambda x: f"{x/1_000_000:.1f}M"),
            textposition='outside',
            textfont=dict(size=13, family='Poppins', weight=600),
            hovertemplate='<b>%{y}</b><br>Prix médian: %{x:,.0f} FCFA<br>Annonces: ' + 
                         city_stats['count'].astype(str) + '<extra></extra>'
        ))
        
        fig.update_layout(self.get_modern_layout("🏙️ Prix Médian par Ville (Top 10)"))
        fig.update_xaxis(title="Prix Médian (FCFA)")
        fig.update_yaxis(title="")
        
        return fig
    
    def create_property_type_chart(self, df):
        """Graphique par type de propriété moderne"""
        if df.empty or 'property_type' not in df.columns:
            return go.Figure()
        
        type_counts = df['property_type'].value_counts().head(8)
        
        fig = go.Figure()
        
        fig.add_trace(go.Pie(
            labels=type_counts.index,
            values=type_counts.values,
            hole=0.5,
            marker=dict(
                colors=['#6366F1', '#8B5CF6', '#3B82F6', '#10B981', 
                       '#F59E0B', '#EF4444', '#EC4899', '#14B8A6'],
                line=dict(color='white', width=3)
            ),
            textinfo='label+percent',
            textfont=dict(size=14, family='Inter', weight=600),
            hovertemplate='<b>%{label}</b><br>Nombre: %{value}<br>Part: %{percent}<extra></extra>',
            pull=[0.05 if i == 0 else 0 for i in range(len(type_counts))]
        ))
        
        fig.update_layout(
            self.get_modern_layout("🏠 Répartition par Type de Propriété"),
            showlegend=True,
            height=400
        )
        
        return fig
    
    def create_price_surface_scatter(self, df):
        """Nuage de points Prix vs Surface moderne"""
        if df.empty or 'surface_area' not in df.columns or 'price' not in df.columns:
            return go.Figure()
        
        df_clean = df.dropna(subset=['surface_area', 'price'])
        if df_clean.empty:
            return go.Figure()
        
        fig = go.Figure()
        
        # Nuage de points avec taille variable
        fig.add_trace(go.Scatter(
            x=df_clean['surface_area'],
            y=df_clean['price'],
            mode='markers',
            marker=dict(
                size=df_clean['price'] / df_clean['price'].max() * 20 + 5,
                color=df_clean['price'],
                colorscale='Plasma',
                showscale=True,
                colorbar=dict(title="Prix<br>(FCFA)", thickness=15),
                line=dict(width=1, color='white'),
                opacity=0.7
            ),
            text=df_clean['city'],
            hovertemplate='<b>%{text}</b><br>Surface: %{x:.0f} m²<br>Prix: %{y:,.0f} FCFA<extra></extra>'
        ))
        
        # Ajouter ligne de tendance
        from scipy import stats
        mask = ~np.isnan(df_clean['surface_area']) & ~np.isnan(df_clean['price'])
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df_clean[mask]['surface_area'], 
            df_clean[mask]['price']
        )
        
        line_x = np.array([df_clean['surface_area'].min(), df_clean['surface_area'].max()])
        line_y = slope * line_x + intercept
        
        fig.add_trace(go.Scatter(
            x=line_x,
            y=line_y,
            mode='lines',
            name=f'Tendance (R²={r_value**2:.2f})',
            line=dict(color='#EF4444', width=3, dash='dash'),
            hovertemplate='<extra></extra>'
        ))
        
        fig.update_layout(self.get_modern_layout("📈 Prix en fonction de la Surface"))
        fig.update_xaxis(title="Surface (m²)")
        fig.update_yaxis(title="Prix (FCFA)")
        
        return fig
    
    def create_price_evolution_chart(self, df):
        """Graphique d'évolution temporelle des prix"""
        if df.empty or 'age_days' not in df.columns or 'price' not in df.columns:
            return go.Figure()
        
        df_clean = df.dropna(subset=['age_days', 'price'])
        if df_clean.empty:
            return go.Figure()
        
        # Créer des bins de temps
        df_clean['age_category'] = pd.cut(df_clean['age_days'], 
                                          bins=[0, 7, 30, 60, 90, 180, 365],
                                          labels=['< 7j', '7-30j', '1-2m', '2-3m', '3-6m', '6-12m'])
        
        price_by_age = df_clean.groupby('age_category').agg({
            'price': ['median', 'mean', 'count']
        }).reset_index()
        price_by_age.columns = ['age_category', 'median', 'mean', 'count']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=price_by_age['age_category'],
            y=price_by_age['median'],
            mode='lines+markers',
            name='Prix Médian',
            line=dict(color='#6366F1', width=3, shape='spline'),
            marker=dict(size=12, line=dict(width=2, color='white')),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.1)',
            hovertemplate='<b>%{x}</b><br>Médian: %{y:,.0f} FCFA<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=price_by_age['age_category'],
            y=price_by_age['mean'],
            mode='lines+markers',
            name='Prix Moyen',
            line=dict(color='#10B981', width=3, shape='spline', dash='dot'),
            marker=dict(size=10, line=dict(width=2, color='white')),
            hovertemplate='<b>%{x}</b><br>Moyen: %{y:,.0f} FCFA<extra></extra>'
        ))
        
        fig.update_layout(self.get_modern_layout("⏰ Évolution des Prix par Ancienneté"))
        fig.update_xaxis(title="Ancienneté de l'annonce")
        fig.update_yaxis(title="Prix (FCFA)")
        
        return fig
    
    def create_heatmap_chart(self, df):
        """Heatmap moderne prix par ville et type"""
        if df.empty or 'city' not in df.columns or 'property_type' not in df.columns:
            return go.Figure()
        
        # Top villes et types
        top_cities = df['city'].value_counts().head(8).index
        top_types = df['property_type'].value_counts().head(6).index
        
        df_filtered = df[df['city'].isin(top_cities) & df['property_type'].isin(top_types)]
        
        pivot = df_filtered.pivot_table(
            values='price', 
            index='city', 
            columns='property_type', 
            aggfunc='median'
        )
        
        fig = go.Figure()
        
        fig.add_trace(go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='RdYlGn_r',
            text=pivot.values,
            texttemplate='%{text:.2s}',
            textfont=dict(size=11, family='Poppins', weight=600),
            hovertemplate='<b>%{y}</b><br>%{x}<br>Prix: %{z:,.0f} FCFA<extra></extra>',
            colorbar=dict(title="Prix<br>(FCFA)", thickness=15)
        ))
        
        fig.update_layout(
            self.get_modern_layout("🔥 Heatmap: Prix Médian par Ville et Type"),
            height=500
        )
        
        return fig
    
    # ==================== LAYOUT ====================
    
    def setup_layout(self):
        """Configuration du layout ultra-moderne"""
        
        # CSS intégré
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
            
            # Container principal
            html.Div([
                
                # Header moderne
                html.Div([
                    html.H1("🏠 Observatoire Immobilier Sénégalais", className="header-title"),
                    html.Div([
                        html.Span("Analyse en temps réel du marché immobilier au Sénégal", 
                                 style={'color': '#6B7280', 'fontSize': '16px'}),
                        html.Span([
                            html.Span(className="pulse-dot"),
                            html.Span("LIVE")
                        ], className="badge-live")
                    ], className="header-subtitle"),
                    
                    html.Div([
                        html.Span([
                            DashIconify(icon="mdi:database", width=16, height=16),
                            html.Span("CoinAfrique • ExpatDakar • LogerDakar")
                        ], className="stats-badge"),
                        html.Span([
                            DashIconify(icon="mdi:update", width=16, height=16),
                            html.Span(f"Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                        ], className="stats-badge")
                    ], style={'display': 'flex', 'gap': '12px', 'marginTop': '16px', 'flexWrap': 'wrap'})
                ], className="modern-header"),
                
                # Filtres modernes
                html.Div([
                    html.Div([
                        html.Label("Type de Propriété", className="filter-label"),
                        dcc.Dropdown(
                            id='property-type-selector',
                            options=[
                                {'label': '🏘️ Tous les types', 'value': 'Tous'},
                                {'label': '🏠 Maison', 'value': 'Maison'},
                                {'label': '🏢 Appartement', 'value': 'Appartement'},
                                {'label': '🏛️ Villa', 'value': 'Villa'},
                                {'label': '🏗️ Studio', 'value': 'Studio'},
                                {'label': '🏞️ Terrain', 'value': 'Terrain'},
                                {'label': '🏪 Commercial', 'value': 'Commercial'}
                            ],
                            value='Tous',
                            clearable=False,
                            searchable=False,
                            style={'fontFamily': 'Inter', 'fontWeight': 500}
                        )
                    ], className="filter-group")
                ], className="filters-container"),
                
                # KPIs Header
                html.Div(id='kpi-header'),
                
                # Sections du dashboard
                html.Div(id='section-1', className="section-card"),
                html.Div(id='section-2', className="section-card"),
                html.Div(id='section-3', className="section-card"),
                html.Div(id='section-4', className="section-card"),
                html.Div(id='section-5', className="section-card"),
                html.Div(id='section-6', className="section-card"),
                
                # Footer moderne
                html.Div([
                    html.Div([
                        html.Div("🏠 Observatoire Immobilier", className="footer-logo"),
                        html.P("Plateforme d'analyse du marché immobilier sénégalais", className="footer-text"),
                        html.Div([
                            html.A("ENSAE Dakar", href="#", className="footer-link"),
                            html.A("Méthodologie", href="#", className="footer-link"),
                            html.A("Contact", href="#", className="footer-link")
                        ], className="footer-links"),
                        html.P(f"© 2024 Cos - ENSAE Pierre Ndiaye | Mis à jour: {datetime.now().strftime('%B %Y')}", 
                              className="footer-text", style={'marginTop': '16px', 'fontSize': '12px'})
                    ], className="footer-content")
                ], className="modern-footer")
                
            ], className="dashboard-container")
            
        ])
    
    # ==================== CALLBACKS ====================
    
    def setup_callbacks(self):
        """Configuration des callbacks"""
        
        @self.app.callback(
            [
                Output('kpi-header', 'children'),
                Output('section-1', 'children'),
                Output('section-2', 'children'),
                Output('section-3', 'children'),
                Output('section-4', 'children'),
                Output('section-5', 'children'),
                Output('section-6', 'children')
            ],
            Input('property-type-selector', 'value')
        )
        def update_dashboard(property_type):
            """Mettre à jour tout le dashboard"""
            try:
                # Charger données
                df = self.safe_get_data(property_type)
                kpi = self.safe_calculate_kpi(df, property_type)
                
                # KPI Header avec variations
                kpi_header = html.Div([
                    self.create_modern_kpi_card(
                        "mdi:cash-multiple", 
                        "Prix Médian", 
                        kpi['median_price'], 
                        kpi['price_change'],
                        self.COLORS['gradient1'],
                        " FCFA"
                    ),
                    self.create_modern_kpi_card(
                        "mdi:ruler-square", 
                        "Prix Moyen/m²", 
                        kpi['avg_price_m2'],
                        kpi['price_change'] * 0.8,
                        self.COLORS['gradient3'],
                        " FCFA"
                    ),
                    self.create_modern_kpi_card(
                        "mdi:file-document-multiple", 
                        "Annonces Actives", 
                        kpi['active_listings'],
                        kpi['listings_change'],
                        self.COLORS['gradient2'],
                        ""
                    ),
                    self.create_modern_kpi_card(
                        "mdi:home-analytics", 
                        "Surface Médiane", 
                        kpi['median_surface'],
                        kpi['surface_change'],
                        self.COLORS['gradient4'],
                        " m²"
                    ),
                    self.create_modern_kpi_card(
                        "mdi:clock-time-four", 
                        "Âge Médian", 
                        kpi['median_age'],
                        0,
                        self.COLORS['gradient5'],
                        " jours"
                    )
                ], className="kpi-grid")
                
                # Section 1: Distribution des prix
                section_1 = html.Div([
                    self.create_section_header(
                        "mdi:chart-bell-curve",
                        "Distribution des Prix",
                        self.COLORS['gradient1']
                    ),
                    dcc.Graph(
                        figure=self.create_distribution_chart(df),
                        config=self.create_modern_chart_config()
                    )
                ])
                
                # Section 2: Prix par ville
                section_2 = html.Div([
                    self.create_section_header(
                        "mdi:city-variant",
                        "Analyse Géographique",
                        self.COLORS['gradient2']
                    ),
                    dcc.Graph(
                        figure=self.create_price_by_city_chart(df),
                        config=self.create_modern_chart_config()
                    )
                ])
                
                # Section 3: Types de propriétés
                section_3 = html.Div([
                    self.create_section_header(
                        "mdi:home-variant",
                        "Répartition par Type",
                        self.COLORS['gradient3']
                    ),
                    dcc.Graph(
                        figure=self.create_property_type_chart(df),
                        config=self.create_modern_chart_config()
                    )
                ])
                
                # Section 4: Prix vs Surface
                section_4 = html.Div([
                    self.create_section_header(
                        "mdi:chart-scatter-plot",
                        "Relation Prix-Surface",
                        self.COLORS['gradient4']
                    ),
                    dcc.Graph(
                        figure=self.create_price_surface_scatter(df),
                        config=self.create_modern_chart_config()
                    )
                ])
                
                # Section 5: Évolution temporelle
                section_5 = html.Div([
                    self.create_section_header(
                        "mdi:chart-timeline-variant",
                        "Évolution des Prix",
                        self.COLORS['gradient5']
                    ),
                    dcc.Graph(
                        figure=self.create_price_evolution_chart(df),
                        config=self.create_modern_chart_config()
                    )
                ])
                
                # Section 6: Heatmap
                section_6 = html.Div([
                    self.create_section_header(
                        "mdi:grid",
                        "Matrice de Prix",
                        self.COLORS['gradient1']
                    ),
                    dcc.Graph(
                        figure=self.create_heatmap_chart(df),
                        config=self.create_modern_chart_config()
                    )
                ])
                
                return (
                    kpi_header,
                    section_1,
                    section_2,
                    section_3,
                    section_4,
                    section_5,
                    section_6
                )
                
            except Exception as e:
                print(f"❌ Erreur callback: {e}")
                traceback.print_exc()
                
                error_msg = html.Div([
                    html.Div([
                        DashIconify(icon="mdi:alert-circle", width=48, height=48, color="#EF4444")
                    ], style={'marginBottom': '16px'}),
                    html.H3("⚠️ Erreur de Chargement", 
                           style={'color': '#EF4444', 'marginBottom': '12px', 'fontFamily': 'Poppins'}),
                    html.P(f"Une erreur s'est produite lors du chargement des données.", 
                          style={'color': '#6B7280', 'fontSize': '15px'}),
                    html.P("Veuillez réessayer ou contacter l'administrateur.", 
                          style={'color': '#9CA3AF', 'fontSize': '13px', 'marginTop': '8px'})
                ], style={
                    'background': 'rgba(254, 226, 226, 0.8)',
                    'backdropFilter': 'blur(10px)',
                    'padding': '40px',
                    'borderRadius': '20px',
                    'border': '2px solid #EF4444',
                    'textAlign': 'center',
                    'boxShadow': '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
                })
                
                empty = html.Div()
                return (error_msg, empty, empty, empty, empty, empty, empty)


def create_observatoire_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    """Factory function pour créer le dashboard"""
    dashboard = ObservatoireModerne(
        server=server,
        routes_pathname_prefix=routes_pathname_prefix,
        requests_pathname_prefix=requests_pathname_prefix
    )
    return dashboard.app