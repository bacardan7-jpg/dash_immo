"""
👁️ VIEWER DASHBOARD - INTERFACE UTILISATEUR FINALE
Dashboard avec chatbot IA, recherche intelligente et recommandations personnalisées
Auteur: Cos - ENSAE Dakar
Version: 1.0 - Viewer Experience
"""

import dash
from dash import html, dcc, Input, Output, State, ALL, callback_context, MATCH
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
import re

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


class AIAssistant:
    """Assistant IA pour analyser les messages et générer des réponses intelligentes"""
    
    @staticmethod
    def extract_budget(message):
        """Extraire le budget du message"""
        # Chercher des nombres suivis de M, millions, FCFA, etc.
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:millions?|m)\s*(?:fcfa|cfa)?',
            r'(\d+(?:\.\d+)?)\s*(?:k|mille)\s*(?:fcfa|cfa)?',
            r'(\d{1,3}(?:\s*\d{3})*)\s*(?:fcfa|cfa)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                value = float(match.group(1).replace(' ', ''))
                if 'k' in message.lower() or 'mille' in message.lower():
                    return int(value * 1000)
                elif 'm' in message.lower() or 'million' in message.lower():
                    return int(value * 1_000_000)
                else:
                    return int(value)
        return None
    
    @staticmethod
    def extract_bedrooms(message):
        """Extraire le nombre de chambres"""
        patterns = [
            r'(\d+)\s*chambres?',
            r'(\d+)\s*ch\b',
            r'(\d+)\s*pieces?',
            r'f(\d+)',  # F3, F4, etc.
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                return int(match.group(1))
        return None
    
    @staticmethod
    def extract_city(message):
        """Extraire la ville du message"""
        cities = {
            'dakar': 'Dakar',
            'pikine': 'Pikine',
            'guediawaye': 'Guédiawaye',
            'guédiawaye': 'Guédiawaye',
            'rufisque': 'Rufisque',
            'thies': 'Thiès',
            'thiès': 'Thiès',
            'mbour': 'Mbour',
            'saint-louis': 'Saint-Louis',
            'kaolack': 'Kaolack',
            'ziguinchor': 'Ziguinchor'
        }
        
        message_lower = message.lower()
        for key, value in cities.items():
            if key in message_lower:
                return value
        return None
    
    @staticmethod
    def extract_property_type(message):
        """Extraire le type de propriété"""
        types = {
            'appartement': 'Appartement',
            'appart': 'Appartement',
            'villa': 'Villa',
            'maison': 'Villa',
            'studio': 'Studio',
            'duplex': 'Duplex',
            'terrain': 'Terrain',
            'parcelle': 'Terrain'
        }
        
        message_lower = message.lower()
        for key, value in types.items():
            if key in message_lower:
                return value
        return None
    
    @staticmethod
    def detect_transaction_type(message):
        """Détecter Vente ou Location"""
        message_lower = message.lower()
        
        location_keywords = ['louer', 'location', 'loyer', 'mensuel', 'mois', 'bail']
        vente_keywords = ['acheter', 'achat', 'vendre', 'vente', 'acquisition', 'acquérir']
        
        has_location = any(kw in message_lower for kw in location_keywords)
        has_vente = any(kw in message_lower for kw in vente_keywords)
        
        if has_location and not has_vente:
            return 'Location'
        elif has_vente and not has_location:
            return 'Vente'
        return None
    
    @staticmethod
    def generate_response(message, extracted_data, current_filters):
        """Générer une réponse intelligente basée sur l'analyse"""
        response_parts = []
        suggestions = []
        
        # Salutations
        greetings = ['salut', 'bonjour', 'bonsoir', 'hello', 'hi']
        if any(g in message.lower() for g in greetings):
            response_parts.append("👋 **Bonjour !** Je suis ravi de vous aider à trouver votre bien idéal.")
            response_parts.append("\n💡 **Comment puis-je vous aider ?**\n- Dites-moi votre budget\n- Précisez le type de bien recherché\n- Indiquez votre ville préférée\n- Mentionnez vos besoins en confort")
            return {'message': '\n'.join(response_parts), 'suggestions': [], 'filters': {}}
        
        # Budget
        if extracted_data.get('budget'):
            budget = extracted_data['budget']
            if budget < 1_500_000:
                response_parts.append(f"💰 **Budget:** {budget/1_000:.0f}K FCFA → Idéal pour une **location**")
                suggestions.append({
                    'type': 'status',
                    'value': 'Location',
                    'label': '🏠 Chercher en Location',
                    'icon': 'mdi:home-city'
                })
            else:
                response_parts.append(f"💰 **Budget:** {budget/1_000_000:.1f}M FCFA → Vous pouvez envisager un **achat**")
                suggestions.append({
                    'type': 'status',
                    'value': 'Vente',
                    'label': '💰 Chercher à l\'achat',
                    'icon': 'mdi:cash'
                })
        
        # Type de transaction
        if extracted_data.get('transaction_type'):
            trans_type = extracted_data['transaction_type']
            icon = '🏠' if trans_type == 'Location' else '💰'
            response_parts.append(f"{icon} **Type:** Vous cherchez en **{trans_type}**")
            suggestions.append({
                'type': 'status',
                'value': trans_type,
                'label': f'{icon} {trans_type}',
                'icon': 'mdi:home-city' if trans_type == 'Location' else 'mdi:cash'
            })
        
        # Type de bien
        if extracted_data.get('property_type'):
            prop_type = extracted_data['property_type']
            response_parts.append(f"🏠 **Type de bien:** {prop_type}")
            suggestions.append({
                'type': 'property_type',
                'value': prop_type,
                'label': f'🏠 {prop_type}',
                'icon': 'mdi:home'
            })
        
        # Chambres
        if extracted_data.get('bedrooms'):
            bedrooms = extracted_data['bedrooms']
            response_parts.append(f"🛏️ **Chambres:** Minimum {bedrooms} chambres")
            suggestions.append({
                'type': 'bedrooms',
                'value': bedrooms,
                'label': f'🛏️ {bedrooms}+ chambres',
                'icon': 'mdi:bed'
            })
        
        # Ville
        if extracted_data.get('city'):
            city = extracted_data['city']
            response_parts.append(f"📍 **Localisation:** {city}")
            suggestions.append({
                'type': 'city',
                'value': city,
                'label': f'📍 {city}',
                'icon': 'mdi:map-marker'
            })
        
        # Recommandations intelligentes
        if extracted_data.get('budget') and extracted_data.get('transaction_type'):
            budget = extracted_data['budget']
            trans = extracted_data['transaction_type']
            
            if trans == 'Location' and budget < 500_000:
                response_parts.append("\n💡 **Recommandation:** Avec ce budget, je vous suggère de chercher des **studios** ou **chambres meublées**.")
            elif trans == 'Vente' and budget < 30_000_000:
                response_parts.append("\n💡 **Recommandation:** Ce budget est parfait pour un **appartement** ou un **terrain** en périphérie.")
            elif trans == 'Vente' and budget >= 100_000_000:
                response_parts.append("\n💡 **Recommandation:** Excellent budget ! Vous pouvez viser des **villas haut de gamme** ou **immeubles**.")
        
        # Message par défaut si rien n'est extrait
        if not response_parts:
            response_parts.append("🤔 Je n'ai pas bien compris votre demande.")
            response_parts.append("\n**Exemples de questions que vous pouvez poser:**")
            response_parts.append("- *Je cherche à louer un appartement 3 chambres à Dakar*")
            response_parts.append("- *Quel est le prix moyen d'une villa à Rufisque ?*")
            response_parts.append("- *J'ai un budget de 50 millions, que puis-je acheter ?*")
            response_parts.append("- *Studio meublé en location à Pikine*")
        
        # Appel à l'action
        if suggestions:
            response_parts.append("\n✨ **Cliquez sur les suggestions ci-dessous pour appliquer les filtres automatiquement !**")
        
        return {
            'message': '\n\n'.join(response_parts),
            'suggestions': suggestions,
            'filters': extracted_data
        }
    
    @staticmethod
    def analyze_message(message, current_filters):
        """Analyser le message complet et retourner la réponse"""
        extracted = {
            'budget': AIAssistant.extract_budget(message),
            'bedrooms': AIAssistant.extract_bedrooms(message),
            'city': AIAssistant.extract_city(message),
            'property_type': AIAssistant.extract_property_type(message),
            'transaction_type': AIAssistant.detect_transaction_type(message)
        }
        
        return AIAssistant.generate_response(message, extracted, current_filters)


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
        * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
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
            cursor: pointer;
        }
        .filter-chip:hover {
            transform: scale(1.05);
        }
        
        .favorite-heart {
            transition: all 0.2s ease;
            cursor: pointer;
        }
        .favorite-heart:hover {
            transform: scale(1.2);
        }
        
        .suggestion-chip {
            transition: all 0.2s ease;
            cursor: pointer;
            display: inline-block;
        }
        .suggestion-chip:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(30, 64, 175, 0.3);
        }
        
        /* Scrollbar personnalisée */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #F1F5F9;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #CBD5E1;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #94A3B8;
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
        """Recherche intelligente de propriétés avec filtres avancés"""
        try:
            db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty = self.safe_import_models()
            
            if not db:
                return pd.DataFrame()
            
            all_properties = []
            
            # Extraire les filtres
            min_budget = filters.get('min_budget', 0)
            max_budget = filters.get('max_budget', 1e12)
            status_filter = filters.get('status')
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
                    query = db.session.query(model)
                    
                    # Filtres de base
                    query = query.filter(
                        model.price.isnot(None),
                        model.price >= min_budget,
                        model.price <= max_budget
                    )
                    
                    if city and city != '':
                        query = query.filter(model.city.ilike(f'%{city}%'))
                    
                    if property_type and property_type != '':
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
                            title = str(prop.title) if hasattr(prop, 'title') and prop.title else None
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
                            if status_filter and status_filter != 'Tous' and status != status_filter:
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
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    # ==================== LAYOUT ====================
    
    def setup_layout(self):
        """Configuration du layout"""
        
        css_b64 = base64.b64encode(self.custom_css.encode()).decode()
        
        self.app.layout = html.Div([
            # CSS
            html.Link(rel='stylesheet', href=f'data:text/css;base64,{css_b64}'),
            
            # Stores
            dcc.Store(id='user-filters-store', data={
                'max_budget': 50_000_000,
                'min_budget': 0,
                'status': 'Tous',
                'property_type': '',
                'city': '',
                'min_bedrooms': 0,
                'min_bathrooms': 0
            }),
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
                                html.Span("Assistant IA Immobilier", style={
                                    'fontSize': '18px',
                                    'fontWeight': '700',
                                    'color': self.COLORS['text_primary'],
                                    'marginLeft': '12px'
                                })
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),
                            
                            # Zone messages
                            html.Div(id='chat-messages', children=[
                                # Message de bienvenue initial
                                self.create_ai_message(
                                    "👋 **Bonjour !** Je suis votre assistant immobilier intelligent.\n\n"
                                    "💬 **Dites-moi ce que vous cherchez**, par exemple:\n"
                                    "- *Je veux louer un appartement 3 chambres à Dakar*\n"
                                    "- *J'ai un budget de 50 millions pour acheter*\n"
                                    "- *Studio meublé en location à Pikine*\n\n"
                                    "✨ Je vais analyser votre demande et vous proposer les meilleures options !"
                                )
                            ], style={
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
                                    placeholder="Décrivez votre recherche... (ex: appartement 2 chambres à louer)",
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
                                ], id='chat-send-button', n_clicks=0, style={
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
                                html.Div(id='budget-display', children="50 Millions FCFA", style={
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
                                        {'label': ' Tous', 'value': 'Tous'},
                                        {'label': ' Vente', 'value': 'Vente'},
                                        {'label': ' Location', 'value': 'Location'}
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
                            ], id='search-button', n_clicks=0, style={
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
                        html.Div(id='search-stats', children=[
                            html.Div([
                                DashIconify(icon="mdi:information-outline", width=24, color=self.COLORS['info']),
                                html.Span("Utilisez les filtres ou le chatbot pour commencer votre recherche", style={
                                    'marginLeft': '12px',
                                    'fontSize': '14px',
                                    'color': self.COLORS['text_secondary']
                                })
                            ], style={
                                'display': 'flex',
                                'alignItems': 'center',
                                'padding': '20px',
                                'background': 'white',
                                'borderRadius': '12px',
                                'boxShadow': '0 2px 8px rgba(0,0,0,0.06)'
                            })
                        ], style={'marginBottom': '24px'}),
                        
                        # Résultats
                        html.Div(id='search-results', children=[
                            html.Div([
                                DashIconify(icon="mdi:magnify", width=80, color=self.COLORS['text_secondary'], style={'opacity': '0.3'}),
                                html.H3("Lancez une recherche", style={
                                    'color': self.COLORS['text_secondary'],
                                    'marginTop': '16px'
                                }),
                                html.P("Décrivez votre besoin au chatbot ou ajustez les filtres pour trouver votre bien idéal", style={
                                    'color': self.COLORS['text_secondary'],
                                    'opacity': '0.7'
                                })
                            ], style={
                                'display': 'flex',
                                'flexDirection': 'column',
                                'alignItems': 'center',
                                'justifyContent': 'center',
                                'padding': '80px 20px',
                                'background': 'white',
                                'borderRadius': '20px',
                                'textAlign': 'center'
                            })
                        ], style={
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
                    'padding': '0 32px 60px 32px',
                    'flexWrap': 'wrap'
                })
            ], style={'background': self.COLORS['bg_main'], 'minHeight': 'calc(100vh - 200px)'})
        ])
    
    # ==================== UI HELPERS ====================
    
    def create_user_message(self, message):
        """Créer une bulle de message utilisateur"""
        return html.Div([
            html.Div([
                html.Div(message, style={
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
    
    def create_ai_message(self, message, suggestions=None):
        """Créer une bulle de message IA avec suggestions optionnelles"""
        elements = [
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
                    dcc.Markdown(message, style={
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
            ], style={
                'display': 'flex',
                'marginBottom': '12px'
            })
        ]
        
        # Ajouter les suggestions si présentes
        if suggestions and len(suggestions) > 0:
            suggestion_chips = []
            for i, sug in enumerate(suggestions):
                suggestion_chips.append(
                    html.Div([
                        DashIconify(icon=sug.get('icon', 'mdi:check'), width=16, color=self.COLORS['primary']),
                        html.Span(sug['label'], style={'marginLeft': '6px', 'fontSize': '13px'})
                    ], id={'type': 'suggestion-chip', 'index': i}, className='suggestion-chip', style={
                        'background': f'{self.COLORS["primary"]}10',
                        'color': self.COLORS['primary'],
                        'border': f'1px solid {self.COLORS["primary"]}30',
                        'padding': '8px 14px',
                        'borderRadius': '20px',
                        'fontSize': '13px',
                        'fontWeight': '500',
                        'marginRight': '8px',
                        'marginBottom': '8px',
                        'display': 'inline-flex',
                        'alignItems': 'center'
                    })
                )
            
            elements.append(
                html.Div(suggestion_chips, style={
                    'display': 'flex',
                    'flexWrap': 'wrap',
                    'marginLeft': '52px',
                    'marginBottom': '8px'
                })
            )
        
        return html.Div(elements, className='chat-message', style={'marginBottom': '16px'})
    
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
            ],
            prevent_initial_call=True
        )
        def perform_search(n_clicks, budget, status, prop_type, city, bedrooms):
            if not n_clicks:
                return dash.no_update, []
            
            filters = {
                'max_budget': budget,
                'min_budget': 0,
                'status': status,
                'property_type': prop_type,
                'city': city,
                'min_bedrooms': bedrooms
            }
            
            print(f"🔍 Recherche avec filtres: {filters}")
            
            df = self.search_properties(filters)
            
            if df.empty:
                return filters, []
            
            results = df.to_dict('records')
            print(f"✅ {len(results)} résultats trouvés")
            return filters, results
        
        @self.app.callback(
            Output('search-stats', 'children'),
            Input('search-results-store', 'data')
        )
        def update_search_stats(results):
            if not results:
                return html.Div([
                    DashIconify(icon="mdi:information-outline", width=24, color=self.COLORS['info']),
                    html.Span("Utilisez les filtres ou le chatbot pour commencer votre recherche", style={
                        'marginLeft': '12px',
                        'fontSize': '14px',
                        'color': self.COLORS['text_secondary']
                    })
                ], style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'padding': '20px',
                    'background': 'white',
                    'borderRadius': '12px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.06)'
                })
            
            df = pd.DataFrame(results)
            
            vente_count = len(df[df['status'] == 'Vente'])
            location_count = len(df[df['status'] == 'Location'])
            
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
                        html.Span(f"💰 {vente_count} à vendre", style={
                            'fontSize': '14px',
                            'color': self.COLORS['text_secondary'],
                            'marginRight': '20px'
                        }),
                        html.Span(f"🏠 {location_count} en location", style={
                            'fontSize': '14px',
                            'color': self.COLORS['text_secondary'],
                            'marginRight': '20px'
                        }),
                        html.Span(f"Prix moyen: {df['price'].mean()/1_000_000:.1f}M FCFA", style={
                            'fontSize': '14px',
                            'color': self.COLORS['text_secondary']
                        })
                    ], style={'marginTop': '8px'})
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
                    html.P("Décrivez votre besoin au chatbot ou ajustez les filtres pour trouver votre bien idéal", style={
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
                    'borderRadius': '20px',
                    'textAlign': 'center'
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
                            }),
                            html.Span(prop['source'], style={
                                'background': self.COLORS['bg_main'],
                                'color': self.COLORS['text_secondary'],
                                'padding': '4px 10px',
                                'borderRadius': '6px',
                                'fontSize': '10px',
                                'fontWeight': '600',
                                'marginLeft': '8px'
                            })
                        ], style={'marginBottom': '12px', 'display': 'flex'}),
                        
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
                            html.Span(" FCFA" + (" /mois" if prop['status'] == 'Location' else ""), style={
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
                Output('chat-input', 'value'),
                Output('budget-slider', 'value'),
                Output('status-filter', 'value'),
                Output('property-type-filter', 'value'),
                Output('city-filter', 'value'),
                Output('bedrooms-slider', 'value')
            ],
            [
                Input('chat-send-button', 'n_clicks'),
                Input('chat-input', 'n_submit')
            ],
            [
                State('chat-input', 'value'),
                State('chat-history-store', 'data'),
                State('user-filters-store', 'data'),
                State('budget-slider', 'value'),
                State('status-filter', 'value'),
                State('property-type-filter', 'value'),
                State('city-filter', 'value'),
                State('bedrooms-slider', 'value')
            ],
            prevent_initial_call=True
        )
        def update_chat(n_clicks, n_submit, message, history, filters, 
                       current_budget, current_status, current_prop_type, 
                       current_city, current_bedrooms):
            
            # Vérifier si appelé
            if not message or (not n_clicks and not n_submit):
                return dash.no_update, dash.no_update, dash.no_update, \
                       dash.no_update, dash.no_update, dash.no_update, \
                       dash.no_update, dash.no_update
            
            # Ajouter le message utilisateur
            if not history:
                history = []
            
            history.append({
                'role': 'user',
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Analyser le message avec l'IA
            print(f"🤖 Analyse du message: {message}")
            ai_response = AIAssistant.analyze_message(message, filters)
            print(f"✅ Réponse IA: {ai_response}")
            
            # Ajouter la réponse IA
            history.append({
                'role': 'assistant',
                'message': ai_response['message'],
                'suggestions': ai_response.get('suggestions', []),
                'timestamp': datetime.now().isoformat()
            })
            
            # Mettre à jour les filtres si l'IA a extrait des infos
            extracted = ai_response.get('filters', {})
            
            new_budget = extracted.get('budget', current_budget)
            if new_budget is None:
                new_budget = current_budget
            
            new_status = extracted.get('transaction_type', current_status)
            if new_status is None:
                new_status = current_status
            
            new_prop_type = extracted.get('property_type', current_prop_type)
            if new_prop_type is None:
                new_prop_type = current_prop_type
            
            new_city = extracted.get('city', current_city)
            if new_city is None:
                new_city = current_city
            
            new_bedrooms = extracted.get('bedrooms', current_bedrooms)
            if new_bedrooms is None:
                new_bedrooms = current_bedrooms
            
            # Rendre l'historique du chat
            messages_ui = []
            for msg in history:
                if msg['role'] == 'user':
                    messages_ui.append(self.create_user_message(msg['message']))
                else:
                    messages_ui.append(
                        self.create_ai_message(
                            msg['message'],
                            msg.get('suggestions', [])
                        )
                    )
            
            return messages_ui, history, "", new_budget, new_status, \
                   new_prop_type, new_city, new_bedrooms
        
        @self.app.callback(
            Output('favorites-count', 'children'),
            Input('favorites-store', 'data')
        )
        def update_favorites_count(favorites):
            return str(len(favorites))


from ..components.dash_sidebar_component import create_sidebar_layout

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


