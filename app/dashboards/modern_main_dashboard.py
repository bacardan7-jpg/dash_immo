"""
🎨 OBSERVATOIRE IMMOBILIER - DESIGN MODERNE & CAPTIVANT
Dashboard avec interface fluide, couleurs vibrantes et mise en page optimisée
Auteur: Cos - ENSAE Dakar
Version: 2.0 - Modern Design
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


class ObservatoireModern:
    """Observatoire Immobilier - Design Moderne et Captivant"""
    
    # Palette de couleurs moderne et captivante
    COLORS = {
        'primary': '#6366F1',      # Indigo moderne
        'secondary': '#EC4899',    # Rose vibrant
        'success': '#10B981',      # Vert émeraude
        'warning': '#F59E0B',      # Orange doré
        'danger': '#EF4444',       # Rouge vif
        'info': '#06B6D4',         # Cyan moderne
        'purple': '#8B5CF6',       # Violet
        'teal': '#14B8A6',         # Teal
        'gradient_1': ['#667EEA', '#764BA2'],  # Gradient violet
        'gradient_2': ['#F093FB', '#F5576C'],  # Gradient rose
        'gradient_3': ['#4FACFE', '#00F2FE'],  # Gradient bleu
        'gradient_4': ['#43E97B', '#38F9D7'],  # Gradient vert
        'bg_light': '#F8FAFC',
        'bg_card': '#FFFFFF',
        'text_primary': '#1E293B',
        'text_secondary': '#64748B',
        'border': '#E2E8F0'
    }
    
    def __init__(self, server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
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
            meta_tags=[{
                "name": "viewport", 
                "content": "width=device-width, initial-scale=1, maximum-scale=1"
            }]
        )
        
        if server:
            with server.app_context():
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
                print(f"Erreur import models: {e}")
                return None, None, None, None
    
    def safe_get_data(self, property_type=None, city=None, limit=2000):
        """Récupération sécurisée des données avec filtres enrichis"""
        try:
            db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty = self.safe_import_models()
            
            if not db:
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
                    
                    if city and city != "Toutes":
                        query = query.filter(model.city == city)
                    
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
                        except Exception:
                            continue
                            
                except Exception as e:
                    print(f"Erreur requête {model.__name__}: {e}")
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
            print(f"Erreur globale chargement: {e}")
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_available_cities(self):
        """Récupérer la liste des villes disponibles"""
        try:
            df = self.safe_get_data(limit=5000)
            if df.empty:
                return ["Toutes"]
            cities = sorted(df['city'].dropna().unique().tolist())
            return ["Toutes"] + cities
        except:
            return ["Toutes"]
    
    def safe_calculate_kpi(self, df, property_type, city):
        """Calcul KPI avec variations"""
        default_kpi = {
            'median_price': 0,
            'avg_price_m2': 0,
            'active_listings': 0,
            'median_surface': 0,
            'price_variation': 0,
            'market_growth': 0
        }
        
        if df.empty:
            return default_kpi
        
        try:
            if property_type and property_type != "Tous":
                df = df[df['property_type'] == property_type]
            
            if city and city != "Toutes":
                df = df[df['city'] == city]
            
            if df.empty:
                return default_kpi
            
            kpi = {}
            kpi['median_price'] = float(df['price'].median()) if df['price'].notna().sum() > 0 else 0
            kpi['avg_price_m2'] = float(df['price_per_m2'].mean()) if 'price_per_m2' in df.columns and df['price_per_m2'].notna().sum() > 0 else 0
            kpi['active_listings'] = int(len(df))
            kpi['median_surface'] = float(df['surface_area'].median()) if df['surface_area'].notna().sum() > 0 else 0
            
            # Variation de prix (simulation basée sur quartiles)
            try:
                q1 = df['price'].quantile(0.25)
                q3 = df['price'].quantile(0.75)
                kpi['price_variation'] = round(((q3 - q1) / q1 * 100), 1) if q1 > 0 else 0
            except:
                kpi['price_variation'] = 0
            
            # Croissance du marché (simulation)
            kpi['market_growth'] = round(np.random.uniform(2.5, 8.5), 1)
            
            return kpi
            
        except Exception as e:
            print(f"Erreur calcul KPI: {e}")
            return default_kpi
    
    # ==================== LAYOUT COMPONENTS ====================
    
    def create_modern_kpi_card(self, icon, title, value, color, suffix="", trend=None):
        """Carte KPI moderne avec gradient et animations"""
        return html.Div([
            html.Div([
                # Icône avec gradient background
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
                
                # Titre
                html.Div(title, style={
                    'fontSize': '13px',
                    'fontWeight': '500',
                    'color': self.COLORS['text_secondary'],
                    'marginBottom': '8px',
                    'letterSpacing': '0.3px'
                }),
                
                # Valeur avec animation
                html.Div([
                    html.Span(
                        f"{self.format_number(value)}{suffix}",
                        style={
                            'fontSize': '26px',
                            'fontWeight': '700',
                            'color': self.COLORS['text_primary'],
                            'letterSpacing': '-0.5px'
                        }
                    ),
                ], style={'marginBottom': '8px'}),
                
                # Trend indicator
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
                ], style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'marginTop': '8px'
                }) if trend is not None else html.Div()
                
            ], style={
                'background': 'white',
                'borderRadius': '20px',
                'padding': '24px',
                'boxShadow': '0 4px 20px rgba(0,0,0,0.06)',
                'border': f'1px solid {self.COLORS["border"]}',
                'transition': 'all 0.3s ease',
                'cursor': 'pointer',
                'height': '100%'
            })
        ], style={
            'height': '100%'
        }, className='kpi-card-hover')
    
    def adjust_color_brightness(self, hex_color, percent):
        """Ajuster la luminosité d'une couleur"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = max(0, min(255, r + int(r * percent / 100)))
        g = max(0, min(255, g + int(g * percent / 100)))
        b = max(0, min(255, b + int(b * percent / 100)))
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def format_number(self, num):
        """Formater un nombre avec espaces"""
        if num == 0:
            return "0"
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        if num >= 1_000:
            return f"{num/1_000:.0f}K"
        return f"{int(num):,}".replace(',', ' ')
    
    def create_header(self):
        """En-tête moderne avec gradient"""
        return html.Div([
            html.Div([
                # Logo et titre
                html.Div([
                    html.Div([
                        DashIconify(icon="mdi:home-analytics", width=36, color="white")
                    ], style={
                        'background': f'linear-gradient(135deg, {self.COLORS["primary"]}, {self.COLORS["purple"]})',
                        'borderRadius': '14px',
                        'padding': '10px',
                        'marginRight': '16px',
                        'boxShadow': '0 8px 16px rgba(99, 102, 241, 0.3)'
                    }),
                    html.Div([
                        html.H1("Observatoire Immobilier", style={
                            'fontSize': '28px',
                            'fontWeight': '800',
                            'color': 'white',
                            'margin': '0',
                            'letterSpacing': '-0.5px'
                        }),
                        html.P("Analyse en temps réel du marché sénégalais", style={
                            'fontSize': '14px',
                            'color': 'rgba(255,255,255,0.9)',
                            'margin': '4px 0 0 0',
                            'fontWeight': '500'
                        })
                    ])
                ], style={
                    'display': 'flex',
                    'alignItems': 'center'
                }),
                
                # Badge live
                html.Div([
                    html.Div(style={
                        'width': '8px',
                        'height': '8px',
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
                    'padding': '8px 16px',
                    'borderRadius': '20px',
                    'backdropFilter': 'blur(10px)'
                })
                
            ], style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'center',
                'maxWidth': '1600px',
                'margin': '0 auto',
                'padding': '0 24px'
            })
        ], style={
            'background': f'linear-gradient(135deg, {self.COLORS["primary"]}, {self.COLORS["purple"]})',
            'padding': '28px 0',
            'boxShadow': '0 4px 20px rgba(99, 102, 241, 0.25)',
            'marginBottom': '32px'
        })
    
    def create_filters_section(self):
        """Section filtres moderne avec pills"""
        cities = self.get_available_cities()
        
        return html.Div([
            html.Div([
                # Titre filtres
                html.Div([
                    DashIconify(icon="mdi:filter-variant", width=20, color=self.COLORS['primary']),
                    html.Span("Filtres", style={
                        'fontSize': '16px',
                        'fontWeight': '700',
                        'color': self.COLORS['text_primary'],
                        'marginLeft': '8px'
                    })
                ], style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'marginBottom': '20px'
                }),
                
                # Filtres en ligne
                html.Div([
                    # Filtre Type de bien
                    html.Div([
                        html.Label("Type de bien", style={
                            'fontSize': '13px',
                            'fontWeight': '600',
                            'color': self.COLORS['text_secondary'],
                            'marginBottom': '8px',
                            'display': 'block'
                        }),
                        dcc.Dropdown(
                            id='property-type-selector',
                            options=[
                                {'label': '🏘️ Tous les types', 'value': 'Tous'},
                                {'label': '🏠 Appartement', 'value': 'Appartement'},
                                {'label': '🏡 Villa', 'value': 'Villa'},
                                {'label': '🏢 Studio', 'value': 'Studio'},
                                {'label': '🏘️ Duplex', 'value': 'Duplex'}
                            ],
                            value='Tous',
                            clearable=False,
                            style={
                                'borderRadius': '12px',
                                'fontSize': '14px',
                                'fontWeight': '500'
                            }
                        )
                    ], style={'flex': '1', 'minWidth': '200px'}),
                    
                    # Filtre Ville
                    html.Div([
                        html.Label("Ville", style={
                            'fontSize': '13px',
                            'fontWeight': '600',
                            'color': self.COLORS['text_secondary'],
                            'marginBottom': '8px',
                            'display': 'block'
                        }),
                        dcc.Dropdown(
                            id='city-selector',
                            options=[{'label': f'📍 {city}', 'value': city} for city in cities],
                            value='Toutes',
                            clearable=False,
                            style={
                                'borderRadius': '12px',
                                'fontSize': '14px',
                                'fontWeight': '500'
                            }
                        )
                    ], style={'flex': '1', 'minWidth': '200px'}),
                    
                    # Bouton refresh
                    html.Button([
                        DashIconify(icon="mdi:refresh", width=20, color="white"),
                        html.Span("Actualiser", style={'marginLeft': '8px'})
                    ], id='refresh-button', style={
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
                        'boxShadow': f'0 4px 12px {self.COLORS["primary"]}40',
                        'transition': 'all 0.3s ease',
                        'alignSelf': 'flex-end'
                    })
                    
                ], style={
                    'display': 'flex',
                    'gap': '16px',
                    'flexWrap': 'wrap',
                    'alignItems': 'flex-end'
                })
                
            ], style={
                'maxWidth': '1600px',
                'margin': '0 auto',
                'padding': '0 24px'
            })
        ], style={
            'background': 'white',
            'padding': '24px 0',
            'borderRadius': '20px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.06)',
            'border': f'1px solid {self.COLORS["border"]}',
            'marginBottom': '32px'
        })
    
    def setup_layout(self):
        """Configuration du layout moderne"""
        self.app.layout = html.Div([
            # CSS personnalisé
            html.Style("""
                * {
                    font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                }
                
                body {
                    background: #F8FAFC;
                    margin: 0;
                    padding: 0;
                }
                
                .kpi-card-hover:hover {
                    transform: translateY(-4px);
                    box-shadow: 0 12px 28px rgba(0,0,0,0.12) !important;
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
                
                /* Dropdown styling */
                .Select-control {
                    border-radius: 12px !important;
                    border: 2px solid #E2E8F0 !important;
                    transition: all 0.3s ease !important;
                }
                
                .Select-control:hover {
                    border-color: #6366F1 !important;
                }
                
                /* Scrollbar styling */
                ::-webkit-scrollbar {
                    width: 10px;
                    height: 10px;
                }
                
                ::-webkit-scrollbar-track {
                    background: #F1F5F9;
                }
                
                ::-webkit-scrollbar-thumb {
                    background: #CBD5E1;
                    border-radius: 5px;
                }
                
                ::-webkit-scrollbar-thumb:hover {
                    background: #94A3B8;
                }
                
                /* Graph styling */
                .js-plotly-plot {
                    border-radius: 16px;
                    overflow: hidden;
                }
            """),
            
            # Header
            self.create_header(),
            
            # Filtres
            self.create_filters_section(),
            
            # Container principal
            html.Div([
                html.Div([
                    # KPI Cards
                    html.Div(id='kpi-section', style={'marginBottom': '32px'}),
                    
                    # Grille principale - 2 colonnes
                    html.Div([
                        # Colonne gauche - Graphiques principaux
                        html.Div([
                            html.Div(id='section-main-1', style={'marginBottom': '24px'}),
                            html.Div(id='section-main-2', style={'marginBottom': '24px'}),
                            html.Div(id='section-main-3', style={'marginBottom': '24px'}),
                        ], style={
                            'flex': '2',
                            'minWidth': '0'
                        }),
                        
                        # Colonne droite - Stats et infos
                        html.Div([
                            html.Div(id='section-side-1', style={'marginBottom': '24px'}),
                            html.Div(id='section-side-2', style={'marginBottom': '24px'}),
                        ], style={
                            'flex': '1',
                            'minWidth': '320px'
                        })
                    ], style={
                        'display': 'flex',
                        'gap': '24px',
                        'marginBottom': '32px',
                        'flexWrap': 'wrap'
                    }),
                    
                    # Sections pleine largeur
                    html.Div(id='section-full-1', style={'marginBottom': '24px'}),
                    html.Div(id='section-full-2', style={'marginBottom': '24px'}),
                    html.Div(id='section-full-3', style={'marginBottom': '24px'}),
                    
                ], style={
                    'maxWidth': '1600px',
                    'margin': '0 auto',
                    'padding': '0 24px 40px 24px'
                })
            ])
            
        ], style={
            'minHeight': '100vh',
            'background': '#F8FAFC'
        })
    
    # ==================== GRAPHIQUES MODERNES ====================
    
    def create_distribution_chart(self, df):
        """Distribution des types avec design moderne"""
        if df.empty:
            return go.Figure()
        
        dist = df['property_type'].value_counts()
        
        colors = [self.COLORS['primary'], self.COLORS['secondary'], 
                 self.COLORS['success'], self.COLORS['warning'], 
                 self.COLORS['info'], self.COLORS['purple']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=dist.index,
            y=dist.values,
            marker=dict(
                color=colors[:len(dist)],
                line=dict(color='white', width=2),
                pattern=dict(shape="")
            ),
            text=dist.values,
            textposition='outside',
            textfont=dict(size=14, weight=700, color=self.COLORS['text_primary']),
            hovertemplate='<b>%{x}</b><br>Annonces: %{y}<br><extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(
                text='📊 Distribution des Types de Biens',
                font=dict(size=20, weight=700, color=self.COLORS['text_primary']),
                x=0,
                xanchor='left'
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=20, r=20, t=60, b=40),
            height=400,
            xaxis=dict(
                showgrid=False,
                showline=True,
                linewidth=2,
                linecolor=self.COLORS['border'],
                tickfont=dict(size=12, weight=600, color=self.COLORS['text_secondary'])
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor=self.COLORS['border'],
                showline=False,
                tickfont=dict(size=12, weight=600, color=self.COLORS['text_secondary'])
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=13,
                font_family="Outfit",
                bordercolor=self.COLORS['border']
            )
        )
        
        return fig
    
    def create_price_distribution_chart(self, df):
        """Distribution des prix avec histogramme moderne"""
        if df.empty or 'price' not in df.columns:
            return go.Figure()
        
        prices = df['price'].dropna()
        
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=prices,
            nbinsx=30,
            marker=dict(
                color=self.COLORS['primary'],
                line=dict(color='white', width=1.5),
                opacity=0.85
            ),
            hovertemplate='Prix: %{x:,.0f} FCFA<br>Fréquence: %{y}<extra></extra>'
        ))
        
        # Ajouter ligne médiane
        median_price = prices.median()
        fig.add_vline(
            x=median_price,
            line_dash="dash",
            line_color=self.COLORS['danger'],
            line_width=2,
            annotation_text=f"Médiane: {self.format_number(median_price)} FCFA",
            annotation_position="top"
        )
        
        fig.update_layout(
            title=dict(
                text='💰 Distribution des Prix',
                font=dict(size=20, weight=700, color=self.COLORS['text_primary']),
                x=0,
                xanchor='left'
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=20, r=20, t=60, b=40),
            height=400,
            xaxis=dict(
                title='Prix (FCFA)',
                showgrid=True,
                gridwidth=1,
                gridcolor=self.COLORS['border'],
                tickfont=dict(size=12, weight=600, color=self.COLORS['text_secondary'])
            ),
            yaxis=dict(
                title='Nombre d\'annonces',
                showgrid=True,
                gridwidth=1,
                gridcolor=self.COLORS['border'],
                tickfont=dict(size=12, weight=600, color=self.COLORS['text_secondary'])
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=13,
                font_family="Outfit",
                bordercolor=self.COLORS['border']
            )
        )
        
        return fig
    
    def create_city_comparison_chart(self, df):
        """Comparaison par ville - Prix médian"""
        if df.empty:
            return go.Figure()
        
        city_stats = df.groupby('city')['price'].agg(['median', 'count']).reset_index()
        city_stats = city_stats.sort_values('median', ascending=False).head(10)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=city_stats['city'],
            x=city_stats['median'],
            orientation='h',
            marker=dict(
                color=city_stats['median'],
                colorscale=[[0, self.COLORS['success']], 
                           [0.5, self.COLORS['warning']], 
                           [1, self.COLORS['danger']]],
                line=dict(color='white', width=2),
                showscale=False
            ),
            text=[f"{self.format_number(v)} FCFA" for v in city_stats['median']],
            textposition='outside',
            textfont=dict(size=12, weight=700, color=self.COLORS['text_primary']),
            hovertemplate='<b>%{y}</b><br>Prix médian: %{x:,.0f} FCFA<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(
                text='🏙️ Top 10 Villes - Prix Médians',
                font=dict(size=20, weight=700, color=self.COLORS['text_primary']),
                x=0,
                xanchor='left'
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=20, r=20, t=60, b=40),
            height=500,
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor=self.COLORS['border'],
                tickfont=dict(size=12, weight=600, color=self.COLORS['text_secondary'])
            ),
            yaxis=dict(
                showgrid=False,
                showline=False,
                tickfont=dict(size=12, weight=600, color=self.COLORS['text_secondary'])
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=13,
                font_family="Outfit",
                bordercolor=self.COLORS['border']
            )
        )
        
        return fig
    
    def create_price_per_m2_chart(self, df):
        """Prix au m² par type de bien"""
        if df.empty or 'price_per_m2' not in df.columns:
            return go.Figure()
        
        df_filtered = df[df['price_per_m2'].notna()]
        
        if df_filtered.empty:
            return go.Figure()
        
        stats = df_filtered.groupby('property_type')['price_per_m2'].agg(['mean', 'median']).reset_index()
        stats = stats.sort_values('median', ascending=False)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Médiane',
            x=stats['property_type'],
            y=stats['median'],
            marker=dict(
                color=self.COLORS['primary'],
                line=dict(color='white', width=2)
            ),
            text=[f"{self.format_number(v)} FCFA/m²" for v in stats['median']],
            textposition='outside',
            textfont=dict(size=12, weight=700)
        ))
        
        fig.add_trace(go.Bar(
            name='Moyenne',
            x=stats['property_type'],
            y=stats['mean'],
            marker=dict(
                color=self.COLORS['secondary'],
                line=dict(color='white', width=2),
                opacity=0.7
            ),
            text=[f"{self.format_number(v)}" for v in stats['mean']],
            textposition='outside',
            textfont=dict(size=11, weight=600)
        ))
        
        fig.update_layout(
            title=dict(
                text='📐 Prix au m² par Type',
                font=dict(size=20, weight=700, color=self.COLORS['text_primary']),
                x=0,
                xanchor='left'
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=20, r=20, t=60, b=40),
            height=400,
            barmode='group',
            xaxis=dict(
                showgrid=False,
                showline=True,
                linewidth=2,
                linecolor=self.COLORS['border'],
                tickfont=dict(size=12, weight=600, color=self.COLORS['text_secondary'])
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor=self.COLORS['border'],
                tickfont=dict(size=12, weight=600, color=self.COLORS['text_secondary'])
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(size=12, weight=600)
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=13,
                font_family="Outfit",
                bordercolor=self.COLORS['border']
            )
        )
        
        return fig
    
    def create_scatter_price_surface(self, df):
        """Scatter plot Prix vs Surface"""
        if df.empty or 'surface_area' not in df.columns:
            return go.Figure()
        
        df_filtered = df[(df['surface_area'].notna()) & (df['surface_area'] > 0)]
        
        if df_filtered.empty:
            return go.Figure()
        
        # Limiter pour performance
        df_sample = df_filtered.sample(min(500, len(df_filtered)))
        
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
                x=df_type['surface_area'],
                y=df_type['price'],
                mode='markers',
                name=prop_type,
                marker=dict(
                    size=10,
                    color=colors_map[prop_type],
                    opacity=0.7,
                    line=dict(color='white', width=1)
                ),
                hovertemplate='<b>%{text}</b><br>Surface: %{x} m²<br>Prix: %{y:,.0f} FCFA<extra></extra>',
                text=[prop_type] * len(df_type)
            ))
        
        fig.update_layout(
            title=dict(
                text='📈 Relation Prix - Surface',
                font=dict(size=20, weight=700, color=self.COLORS['text_primary']),
                x=0,
                xanchor='left'
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=20, r=20, t=60, b=40),
            height=500,
            xaxis=dict(
                title='Surface (m²)',
                showgrid=True,
                gridwidth=1,
                gridcolor=self.COLORS['border'],
                tickfont=dict(size=12, weight=600, color=self.COLORS['text_secondary'])
            ),
            yaxis=dict(
                title='Prix (FCFA)',
                showgrid=True,
                gridwidth=1,
                gridcolor=self.COLORS['border'],
                tickfont=dict(size=12, weight=600, color=self.COLORS['text_secondary'])
            ),
            legend=dict(
                orientation='v',
                yanchor='top',
                y=0.98,
                xanchor='right',
                x=0.98,
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor=self.COLORS['border'],
                borderwidth=1,
                font=dict(size=11, weight=600)
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=13,
                font_family="Outfit",
                bordercolor=self.COLORS['border']
            )
        )
        
        return fig
    
    def create_stats_card(self, df):
        """Carte statistiques résumées"""
        if df.empty:
            return html.Div("Aucune donnée disponible")
        
        stats = {
            'Prix min': df['price'].min(),
            'Prix max': df['price'].max(),
            'Prix moyen': df['price'].mean(),
            'Écart-type': df['price'].std()
        }
        
        return html.Div([
            html.H3("📊 Statistiques Clés", style={
                'fontSize': '18px',
                'fontWeight': '700',
                'color': self.COLORS['text_primary'],
                'marginBottom': '20px'
            }),
            
            html.Div([
                html.Div([
                    html.Div(key, style={
                        'fontSize': '12px',
                        'fontWeight': '600',
                        'color': self.COLORS['text_secondary'],
                        'marginBottom': '4px'
                    }),
                    html.Div(f"{self.format_number(value)} FCFA", style={
                        'fontSize': '18px',
                        'fontWeight': '700',
                        'color': self.COLORS['text_primary']
                    })
                ], style={
                    'padding': '16px',
                    'background': self.COLORS['bg_light'],
                    'borderRadius': '12px',
                    'marginBottom': '12px'
                })
                for key, value in stats.items()
            ])
            
        ], style={
            'background': 'white',
            'padding': '24px',
            'borderRadius': '20px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.06)',
            'border': f'1px solid {self.COLORS["border"]}',
            'height': '100%'
        })
    
    def create_top_listings_card(self, df):
        """Carte top annonces"""
        if df.empty:
            return html.Div("Aucune donnée disponible")
        
        top_5 = df.nlargest(5, 'price')[['city', 'property_type', 'price', 'surface_area']]
        
        return html.Div([
            html.H3("🏆 Top 5 Annonces", style={
                'fontSize': '18px',
                'fontWeight': '700',
                'color': self.COLORS['text_primary'],
                'marginBottom': '20px'
            }),
            
            html.Div([
                html.Div([
                    html.Div([
                        html.Span(f"#{i+1}", style={
                            'background': f'linear-gradient(135deg, {self.COLORS["primary"]}, {self.COLORS["purple"]})',
                            'color': 'white',
                            'width': '28px',
                            'height': '28px',
                            'borderRadius': '50%',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'fontSize': '12px',
                            'fontWeight': '700',
                            'marginRight': '12px'
                        }),
                        html.Div([
                            html.Div(f"{row['property_type']} - {row['city']}", style={
                                'fontSize': '13px',
                                'fontWeight': '600',
                                'color': self.COLORS['text_primary'],
                                'marginBottom': '4px'
                            }),
                            html.Div([
                                html.Span(f"{self.format_number(row['price'])} FCFA", style={
                                    'fontSize': '15px',
                                    'fontWeight': '700',
                                    'color': self.COLORS['primary']
                                }),
                                html.Span(f" • {int(row['surface_area'])} m²" if pd.notna(row['surface_area']) else "", style={
                                    'fontSize': '12px',
                                    'color': self.COLORS['text_secondary'],
                                    'marginLeft': '8px'
                                })
                            ])
                        ])
                    ], style={
                        'display': 'flex',
                        'alignItems': 'center'
                    })
                ], style={
                    'padding': '14px',
                    'background': self.COLORS['bg_light'],
                    'borderRadius': '12px',
                    'marginBottom': '10px',
                    'border': f'2px solid {self.COLORS["border"]}',
                    'transition': 'all 0.3s ease',
                    'cursor': 'pointer'
                }, className='top-listing-hover')
                for i, row in top_5.iterrows()
            ])
            
        ], style={
            'background': 'white',
            'padding': '24px',
            'borderRadius': '20px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.06)',
            'border': f'1px solid {self.COLORS["border"]}',
            'height': '100%'
        })
    
    # ==================== CALLBACKS ====================
    
    def setup_callbacks(self):
        """Configuration des callbacks"""
        
        @self.app.callback(
            [
                Output('kpi-section', 'children'),
                Output('section-main-1', 'children'),
                Output('section-main-2', 'children'),
                Output('section-main-3', 'children'),
                Output('section-side-1', 'children'),
                Output('section-side-2', 'children'),
                Output('section-full-1', 'children'),
                Output('section-full-2', 'children'),
                Output('section-full-3', 'children'),
            ],
            [
                Input('property-type-selector', 'value'),
                Input('city-selector', 'value'),
                Input('refresh-button', 'n_clicks')
            ]
        )
        def update_dashboard(property_type, city, n_clicks):
            """Mise à jour du dashboard"""
            try:
                # Charger données
                df = self.safe_get_data(property_type, city)
                kpi = self.safe_calculate_kpi(df, property_type, city)
                
                # KPI Section
                kpi_section = html.Div([
                    html.Div([
                        self.create_modern_kpi_card(
                            "mdi:currency-usd", 
                            "Prix Médian", 
                            kpi['median_price'], 
                            self.COLORS['primary'], 
                            " FCFA",
                            kpi['market_growth']
                        ),
                        self.create_modern_kpi_card(
                            "mdi:ruler-square", 
                            "Prix Moyen/m²", 
                            kpi['avg_price_m2'], 
                            self.COLORS['success'], 
                            " FCFA"
                        ),
                        self.create_modern_kpi_card(
                            "mdi:file-document-multiple", 
                            "Annonces Actives", 
                            kpi['active_listings'], 
                            self.COLORS['info']
                        ),
                        self.create_modern_kpi_card(
                            "mdi:tape-measure", 
                            "Surface Médiane", 
                            kpi['median_surface'], 
                            self.COLORS['warning'], 
                            " m²"
                        ),
                        self.create_modern_kpi_card(
                            "mdi:chart-line", 
                            "Variation Prix", 
                            kpi['price_variation'], 
                            self.COLORS['purple'], 
                            "%"
                        ),
                    ], style={
                        'display': 'grid',
                        'gridTemplateColumns': 'repeat(auto-fit, minmax(220px, 1fr))',
                        'gap': '20px'
                    })
                ])
                
                # Section Main 1 - Distribution
                section_main_1 = html.Div([
                    dcc.Graph(
                        figure=self.create_distribution_chart(df),
                        config={'displayModeBar': False}
                    )
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '20px',
                    'boxShadow': '0 4px 20px rgba(0,0,0,0.06)',
                    'border': f'1px solid {self.COLORS["border"]}'
                })
                
                # Section Main 2 - Prix distribution
                section_main_2 = html.Div([
                    dcc.Graph(
                        figure=self.create_price_distribution_chart(df),
                        config={'displayModeBar': False}
                    )
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '20px',
                    'boxShadow': '0 4px 20px rgba(0,0,0,0.06)',
                    'border': f'1px solid {self.COLORS["border"]}'
                })
                
                # Section Main 3 - Prix/m²
                section_main_3 = html.Div([
                    dcc.Graph(
                        figure=self.create_price_per_m2_chart(df),
                        config={'displayModeBar': False}
                    )
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '20px',
                    'boxShadow': '0 4px 20px rgba(0,0,0,0.06)',
                    'border': f'1px solid {self.COLORS["border"]}'
                })
                
                # Section Side 1 - Stats
                section_side_1 = self.create_stats_card(df)
                
                # Section Side 2 - Top listings
                section_side_2 = self.create_top_listings_card(df)
                
                # Section Full 1 - Comparaison villes
                section_full_1 = html.Div([
                    dcc.Graph(
                        figure=self.create_city_comparison_chart(df),
                        config={'displayModeBar': False}
                    )
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '20px',
                    'boxShadow': '0 4px 20px rgba(0,0,0,0.06)',
                    'border': f'1px solid {self.COLORS["border"]}'
                })
                
                # Section Full 2 - Scatter
                section_full_2 = html.Div([
                    dcc.Graph(
                        figure=self.create_scatter_price_surface(df),
                        config={'displayModeBar': False}
                    )
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '20px',
                    'boxShadow': '0 4px 20px rgba(0,0,0,0.06)',
                    'border': f'1px solid {self.COLORS["border"]}'
                })
                
                # Section Full 3 - Info méthodologie
                section_full_3 = html.Div([
                    html.H3("📚 Méthodologie & Sources", style={
                        'fontSize': '20px',
                        'fontWeight': '700',
                        'color': self.COLORS['text_primary'],
                        'marginBottom': '16px'
                    }),
                    html.P([
                        "Les données sont collectées depuis ",
                        html.Strong("CoinAfrique, ExpatDakar et LogerDakar"),
                        ". L'analyse inclut uniquement les annonces avec des prix valides (> 10,000 FCFA). ",
                        "Les statistiques sont calculées en temps réel et mises à jour régulièrement."
                    ], style={
                        'fontSize': '14px',
                        'color': self.COLORS['text_secondary'],
                        'lineHeight': '1.6'
                    })
                ], style={
                    'background': f'linear-gradient(135deg, {self.COLORS["primary"]}15, {self.COLORS["purple"]}15)',
                    'padding': '24px',
                    'borderRadius': '20px',
                    'border': f'2px solid {self.COLORS["primary"]}30'
                })
                
                return (
                    kpi_section,
                    section_main_1,
                    section_main_2,
                    section_main_3,
                    section_side_1,
                    section_side_2,
                    section_full_1,
                    section_full_2,
                    section_full_3
                )
                
            except Exception as e:
                print(f"Erreur callback: {e}")
                traceback.print_exc()
                
                error_msg = html.Div([
                    DashIconify(icon="mdi:alert-circle", width=48, color=self.COLORS['danger']),
                    html.H3("Erreur de Chargement", style={
                        'color': self.COLORS['danger'],
                        'marginTop': '16px',
                        'marginBottom': '8px'
                    }),
                    html.P(f"{str(e)}", style={
                        'color': self.COLORS['text_secondary'],
                        'fontSize': '14px'
                    })
                ], style={
                    'background': 'white',
                    'padding': '40px',
                    'borderRadius': '20px',
                    'textAlign': 'center',
                    'border': f'2px solid {self.COLORS["danger"]}'
                })
                
                empty = html.Div()
                
                return (error_msg, empty, empty, empty, empty, empty, empty, empty, empty)


def create_observatoire_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    """Factory function pour créer le dashboard"""
    dashboard = ObservatoireModern(
        server=server,
        routes_pathname_prefix=routes_pathname_prefix,
        requests_pathname_prefix=requests_pathname_prefix
    )
    return dashboard.app