"""
👁️ VIEWER DASHBOARD - INTERFACE UTILISATEUR FINALE
Dashboard avec chatbot IA, recherche intelligente et recommandations personnalisées
Auteur: Cos - ENSAE Dakar
Version: 1.0 - Viewer Experience
"""

import dash
from dash import html, dcc, Input, Output, State, ALL, callback_context
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd
import numpy as np
import json
import base64
from sqlalchemy import func, and_, or_

# Import du détecteur de statut
try:
    from .status_detector import detect_listing_status
except ImportError:
    try:
        from status_detector import detect_listing_status
    except ImportError:
        def detect_listing_status(title=None, price=None, property_type=None, source=None, native_status=None):
            if price and price < 1_500_000:
                return 'Location'
            return 'Vente'


class ViewerDashboard:
    """Dashboard interactif pour les utilisateurs viewers"""
    
    COLORS = {
        'primary': '#1E40AF',
        'secondary': '#EC4899',
        'success': '#10B981',
        'warning': '#F59E0B',
        'danger': '#EF4444',
        'info': '#06B6D4',
        'purple': '#8B5CF6',
        'teal': '#14B8A6',
        'bg_main': '#F8FAFC',
        'bg_card': '#FFFFFF',
        'text_primary': '#1E293B',
        'text_secondary': '#64748B',
        'border': '#E2E8F0'
    }
    
    def __init__(self, server=None, routes_pathname_prefix="/viewer/", requests_pathname_prefix="/viewer/"):
        
        # CSS personnalisé
        self.custom_css = """
        * { font-family: 'Inter', sans-serif; }
        body { background: #F8FAFC; margin: 0; padding: 0; }
        
        .property-card { 
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .property-card:hover { 
            transform: translateY(-4px);
            box-shadow: 0 12px 28px rgba(0,0,0,0.15) !important;
        }
        
        .chat-message {
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .filter-chip {
            transition: all 0.2s ease;
        }
        .filter-chip:hover {
            transform: scale(1.05);
        }
        
        .favorite-heart {
            transition: all 0.2s ease;
        }
        .favorite-heart:hover {
            transform: scale(1.2);
        }
        """
        
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[
                'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
            ],
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix,
            suppress_callback_exceptions=True,
            meta_tags=[{
                "name": "viewport",
                "content": "width=device-width, initial-scale=1"
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
                print(f"Erreur import models: {e}")
                return None, None, None, None
    
    def search_properties(self, filters):
        """
        Recherche intelligente de propriétés avec filtres avancés
        
        Args:
            filters: dict avec budget, status, type, ville, chambres, etc.
        """
        try:
            db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty = self.safe_import_models()
            
            if not db:
                return pd.DataFrame()
            
            all_properties = []
            
            # Budget
            min_budget = filters.get('min_budget', 0)
            max_budget = filters.get('max_budget', 1e12)
            
            # Autres filtres
            status_filter = filters.get('status')  # Vente ou Location
            property_type = filters.get('property_type')
            city = filters.get('city')
            min_bedrooms = filters.get('min_bedrooms', 0)
            min_bathrooms = filters.get('min_bathrooms', 0)
            min_surface = filters.get('min_surface', 0)
            
            for model, source_name in [
                (CoinAfrique, 'CoinAfrique'),
                (ExpatDakarProperty, 'ExpatDakar'),
                (LogerDakarProperty, 'LogerDakar')
            ]:
                try:
                    query = db.session.query(
                        model.id,
                        model.title,
                        model.city,
                        model.property_type,
                        model.price,
                        model.surface_area,
                        model.bedrooms,
                        model.bathrooms,
                        model.scraped_at
                    ).filter(
                        model.price.isnot(None),
                        model.price >= min_budget,
                        model.price <= max_budget
                    )
                    
                    if city:
                        query = query.filter(model.city.ilike(f'%{city}%'))
                    
                    if property_type:
                        query = query.filter(model.property_type.ilike(f'%{property_type}%'))
                    
                    if min_bedrooms > 0:
                        query = query.filter(model.bedrooms >= min_bedrooms)
                    
                    if min_bathrooms > 0:
                        query = query.filter(model.bathrooms >= min_bathrooms)
                    
                    if min_surface > 0:
                        query = query.filter(model.surface_area >= min_surface)
                    
                    properties = query.limit(100).all()
                    
                    for prop in properties:
                        try:
                            price = float(prop.price) if prop.price else 0
                            title = str(prop.title) if prop.title else None
                            prop_type = str(prop.property_type) if prop.property_type else 'Autre'
                            
                            # Détecter le statut
                            native_status = str(prop.status) if hasattr(prop, 'status') and prop.status else None
                            status = detect_listing_status(
                                title=title,
                                price=price,
                                property_type=prop_type,
                                source=source_name,
                                native_status=native_status
                            )
                            
                            # Filtrer par statut si spécifié
                            if status_filter and status != status_filter:
                                continue
                            
                            all_properties.append({
                                'id': f"{source_name}-{prop.id}",
                                'title': title[:80] if title else 'Sans titre',
                                'city': str(prop.city) if prop.city else 'Non spécifié',
                                'property_type': prop_type,
                                'status': status,
                                'price': price,
                                'surface_area': float(prop.surface_area) if prop.surface_area and prop.surface_area > 0 else None,
                                'bedrooms': int(prop.bedrooms) if prop.bedrooms else 0,
                                'bathrooms': int(prop.bathrooms) if prop.bathrooms else 0,
                                'price_per_m2': price / prop.surface_area if prop.surface_area and prop.surface_area > 0 else None,
                                'source': source_name,
                                'scraped_at': prop.scraped_at
                            })
                            
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    print(f"Erreur requête {source_name}: {e}")
                    continue
            
            return pd.DataFrame(all_properties)
            
        except Exception as e:
            print(f"Erreur search_properties: {e}")
            return pd.DataFrame()
    
    def generate_ai_response(self, user_message, user_filters):
        """
        Génère une réponse IA basée sur le message de l'utilisateur
        """
        # Analyser l'intention de l'utilisateur
        message_lower = user_message.lower()
        
        # Budget mentions
        budget_keywords = ['budget', 'prix', 'coût', 'coute', 'argent', 'million', 'fcfa']
        location_keywords = ['louer', 'location', 'loyer', 'mensuel', 'mois']
        vente_keywords = ['acheter', 'achat', 'vendre', 'vente', 'acquisition']
        confort_keywords = ['chambre', 'salle de bain', 'surface', 'm²', 'grand', 'spacieux']
        ville_keywords = ['dakar', 'pikine', 'rufisque', 'thiès', 'ville', 'quartier']
        
        # Construire la réponse
        response_parts = []
        suggestions = []
        
        # Détection budget
        if any(kw in message_lower for kw in budget_keywords):
            budget = user_filters.get('max_budget', 0)
            if budget > 0:
                if budget < 1_500_000:
                    response_parts.append(f"💰 Avec un budget de {budget/1_000_000:.1f}M FCFA, je vous recommande de chercher en **location**.")
                    suggestions.append({'type': 'status', 'value': 'Location', 'label': '🏠 Chercher en Location'})
                else:
                    response_parts.append(f"💰 Votre budget de {budget/1_000_000:.1f}M FCFA vous permet d'envisager un **achat**.")
                    suggestions.append({'type': 'status', 'value': 'Vente', 'label': '💰 Chercher à l\'achat'})
        
        # Détection intention vente/location
        if any(kw in message_lower for kw in location_keywords):
            response_parts.append("🏠 Vous cherchez une **location**. Je vais filtrer les annonces de loyer pour vous.")
            suggestions.append({'type': 'status', 'value': 'Location', 'label': '🏠 Locations uniquement'})
        
        if any(kw in message_lower for kw in vente_keywords):
            response_parts.append("💰 Vous cherchez à **acheter**. Je vais vous montrer les propriétés à vendre.")
            suggestions.append({'type': 'status', 'value': 'Vente', 'label': '💰 Ventes uniquement'})
        
        # Détection confort
        if any(kw in message_lower for kw in confort_keywords):
            if 'chambre' in message_lower:
                # Extraire le nombre si mentionné
                import re
                numbers = re.findall(r'\d+', message_lower)
                if numbers:
                    nb_chambres = int(numbers[0])
                    response_parts.append(f"🛏️ Vous recherchez un bien avec **{nb_chambres} chambres minimum**.")
                    suggestions.append({'type': 'bedrooms', 'value': nb_chambres, 'label': f'🛏️ {nb_chambres}+ chambres'})
        
        # Détection ville
        if any(kw in message_lower for kw in ville_keywords):
            for ville in ['dakar', 'pikine', 'rufisque', 'thiès', 'guédiawaye', 'mbour']:
                if ville in message_lower:
                    response_parts.append(f"📍 Recherche concentrée sur **{ville.title()}**.")
                    suggestions.append({'type': 'city', 'value': ville.title(), 'label': f'📍 {ville.title()}'})
                    break
        
        # Réponse par défaut
        if not response_parts:
            response_parts.append("👋 Bonjour ! Je suis votre assistant immobilier. Comment puis-je vous aider dans votre recherche ?")
            response_parts.append("\n\n**Quelques exemples de questions :**")
            response_parts.append("- Quel est mon budget ?")
            response_parts.append("- Je cherche à louer à Dakar")
            response_parts.append("- Appartement 3 chambres à vendre")
            response_parts.append("- Maison avec jardin à Rufisque")
        
        return {
            'message': '\n\n'.join(response_parts),
            'suggestions': suggestions
        }
    
    # ==================== LAYOUT ====================
    
    def setup_layout(self):
        """Configuration du layout"""
        
        css_b64 = base64.b64encode(self.custom_css.encode()).decode()
        
        self.app.layout = html.Div([
            # CSS
            html.Link(rel='stylesheet', href=f'data:text/css;base64,{css_b64}'),
            
            # Stores
            dcc.Store(id='user-filters-store', data={}),
            dcc.Store(id='favorites-store', data=[]),
            dcc.Store(id='search-results-store', data=[]),
            dcc.Store(id='chat-history-store', data=[]),
            
            # Header
            html.Div([
                html.Div([
                    html.Div([
                        DashIconify(icon="mdi:home-search", width=40, color="white"),
                        html.Div([
                            html.H1("Trouvez Votre Bien Idéal", style={
                                'fontSize': '28px',
                                'fontWeight': '800',
                                'color': 'white',
                                'margin': '0'
                            }),
                            html.P("Recherche intelligente avec assistant IA", style={
                                'fontSize': '14px',
                                'color': 'rgba(255,255,255,0.9)',
                                'margin': '4px 0 0 0'
                            })
                        ], style={'marginLeft': '16px'})
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                    
                    html.Div([
                        html.Button([
                            DashIconify(icon="mdi:heart", width=20, color="white"),
                            html.Span(id='favorites-count', children="0", style={
                                'marginLeft': '8px',
                                'fontSize': '14px',
                                'fontWeight': '600'
                            })
                        ], id='favorites-button', style={
                            'background': 'rgba(255,255,255,0.2)',
                            'border': '1px solid rgba(255,255,255,0.3)',
                            'borderRadius': '12px',
                            'padding': '10px 20px',
                            'color': 'white',
                            'cursor': 'pointer',
                            'display': 'flex',
                            'alignItems': 'center',
                            'backdropFilter': 'blur(10px)'
                        })
                    ])
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
                'padding': '28px 0',
                'boxShadow': '0 4px 20px rgba(0,0,0,0.1)',
                'marginBottom': '32px'
            }),
            
            # Main Container
            html.Div([
                html.Div([
                    # Section gauche - Chatbot + Filtres
                    html.Div([
                        # Chatbot
                        html.Div([
                            html.Div([
                                DashIconify(icon="mdi:robot", width=24, color=self.COLORS['primary']),
                                html.Span("Assistant IA", style={
                                    'fontSize': '18px',
                                    'fontWeight': '700',
                                    'color': self.COLORS['text_primary'],
                                    'marginLeft': '12px'
                                })
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),
                            
                            # Zone messages
                            html.Div(id='chat-messages', style={
                                'height': '400px',
                                'overflowY': 'auto',
                                'marginBottom': '16px',
                                'padding': '16px',
                                'background': self.COLORS['bg_main'],
                                'borderRadius': '12px',
                                'border': f'1px solid {self.COLORS["border"]}'
                            }),
                            
                            # Input message
                            html.Div([
                                dcc.Input(
                                    id='chat-input',
                                    type='text',
                                    placeholder="Posez votre question... (ex: Je cherche un appartement 2 chambres à louer)",
                                    style={
                                        'flex': '1',
                                        'padding': '12px 16px',
                                        'borderRadius': '12px',
                                        'border': f'2px solid {self.COLORS["border"]}',
                                        'fontSize': '14px',
                                        'outline': 'none'
                                    }
                                ),
                                html.Button([
                                    DashIconify(icon="mdi:send", width=20, color="white")
                                ], id='chat-send-button', style={
                                    'background': f'linear-gradient(135deg, {self.COLORS["primary"]}, {self.COLORS["purple"]})',
                                    'border': 'none',
                                    'borderRadius': '12px',
                                    'padding': '12px 20px',
                                    'marginLeft': '12px',
                                    'cursor': 'pointer',
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'boxShadow': f'0 4px 12px {self.COLORS["primary"]}40'
                                })
                            ], style={'display': 'flex', 'alignItems': 'center'})
                        ], style={
                            'background': 'white',
                            'padding': '24px',
                            'borderRadius': '20px',
                            'boxShadow': '0 4px 20px rgba(0,0,0,0.08)',
                            'marginBottom': '24px'
                        }),
                        
                        # Filtres Avancés
                        html.Div([
                            html.Div([
                                DashIconify(icon="mdi:filter-variant", width=20, color=self.COLORS['primary']),
                                html.Span("Filtres de Recherche", style={
                                    'fontSize': '16px',
                                    'fontWeight': '700',
                                    'color': self.COLORS['text_primary'],
                                    'marginLeft': '12px'
                                })
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),
                            
                            # Budget
                            html.Div([
                                html.Label("💰 Budget Maximum", style={
                                    'fontSize': '13px',
                                    'fontWeight': '600',
                                    'color': self.COLORS['text_secondary'],
                                    'marginBottom': '8px',
                                    'display': 'block'
                                }),
                                dcc.Slider(
                                    id='budget-slider',
                                    min=0,
                                    max=200_000_000,
                                    step=5_000_000,
                                    value=50_000_000,
                                    marks={
                                        0: '0',
                                        50_000_000: '50M',
                                        100_000_000: '100M',
                                        150_000_000: '150M',
                                        200_000_000: '200M+'
                                    },
                                    tooltip={"placement": "bottom", "always_visible": True}
                                ),
                                html.Div(id='budget-display', style={
                                    'textAlign': 'center',
                                    'marginTop': '8px',
                                    'fontSize': '16px',
                                    'fontWeight': '600',
                                    'color': self.COLORS['primary']
                                })
                            ], style={'marginBottom': '24px'}),
                            
                            # Statut
                            html.Div([
                                html.Label("🏘️ Type de Transaction", style={
                                    'fontSize': '13px',
                                    'fontWeight': '600',
                                    'color': self.COLORS['text_secondary'],
                                    'marginBottom': '8px',
                                    'display': 'block'
                                }),
                                dcc.RadioItems(
                                    id='status-filter',
                                    options=[
                                        {'label': '  Tous', 'value': 'Tous'},
                                        {'label': '  Vente', 'value': 'Vente'},
                                        {'label': '  Location', 'value': 'Location'}
                                    ],
                                    value='Tous',
                                    inline=True,
                                    style={'fontSize': '14px'}
                                )
                            ], style={'marginBottom': '24px'}),
                            
                            # Type de bien
                            html.Div([
                                html.Label("🏠 Type de Bien", style={
                                    'fontSize': '13px',
                                    'fontWeight': '600',
                                    'color': self.COLORS['text_secondary'],
                                    'marginBottom': '8px',
                                    'display': 'block'
                                }),
                                dcc.Dropdown(
                                    id='property-type-filter',
                                    options=[
                                        {'label': 'Tous les types', 'value': ''},
                                        {'label': '🏠 Appartement', 'value': 'Appartement'},
                                        {'label': '🏡 Villa', 'value': 'Villa'},
                                        {'label': '🏢 Studio', 'value': 'Studio'},
                                        {'label': '🏘️ Duplex', 'value': 'Duplex'},
                                        {'label': '🌳 Terrain', 'value': 'Terrain'}
                                    ],
                                    value='',
                                    clearable=False,
                                    style={'borderRadius': '12px'}
                                )
                            ], style={'marginBottom': '24px'}),
                            
                            # Ville
                            html.Div([
                                html.Label("📍 Ville", style={
                                    'fontSize': '13px',
                                    'fontWeight': '600',
                                    'color': self.COLORS['text_secondary'],
                                    'marginBottom': '8px',
                                    'display': 'block'
                                }),
                                dcc.Dropdown(
                                    id='city-filter',
                                    options=[
                                        {'label': 'Toutes les villes', 'value': ''},
                                        {'label': '📍 Dakar', 'value': 'Dakar'},
                                        {'label': '📍 Pikine', 'value': 'Pikine'},
                                        {'label': '📍 Guédiawaye', 'value': 'Guédiawaye'},
                                        {'label': '📍 Rufisque', 'value': 'Rufisque'},
                                        {'label': '📍 Thiès', 'value': 'Thiès'},
                                        {'label': '📍 Mbour', 'value': 'Mbour'}
                                    ],
                                    value='',
                                    clearable=False,
                                    style={'borderRadius': '12px'}
                                )
                            ], style={'marginBottom': '24px'}),
                            
                            # Chambres
                            html.Div([
                                html.Label("🛏️ Chambres Minimum", style={
                                    'fontSize': '13px',
                                    'fontWeight': '600',
                                    'color': self.COLORS['text_secondary'],
                                    'marginBottom': '8px',
                                    'display': 'block'
                                }),
                                dcc.Slider(
                                    id='bedrooms-slider',
                                    min=0,
                                    max=6,
                                    step=1,
                                    value=0,
                                    marks={i: str(i) if i < 6 else '6+' for i in range(7)}
                                )
                            ], style={'marginBottom': '24px'}),
                            
                            # Bouton recherche
                            html.Button([
                                DashIconify(icon="mdi:magnify", width=20, color="white"),
                                html.Span("Rechercher", style={'marginLeft': '8px'})
                            ], id='search-button', style={
                                'width': '100%',
                                'background': f'linear-gradient(135deg, {self.COLORS["success"]}, {self.COLORS["teal"]})',
                                'border': 'none',
                                'borderRadius': '12px',
                                'padding': '14px',
                                'color': 'white',
                                'fontSize': '15px',
                                'fontWeight': '600',
                                'cursor': 'pointer',
                                'display': 'flex',
                                'alignItems': 'center',
                                'justifyContent': 'center',
                                'boxShadow': f'0 4px 12px {self.COLORS["success"]}40'
                            })
                        ], style={
                            'background': 'white',
                            'padding': '24px',
                            'borderRadius': '20px',
                            'boxShadow': '0 4px 20px rgba(0,0,0,0.08)'
                        })
                    ], style={'flex': '1', 'minWidth': '400px', 'maxWidth': '450px'}),
                    
                    # Section droite - Résultats
                    html.Div([
                        # Stats rapides
                        html.Div(id='search-stats', style={'marginBottom': '24px'}),
                        
                        # Résultats
                        html.Div(id='search-results', style={
                            'display': 'grid',
                            'gridTemplateColumns': 'repeat(auto-fill, minmax(320px, 1fr))',
                            'gap': '20px'
                        })
                    ], style={'flex': '2', 'minWidth': '0'})
                    
                ], style={
                    'display': 'flex',
                    'gap': '32px',
                    'maxWidth': '1800px',
                    'margin': '0 auto',
                    'padding': '0 32px 60px 32px'
                })
            ], style={'background': self.COLORS['bg_main'], 'minHeight': 'calc(100vh - 200px)'})
        ])
    
    # ==================== CALLBACKS ====================
    
    def setup_callbacks(self):
        """Configuration des callbacks"""
        
        @self.app.callback(
            Output('budget-display', 'children'),
            Input('budget-slider', 'value')
        )
        def update_budget_display(budget):
            if budget >= 1_000_000:
                return f"{budget/1_000_000:.0f} Millions FCFA"
            else:
                return f"{budget:,} FCFA".replace(',', ' ')
        
        @self.app.callback(
            [
                Output('user-filters-store', 'data'),
                Output('search-results-store', 'data')
            ],
            Input('search-button', 'n_clicks'),
            [
                State('budget-slider', 'value'),
                State('status-filter', 'value'),
                State('property-type-filter', 'value'),
                State('city-filter', 'value'),
                State('bedrooms-slider', 'value')
            ]
        )
        def perform_search(n_clicks, budget, status, prop_type, city, bedrooms):
            if not n_clicks:
                return {}, []
            
            filters = {
                'max_budget': budget,
                'min_budget': 0,
                'status': status if status != 'Tous' else None,
                'property_type': prop_type if prop_type else None,
                'city': city if city else None,
                'min_bedrooms': bedrooms if bedrooms > 0 else 0
            }
            
            df = self.search_properties(filters)
            
            if df.empty:
                return filters, []
            
            results = df.to_dict('records')
            return filters, results
        
        @self.app.callback(
            Output('search-stats', 'children'),
            Input('search-results-store', 'data')
        )
        def update_search_stats(results):
            if not results:
                return html.Div("Aucun résultat. Ajustez vos critères de recherche.", style={
                    'padding': '20px',
                    'textAlign': 'center',
                    'color': self.COLORS['text_secondary'],
                    'background': 'white',
                    'borderRadius': '12px'
                })
            
            df = pd.DataFrame(results)
            
            return html.Div([
                html.Div([
                    html.Div([
                        html.Span(str(len(df)), style={
                            'fontSize': '32px',
                            'fontWeight': '800',
                            'color': self.COLORS['primary']
                        }),
                        html.Span(" résultats trouvés", style={
                            'fontSize': '16px',
                            'color': self.COLORS['text_secondary'],
                            'marginLeft': '8px'
                        })
                    ]),
                    html.Div([
                        html.Span(f"Prix moyen: {df['price'].mean()/1_000_000:.1f}M FCFA", style={
                            'fontSize': '14px',
                            'color': self.COLORS['text_secondary'],
                            'marginRight': '20px'
                        }),
                        html.Span(f"Surface moyenne: {df['surface_area'].mean():.0f}m²" if df['surface_area'].notna().sum() > 0 else "", style={
                            'fontSize': '14px',
                            'color': self.COLORS['text_secondary']
                        })
                    ])
                ])
            ], style={
                'background': 'white',
                'padding': '20px 24px',
                'borderRadius': '12px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.06)'
            })
        
        @self.app.callback(
            Output('search-results', 'children'),
            [
                Input('search-results-store', 'data'),
                Input('favorites-store', 'data')
            ]
        )
        def update_search_results(results, favorites):
            if not results:
                return html.Div([
                    DashIconify(icon="mdi:magnify", width=80, color=self.COLORS['text_secondary'], style={'opacity': '0.3'}),
                    html.H3("Lancez une recherche", style={
                        'color': self.COLORS['text_secondary'],
                        'marginTop': '16px'
                    }),
                    html.P("Utilisez les filtres ou le chatbot pour trouver votre bien idéal", style={
                        'color': self.COLORS['text_secondary'],
                        'opacity': '0.7'
                    })
                ], style={
                    'gridColumn': '1 / -1',
                    'display': 'flex',
                    'flexDirection': 'column',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'padding': '80px 20px',
                    'background': 'white',
                    'borderRadius': '20px'
                })
            
            cards = []
            for prop in results[:50]:  # Limiter à 50 résultats
                is_favorite = prop['id'] in favorites
                
                card = html.Div([
                    # Image placeholder
                    html.Div([
                        DashIconify(
                            icon="mdi:home-city" if prop['property_type'] == 'Appartement' else "mdi:home",
                            width=60,
                            color=self.COLORS['primary'],
                            style={'opacity': '0.3'}
                        ),
                        html.Div([
                            DashIconify(
                                icon="mdi:heart" if is_favorite else "mdi:heart-outline",
                                width=24,
                                color=self.COLORS['danger'] if is_favorite else 'white'
                            )
                        ], id={'type': 'favorite-btn', 'index': prop['id']}, className='favorite-heart', style={
                            'position': 'absolute',
                            'top': '12px',
                            'right': '12px',
                            'background': 'rgba(255,255,255,0.9)' if not is_favorite else 'white',
                            'borderRadius': '50%',
                            'padding': '8px',
                            'cursor': 'pointer',
                            'boxShadow': '0 2px 8px rgba(0,0,0,0.15)'
                        })
                    ], style={
                        'height': '160px',
                        'background': f'linear-gradient(135deg, {self.COLORS["bg_main"]}, {self.COLORS["border"]})',
                        'borderRadius': '12px 12px 0 0',
                        'display': 'flex',
                        'alignItems': 'center',
                        'justifyContent': 'center',
                        'position': 'relative'
                    }),
                    
                    # Info
                    html.Div([
                        html.Div([
                            html.Span(prop['status'], style={
                                'background': self.COLORS['success'] if prop['status'] == 'Vente' else self.COLORS['info'],
                                'color': 'white',
                                'padding': '4px 12px',
                                'borderRadius': '6px',
                                'fontSize': '11px',
                                'fontWeight': '600'
                            })
                        ], style={'marginBottom': '12px'}),
                        
                        html.H4(prop['title'], style={
                            'fontSize': '15px',
                            'fontWeight': '600',
                            'color': self.COLORS['text_primary'],
                            'marginBottom': '8px',
                            'lineHeight': '1.4',
                            'height': '42px',
                            'overflow': 'hidden'
                        }),
                        
                        html.Div([
                            DashIconify(icon="mdi:map-marker", width=14, color=self.COLORS['text_secondary']),
                            html.Span(prop['city'], style={
                                'fontSize': '13px',
                                'color': self.COLORS['text_secondary'],
                                'marginLeft': '4px'
                            })
                        ], style={'marginBottom': '12px'}),
                        
                        html.Div([
                            html.Div([
                                DashIconify(icon="mdi:bed", width=16, color=self.COLORS['text_secondary']),
                                html.Span(f"{prop['bedrooms']}" if prop['bedrooms'] > 0 else "N/A", style={
                                    'fontSize': '12px',
                                    'marginLeft': '4px'
                                })
                            ], style={'marginRight': '12px'}),
                            html.Div([
                                DashIconify(icon="mdi:shower", width=16, color=self.COLORS['text_secondary']),
                                html.Span(f"{prop['bathrooms']}" if prop['bathrooms'] > 0 else "N/A", style={
                                    'fontSize': '12px',
                                    'marginLeft': '4px'
                                })
                            ], style={'marginRight': '12px'}),
                            html.Div([
                                DashIconify(icon="mdi:ruler-square", width=16, color=self.COLORS['text_secondary']),
                                html.Span(f"{prop['surface_area']:.0f}m²" if prop['surface_area'] else "N/A", style={
                                    'fontSize': '12px',
                                    'marginLeft': '4px'
                                })
                            ])
                        ], style={
                            'display': 'flex',
                            'marginBottom': '16px',
                            'paddingBottom': '16px',
                            'borderBottom': f'1px solid {self.COLORS["border"]}'
                        }),
                        
                        html.Div([
                            html.Span(f"{prop['price']/1_000_000:.1f}M", style={
                                'fontSize': '22px',
                                'fontWeight': '800',
                                'color': self.COLORS['primary']
                            }),
                            html.Span(" FCFA" + ("/mois" if prop['status'] == 'Location' else ""), style={
                                'fontSize': '13px',
                                'color': self.COLORS['text_secondary'],
                                'marginLeft': '4px'
                            })
                        ])
                    ], style={'padding': '16px'})
                ], className='property-card', style={
                    'background': 'white',
                    'borderRadius': '16px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
                    'overflow': 'hidden'
                })
                
                cards.append(card)
            
            return cards
        
        @self.app.callback(
            [
                Output('chat-messages', 'children'),
                Output('chat-history-store', 'data'),
                Output('chat-input', 'value')
            ],
            [
                Input('chat-send-button', 'n_clicks'),
                Input('chat-input', 'n_submit')
            ],
            [
                State('chat-input', 'value'),
                State('chat-history-store', 'data'),
                State('user-filters-store', 'data')
            ]
        )
        def update_chat(n_clicks, n_submit, message, history, filters):
            if not message or (not n_clicks and not n_submit):
                if not history:
                    # Message de bienvenue
                    return [
                        html.Div([
                            html.Div([
                                DashIconify(icon="mdi:robot", width=32, color=self.COLORS['primary'])
                            ], style={
                                'width': '40px',
                                'height': '40px',
                                'borderRadius': '50%',
                                'background': f'{self.COLORS["primary"]}15',
                                'display': 'flex',
                                'alignItems': 'center',
                                'justifyContent': 'center',
                                'marginRight': '12px'
                            }),
                            html.Div([
                                html.Div("Assistant IA", style={
                                    'fontSize': '12px',
                                    'fontWeight': '600',
                                    'color': self.COLORS['text_secondary'],
                                    'marginBottom': '4px'
                                }),
                                html.Div("👋 Bonjour ! Je suis votre assistant immobilier. Dites-moi ce que vous recherchez et je vous aiderai à trouver le bien idéal !", style={
                                    'fontSize': '14px',
                                    'lineHeight': '1.6',
                                    'color': self.COLORS['text_primary']
                                })
                            ], style={
                                'background': 'white',
                                'padding': '12px 16px',
                                'borderRadius': '12px',
                                'boxShadow': '0 2px 8px rgba(0,0,0,0.06)',
                                'flex': '1'
                            })
                        ], className='chat-message', style={
                            'display': 'flex',
                            'marginBottom': '16px'
                        })
                    ], history, ""
                return [self.render_chat_history(history)], history, ""
            
            # Ajouter le message utilisateur
            history.append({
                'role': 'user',
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Générer réponse IA
            ai_response = self.generate_ai_response(message, filters)
            
            history.append({
                'role': 'assistant',
                'message': ai_response['message'],
                'suggestions': ai_response.get('suggestions', []),
                'timestamp': datetime.now().isoformat()
            })
            
            return [self.render_chat_history(history)], history, ""
        
        @self.app.callback(
            Output('favorites-count', 'children'),
            Input('favorites-store', 'data')
        )
        def update_favorites_count(favorites):
            return str(len(favorites))
    
    def render_chat_history(self, history):
        """Rendre l'historique du chat"""
        messages = []
        
        for msg in history:
            if msg['role'] == 'user':
                messages.append(
                    html.Div([
                        html.Div([
                            html.Div(msg['message'], style={
                                'background': f'linear-gradient(135deg, {self.COLORS["primary"]}, {self.COLORS["purple"]})',
                                'color': 'white',
                                'padding': '12px 16px',
                                'borderRadius': '12px',
                                'fontSize': '14px',
                                'maxWidth': '80%',
                                'marginLeft': 'auto',
                                'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
                            })
                        ], style={'display': 'flex', 'justifyContent': 'flex-end'})
                    ], className='chat-message', style={'marginBottom': '16px'})
                )
            else:
                messages.append(
                    html.Div([
                        html.Div([
                            DashIconify(icon="mdi:robot", width=32, color=self.COLORS['primary'])
                        ], style={
                            'width': '40px',
                            'height': '40px',
                            'borderRadius': '50%',
                            'background': f'{self.COLORS["primary"]}15',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'marginRight': '12px',
                            'flexShrink': '0'
                        }),
                        html.Div([
                            dcc.Markdown(msg['message'], style={
                                'fontSize': '14px',
                                'lineHeight': '1.6',
                                'color': self.COLORS['text_primary']
                            })
                        ], style={
                            'background': 'white',
                            'padding': '12px 16px',
                            'borderRadius': '12px',
                            'boxShadow': '0 2px 8px rgba(0,0,0,0.06)',
                            'flex': '1'
                        })
                    ], className='chat-message', style={
                        'display': 'flex',
                        'marginBottom': '16px'
                    })
                )
        
        return messages


def create_viewer_dashboard(server=None, routes_pathname_prefix="/viewer/", requests_pathname_prefix="/viewer/"):
    """Factory function pour créer le viewer dashboard"""
    try:
        dashboard = ViewerDashboard(
            server=server,
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix
        )
        print("✅ Viewer Dashboard créé avec succès")
        return dashboard.app
    except Exception as e:
        print(f"❌ ERREUR création Viewer Dashboard: {e}")
        import traceback
        traceback.print_exc()
        raise