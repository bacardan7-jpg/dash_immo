"""
Sidebar intelligent et adaptative selon le rôle
À inclure dans base.html ou comme composant séparé
"""

SIDEBAR_HTML = """
<!-- Sidebar Toggle Button (Mobile) -->
<button class="sidebar-toggle d-lg-none" id="sidebarToggle" style="
    position: fixed;
    top: 80px;
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
    transition: all 0.3s ease;
">
    <i class="fas fa-bars"></i>
</button>

<!-- Sidebar -->
<aside class="sidebar" id="mainSidebar" style="
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    width: 280px;
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
    transition: transform 0.3s ease;
    padding-top: 70px;
">
    <!-- Logo Section -->
    <div class="sidebar-header" style="padding: 1.5rem; text-align: center; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
        <a href="{{ url_for('index') }}" style="text-decoration: none;">
            <i class="fas fa-home" style="font-size: 2.5rem; color: #ffd700; filter: drop-shadow(0 0 10px rgba(255, 215, 0, 0.5));"></i>
            <h3 style="
                margin-top: 0.5rem;
                font-size: 1.5rem;
                font-weight: 800;
                background: linear-gradient(45deg, #ffd700, #ffed4e);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            ">ImmoAnalytics</h3>
        </a>
    </div>
    
    <!-- User Info Card -->
    {% if current_user.is_authenticated %}
    <div class="user-card" style="
        margin: 1.5rem;
        padding: 1.5rem;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        text-align: center;
    ">
        <div class="user-avatar" style="
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
        ">
            {{ current_user.first_name[0] }}{{ current_user.last_name[0] }}
        </div>
        <h5 style="color: white; margin-bottom: 0.5rem; font-weight: 600;">
            {{ current_user.first_name }} {{ current_user.last_name }}
        </h5>
        <div class="user-role" style="display: inline-block; padding: 0.25rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">
            {% if current_user.role == 'admin' %}
                <span style="background: rgba(220, 53, 69, 0.2); color: #dc3545; border: 1px solid rgba(220, 53, 69, 0.3); padding: 0.4rem 1rem; border-radius: 20px;">
                    <i class="fas fa-user-shield me-1"></i>Administrateur
                </span>
            {% elif current_user.role == 'analyst' %}
                <span style="background: rgba(13, 110, 253, 0.2); color: #0d6efd; border: 1px solid rgba(13, 110, 253, 0.3); padding: 0.4rem 1rem; border-radius: 20px;">
                    <i class="fas fa-user-tie me-1"></i>Analyste
                </span>
            {% else %}
                <span style="background: rgba(25, 135, 84, 0.2); color: #198754; border: 1px solid rgba(25, 135, 84, 0.3); padding: 0.4rem 1rem; border-radius: 20px;">
                    <i class="fas fa-user me-1"></i>Viewer
                </span>
            {% endif %}
        </div>
    </div>
    {% endif %}
    
    <!-- Navigation Menu -->
    <nav class="sidebar-nav" style="padding: 0 1rem;">
        {% if current_user.is_authenticated %}
            
            <!-- Section: Dashboards (Admin + Analyst) -->
            {% if user_capabilities.can_view_dashboard %}
            <div class="nav-section">
                <div class="nav-section-title" style="
                    color: rgba(255, 255, 255, 0.5);
                    font-size: 0.75rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    padding: 1rem 0.5rem 0.5rem;
                ">Tableaux de bord</div>
                
                <a href="{{ url_for('dashboard') }}" class="nav-item {% if request.endpoint == 'dashboard' %}active{% endif %}" style="
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
                ">
                    <i class="fas fa-chart-line" style="width: 20px; text-align: center; font-size: 1.1rem;"></i>
                    <span>Dashboard Principal</span>
                </a>
                
                <a href="{{ url_for('analytics') }}" class="nav-item {% if request.endpoint == 'analytics' %}active{% endif %}" style="
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
                ">
                    <i class="fas fa-chart-bar" style="width: 20px; text-align: center; font-size: 1.1rem;"></i>
                    <span>Analytics Avancés</span>
                </a>
                
                <a href="{{ url_for('map_view') }}" class="nav-item {% if request.endpoint == 'map_view' %}active{% endif %}" style="
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
                ">
                    <i class="fas fa-map-marked-alt" style="width: 20px; text-align: center; font-size: 1.1rem;"></i>
                    <span>Vue Cartographique</span>
                </a>
            </div>
            {% endif %}
            
            <!-- Section: Recherche (Tous) -->
            <div class="nav-section">
                {% if user_capabilities.can_view_dashboard %}
                <div class="nav-section-title" style="
                    color: rgba(255, 255, 255, 0.5);
                    font-size: 0.75rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    padding: 1rem 0.5rem 0.5rem;
                ">Recherche</div>
                {% endif %}
                
                <a href="{{ url_for('viewer') }}" class="nav-item {% if request.endpoint == 'viewer' %}active{% endif %}" style="
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
                ">
                    <i class="fas fa-search" style="width: 20px; text-align: center; font-size: 1.1rem;"></i>
                    <span>Recherche IA</span>
                    <span style="
                        margin-left: auto;
                        background: linear-gradient(45deg, #667eea, #764ba2);
                        padding: 0.25rem 0.75rem;
                        border-radius: 12px;
                        font-size: 0.7rem;
                        font-weight: 700;
                    ">NEW</span>
                </a>
            </div>
            
            <!-- Section: Administration (Admin only) -->
            {% if user_capabilities.can_manage_users %}
            <div class="nav-section">
                <div class="nav-section-title" style="
                    color: rgba(255, 255, 255, 0.5);
                    font-size: 0.75rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    padding: 1rem 0.5rem 0.5rem;
                ">Administration</div>
                
                <a href="{{ url_for('admin') }}" class="nav-item {% if request.endpoint == 'admin' %}active{% endif %}" style="
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
                    background: rgba(255, 215, 0, 0.1);
                    border: 1px solid rgba(255, 215, 0, 0.2);
                ">
                    <i class="fas fa-user-shield" style="width: 20px; text-align: center; font-size: 1.1rem; color: #ffd700;"></i>
                    <span>Panneau Admin</span>
                </a>
            </div>
            {% endif %}
            
            <!-- Divider -->
            <div style="height: 1px; background: rgba(255, 255, 255, 0.1); margin: 1.5rem 0.5rem;"></div>
            
            <!-- Section: Compte -->
            <div class="nav-section">
                <div class="nav-section-title" style="
                    color: rgba(255, 255, 255, 0.5);
                    font-size: 0.75rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    padding: 1rem 0.5rem 0.5rem;
                ">Mon Compte</div>
                
                <a href="{{ url_for('auth.profile') }}" class="nav-item {% if request.endpoint == 'auth.profile' %}active{% endif %}" style="
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
                ">
                    <i class="fas fa-user-circle" style="width: 20px; text-align: center; font-size: 1.1rem;"></i>
                    <span>Mon Profil</span>
                </a>
                
                <a href="{{ url_for('auth.settings') }}" class="nav-item {% if request.endpoint == 'auth.settings' %}active{% endif %}" style="
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
                ">
                    <i class="fas fa-cog" style="width: 20px; text-align: center; font-size: 1.1rem;"></i>
                    <span>Paramètres</span>
                </a>
                
                <a href="{{ url_for('auth.logout') }}" class="nav-item" style="
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                    padding: 0.875rem 1rem;
                    color: #ff6b6b;
                    text-decoration: none;
                    border-radius: 12px;
                    margin-bottom: 0.5rem;
                    transition: all 0.3s ease;
                    font-weight: 500;
                    background: rgba(255, 107, 107, 0.1);
                    border: 1px solid rgba(255, 107, 107, 0.2);
                ">
                    <i class="fas fa-sign-out-alt" style="width: 20px; text-align: center; font-size: 1.1rem;"></i>
                    <span>Déconnexion</span>
                </a>
            </div>
            
        {% else %}
            <!-- Non connecté -->
            <div class="nav-section">
                <a href="{{ url_for('auth.login') }}" class="nav-item" style="
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
                    background: linear-gradient(45deg, #667eea, #764ba2);
                ">
                    <i class="fas fa-sign-in-alt" style="width: 20px; text-align: center;"></i>
                    <span>Connexion</span>
                </a>
                
                <a href="{{ url_for('auth.register') }}" class="nav-item" style="
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
                    border: 1px solid rgba(255, 255, 255, 0.2);
                ">
                    <i class="fas fa-user-plus" style="width: 20px; text-align: center;"></i>
                    <span>Inscription</span>
                </a>
            </div>
        {% endif %}
    </nav>
    
    <!-- Footer -->
    <div class="sidebar-footer" style="
        padding: 1.5rem;
        text-align: center;
        margin-top: auto;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    ">
        <p style="color: rgba(255, 255, 255, 0.5); font-size: 0.85rem; margin: 0;">
            © 2024 ImmoAnalytics
        </p>
        <p style="color: rgba(255, 255, 255, 0.3); font-size: 0.75rem; margin: 0.5rem 0 0;">
            v1.0.0
        </p>
    </div>
</aside>

<!-- Main Content Wrapper -->
<div class="main-content" id="mainContent" style="
    margin-left: 280px;
    min-height: 100vh;
    transition: margin-left 0.3s ease;
">
    <!-- Votre contenu ici -->
</div>

<style>
/* Hover effects pour les nav items */
.nav-item:hover {
    background: rgba(255, 255, 255, 0.1) !important;
    transform: translateX(5px);
}

.nav-item.active {
    background: rgba(102, 126, 234, 0.2) !important;
    border-left: 3px solid #667eea;
}

/* Scrollbar personnalisée */
.sidebar::-webkit-scrollbar {
    width: 6px;
}

.sidebar::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
}

.sidebar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
}

.sidebar::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.3);
}

/* Mobile responsive */
@media (max-width: 991px) {
    .sidebar {
        transform: translateX(-100%);
    }
    
    .sidebar.show {
        transform: translateX(0);
    }
    
    .main-content {
        margin-left: 0 !important;
    }
    
    .sidebar-toggle:hover {
        transform: scale(1.1);
    }
}

/* Animation pour le toggle button */
.sidebar-toggle {
    transition: all 0.3s ease;
}

.sidebar-toggle:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.sidebar-toggle.active i {
    transform: rotate(90deg);
}

/* Overlay pour mobile */
.sidebar-overlay {
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
}

.sidebar-overlay.show {
    display: block;
    opacity: 1;
}
</style>

<script>
// Toggle sidebar sur mobile
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('mainSidebar');
    const toggleBtn = document.getElementById('sidebarToggle');
    const mainContent = document.getElementById('mainContent');
    
    // Créer l'overlay
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    overlay.id = 'sidebarOverlay';
    document.body.appendChild(overlay);
    
    // Toggle function
    function toggleSidebar() {
        sidebar.classList.toggle('show');
        overlay.classList.toggle('show');
        toggleBtn.classList.toggle('active');
    }
    
    // Event listeners
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleSidebar);
    }
    
    if (overlay) {
        overlay.addEventListener('click', toggleSidebar);
    }
    
    // Fermer sur escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('show')) {
            toggleSidebar();
        }
    });
    
    // Fermer sidebar sur clic de lien (mobile)
    const navItems = sidebar.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            if (window.innerWidth < 992) {
                toggleSidebar();
            }
        });
    });
});
</script>
"""


def render_sidebar():
    """Fonction pour rendre la sidebar (à utiliser dans Flask)"""
    from flask import render_template_string
    return render_template_string(SIDEBAR_HTML)