"""
Composant Sidebar pour les dashboards Dash - VERSION CORRIGÉE
À intégrer dans tous les dashboards (viewer, analytics, map, admin)
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import dash_mantine_components as dmc
from flask_login import current_user
from flask import has_request_context


def create_sidebar_layout(app_content):
    """
    Wrapper pour ajouter la sidebar à n'importe quel dashboard Dash
    
    Usage:
        app.layout = create_sidebar_layout(
            html.Div([
                # Votre contenu dashboard ici
            ])
        )
    
    IMPORTANT: Cette fonction retourne une FONCTION (serve_layout) qui sera appelée
    à chaque requête, permettant d'accéder à current_user au bon moment.
    """
    
    # Fonction qui sera appelée à chaque requête
    def serve_layout():
        # Valeurs par défaut
        is_admin = False
        is_analyst = False
        is_viewer = True
        avatar_text = "U"
        username = "User"
        role_badge = "Viewer"
        role_color = "success"
        role_icon = "fa-user"
        
        # Vérifier si on est dans un contexte de requête ET si current_user existe
        if has_request_context():
            try:
                # Vérifier que current_user n'est pas None
                if current_user and hasattr(current_user, 'is_authenticated'):
                    is_admin = current_user.is_authenticated and hasattr(current_user, 'is_admin') and current_user.is_admin()
                    is_analyst = current_user.is_authenticated and hasattr(current_user, 'is_analyst') and current_user.is_analyst()
                    is_viewer = current_user.is_authenticated and not is_admin and not is_analyst
                    
                    # Avatar et informations utilisateur
                    if current_user.is_authenticated:
                        # Essayer de récupérer first_name et last_name
                        if (hasattr(current_user, 'first_name') and 
                            hasattr(current_user, 'last_name') and 
                            current_user.first_name and 
                            current_user.last_name):
                            avatar_text = f"{current_user.first_name[0]}{current_user.last_name[0]}".upper()
                            username = f"{current_user.first_name} {current_user.last_name}"
                        elif hasattr(current_user, 'username') and current_user.username:
                            avatar_text = current_user.username[:2].upper()
                            username = current_user.username
                        
                        # Déterminer le badge de rôle
                        if is_admin:
                            role_badge = "Administrateur"
                            role_color = "danger"
                            role_icon = "fa-user-shield"
                        elif is_analyst:
                            role_badge = "Analyste"
                            role_color = "primary"
                            role_icon = "fa-user-tie"
                        else:
                            role_badge = "Viewer"
                            role_color = "success"
                            role_icon = "fa-user"
                            
            except Exception as e:
                # En cas d'erreur, utiliser valeurs par défaut
                print(f"⚠️ Erreur lors de la lecture de current_user: {e}")
                pass  # Garder les valeurs par défaut
        
        # Construction de la sidebar
        sidebar = html.Aside(
            id="dash-sidebar",
            className="glass-sidebar",
            children=[
                # Header
                html.Div(
                    className="sidebar-header",
                    children=[
                        html.A(
                            href="/",
                            style={"textDecoration": "none"},
                            children=[
                                html.I(className="fas fa-home sidebar-logo"),
                                html.H3("ImmoAnalytics", className="sidebar-title")
                            ]
                        )
                    ]
                ),
                
                # User Card
                html.Div(
                    className="sidebar-user-card",
                    children=[
                        html.Div(avatar_text, className="sidebar-avatar"),
                        html.H5(username, className="sidebar-username"),
                        html.Div(
                            className=f"sidebar-role-badge role-{role_color}",
                            children=[
                                html.I(className=f"fas {role_icon} me-1"),
                                role_badge
                            ]
                        )
                    ]
                ),
                
                # Navigation
                html.Nav(
                    className="sidebar-nav",
                    children=[
                        html.Ul(
                            className="sidebar-links",
                            children=get_nav_items(is_admin, is_analyst, is_viewer)
                        )
                    ]
                ),
                
                # Footer
                html.Div(
                    className="sidebar-footer",
                    children=[
                        html.P("© 2024 ImmoAnalytics"),
                        html.P("v1.0.0", style={"color": "rgba(255, 255, 255, 0.3)", "fontSize": "0.75rem"})
                    ]
                )
            ]
        )
        
        # Toggle button pour mobile
        toggle_button = html.Button(
            id="sidebar-toggle-mobile",
            className="sidebar-toggle-mobile",
            children=[html.I(className="fas fa-bars")]
        )
        
        # Main content avec sidebar
        layout = html.Div([
            # Toggle button
            toggle_button,
            
            # Sidebar
            sidebar,
            
            # Main content
            html.Main(
                id="dash-main-content",
                className="has-sidebar",
                children=[
                    html.Div(
                        className="container-fluid px-4 py-4",
                        children=app_content
                    )
                ]
            )
        ])
        
        return layout
    
    # IMPORTANT: Retourner la fonction serve_layout, pas le layout directement
    # Dash appellera cette fonction à chaque requête
    return serve_layout


def get_nav_items(is_admin, is_analyst, is_viewer):
    """Construire les items de navigation selon le rôle"""
    
    items = []
    
    # Dashboards (Admin + Analyst)
    if is_admin or is_analyst:
        items.append(
            html.Div(
                className="sidebar-section-title",
                children="TABLEAUX DE BORD"
            )
        )
        
        items.extend([
            html.Li(
                className="nav-item",
                children=[
                    html.A(
                        href="/dashboard",
                        className="nav-link",
                        children=[
                            html.I(className="fas fa-chart-line"),
                            html.Span("Dashboard Principal")
                        ]
                    )
                ]
            ),
            html.Li(
                className="nav-item",
                children=[
                    html.A(
                        href="/analytics",
                        className="nav-link",
                        children=[
                            html.I(className="fas fa-chart-bar"),
                            html.Span("Analytics Avancés")
                        ]
                    )
                ]
            ),
            html.Li(
                className="nav-item",
                children=[
                    html.A(
                        href="/map",
                        className="nav-link",
                        children=[
                            html.I(className="fas fa-map-marked-alt"),
                            html.Span("Vue Cartographique")
                        ]
                    )
                ]
            )
        ])
    
    # Recherche (Tous)
    items.append(
        html.Div(
            className="sidebar-section-title",
            children="RECHERCHE" if (is_admin or is_analyst) else ""
        )
    )
    
    items.append(
        html.Li(
            className="nav-item",
            children=[
                html.A(
                    href="/viewer",
                    className="nav-link",
                    children=[
                        html.I(className="fas fa-search"),
                        html.Span("Recherche IA"),
                        html.Span("NEW", className="nav-badge")
                    ]
                )
            ]
        )
    )
    
    # Administration (Admin only)
    if is_admin:
        items.append(
            html.Div(
                className="sidebar-section-title",
                children="ADMINISTRATION"
            )
        )
        
        items.append(
            html.Li(
                className="nav-item",
                children=[
                    html.A(
                        href="/admin",
                        className="nav-link nav-link-admin",
                        children=[
                            html.I(className="fas fa-user-shield"),
                            html.Span("Panneau Admin")
                        ]
                    )
                ]
            )
        )
    
    # Divider
    items.append(html.Div(className="sidebar-divider"))
    
    # Mon Compte
    items.append(
        html.Div(
            className="sidebar-section-title",
            children="MON COMPTE"
        )
    )
    
    items.extend([
        html.Li(
            className="nav-item",
            children=[
                html.A(
                    href="/auth/profile",
                    className="nav-link",
                    children=[
                        html.I(className="fas fa-user-circle"),
                        html.Span("Mon Profil")
                    ]
                )
            ]
        ),
        html.Li(
            className="nav-item",
            children=[
                html.A(
                    href="/auth/settings",
                    className="nav-link",
                    children=[
                        html.I(className="fas fa-cog"),
                        html.Span("Paramètres")
                    ]
                )
            ]
        ),
        html.Li(
            className="nav-item",
            children=[
                html.A(
                    href="/auth/logout",
                    className="nav-link nav-link-danger",
                    children=[
                        html.I(className="fas fa-sign-out-alt"),
                        html.Span("Déconnexion")
                    ]
                )
            ]
        )
    ])
    
    return items