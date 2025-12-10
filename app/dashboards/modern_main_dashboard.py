"""
🟦 OBSERVATOIRE IMMOBILIER - DASHBOARD INSTITUTIONNEL
Analyse Descriptive Pure & Segmentée par Type de Logement
Auteur: Cos - ENSAE Dakar
"""

import dash
from dash import html, dcc, Input, Output, State, callback, dash_table
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import func
from ..database.models import db, CoinAfrique, ExpatDakarProperty, LogerDakarProperty


class ObservatoireImmobilier:
    """Observatoire Immobilier - Lecture Institutionnelle"""
    
    COLORS = {
        'primary': '#1E40AF',
        'secondary': '#7C3AED',
        'success': '#059669',
        'warning': '#D97706',
        'danger': '#DC2626',
        'info': '#0891B2',
        'neutral': '#6B7280'
    }
    
    PROPERTY_TYPES = [
        'Appartement', 'Villa', 'Studio', 'Duplex', 
        'Maison', 'Terrain', 'Bureaux', 'Autre'
    ]
    
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
    
    def get_consolidated_data(self, property_type=None):
        """Récupérer données consolidées avec filtrage optionnel"""
        try:
            all_data = []
            
            for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
                query = db.session.query(
                    model.city,
                    model.property_type,
                    model.price,
                    model.surface_area,
                    model.bedrooms,
                    model.bathrooms,
                    model.scraped_at
                ).filter(model.price > 1000, model.price < 1e10)
                
                if property_type and property_type != "Tous":
                    query = query.filter(model.property_type == property_type)
                
                records = query.all()
                
                for r in records:
                    if r.scraped_at:
                        age_days = (datetime.utcnow() - r.scraped_at).days
                    else:
                        age_days = None
                    
                    all_data.append({
                        'city': r.city,
                        'property_type': r.property_type,
                        'price': float(r.price) if r.price else 0,
                        'surface_area': float(r.surface_area) if r.surface_area else None,
                        'bedrooms': int(r.bedrooms) if r.bedrooms else None,
                        'bathrooms': int(r.bathrooms) if r.bathrooms else None,
                        'scraped_at': r.scraped_at,
                        'age_days': age_days
                    })
            
            df = pd.DataFrame(all_data)
            
            # Ajouter prix/m²
            if not df.empty and 'surface_area' in df.columns:
                df['price_per_m2'] = df.apply(
                    lambda x: x['price'] / x['surface_area'] if x['surface_area'] and x['surface_area'] > 0 else None,
                    axis=1
                )
            
            return df
        except Exception as e:
            print(f"Erreur chargement données: {e}")
            return pd.DataFrame()
    
    def calculate_kpi_segmented(self, df, property_type):
        """KPI segmentés par type de logement"""
        if df.empty:
            return {
                'median_price': 0,
                'avg_price_m2': 0,
                'active_listings': 0,
                'median_surface': 0,
                'median_age': 0
            }
        
        # Filtrer par type si spécifié
        if property_type and property_type != "Tous":
            df = df[df['property_type'] == property_type]
        
        kpi = {
            'median_price': df['price'].median() if len(df) > 0 else 0,
            'avg_price_m2': df['price_per_m2'].mean() if 'price_per_m2' in df.columns and df['price_per_m2'].notna().sum() > 0 else 0,
            'active_listings': len(df),
            'median_surface': df['surface_area'].median() if df['surface_area'].notna().sum() > 0 else 0,
            'median_age': df['age_days'].median() if 'age_days' in df.columns and df['age_days'].notna().sum() > 0 else 0
        }
        
        return kpi
    
    # ==================== VISUALIZATIONS ====================
    
    def create_kpi_header(self, kpi, property_type):
        """Bandeau KPI institutionnel"""
        kpi_style = {
            'background': 'white',
            'padding': '20px',
            'borderRadius': '12px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
            'textAlign': 'center',
            'border': '1px solid #E5E7EB'
        }
        
        return html.Div([
            html.Div([
                html.H3(f"Type analysé : {property_type}", 
                       style={'color': self.COLORS['primary'], 'marginBottom': '24px', 
                             'fontSize': '20px', 'fontWeight': 600}),
                
                html.Div([
                    # KPI 1
                    html.Div([
                        html.Div([
                            DashIconify(icon="mdi:currency-usd", width=32, color=self.COLORS['primary']),
                        ], style={'marginBottom': '8px'}),
                        html.Div("Prix Médian", style={'fontSize': '13px', 'color': '#6B7280', 'marginBottom': '4px'}),
                        html.Div(f"{kpi['median_price']:,.0f} FCFA", 
                                style={'fontSize': '22px', 'fontWeight': 700, 'color': self.COLORS['primary']})
                    ], style=kpi_style),
                    
                    # KPI 2
                    html.Div([
                        html.Div([
                            DashIconify(icon="mdi:ruler-square", width=32, color=self.COLORS['success']),
                        ], style={'marginBottom': '8px'}),
                        html.Div("Prix Moyen/m²", style={'fontSize': '13px', 'color': '#6B7280', 'marginBottom': '4px'}),
                        html.Div(f"{kpi['avg_price_m2']:,.0f} FCFA", 
                                style={'fontSize': '22px', 'fontWeight': 700, 'color': self.COLORS['success']})
                    ], style=kpi_style),
                    
                    # KPI 3
                    html.Div([
                        html.Div([
                            DashIconify(icon="mdi:file-document-multiple", width=32, color=self.COLORS['info']),
                        ], style={'marginBottom': '8px'}),
                        html.Div("Annonces Actives", style={'fontSize': '13px', 'color': '#6B7280', 'marginBottom': '4px'}),
                        html.Div(f"{kpi['active_listings']:,}", 
                                style={'fontSize': '22px', 'fontWeight': 700, 'color': self.COLORS['info']})
                    ], style=kpi_style),
                    
                    # KPI 4
                    html.Div([
                        html.Div([
                            DashIconify(icon="mdi:tape-measure", width=32, color=self.COLORS['warning']),
                        ], style={'marginBottom': '8px'}),
                        html.Div("Surface Médiane", style={'fontSize': '13px', 'color': '#6B7280', 'marginBottom': '4px'}),
                        html.Div(f"{kpi['median_surface']:.0f} m²", 
                                style={'fontSize': '22px', 'fontWeight': 700, 'color': self.COLORS['warning']})
                    ], style=kpi_style),
                    
                    # KPI 5
                    html.Div([
                        html.Div([
                            DashIconify(icon="mdi:calendar-clock", width=32, color=self.COLORS['secondary']),
                        ], style={'marginBottom': '8px'}),
                        html.Div("Âge Médian", style={'fontSize': '13px', 'color': '#6B7280', 'marginBottom': '4px'}),
                        html.Div(f"{kpi['median_age']:.0f} jours", 
                                style={'fontSize': '22px', 'fontWeight': 700, 'color': self.COLORS['secondary']})
                    ], style=kpi_style),
                    
                ], style={
                    'display': 'grid',
                    'gridTemplateColumns': 'repeat(auto-fit, minmax(180px, 1fr))',
                    'gap': '16px'
                })
            ])
        ], style={'marginBottom': '32px'})
    
    def create_offer_structure(self, df):
        """Section 2: Structure de l'offre"""
        if df.empty:
            return html.Div("Pas de données disponibles")
        
        # Graphique 1: Répartition par type
        type_dist = df['property_type'].value_counts().reset_index()
        type_dist.columns = ['Type', 'Count']
        type_dist['Percentage'] = (type_dist['Count'] / type_dist['Count'].sum() * 100).round(1)
        
        fig1 = go.Figure(go.Bar(
            x=type_dist['Type'],
            y=type_dist['Count'],
            marker_color=self.COLORS['primary'],
            text=type_dist['Count'],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Annonces: %{y}<extra></extra>'
        ))
        
        fig1.update_layout(
            title=dict(text='<b>Répartition par Type de Logement</b>', x=0.5),
            xaxis_title="Type",
            yaxis_title="Nombre d'annonces",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', size=12)
        )
        
        # Graphique 2: Répartition par chambres
        bedrooms_data = df[df['bedrooms'].notna()].groupby(['property_type', 'bedrooms']).size().reset_index(name='count')
        
        fig2 = go.Figure()
        for ptype in bedrooms_data['property_type'].unique()[:5]:  # Top 5 types
            data = bedrooms_data[bedrooms_data['property_type'] == ptype]
            fig2.add_trace(go.Bar(
                name=ptype,
                x=data['bedrooms'],
                y=data['count'],
                hovertemplate=f'<b>{ptype}</b><br>Chambres: %{{x}}<br>Annonces: %{{y}}<extra></extra>'
            ))
        
        fig2.update_layout(
            title=dict(text='<b>Répartition par Nombre de Chambres</b>', x=0.5),
            barmode='stack',
            xaxis_title="Nombre de chambres",
            yaxis_title="Nombre d'annonces",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', size=12)
        )
        
        # Graphique 3: Distribution des surfaces
        surfaces = df[df['surface_area'].notna() & (df['surface_area'] > 0)]['surface_area']
        
        fig3 = go.Figure(go.Histogram(
            x=surfaces,
            nbinsx=30,
            marker_color=self.COLORS['info'],
            hovertemplate='Surface: %{x:.0f}m²<br>Fréquence: %{y}<extra></extra>'
        ))
        
        fig3.update_layout(
            title=dict(text='<b>Distribution des Surfaces</b>', x=0.5),
            xaxis_title="Surface (m²)",
            yaxis_title="Fréquence",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', size=12)
        )
        
        # Table synthétique
        table_data = df.groupby('property_type').agg({
            'property_type': 'count',
            'surface_area': 'median'
        }).reset_index()
        table_data.columns = ['Type', 'Nb_annonces', 'Surface_mediane']
        table_data['Pourcentage'] = (table_data['Nb_annonces'] / table_data['Nb_annonces'].sum() * 100).round(1)
        table_data = table_data.sort_values('Nb_annonces', ascending=False)
        
        return html.Div([
            html.H2("🟦 2. Structure de l'Offre", 
                   style={'color': self.COLORS['primary'], 'marginBottom': '20px'}),
            
            html.Div([
                html.Div([dcc.Graph(figure=fig1, config={'displayModeBar': False})], 
                        style={'flex': '1'}),
                html.Div([dcc.Graph(figure=fig2, config={'displayModeBar': False})], 
                        style={'flex': '1'}),
            ], style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px', 'flexWrap': 'wrap'}),
            
            html.Div([dcc.Graph(figure=fig3, config={'displayModeBar': False})], 
                    style={'marginBottom': '20px'}),
            
            dash_table.DataTable(
                data=table_data.to_dict('records'),
                columns=[
                    {'name': 'Type de Logement', 'id': 'Type'},
                    {'name': 'Nb Annonces', 'id': 'Nb_annonces', 'type': 'numeric', 'format': {'specifier': ','}},
                    {'name': 'Surface Médiane (m²)', 'id': 'Surface_mediane', 'type': 'numeric', 'format': {'specifier': '.0f'}},
                    {'name': '% du Total', 'id': 'Pourcentage', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                ],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '12px', 'fontFamily': 'Inter'},
                style_header={'backgroundColor': '#F3F4F6', 'fontWeight': 600, 'color': self.COLORS['primary']},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#F9FAFB'}
                ]
            )
        ], style={
            'background': 'white',
            'padding': '24px',
            'borderRadius': '12px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
            'marginBottom': '32px'
        })
    
    def create_price_levels(self, df):
        """Section 3: Niveau des prix (segmenté)"""
        if df.empty:
            return html.Div("Pas de données disponibles")
        
        # Boxplot par type
        fig1 = go.Figure()
        
        types = df['property_type'].value_counts().head(8).index
        for ptype in types:
            data = df[df['property_type'] == ptype]['price']
            fig1.add_trace(go.Box(
                y=data,
                name=ptype,
                boxmean='sd',
                marker_color=self.COLORS['primary']
            ))
        
        fig1.update_layout(
            title=dict(text='<b>Distribution des Prix par Type</b>', x=0.5),
            yaxis_title="Prix (FCFA)",
            height=450,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', size=12)
        )
        
        # Table statistiques prix
        price_stats = df.groupby('property_type')['price'].agg([
            ('median', 'median'),
            ('p25', lambda x: x.quantile(0.25)),
            ('p75', lambda x: x.quantile(0.75)),
            ('max', 'max')
        ]).reset_index()
        price_stats = price_stats.sort_values('median', ascending=False)
        
        return html.Div([
            html.H2("🟦 3. Niveau des Prix (Segmenté)", 
                   style={'color': self.COLORS['primary'], 'marginBottom': '20px'}),
            
            dcc.Graph(figure=fig1, config={'displayModeBar': False}, style={'marginBottom': '20px'}),
            
            dash_table.DataTable(
                data=price_stats.to_dict('records'),
                columns=[
                    {'name': 'Type', 'id': 'property_type'},
                    {'name': 'Prix Médian', 'id': 'median', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                    {'name': 'P25', 'id': 'p25', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                    {'name': 'P75', 'id': 'p75', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                    {'name': 'Prix Max', 'id': 'max', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                ],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '12px', 'fontFamily': 'Inter'},
                style_header={'backgroundColor': '#F3F4F6', 'fontWeight': 600, 'color': self.COLORS['primary']},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#F9FAFB'}
                ]
            )
        ], style={
            'background': 'white',
            'padding': '24px',
            'borderRadius': '12px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
            'marginBottom': '32px'
        })
    
    def create_price_per_m2_analysis(self, df):
        """Section 4: Prix au m² (référence économique)"""
        if df.empty or 'price_per_m2' not in df.columns:
            return html.Div("Pas de données disponibles")
        
        df_valid = df[df['price_per_m2'].notna() & (df['price_per_m2'] > 0)]
        
        if df_valid.empty:
            return html.Div("Données insuffisantes pour l'analyse prix/m²")
        
        # Prix/m² par type
        price_m2_by_type = df_valid.groupby('property_type')['price_per_m2'].median().sort_values(ascending=True)
        
        fig1 = go.Figure(go.Bar(
            x=price_m2_by_type.values,
            y=price_m2_by_type.index,
            orientation='h',
            marker_color=self.COLORS['success'],
            text=[f'{x:,.0f}' for x in price_m2_by_type.values],
            textposition='outside'
        ))
        
        fig1.update_layout(
            title=dict(text='<b>Prix Médian au m² par Type</b>', x=0.5),
            xaxis_title="Prix/m² (FCFA)",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', size=12)
        )
        
        # Boxplot dispersion
        fig2 = go.Figure()
        for ptype in price_m2_by_type.index[-6:]:  # Top 6
            data = df_valid[df_valid['property_type'] == ptype]['price_per_m2']
            fig2.add_trace(go.Box(
                y=data,
                name=ptype,
                marker_color=self.COLORS['success']
            ))
        
        fig2.update_layout(
            title=dict(text='<b>Dispersion Prix/m²</b>', x=0.5),
            yaxis_title="Prix/m² (FCFA)",
            height=400,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', size=12)
        )
        
        # Table
        price_m2_stats = df_valid.groupby('property_type')['price_per_m2'].agg([
            ('median', 'median'),
            ('p25', lambda x: x.quantile(0.25)),
            ('p75', lambda x: x.quantile(0.75))
        ]).reset_index()
        price_m2_stats = price_m2_stats.sort_values('median', ascending=False)
        
        return html.Div([
            html.H2("🟦 4. Prix au m² (Référence Économique)", 
                   style={'color': self.COLORS['primary'], 'marginBottom': '20px'}),
            
            html.Div([
                html.Div([dcc.Graph(figure=fig1, config={'displayModeBar': False})], style={'flex': '1'}),
                html.Div([dcc.Graph(figure=fig2, config={'displayModeBar': False})], style={'flex': '1'}),
            ], style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px', 'flexWrap': 'wrap'}),
            
            dash_table.DataTable(
                data=price_m2_stats.to_dict('records'),
                columns=[
                    {'name': 'Type', 'id': 'property_type'},
                    {'name': 'Prix/m² Médian', 'id': 'median', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                    {'name': 'P25', 'id': 'p25', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                    {'name': 'P75', 'id': 'p75', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                ],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '12px', 'fontFamily': 'Inter'},
                style_header={'backgroundColor': '#F3F4F6', 'fontWeight': 600, 'color': self.COLORS['primary']},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#F9FAFB'}
                ]
            )
        ], style={
            'background': 'white',
            'padding': '24px',
            'borderRadius': '12px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
            'marginBottom': '32px'
        })
    
    def create_territorial_analysis(self, df):
        """Section 5: Analyse territoriale"""
        if df.empty or df['city'].isna().all():
            return html.Div("Pas de données géographiques disponibles")
        
        # Prix médian par zone
        city_prices = df.groupby('city').agg({
            'price': 'median',
            'price_per_m2': 'median',
            'city': 'count'
        }).reset_index()
        city_prices.columns = ['city', 'median_price', 'median_price_m2', 'count']
        city_prices = city_prices[city_prices['count'] >= 5]  # Au moins 5 annonces
        
        # Top 10 plus chères
        top_expensive = city_prices.nlargest(10, 'median_price_m2')
        
        fig1 = go.Figure(go.Bar(
            x=top_expensive['median_price_m2'],
            y=top_expensive['city'],
            orientation='h',
            marker_color=self.COLORS['danger'],
            text=[f'{x:,.0f}' for x in top_expensive['median_price_m2']],
            textposition='outside'
        ))
        
        fig1.update_layout(
            title=dict(text='<b>Top 10 Zones les Plus Chères (Prix/m²)</b>', x=0.5),
            xaxis_title="Prix/m² médian (FCFA)",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', size=12)
        )
        
        # Top 10 plus accessibles
        top_accessible = city_prices.nsmallest(10, 'median_price_m2')
        
        fig2 = go.Figure(go.Bar(
            x=top_accessible['median_price_m2'],
            y=top_accessible['city'],
            orientation='h',
            marker_color=self.COLORS['success'],
            text=[f'{x:,.0f}' for x in top_accessible['median_price_m2']],
            textposition='outside'
        ))
        
        fig2.update_layout(
            title=dict(text='<b>Top 10 Zones les Plus Accessibles (Prix/m²)</b>', x=0.5),
            xaxis_title="Prix/m² médian (FCFA)",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', size=12)
        )
        
        # Table
        city_table = city_prices.sort_values('median_price', ascending=False).head(15)
        
        return html.Div([
            html.H2("🟦 5. Analyse Territoriale", 
                   style={'color': self.COLORS['primary'], 'marginBottom': '20px'}),
            
            html.Div([
                html.Div([dcc.Graph(figure=fig1, config={'displayModeBar': False})], style={'flex': '1'}),
                html.Div([dcc.Graph(figure=fig2, config={'displayModeBar': False})], style={'flex': '1'}),
            ], style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px', 'flexWrap': 'wrap'}),
            
            dash_table.DataTable(
                data=city_table.to_dict('records'),
                columns=[
                    {'name': 'Zone', 'id': 'city'},
                    {'name': 'Prix Médian', 'id': 'median_price', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                    {'name': 'Prix/m²', 'id': 'median_price_m2', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                    {'name': 'Nb Annonces', 'id': 'count', 'type': 'numeric'},
                ],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '12px', 'fontFamily': 'Inter'},
                style_header={'backgroundColor': '#F3F4F6', 'fontWeight': 600, 'color': self.COLORS['primary']},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#F9FAFB'}
                ]
            )
        ], style={
            'background': 'white',
            'padding': '24px',
            'borderRadius': '12px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
            'marginBottom': '32px'
        })
    
    def create_methodological_note(self):
        """Note méthodologique institutionnelle"""
        return html.Div([
            html.H2("📋 Règles Méthodologiques", 
                   style={'color': self.COLORS['primary'], 'marginBottom': '20px'}),
            
            html.Ul([
                html.Li("✓ Tous les indicateurs sont segmentés par type de logement"),
                html.Li("✓ Les prix globaux tous biens confondus ne sont pas affichés"),
                html.Li("✓ Données issues d'annonces observées sur le marché"),
                html.Li("✓ Analyse descriptive uniquement - pas de prédiction"),
                html.Li("✓ Médiane privilégiée pour éviter l'influence des valeurs extrêmes"),
                html.Li("✓ Quartiles (P25, P75) utilisés pour mesurer la dispersion"),
                html.Li("✓ Zones avec moins de 5 annonces exclues de l'analyse territoriale"),
            ], style={'fontSize': '14px', 'lineHeight': '1.8', 'color': '#374151'})
        ], style={
            'background': '#FEF3C7',
            'padding': '24px',
            'borderRadius': '12px',
            'border': '2px solid #F59E0B',
            'marginBottom': '32px'
        })
    
    # ==================== LAYOUT ====================
    
    def setup_layout(self):
        """Layout principal de l'observatoire"""
        df = self.get_consolidated_data()
        default_type = "Tous"
        kpi = self.calculate_kpi_segmented(df, default_type)
        
        self.app.layout = html.Div([
            # Header institutionnel
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
                            data=[{'label': 'Tous les types', 'value': 'Tous'}] + 
                                 [{'label': pt, 'value': pt} for pt in self.PROPERTY_TYPES],
                            value=default_type,
                            style={'width': '250px'},
                            icon=DashIconify(icon="mdi:home-variant"),
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
            
            # Contenu principal
            html.Div([
                # Section 1: KPI Header
                html.Div(id='kpi-header'),
                
                # Note méthodologique
                self.create_methodological_note(),
                
                # Sections dynamiques
                html.Div(id='offer-structure'),
                html.Div(id='price-levels'),
                html.Div(id='price-per-m2'),
                html.Div(id='territorial-analysis'),
                
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
    
    def setup_callbacks(self):
        """Callbacks pour l'interactivité"""
        
        @callback(
            [
                Output('kpi-header', 'children'),
                Output('offer-structure', 'children'),
                Output('price-levels', 'children'),
                Output('price-per-m2', 'children'),
                Output('territorial-analysis', 'children')
            ],
            Input('property-type-selector', 'value')
        )
        def update_all_sections(property_type):
            """Mettre à jour toutes les sections selon le type sélectionné"""
            df = self.get_consolidated_data(property_type)
            kpi = self.calculate_kpi_segmented(df, property_type)
            
            return (
                self.create_kpi_header(kpi, property_type),
                self.create_offer_structure(df),
                self.create_price_levels(df),
                self.create_price_per_m2_analysis(df),
                self.create_territorial_analysis(df)
            )


def create_observatoire_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    """Factory pour créer l'observatoire"""
    dashboard = ObservatoireImmobilier(
        server=server,
        routes_pathname_prefix=routes_pathname_prefix,
        requests_pathname_prefix=requests_pathname_prefix
    )
    return dashboard.app