// Sidebar toggle script for Dash dashboards
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