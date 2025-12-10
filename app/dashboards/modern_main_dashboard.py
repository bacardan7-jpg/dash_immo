"""
🟦 OBSERVATOIRE IMMOBILIER - VERSION ULTRA-COMPLÈTE ET ROBUSTE
Dashboard Institutionnel Professionnel avec Gestion d'Erreurs Exhaustive
Toutes les 10 sections + méthodologie
Auteur: Cos - ENSAE Dakar
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


class ObservatoireComplet:
    """Observatoire Immobilier Complet - 10 Sections"""
    
    COLORS = {
        'primary': '#1E40AF',
        'secondary': '#7C3AED',
        'success': '#059669',
        'warning': '#D97706',
        'danger': '#DC2626',
        'info': '#0891B2',
        'neutral': '#6B7280'
    }
    
    def __init__(self, server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[
                'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'
            ],
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix,
            suppress_callback_exceptions=True,
            meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
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
    
    def safe_get_data(self, property_type=None, limit=1000):
        """Récupération ultra-sécurisée des données"""
        try:
            db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty = self.safe_import_models()
            
            if not db:
                print("Impossible d'importer les modèles")
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
                        model.price > 0,
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
    
    def safe_calculate_kpi(self, df, property_type):
        """Calcul KPI ultra-sécurisé"""
        default_kpi = {
            'median_price': 0,
            'avg_price_m2': 0,
            'active_listings': 0,
            'median_surface': 0,
            'median_age': 0
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
            except:
                kpi['median_price'] = 0
            
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
            except:
                kpi['active_listings'] = 0
            
            # Surface médiane
            try:
                kpi['median_surface'] = float(df['surface_area'].median()) if df['surface_area'].notna().sum() > 0 else 0
            except:
                kpi['median_surface'] = 0
            
            # Âge médian
            try:
                if 'age_days' in df.columns:
                    kpi['median_age'] = float(df['age_days'].median()) if df['age_days'].notna().sum() > 0 else 0
                else:
                    kpi['median_age'] = 0
            except:
                kpi['median_age'] = 0
            
            return kpi
            
        except Exception as e:
            print(f"Erreur calcul KPI: {e}")
            return default_kpi
    
    # ==================== VISUALIZATIONS ====================
    
    def create_kpi_card(self, icon, label, value, color, suffix=""):
        """Carte KPI robuste"""
        try:
            return html.Div([
                html.Div([
                    DashIconify(icon=icon, width=32, color=color),
                ], style={'marginBottom': '8px'}),
                html.Div(label, style={'fontSize': '13px', 'color': '#6B7280', 'marginBottom': '4px'}),
                html.Div(f"{value:,.0f}{suffix}", 
                        style={'fontSize': '22px', 'fontWeight': 700, 'color': color})
            ], style={
                'background': 'white',
                'padding': '20px',
                'borderRadius': '12px',
                'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
                'textAlign': 'center',
                'border': '1px solid #E5E7EB'
            })
        except:
            return html.Div("Erreur KPI")
    
    def create_empty_figure(self, message="Aucune donnée disponible"):
        """Figure vide avec message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color='gray')
        )
        fig.update_layout(
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False)
        )
        return fig
    
    def create_section_1(self, df):
        """Section 1: Répartition par type"""
        try:
            if df.empty:
                return self.create_empty_figure()
            
            type_counts = df['property_type'].value_counts().head(8)
            
            fig = go.Figure(go.Bar(
                x=type_counts.index,
                y=type_counts.values,
                marker_color=self.COLORS['primary'],
                text=type_counts.values,
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Annonces: %{y}<extra></extra>'
            ))
            
            fig.update_layout(
                title='<b>Répartition par Type de Logement</b>',
                xaxis_title="Type",
                yaxis_title="Nombre d'annonces",
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12)
            )
            
            return fig
        except Exception as e:
            print(f"Erreur section 1: {e}")
            return self.create_empty_figure("Erreur de chargement")
    
    def create_section_2(self, df):
        """Section 2: Répartition par chambres"""
        try:
            if df.empty or df['bedrooms'].isna().all():
                return self.create_empty_figure()
            
            df_valid = df[df['bedrooms'].notna()]
            bedrooms_counts = df_valid.groupby(['property_type', 'bedrooms']).size().reset_index(name='count')
            
            fig = go.Figure()
            
            for ptype in bedrooms_counts['property_type'].unique()[:5]:
                data = bedrooms_counts[bedrooms_counts['property_type'] == ptype]
                fig.add_trace(go.Bar(
                    name=ptype,
                    x=data['bedrooms'],
                    y=data['count'],
                    hovertemplate=f'<b>{ptype}</b><br>Chambres: %{{x}}<br>Annonces: %{{y}}<extra></extra>'
                ))
            
            fig.update_layout(
                title='<b>Répartition par Nombre de Chambres</b>',
                barmode='stack',
                xaxis_title="Nombre de chambres",
                yaxis_title="Nombre d'annonces",
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12)
            )
            
            return fig
        except Exception as e:
            print(f"Erreur section 2: {e}")
            return self.create_empty_figure("Erreur de chargement")
    
    def create_section_3(self, df):
        """Section 3: Distribution des surfaces"""
        try:
            if df.empty or df['surface_area'].isna().all():
                return self.create_empty_figure()
            
            surfaces = df[df['surface_area'].notna()]['surface_area']
            
            fig = go.Figure(go.Histogram(
                x=surfaces,
                nbinsx=30,
                marker_color=self.COLORS['info'],
                hovertemplate='Surface: %{x:.0f}m²<br>Fréquence: %{y}<extra></extra>'
            ))
            
            fig.update_layout(
                title='<b>Distribution des Surfaces</b>',
                xaxis_title="Surface (m²)",
                yaxis_title="Fréquence",
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12)
            )
            
            return fig
        except Exception as e:
            print(f"Erreur section 3: {e}")
            return self.create_empty_figure("Erreur de chargement")
    
    def create_section_4(self, df):
        """Section 4: Box plot prix par type"""
        try:
            if df.empty:
                return self.create_empty_figure()
            
            types = df['property_type'].value_counts().head(6).index
            
            fig = go.Figure()
            
            for ptype in types:
                data = df[df['property_type'] == ptype]['price']
                fig.add_trace(go.Box(
                    y=data,
                    name=ptype,
                    boxmean='sd',
                    marker_color=self.COLORS['primary']
                ))
            
            fig.update_layout(
                title='<b>Distribution des Prix par Type</b>',
                yaxis_title="Prix (FCFA)",
                height=450,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12)
            )
            
            return fig
        except Exception as e:
            print(f"Erreur section 4: {e}")
            return self.create_empty_figure("Erreur de chargement")
    
    def create_section_5(self, df):
        """Section 5: Prix/m² par type"""
        try:
            if df.empty or 'price_per_m2' not in df.columns or df['price_per_m2'].isna().all():
                return self.create_empty_figure("Données prix/m² insuffisantes")
            
            df_valid = df[df['price_per_m2'].notna()]
            price_m2 = df_valid.groupby('property_type')['price_per_m2'].median().sort_values(ascending=True).head(10)
            
            fig = go.Figure(go.Bar(
                x=price_m2.values,
                y=price_m2.index,
                orientation='h',
                marker_color=self.COLORS['success'],
                text=[f'{x:,.0f}' for x in price_m2.values],
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Prix/m²: %{x:,.0f} FCFA<extra></extra>'
            ))
            
            fig.update_layout(
                title='<b>Prix Médian au m² par Type</b>',
                xaxis_title="Prix/m² (FCFA)",
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12)
            )
            
            return fig
        except Exception as e:
            print(f"Erreur section 5: {e}")
            return self.create_empty_figure("Erreur de chargement")
    
    def create_section_6(self, df):
        """Section 6: Top 10 villes (prix médian)"""
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
                marker_color=self.COLORS['danger'],
                text=[f'{x:,.0f}' for x in city_prices['median_price']],
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Prix médian: %{x:,.0f} FCFA<br>Annonces: %{customdata}<extra></extra>',
                customdata=city_prices['count']
            ))
            
            fig.update_layout(
                title='<b>Top 10 Zones les Plus Chères (Prix Médian)</b>',
                xaxis_title="Prix Médian (FCFA)",
                height=450,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12)
            )
            
            return fig
        except Exception as e:
            print(f"Erreur section 6: {e}")
            return self.create_empty_figure("Erreur de chargement")
    
    def create_section_7(self, df):
        """Section 7: Top 10 villes accessibles"""
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
                marker_color=self.COLORS['success'],
                text=[f'{x:,.0f}' for x in city_prices['median_price']],
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Prix médian: %{x:,.0f} FCFA<br>Annonces: %{customdata}<extra></extra>',
                customdata=city_prices['count']
            ))
            
            fig.update_layout(
                title='<b>Top 10 Zones les Plus Accessibles (Prix Médian)</b>',
                xaxis_title="Prix Médian (FCFA)",
                height=450,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12)
            )
            
            return fig
        except Exception as e:
            print(f"Erreur section 7: {e}")
            return self.create_empty_figure("Erreur de chargement")
    
    def create_section_8(self, df):
        """Section 8: Scatter prix vs surface"""
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
                    colorbar=dict(title="Prix"),
                    line=dict(width=1, color='white')
                ),
                text=[f"Surface: {s:.0f}m²<br>Prix: {p:,.0f} FCFA" 
                      for s, p in zip(df_valid['surface_area'], df_valid['price'])],
                hovertemplate='%{text}<extra></extra>'
            ))
            
            fig.update_layout(
                title='<b>Relation Surface - Prix</b>',
                xaxis_title="Surface (m²)",
                yaxis_title="Prix (FCFA)",
                height=450,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12)
            )
            
            return fig
        except Exception as e:
            print(f"Erreur section 8: {e}")
            return self.create_empty_figure("Erreur de chargement")
    
    def create_section_9(self, df):
        """Section 9: Distribution prix par tranches"""
        try:
            if df.empty:
                return self.create_empty_figure()
            
            # Définir tranches
            tranches = [
                (0, 10000000, "< 10M"),
                (10000000, 25000000, "10M - 25M"),
                (25000000, 50000000, "25M - 50M"),
                (50000000, 100000000, "50M - 100M"),
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
                marker_color=self.COLORS['warning'],
                text=counts,
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Annonces: %{y}<extra></extra>'
            ))
            
            fig.update_layout(
                title='<b>Distribution par Tranche de Prix</b>',
                xaxis_title="Tranche de prix (FCFA)",
                yaxis_title="Nombre d'annonces",
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12)
            )
            
            return fig
        except Exception as e:
            print(f"Erreur section 9: {e}")
            return self.create_empty_figure("Erreur de chargement")
    
    def create_section_10(self, df):
        """Section 10: Statistiques par ville (table)"""
        try:
            if df.empty:
                return html.Div("Aucune donnée disponible")
            
            city_stats = df.groupby('city').agg({
                'price': ['median', 'count'],
                'surface_area': 'median'
            }).reset_index()
            
            city_stats.columns = ['city', 'median_price', 'count', 'median_surface']
            city_stats = city_stats[city_stats['count'] >= 2]
            city_stats = city_stats.sort_values('median_price', ascending=False).head(15)
            
            # Calculer prix/m²
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
                    'fontSize': '14px'
                },
                style_header={
                    'backgroundColor': '#F3F4F6',
                    'fontWeight': 600,
                    'color': self.COLORS['primary'],
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
            print(f"Erreur section 10: {e}")
            return html.Div(f"Erreur: {str(e)}")
    
    # ==================== LAYOUT ====================
    
    def setup_layout(self):
        """Layout complet du dashboard"""
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.Div([
                    html.Div([
                        DashIconify(icon="mdi:office-building", width=56, color="white"),
                        html.Div([
                            html.H1("OBSERVATOIRE IMMOBILIER", 
                                   style={'margin': 0, 'fontSize': '36px', 'fontWeight': 700, 'color': 'white'}),
                            html.P("Lecture Institutionnelle - Analyse Descriptive Pure", 
                                  style={'margin': 0, 'fontSize': '16px', 'color': 'rgba(255,255,255,0.9)'})
                        ], style={'marginLeft': '20px'})
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                    
                    html.Div([
                        dmc.Select(
                            id='property-type-selector',
                            data=[
                                {'label': 'Tous les types', 'value': 'Tous'},
                                {'label': 'Appartement', 'value': 'Appartement'},
                                {'label': 'Villa', 'value': 'Villa'},
                                {'label': 'Studio', 'value': 'Studio'},
                                {'label': 'Maison', 'value': 'Maison'},
                                {'label': 'Duplex', 'value': 'Duplex'}
                            ],
                            value='Tous',
                            style={'width': '250px', 'background': 'white'},
                            size="lg"
                        )
                    ])
                ], style={
                    'display': 'flex',
                    'justifyContent': 'space-between',
                    'alignItems': 'center',
                    'maxWidth': '1400px',
                    'margin': '0 auto',
                    'padding': '32px 24px'
                })
            ], style={
                'background': f'linear-gradient(135deg, {self.COLORS["primary"]} 0%, {self.COLORS["secondary"]} 100%)',
                'marginBottom': '32px'
            }),
            
            # Contenu
            html.Div([
                # Section 0: KPI Header
                html.Div(id='kpi-header', style={'marginBottom': '32px'}),
                
                # Note méthodologique
                html.Div([
                    html.H2("📋 Règles Méthodologiques", 
                           style={'color': self.COLORS['primary'], 'marginBottom': '16px', 'fontSize': '20px'}),
                    html.Ul([
                        html.Li("✓ Tous les indicateurs sont segmentés par type de logement"),
                        html.Li("✓ Les prix globaux tous biens confondus ne sont pas affichés"),
                        html.Li("✓ Données issues d'annonces observées sur le marché"),
                        html.Li("✓ Analyse descriptive uniquement - pas de prédiction"),
                        html.Li("✓ Médiane privilégiée pour éviter l'influence des valeurs extrêmes"),
                        html.Li("✓ Quartiles (P25, P75) utilisés pour mesurer la dispersion"),
                        html.Li("✓ Zones avec moins de 3 annonces exclues de l'analyse territoriale"),
                    ], style={'fontSize': '14px', 'lineHeight': '1.8', 'color': '#374151'})
                ], style={
                    'background': '#FEF3C7',
                    'padding': '24px',
                    'borderRadius': '12px',
                    'border': '2px solid #F59E0B',
                    'marginBottom': '32px'
                }),
                
                # Section 1: Structure de l'offre
                html.Div(id='section-1', style={'marginBottom': '32px'}),
                
                # Section 2: Répartition chambres
                html.Div(id='section-2', style={'marginBottom': '32px'}),
                
                # Section 3: Distribution surfaces
                html.Div(id='section-3', style={'marginBottom': '32px'}),
                
                # Section 4: Niveau des prix
                html.Div(id='section-4', style={'marginBottom': '32px'}),
                
                # Section 5: Prix/m²
                html.Div(id='section-5', style={'marginBottom': '32px'}),
                
                # Section 6 & 7: Analyse territoriale
                html.Div([
                    html.H2("🟦 5. Analyse Territoriale", 
                           style={'color': self.COLORS['primary'], 'marginBottom': '20px'}),
                    html.Div([
                        html.Div(id='section-6', style={'flex': '1'}),
                        html.Div(id='section-7', style={'flex': '1'})
                    ], style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap'})
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '12px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
                    'marginBottom': '32px'
                }),
                
                # Section 8: Dispersion
                html.Div(id='section-8', style={'marginBottom': '32px'}),
                
                # Section 9: Tranches de prix
                html.Div(id='section-9', style={'marginBottom': '32px'}),
                
                # Section 10: Table statistiques
                html.Div([
                    html.H2("🟦 8. Statistiques par Zone", 
                           style={'color': self.COLORS['primary'], 'marginBottom': '20px'}),
                    html.Div(id='section-10')
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '12px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
                    'marginBottom': '32px'
                }),
                
                # Footer
                html.Div([
                    html.P("📊 Observatoire Immobilier - ENSAE Dakar © 2024", 
                          style={'textAlign': 'center', 'color': '#6B7280', 'fontSize': '14px'})
                ], style={'marginTop': '48px', 'paddingTop': '24px', 'borderTop': '1px solid #E5E7EB'})
                
            ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 24px'})
        ], style={
            'fontFamily': "'Inter', sans-serif",
            'background': '#F9FAFB',
            'minHeight': '100vh'
        })
    
    # ==================== CALLBACKS ====================
    
    def setup_callbacks(self):
        """Callbacks ultra-robustes"""
        
        @callback(
            [
                Output('kpi-header', 'children'),
                Output('section-1', 'children'),
                Output('section-2', 'children'),
                Output('section-3', 'children'),
                Output('section-4', 'children'),
                Output('section-5', 'children'),
                Output('section-6', 'children'),
                Output('section-7', 'children'),
                Output('section-8', 'children'),
                Output('section-9', 'children'),
                Output('section-10', 'children')
            ],
            Input('property-type-selector', 'value')
        )
        def update_all_sections(property_type):
            """Mettre à jour toutes les sections"""
            try:
                # Charger données
                df = self.safe_get_data(property_type)
                kpi = self.safe_calculate_kpi(df, property_type)
                
                # KPI Header
                kpi_header = html.Div([
                    html.H3(f"Type analysé : {property_type}", 
                           style={'color': self.COLORS['primary'], 'marginBottom': '24px', 
                                 'fontSize': '20px', 'fontWeight': 600}),
                    html.Div([
                        self.create_kpi_card("mdi:currency-usd", "Prix Médian", 
                                           kpi['median_price'], self.COLORS['primary'], " FCFA"),
                        self.create_kpi_card("mdi:ruler-square", "Prix Moyen/m²", 
                                           kpi['avg_price_m2'], self.COLORS['success'], " FCFA"),
                        self.create_kpi_card("mdi:file-document-multiple", "Annonces Actives", 
                                           kpi['active_listings'], self.COLORS['info']),
                        self.create_kpi_card("mdi:tape-measure", "Surface Médiane", 
                                           kpi['median_surface'], self.COLORS['warning'], " m²"),
                        self.create_kpi_card("mdi:calendar-clock", "Âge Médian", 
                                           kpi['median_age'], self.COLORS['secondary'], " jours"),
                    ], style={
                        'display': 'grid',
                        'gridTemplateColumns': 'repeat(auto-fit, minmax(180px, 1fr))',
                        'gap': '16px'
                    })
                ])
                
                # Section 1
                section_1 = html.Div([
                    html.H2("🟦 2. Structure de l'Offre", 
                           style={'color': self.COLORS['primary'], 'marginBottom': '20px'}),
                    dcc.Graph(figure=self.create_section_1(df), config={'displayModeBar': False})
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '12px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
                })
                
                # Section 2
                section_2 = html.Div([
                    dcc.Graph(figure=self.create_section_2(df), config={'displayModeBar': False})
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '12px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
                })
                
                # Section 3
                section_3 = html.Div([
                    dcc.Graph(figure=self.create_section_3(df), config={'displayModeBar': False})
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '12px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
                })
                
                # Section 4
                section_4 = html.Div([
                    html.H2("🟦 3. Niveau des Prix (Segmenté)", 
                           style={'color': self.COLORS['primary'], 'marginBottom': '20px'}),
                    dcc.Graph(figure=self.create_section_4(df), config={'displayModeBar': False})
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '12px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
                })
                
                # Section 5
                section_5 = html.Div([
                    html.H2("🟦 4. Prix au m² (Référence Économique)", 
                           style={'color': self.COLORS['primary'], 'marginBottom': '20px'}),
                    dcc.Graph(figure=self.create_section_5(df), config={'displayModeBar': False})
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '12px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
                })
                
                # Section 6
                section_6 = html.Div([
                    dcc.Graph(figure=self.create_section_6(df), config={'displayModeBar': False})
                ], style={
                    'background': 'white',
                    'padding': '16px',
                    'borderRadius': '12px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
                })
                
                # Section 7
                section_7 = html.Div([
                    dcc.Graph(figure=self.create_section_7(df), config={'displayModeBar': False})
                ], style={
                    'background': 'white',
                    'padding': '16px',
                    'borderRadius': '12px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
                })
                
                # Section 8
                section_8 = html.Div([
                    html.H2("🟦 6. Dispersion & Hétérogénéité", 
                           style={'color': self.COLORS['primary'], 'marginBottom': '20px'}),
                    dcc.Graph(figure=self.create_section_8(df), config={'displayModeBar': False})
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '12px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
                })
                
                # Section 9
                section_9 = html.Div([
                    html.H2("🟦 7. Accessibilité & Gammes de Prix", 
                           style={'color': self.COLORS['primary'], 'marginBottom': '20px'}),
                    dcc.Graph(figure=self.create_section_9(df), config={'displayModeBar': False})
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '12px',
                    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
                })
                
                # Section 10
                section_10 = self.create_section_10(df)
                
                return (
                    kpi_header,
                    section_1,
                    section_2,
                    section_3,
                    section_4,
                    section_5,
                    section_6,
                    section_7,
                    section_8,
                    section_9,
                    section_10
                )
                
            except Exception as e:
                print(f"Erreur callback principal: {e}")
                traceback.print_exc()
                
                # Message d'erreur
                error_msg = html.Div([
                    html.H3("⚠️ Erreur de Chargement", style={'color': '#DC2626'}),
                    html.P(f"Une erreur s'est produite: {str(e)}", style={'color': '#6B7280'}),
                    html.P("Veuillez réessayer ou contacter l'administrateur.", 
                          style={'color': '#6B7280', 'fontSize': '14px'})
                ], style={
                    'background': '#FEE2E2',
                    'padding': '24px',
                    'borderRadius': '12px',
                    'border': '2px solid #DC2626',
                    'textAlign': 'center'
                })
                
                empty = html.Div()
                
                return (error_msg, empty, empty, empty, empty, empty, empty, empty, empty, empty, empty)


def create_observatoire_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    """Factory function"""
    dashboard = ObservatoireComplet(
        server=server,
        routes_pathname_prefix=routes_pathname_prefix,
        requests_pathname_prefix=requests_pathname_prefix
    )
    return dashboard.app