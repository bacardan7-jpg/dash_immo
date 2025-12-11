# components/sidebar_factory.py

from flask_login import current_user
from flask import has_request_context, url_for
from dash import html
import dash_bootstrap_components as dbc

def get_user_info():
    """Récupère les infos utilisateur de manière sécurisée"""
    # Valeurs par défaut
    info = {
        'is_authenticated': False,
        'is_admin': False,
        'is_analyst': False,
        'is_viewer': True,
        'avatar_text': 'U',
        'username': 'User',
        'role_badge': 'Viewer',
        'role_color': 'viewer',
        'role_icon': 'fa-user'
    }
    
    if has_request_context():
        try:
            if current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                info['is_authenticated'] = True
                info['is_admin'] = hasattr(current_user, 'is_admin') and current_user.is_admin()
                info['is_analyst'] = hasattr(current_user, 'is_analyst') and current_user.is_analyst()
                info['is_viewer'] = not info['is_admin'] and not info['is_analyst']
                
                # Avatar
                if (hasattr(current_user, 'first_name') and 
                    hasattr(current_user, 'last_name') and 
                    current_user.first_name and 
                    current_user.last_name):
                    info['avatar_text'] = f"{current_user.first_name[0]}{current_user.last_name[0]}".upper()
                    info['username'] = f"{current_user.first_name} {current_user.last_name}"
                elif hasattr(current_user, 'username') and current_user.username:
                    info['avatar_text'] = current_user.username[:2].upper()
                    info['username'] = current_user.username
                
                # Rôle
                if info['is_admin']:
                    info['role_badge'] = 'Administrateur'
                    info['role_color'] = 'admin'
                    info['role_icon'] = 'fa-user-shield'
                elif info['is_analyst']:
                    info['role_badge'] = 'Analyste'
                    info['role_color'] = 'analyst'
                    info['role_icon'] = 'fa-user-tie'
                else:
                    info['role_badge'] = 'Viewer'
                    info['role_color'] = 'viewer'
                    info['role_icon'] = 'fa-user'
                    
        except Exception:
            pass
    
    return info

def get_nav_items_for_user(is_admin, is_analyst, is_viewer):
    """Construit les items de navigation selon le rôle"""
    items = []
    
    # SECTION: Dashboards (Admin + Analyst)
    if is_admin or is_analyst:
        items.append({'type': 'section', 'title': 'Tableaux de bord'})
        
        items.extend([
            {'type': 'link', 'href': '/dashboard', 'icon': 'fa-chart-line', 'label': 'Dashboard Principal'},
            {'type': 'link', 'href': '/analytics', 'icon': 'fa-chart-bar', 'label': 'Analytics Avancés'},
            {'type': 'link', 'href': '/map', 'icon': 'fa-map-marked-alt', 'label': 'Vue Cartographique'},
        ])
    
    # SECTION: Recherche (Tous)
    items.append({'type': 'section', 'title': 'Recherche'})
    items.append({
        'type': 'link', 
        'href': '/viewer', 
        'icon': 'fa-search', 
        'label': 'Recherche IA',
        'badge': 'NEW'
    })
    
    # SECTION: Administration (Admin only)
    if is_admin:
        items.append({'type': 'section', 'title': 'Administration'})
        items.append({
            'type': 'link', 
            'href': '/admin', 
            'icon': 'fa-user-shield', 
            'label': 'Panneau Admin',
            'class': 'nav-link-admin'
        })
    
    # SECTION: Mon Compte
    items.append({'type': 'section', 'title': 'Mon Compte'})
    items.extend([
        {'type': 'link', 'href': '/auth/profile', 'icon': 'fa-user-circle', 'label': 'Mon Profil'},
        {'type': 'link', 'href': '/auth/settings', 'icon': 'fa-cog', 'label': 'Paramètres'},
        {'type': 'divider'},
        {'type': 'link', 'href': '/logout', 'icon': 'fa-sign-out-alt', 'label': 'Déconnexion', 'class': 'nav-link-danger'},
    ])
    
    return items

def render_nav_item(item, current_path=None):
    """Rend un item de navigation (pour Dash)"""
    if item['type'] == 'section':
        return html.Div(item['title'], className="sidebar-section-title")
    
    if item['type'] == 'divider':
        return html.Div(className="sidebar-divider")
    
    # Link
    is_active = current_path and item['href'] == current_path
    base_class = "nav-link"
    if is_active:
        base_class += " active"
    if item.get('class'):
        base_class += f" {item['class']}"
    
    children = [
        html.I(className=f"fas {item['icon']}"),
        html.Span(item['label'])
    ]
    
    if item.get('badge'):
        children.append(html.Span(item['badge'], className="nav-badge"))
    
    return html.Li(
        html.A(children, href=item['href'], className=base_class),
        className="nav-item"
    )

def create_sidebar_component(current_path=None):
    """
    CRÉE LE SIDEBAR POUR DASH (utilise les mêmes classes CSS que Flask)
    
    Args:
        current_path: Chemin actuel pour marquer le lien actif
        
    Returns:
        Composant Dash prêt à être intégré
    """
    user_info = get_user_info()
    
    if not user_info['is_authenticated']:
        return html.Div()  # Pas de sidebar si non connecté
    
    # Construction du sidebar
    nav_items = get_nav_items_for_user(
        user_info['is_admin'], 
        user_info['is_analyst'], 
        user_info['is_viewer']
    )
    
    sidebar = html.Aside(
        id="app-sidebar",
        className="app-sidebar",
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
                            html.H3("Jotali Immo", className="sidebar-title")
                        ]
                    )
                ]
            ),
            
            # User Card
            html.Div(
                className="sidebar-user-card",
                children=[
                    html.Div(user_info['avatar_text'], className="sidebar-avatar"),
                    html.H5(user_info['username'], className="sidebar-username"),
                    html.Div(
                        className=f"sidebar-role-badge role-{user_info['role_color']}",
                        children=[
                            html.I(className=f"fas {user_info['role_icon']} me-1"),
                            user_info['role_badge']
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
                        children=[render_nav_item(item, current_path) for item in nav_items]
                    )
                ]
            ),
            
            # Footer
            html.Div(
                className="sidebar-footer",
                children=[
                    html.P("© 2024 Jotali Immo"),
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
    
    # Overlay pour mobile
    overlay = html.Div(id="sidebar-overlay", className="sidebar-overlay")
    
    # JavaScript pour le toggle
    js = html.Script("""
        document.addEventListener('DOMContentLoaded', function() {
            const sidebar = document.getElementById('app-sidebar');
            const toggleBtn = document.getElementById('sidebar-toggle-mobile');
            const overlay = document.getElementById('sidebar-overlay');
            
            if (toggleBtn && sidebar) {
                function toggleSidebar() {
                    sidebar.classList.toggle('show');
                    if (overlay) {
                        overlay.classList.toggle('show');
                    }
                }
                
                toggleBtn.addEventListener('click', toggleSidebar);
                if (overlay) {
                    overlay.addEventListener('click', toggleSidebar);
                }
                
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
    """)
    
    return html.Div([toggle_button, overlay, sidebar, js])