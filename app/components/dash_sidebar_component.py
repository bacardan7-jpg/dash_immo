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
            # Styles CSS inline
            html.Style(SIDEBAR_CSS),
            
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
            ),
            
            # JavaScript pour le toggle
            html.Script(SIDEBAR_JS)
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


# CSS pour la sidebar (inline dans le layout)
SIDEBAR_CSS = """
/* Sidebar Styles for Dash */
.glass-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: 280px;
    height: 100vh;
    background: linear-gradient(180deg, 
        rgba(15, 12, 41, 0.98) 0%, 
        rgba(48, 43, 99, 0.98) 50%, 
        rgba(36, 36, 62, 0.98) 100%
    );
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
    overflow-y: auto;
    z-index: 1000;
    padding-top: 2rem;
    transition: transform 0.3s ease;
}

.glass-sidebar::-webkit-scrollbar {
    width: 6px;
}

.glass-sidebar::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
}

.glass-sidebar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
}

.sidebar-header {
    padding: 0 1.5rem 1.5rem;
    text-align: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-logo {
    font-size: 2.5rem;
    color: #ffd700;
    filter: drop-shadow(0 0 10px rgba(255, 215, 0, 0.5));
    margin-bottom: 0.5rem;
}

.sidebar-title {
    font-size: 1.5rem;
    font-weight: 800;
    background: linear-gradient(45deg, #ffd700, #ffed4e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
}

.sidebar-user-card {
    margin: 1.5rem;
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    text-align: center;
}

.sidebar-avatar {
    width: 70px;
    height: 70px;
    margin: 0 auto 1rem;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    font-weight: 800;
    color: white;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.sidebar-username {
    color: white;
    font-weight: 600;
    margin-bottom: 0.5rem;
    font-size: 1rem;
}

.sidebar-role-badge {
    display: inline-block;
    padding: 0.4rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
}

.role-danger {
    background: rgba(220, 53, 69, 0.2);
    color: #dc3545;
    border: 1px solid rgba(220, 53, 69, 0.3);
}

.role-primary {
    background: rgba(13, 110, 253, 0.2);
    color: #0d6efd;
    border: 1px solid rgba(13, 110, 253, 0.3);
}

.role-success {
    background: rgba(25, 135, 84, 0.2);
    color: #198754;
    border: 1px solid rgba(25, 135, 84, 0.3);
}

.sidebar-nav {
    padding: 0 1rem 2rem;
}

.sidebar-section-title {
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 1rem 0.5rem 0.5rem;
    margin-top: 1rem;
}

.sidebar-links {
    list-style: none;
    padding: 0;
    margin: 0;
}

.sidebar-links .nav-link {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.875rem 1rem;
    color: rgba(255, 255, 255, 0.9);
    text-decoration: none;
    border-radius: 12px;
    margin-bottom: 0.5rem;
    transition: all 0.3s ease;
    font-weight: 500;
}

.sidebar-links .nav-link i {
    width: 20px;
    text-align: center;
    font-size: 1.1rem;
}

.sidebar-links .nav-link:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateX(5px);
    color: white;
}

.sidebar-links .nav-link.active {
    background: rgba(102, 126, 234, 0.2);
    border-left: 3px solid #667eea;
}

.nav-link-admin {
    background: rgba(255, 215, 0, 0.1) !important;
    border: 1px solid rgba(255, 215, 0, 0.2) !important;
}

.nav-link-admin i {
    color: #ffd700 !important;
}

.nav-link-danger {
    color: #ff6b6b !important;
    background: rgba(255, 107, 107, 0.1) !important;
    border: 1px solid rgba(255, 107, 107, 0.2) !important;
}

.nav-badge {
    margin-left: auto;
    background: linear-gradient(45deg, #667eea, #764ba2);
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 700;
}

.has-sidebar {
    margin-left: 280px;
    min-height: 100vh;
    background: #F8FAFC;
}

.sidebar-toggle-mobile {
    position: fixed;
    top: 20px;
    left: 20px;
    z-index: 1001;
    background: linear-gradient(45deg, #667eea, #764ba2);
    border: none;
    border-radius: 12px;
    width: 50px;
    height: 50px;
    color: white;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    cursor: pointer;
    display: none;
}

.sidebar-footer {
    padding: 1.5rem;
    text-align: center;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    margin-top: auto;
}

.sidebar-footer p {
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.85rem;
    margin: 0;
}

.sidebar-divider {
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
    margin: 1.5rem 0.5rem;
}

@media (max-width: 991px) {
    .glass-sidebar {
        transform: translateX(-100%);
    }
    
    .glass-sidebar.show {
        transform: translateX(0);
    }
    
    .has-sidebar {
        margin-left: 0;
    }
    
    .sidebar-toggle-mobile {
        display: flex;
        align-items: center;
        justify-content: center;
    }
}
"""

# JavaScript pour le toggle mobile
SIDEBAR_JS = """
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('dash-sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle-mobile');
    
    if (toggleBtn && sidebar) {
        // Créer l'overlay
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 999;
            display: none;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        overlay.id = 'sidebar-overlay';
        document.body.appendChild(overlay);
        
        function toggleSidebar() {
            sidebar.classList.toggle('show');
            if (sidebar.classList.contains('show')) {
                overlay.style.display = 'block';
                setTimeout(() => overlay.style.opacity = '1', 10);
            } else {
                overlay.style.opacity = '0';
                setTimeout(() => overlay.style.display = 'none', 300);
            }
        }
        
        toggleBtn.addEventListener('click', toggleSidebar);
        overlay.addEventListener('click', toggleSidebar);
        
        // Fermer sur Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && sidebar.classList.contains('show')) {
                toggleSidebar();
            }
        });
        
        // Fermer sur clic de lien (mobile)
        const navLinks = sidebar.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 992) {
                    toggleSidebar();
                }
            });
        });
    }
});
"""