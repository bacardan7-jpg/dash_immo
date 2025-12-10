"""
Dashboard Immobilier Ultra-Complet - Maximum d'Informations
Interface Moderne et Lisible
Auteur: Cos - ENSAE Dakar
"""

import dash
from dash import html, dcc, Input, Output, State, callback
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


class CompleteDashboard:
    """Dashboard Complet avec Maximum d'Informations"""
    
    def __init__(self, server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[
                'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap'
            ],
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix,
            suppress_callback_exceptions=True,
            meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
        )
        
        # Définir les styles CSS personnalisés
        self.custom_css = {
            'body': {
                'fontFamily': "'Inter', sans-serif",
                'background': 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
                'margin': '0'
            },
            '.kpi-hover': {
                'transition': 'transform 0.2s, box-shadow 0.2s'
            },
            '.chart-container': {
                'background': 'white',
                'padding': '24px',
                'borderRadius': '16px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
                'marginBottom': '24px'
            }
        }
        
        if server:
            with server.app_context():
                self.setup_layout()
                self.setup_callbacks()
    
    def get_all_data(self):
        """Récupérer toutes les données consolidées"""
        try:
            all_data = []
            
            for model in [CoinAfrique, ExpatDakarProperty, LogerDakarProperty]:
                records = db.session.query(
                    model.city,
                    model.property_type,
                    model.price,
                    model.surface_area,
                    model.bedrooms,
                    model.bathrooms,
                    model.scraped_at
                ).filter(model.price > 0).all()
                
                for r in records:
                    all_data.append({
                        'city': r.city,
                        'property_type': r.property_type,
                        'price': float(r.price) if r.price else 0,
                        'surface_area': float(r.surface_area) if r.surface_area else 0,
                        'bedrooms': int(r.bedrooms) if r.bedrooms else 0,
                        'bathrooms': int(r.bathrooms) if r.bathrooms else 0,
                        'scraped_at': r.scraped_at
                    })
            
            return pd.DataFrame(all_data)
        except Exception as e:
            print(f"Erreur data: {e}")
            return pd.DataFrame()
    
    def calculate_comprehensive_stats(self, df):
        """Calculer toutes les statistiques possibles"""
        if df.empty:
            return {}
        
        # Prix
        prices = df['price'][df['price'] > 0]
        
        # Surface
        surfaces = df['surface_area'][df['surface_area'] > 0]
        
        # Prix par m²
        df_valid = df[(df['price'] > 0) & (df['surface_area'] > 0)]
        price_per_m2 = df_valid['price'] / df_valid['surface_area']
        
        stats = {
            # Totaux
            'total_properties': len(df),
            'total_cities': df['city'].nunique() if 'city' in df.columns else 0,
            'total_types': df['property_type'].nunique() if 'property_type' in df.columns else 0,
            
            # Prix
            'avg_price': prices.mean() if len(prices) > 0 else 0,
            'median_price': prices.median() if len(prices) > 0 else 0,
            'min_price': prices.min() if len(prices) > 0 else 0,
            'max_price': prices.max() if len(prices) > 0 else 0,
            'std_price': prices.std() if len(prices) > 0 else 0,
            'q1_price': prices.quantile(0.25) if len(prices) > 0 else 0,
            'q3_price': prices.quantile(0.75) if len(prices) > 0 else 0,
            
            # Surface
            'avg_surface': surfaces.mean() if len(surfaces) > 0 else 0,
            'median_surface': surfaces.median() if len(surfaces) > 0 else 0,
            'total_surface': surfaces.sum() if len(surfaces) > 0 else 0,
            
            # Prix/m²
            'avg_price_per_m2': price_per_m2.mean() if len(price_per_m2) > 0 else 0,
            'median_price_per_m2': price_per_m2.median() if len(price_per_m2) > 0 else 0,
            
            # Chambres
            'avg_bedrooms': df['bedrooms'].mean() if 'bedrooms' in df.columns else 0,
            'total_1br': len(df[df['bedrooms'] == 1]) if 'bedrooms' in df.columns else 0,
            'total_2br': len(df[df['bedrooms'] == 2]) if 'bedrooms' in df.columns else 0,
            'total_3br': len(df[df['bedrooms'] == 3]) if 'bedrooms' in df.columns else 0,
            'total_4br': len(df[df['bedrooms'] >= 4]) if 'bedrooms' in df.columns else 0,
            
            # Tendances temporelles
            'recent_7d': 0,
            'recent_30d': 0,
            'growth_rate': 0
        }
        
        # Calculs temporels
        if 'scraped_at' in df.columns:
            now = datetime.utcnow()
            df['scraped_at'] = pd.to_datetime(df['scraped_at'])
            
            stats['recent_7d'] = len(df[df['scraped_at'] >= now - timedelta(days=7)])
            stats['recent_30d'] = len(df[df['scraped_at'] >= now - timedelta(days=30)])
            
            old_count = len(df[df['scraped_at'] < now - timedelta(days=60)])
            recent_count = len(df[df['scraped_at'] >= now - timedelta(days=30)])
            stats['growth_rate'] = ((recent_count - old_count) / old_count * 100) if old_count > 0 else 0
        
        return stats
    
    def create_kpi(self, icon, label, value, color="#3B82F6", trend=None, suffix=""):
        """KPI Card simplifié"""
        return dmc.Paper([
            html.Div([
                html.Div([
                    DashIconify(icon=icon, width=40, height=40, color=color),
                ], style={'marginBottom': '12px'}),
                dmc.Text(label, size="sm", color="dimmed", weight=500),
                dmc.Text(f"{value:,.0f}{suffix}", size="xl", weight=700, 
                        style={'color': color, 'marginTop': '4px'}),
                html.Div([
                    DashIconify(
                        icon="mdi:trending-up" if trend and trend > 0 else "mdi:trending-down",
                        width=16,
                        color="green" if trend and trend > 0 else "red"
                    ) if trend else None,
                    dmc.Text(f"{trend:+.1f}%" if trend else "", 
                            size="xs", 
                            color="green" if trend and trend > 0 else "red",
                            style={'marginLeft': '4px'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginTop': '8px'})
            ], style={'padding': '20px', 'textAlign': 'center'})
        ], shadow="sm", radius="lg", withBorder=True, 
        style={
            'height': '100%', 
            'transition': 'transform 0.2s ease, box-shadow 0.2s ease', 
            'cursor': 'pointer'
        })
    
    def create_price_trends_chart(self, df):
        """Graphique des tendances de prix multidimensionnel"""
        if df.empty:
            return go.Figure()
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Prix Moyen par Ville (Top 10)', 'Distribution des Prix',
                          'Prix par Type de Propriété', 'Prix par Nombre de Chambres'),
            specs=[[{'type': 'bar'}, {'type': 'box'}],
                   [{'type': 'bar'}, {'type': 'scatter'}]],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # 1. Prix moyen par ville
        city_prices = df.groupby('city')['price'].agg(['mean', 'count']).reset_index()
        city_prices = city_prices.sort_values('mean', ascending=False).head(10)
        
        fig.add_trace(
            go.Bar(
                x=city_prices['city'],
                y=city_prices['mean'],
                name='Prix Moyen',
                marker=dict(color='#3B82F6'),
                text=[f'{x:,.0f}' for x in city_prices['mean']],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Prix: %{y:,.0f} FCFA<br>Annonces: %{customdata}<extra></extra>',
                customdata=city_prices['count']
            ),
            row=1, col=1
        )
        
        # 2. Distribution box plot
        fig.add_trace(
            go.Box(
                y=df['price'],
                name='Distribution',
                marker=dict(color='#10B981'),
                boxmean='sd'
            ),
            row=1, col=2
        )
        
        # 3. Prix par type
        type_prices = df.groupby('property_type')['price'].agg(['mean', 'count']).reset_index()
        type_prices = type_prices.sort_values('mean', ascending=False).head(8)
        
        fig.add_trace(
            go.Bar(
                x=type_prices['property_type'],
                y=type_prices['mean'],
                name='Par Type',
                marker=dict(color='#F59E0B'),
                text=[f'{x:,.0f}' for x in type_prices['mean']],
                textposition='outside'
            ),
            row=2, col=1
        )
        
        # 4. Prix par nombre de chambres
        bedroom_prices = df[df['bedrooms'] > 0].groupby('bedrooms')['price'].mean().reset_index()
        bedroom_prices = bedroom_prices[bedroom_prices['bedrooms'] <= 6]
        
        fig.add_trace(
            go.Scatter(
                x=bedroom_prices['bedrooms'],
                y=bedroom_prices['price'],
                mode='lines+markers',
                name='Par Chambres',
                line=dict(color='#8B5CF6', width=3),
                marker=dict(size=10)
            ),
            row=2, col=2
        )
        
        # Mise en page
        fig.update_xaxes(tickangle=-45, row=1, col=1)
        fig.update_xaxes(tickangle=-45, row=2, col=1)
        fig.update_xaxes(title_text="Chambres", row=2, col=2)
        fig.update_yaxes(title_text="Prix (FCFA)", row=1, col=1)
        fig.update_yaxes(title_text="Prix (FCFA)", row=2, col=1)
        fig.update_yaxes(title_text="Prix (FCFA)", row=2, col=2)
        
        fig.update_layout(
            height=700,
            showlegend=False,
            title_text="<b>Analyse Complète des Prix</b>",
            title_x=0.5,
            font=dict(family='Inter', size=12),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_geographic_analysis(self, df):
        """Analyse géographique complète"""
        if df.empty:
            return go.Figure()
        
        city_data = df.groupby('city').agg({
            'price': ['mean', 'median', 'count'],
            'surface_area': 'mean'
        }).reset_index()
        
        city_data.columns = ['city', 'avg_price', 'median_price', 'count', 'avg_surface']
        city_data = city_data.sort_values('count', ascending=False).head(15)
        
        fig = go.Figure()
        
        # Barres pour le nombre d'annonces
        fig.add_trace(go.Bar(
            x=city_data['city'],
            y=city_data['count'],
            name='Nombre d\'Annonces',
            marker=dict(color='#3B82F6'),
            yaxis='y',
            text=city_data['count'],
            textposition='outside'
        ))
        
        # Ligne pour le prix moyen
        fig.add_trace(go.Scatter(
            x=city_data['city'],
            y=city_data['avg_price'],
            name='Prix Moyen',
            mode='lines+markers',
            line=dict(color='#EF4444', width=3),
            marker=dict(size=10),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title=dict(text='<b>Analyse par Ville - Volume et Prix</b>', x=0.5),
            xaxis=dict(title='Ville', tickangle=-45),
            yaxis=dict(title='Nombre d\'Annonces', side='left'),
            yaxis2=dict(title='Prix Moyen (FCFA)', overlaying='y', side='right'),
            height=500,
            hovermode='x unified',
            font=dict(family='Inter', size=12),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        
        return fig
    
    def create_property_matrix(self, df):
        """Matrice des propriétés par type et chambres"""
        if df.empty:
            return go.Figure()
        
        # Créer une matrice
        matrix_data = df.groupby(['property_type', 'bedrooms'])['price'].agg(['mean', 'count']).reset_index()
        matrix_pivot = matrix_data.pivot(index='property_type', columns='bedrooms', values='mean')
        
        # Limiter aux types les plus courants
        top_types = df['property_type'].value_counts().head(8).index
        matrix_pivot = matrix_pivot.loc[matrix_pivot.index.isin(top_types)]
        
        fig = go.Figure(data=go.Heatmap(
            z=matrix_pivot.values,
            x=[f'{int(x)} Ch' for x in matrix_pivot.columns],
            y=matrix_pivot.index,
            colorscale='Viridis',
            text=np.round(matrix_pivot.values, 0),
            texttemplate='%{text:,.0f}',
            textfont={"size": 10},
            colorbar=dict(title="Prix (FCFA)")
        ))
        
        fig.update_layout(
            title=dict(text='<b>Matrice Prix: Type × Chambres</b>', x=0.5),
            xaxis=dict(title='Nombre de Chambres'),
            yaxis=dict(title='Type de Propriété'),
            height=500,
            font=dict(family='Inter', size=12),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_time_evolution(self, df):
        """Évolution temporelle des annonces et prix"""
        if df.empty or 'scraped_at' not in df.columns:
            return go.Figure()
        
        df['scraped_at'] = pd.to_datetime(df['scraped_at'])
        df['date'] = df['scraped_at'].dt.date
        
        daily_data = df.groupby('date').agg({
            'price': ['mean', 'count']
        }).reset_index()
        daily_data.columns = ['date', 'avg_price', 'count']
        daily_data = daily_data.sort_values('date')
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Prix Moyen Quotidien', 'Nouvelles Annonces par Jour'),
            vertical_spacing=0.15
        )
        
        # Prix moyen
        fig.add_trace(
            go.Scatter(
                x=daily_data['date'],
                y=daily_data['avg_price'],
                mode='lines',
                fill='tozeroy',
                name='Prix Moyen',
                line=dict(color='#3B82F6', width=2)
            ),
            row=1, col=1
        )
        
        # Nombre d'annonces
        fig.add_trace(
            go.Bar(
                x=daily_data['date'],
                y=daily_data['count'],
                name='Nouvelles Annonces',
                marker=dict(color='#10B981')
            ),
            row=2, col=1
        )
        
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Prix (FCFA)", row=1, col=1)
        fig.update_yaxes(title_text="Nombre", row=2, col=1)
        
        fig.update_layout(
            height=600,
            showlegend=False,
            title_text="<b>Évolution Temporelle du Marché</b>",
            title_x=0.5,
            font=dict(family='Inter', size=12),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_surface_analysis(self, df):
        """Analyse des surfaces"""
        if df.empty:
            return go.Figure()
        
        df_valid = df[(df['surface_area'] > 0) & (df['price'] > 0)]
        df_valid['price_per_m2'] = df_valid['price'] / df_valid['surface_area']
        
        fig = go.Figure()
        
        # Scatter plot
        fig.add_trace(go.Scatter(
            x=df_valid['surface_area'],
            y=df_valid['price'],
            mode='markers',
            marker=dict(
                size=8,
                color=df_valid['price_per_m2'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Prix/m²"),
                line=dict(width=1, color='white')
            ),
            text=[f"Surface: {s:.0f}m²<br>Prix: {p:,.0f} FCFA<br>Prix/m²: {pm:,.0f}" 
                  for s, p, pm in zip(df_valid['surface_area'], df_valid['price'], df_valid['price_per_m2'])],
            hovertemplate='%{text}<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(text='<b>Relation Surface - Prix</b>', x=0.5),
            xaxis=dict(title='Surface (m²)'),
            yaxis=dict(title='Prix (FCFA)'),
            height=500,
            font=dict(family='Inter', size=12),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_statistics_table(self, stats):
        """Tableau de statistiques détaillées"""
        data = [
            ['Total Propriétés', f"{stats.get('total_properties', 0):,}"],
            ['Villes Couvertes', f"{stats.get('total_cities', 0)}"],
            ['Types de Propriétés', f"{stats.get('total_types', 0)}"],
            ['Prix Moyen', f"{stats.get('avg_price', 0):,.0f} FCFA"],
            ['Prix Médian', f"{stats.get('median_price', 0):,.0f} FCFA"],
            ['Prix Min', f"{stats.get('min_price', 0):,.0f} FCFA"],
            ['Prix Max', f"{stats.get('max_price', 0):,.0f} FCFA"],
            ['Surface Moyenne', f"{stats.get('avg_surface', 0):.1f} m²"],
            ['Prix/m² Moyen', f"{stats.get('avg_price_per_m2', 0):,.0f} FCFA"],
            ['Chambres Moyennes', f"{stats.get('avg_bedrooms', 0):.1f}"],
        ]
        
        return dmc.Table([
            html.Thead(html.Tr([html.Th("Indicateur"), html.Th("Valeur")])),
            html.Tbody([html.Tr([html.Td(row[0]), html.Td(row[1], style={'fontWeight': 600})]) 
                       for row in data])
        ], striped=True, highlightOnHover=True, withBorder=True, style={'fontSize': '14px'})
    
    def setup_layout(self):
        """Layout principal ultra-complet"""
        df = self.get_all_data()
        stats = self.calculate_comprehensive_stats(df)
        
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.Div([
                    html.Div([
                        DashIconify(icon="mdi:home-analytics", width=48, color="#3B82F6"),
                        html.Div([
                            html.H1("Dashboard Immobilier Complet", 
                                   style={'margin': 0, 'fontSize': '32px', 'fontWeight': 700, 
                                         'fontFamily': 'Inter, sans-serif'}),
                            html.P("Analyse Détaillée du Marché Sénégalais", 
                                  style={'margin': 0, 'color': '#6B7280', 'fontSize': '16px',
                                        'fontFamily': 'Inter, sans-serif'})
                        ], style={'marginLeft': '16px'})
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                    html.Div([
                        html.Button([
                            DashIconify(icon="mdi:refresh", width=20),
                            html.Span("Actualiser", style={'marginLeft': '8px'})
                        ], id='refresh-btn', style={
                            'display': 'flex', 'alignItems': 'center', 'padding': '10px 20px',
                            'background': '#3B82F6', 'color': 'white', 'border': 'none',
                            'borderRadius': '8px', 'cursor': 'pointer', 'fontSize': '14px',
                            'fontWeight': 600, 'fontFamily': 'Inter, sans-serif'
                        })
                    ])
                ], style={
                    'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                    'maxWidth': '1400px', 'margin': '0 auto', 'padding': '24px'
                })
            ], style={'background': 'white', 'borderBottom': '1px solid #E5E7EB', 'marginBottom': '32px'}),
            
            html.Div(id='notification'),
            
            # Main Content
            html.Div([
                # KPIs Grid - 8 indicateurs
                html.Div([
                    self.create_kpi("mdi:home-city", "Total Annonces", 
                                   stats['total_properties'], "#3B82F6", stats.get('growth_rate')),
                    self.create_kpi("mdi:cash-multiple", "Prix Moyen", 
                                   stats['avg_price'], "#10B981", suffix=" FCFA"),
                    self.create_kpi("mdi:chart-line", "Prix Médian", 
                                   stats['median_price'], "#8B5CF6", suffix=" FCFA"),
                    self.create_kpi("mdi:ruler-square", "Surface Moy.", 
                                   stats['avg_surface'], "#F59E0B", suffix=" m²"),
                    self.create_kpi("mdi:map-marker-multiple", "Villes", 
                                   stats['total_cities'], "#06B6D4"),
                    self.create_kpi("mdi:home-variant", "Types", 
                                   stats['total_types'], "#EC4899"),
                    self.create_kpi("mdi:bed", "Chambres Moy.", 
                                   stats['avg_bedrooms'], "#14B8A6"),
                    self.create_kpi("mdi:new-box", "Nouveau (7j)", 
                                   stats['recent_7d'], "#F97316", trend=15.3),
                ], style={
                    'display': 'grid',
                    'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))',
                    'gap': '16px',
                    'marginBottom': '32px'
                }),
                
                # Row 1: Prix Trends + Table Stats
                html.Div([
                    html.Div([
                        html.Div([
                            dcc.Graph(id='price-trends', config={'displayModeBar': False})
                        ], style={
                            'background': 'white',
                            'padding': '24px',
                            'borderRadius': '16px',
                            'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
                            'marginBottom': '24px'
                        })
                    ], style={'flex': '2', 'minWidth': '0'}),
                    
                    html.Div([
                        html.Div([
                            html.H3("📊 Statistiques Clés", style={'marginTop': 0, 'fontFamily': 'Inter, sans-serif'}),
                            html.Div(id='stats-table')
                        ], style={
                            'background': 'white',
                            'padding': '24px',
                            'borderRadius': '16px',
                            'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
                            'marginBottom': '24px'
                        })
                    ], style={'flex': '1', 'minWidth': '300px'})
                ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '24px', 
                         'flexWrap': 'wrap'}),
                
                # Row 2: Geo Analysis
                html.Div([
                    dcc.Graph(id='geo-analysis', config={'displayModeBar': False})
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '16px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
                    'marginBottom': '24px'
                }),
                
                # Row 3: Matrix + Time Evolution
                html.Div([
                    html.Div([
                        html.Div([
                            dcc.Graph(id='property-matrix', config={'displayModeBar': False})
                        ], style={
                            'background': 'white',
                            'padding': '24px',
                            'borderRadius': '16px',
                            'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
                            'marginBottom': '24px'
                        })
                    ], style={'flex': '1'}),
                    
                    html.Div([
                        html.Div([
                            dcc.Graph(id='time-evolution', config={'displayModeBar': False})
                        ], style={
                            'background': 'white',
                            'padding': '24px',
                            'borderRadius': '16px',
                            'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
                            'marginBottom': '24px'
                        })
                    ], style={'flex': '1'})
                ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '24px',
                         'flexWrap': 'wrap'}),
                
                # Row 4: Surface Analysis
                html.Div([
                    dcc.Graph(id='surface-analysis', config={'displayModeBar': False})
                ], style={
                    'background': 'white',
                    'padding': '24px',
                    'borderRadius': '16px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
                    'marginBottom': '24px'
                }),
                
                # Footer
                html.Div([
                    html.P("Dashboard Immobilier Premium - ENSAE Dakar © 2024", 
                          style={'textAlign': 'center', 'color': '#6B7280', 
                                'margin': '32px 0', 'fontSize': '14px'})
                ])
                
            ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 24px'})
        ], style={
            'fontFamily': "'Inter', sans-serif",
            'background': 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
            'minHeight': '100vh',
            'margin': '0',
            'padding': '0'
        })
    
    def setup_callbacks(self):
        """Callbacks pour l'interactivité"""
        
        @callback(
            [
                Output('price-trends', 'figure'),
                Output('geo-analysis', 'figure'),
                Output('property-matrix', 'figure'),
                Output('time-evolution', 'figure'),
                Output('surface-analysis', 'figure'),
                Output('stats-table', 'children'),
                Output('notification', 'children')
            ],
            Input('refresh-btn', 'n_clicks'),
            prevent_initial_call=True
        )
        def update_all(n_clicks):
            """Actualiser tous les graphiques"""
            try:
                df = self.get_all_data()
                stats = self.calculate_comprehensive_stats(df)
                
                notification = html.Div([
                    html.Div([
                        DashIconify(icon="mdi:check-circle", width=24, color="white"),
                        html.Span("Données actualisées avec succès !", 
                                 style={'marginLeft': '8px', 'color': 'white', 'fontWeight': 600})
                    ], style={
                        'display': 'flex', 'alignItems': 'center', 'padding': '12px 20px',
                        'background': '#10B981', 'borderRadius': '8px', 'marginBottom': '16px',
                        'animation': 'slideIn 0.3s ease-out'
                    })
                ])
                
                return (
                    self.create_price_trends_chart(df),
                    self.create_geographic_analysis(df),
                    self.create_property_matrix(df),
                    self.create_time_evolution(df),
                    self.create_surface_analysis(df),
                    self.create_statistics_table(stats),
                    notification
                )
            except Exception as e:
                print(f"Erreur: {e}")
                return (go.Figure(),) * 5 + (html.Div("Erreur"), html.Div())


def create_complete_dashboard(server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
    """Factory pour créer le dashboard"""
    dashboard = CompleteDashboard(
        server=server,
        routes_pathname_prefix=routes_pathname_prefix,
        requests_pathname_prefix=requests_pathname_prefix
    )
    return dashboard.app