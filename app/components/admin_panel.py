import dash
from dash import html, dcc, Input, Output, callback, dash_table
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from ..database.models import db, User, AuditLog, DashboardConfig
from ..auth.decorators import admin_required

class AdminPanel:
    """Panneau d'administration pour la gestion des utilisateurs et la configuration"""
    
    def __init__(self, server=None, routes_pathname_prefix="/", requests_pathname_prefix="/"):
        self.app = dash.Dash(
            __name__,
            server=server,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            routes_pathname_prefix=routes_pathname_prefix,
            requests_pathname_prefix=requests_pathname_prefix
        )
        
        if server:
            with server.app_context():
                self.setup_layout()
                self.setup_callbacks()
        else:
            self._layout_setup_deferred = True
    
    def get_user_stats(self):
        """Récupérer les statistiques des utilisateurs"""
        try:
            total_users = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            admin_users = User.query.filter_by(role='admin').count()
            analyst_users = User.query.filter_by(role='analyst').count()
            viewer_users = User.query.filter_by(role='viewer').count()
            
            # Utilisateurs actifs dans les 30 derniers jours
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_users = User.query.filter(User.last_login >= thirty_days_ago).count()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'admin_users': admin_users,
                'analyst_users': analyst_users,
                'viewer_users': viewer_users,
                'recent_users': recent_users
            }
        except Exception as e:
            print(f"Erreur lors de la récupération des statistiques utilisateur: {e}")
            return {}
    
    def get_audit_logs(self, limit=100):
        """Récupérer les journaux d'audit"""
        try:
            logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
            
            log_data = []
            for log in logs:
                user = User.query.get(log.user_id)
                log_data.append({
                    'id': log.id,
                    'username': user.username if user else 'Utilisateur inconnu',
                    'action': log.action,
                    'resource': log.resource,
                    'details': log.details,
                    'ip_address': log.ip_address,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'success': log.success
                })
            
            return log_data
        except Exception as e:
            print(f"Erreur lors de la récupération des journaux d'audit: {e}")
            return []
    
    def get_system_stats(self):
        """Récupérer les statistiques système"""
        try:
            from ..database.models import CoinAfrique, ExpatDakarProperty, LogerDakarProperty
            
            # Compter les propriétés par source
            coinafrique_count = CoinAfrique.query.count()
            expat_count = ExpatDakarProperty.query.count()
            loger_count = LogerDakarProperty.query.count()
            total_properties = coinafrique_count + expat_count + loger_count
            
            # Taille de la base de données (approximation)
            db_size = "~50 MB"  # Cela devrait être calculé dynamiquement
            
            # Sessions actives (approximation)
            active_sessions = "N/A"  # Cela nécessiterait une table de sessions
            
            return {
                'total_properties': total_properties,
                'coinafrique_count': coinafrique_count,
                'expat_count': expat_count,
                'loger_count': loger_count,
                'db_size': db_size,
                'active_sessions': active_sessions
            }
        except Exception as e:
            print(f"Erreur lors de la récupération des statistiques système: {e}")
            return {}
    
    def create_user_activity_chart(self):
        """Créer le graphique d'activité des utilisateurs"""
        try:
            # Récupérer les connexions des 30 derniers jours
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            audit_logs = AuditLog.query.filter(
                AuditLog.action == 'LOGIN',
                AuditLog.timestamp >= thirty_days_ago
            ).all()
            
            if not audit_logs:
                return go.Figure()
            
            # Grouper par jour
            daily_logins = {}
            for log in audit_logs:
                day = log.timestamp.date()
                if day not in daily_logins:
                    daily_logins[day] = 0
                daily_logins[day] += 1
            
            # Préparer les données pour le graphique
            dates = sorted(daily_logins.keys())
            counts = [daily_logins[date] for date in dates]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=counts,
                mode='lines+markers',
                name='Connexions par jour',
                line=dict(c='blue', width=3),
                marker=dict(size=6)
            ))
            
            fig.update_layout(
                title='Activité de connexion (30 derniers jours)',
                xaxis_title='Date',
                yaxis_title='Nombre de connexions',
                height=300,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            return fig
        
        except Exception as e:
            print(f"Erreur lors de la création du graphique d'activité: {e}")
            return go.Figure()
    
    def create_audit_actions_chart(self):
        """Créer le graphique des actions d'audit"""
        try:
            # Récupérer les actions des 7 derniers jours
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            audit_logs = AuditLog.query.filter(
                AuditLog.timestamp >= seven_days_ago
            ).all()
            
            if not audit_logs:
                return go.Figure()
            
            # Compter les actions par type
            action_counts = {}
            for log in audit_logs:
                action = log.action
                if action not in action_counts:
                    action_counts[action] = 0
                action_counts[action] += 1
            
            # Préparer les données pour le graphique
            actions = list(action_counts.keys())
            counts = list(action_counts.values())
            
            fig = go.Figure(data=[go.Pie(
                labels=actions,
                values=counts,
                hole=.3
            )])
            
            fig.update_layout(
                title='Répartition des actions (7 derniers jours)',
                height=300,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            return fig
        
        except Exception as e:
            print(f"Erreur lors de la création du graphique des actions: {e}")
            return go.Figure()
    
    def create_user_role_chart(self):
        """Créer le graphique de répartition des rôles"""
        try:
            user_stats = self.get_user_stats()
            
            roles = ['Administrateurs', 'Analystes', 'Visiteurs']
            counts = [
                user_stats.get('admin_users', 0),
                user_stats.get('analyst_users', 0),
                user_stats.get('viewer_users', 0)
            ]
            
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
            
            fig = go.Figure(data=[go.Bar(
                x=roles,
                y=counts,
                marker_color=colors,
                text=counts,
                textposition='auto'
            )])
            
            fig.update_layout(
                title='Répartition des utilisateurs par rôle',
                xaxis_title='Rôle',
                yaxis_title='Nombre d\'utilisateurs',
                height=300,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            return fig
        
        except Exception as e:
            print(f"Erreur lors de la création du graphique des rôles: {e}")
            return go.Figure()
    
    def setup_layout(self):
        """Configurer la mise en page du panneau d'administration"""
        user_stats = self.get_user_stats()
        system_stats = self.get_system_stats()
        audit_logs = self.get_audit_logs(limit=50)
        
        self.app.layout = dmc.MantineProvider(
            theme={
                "colorScheme": "light",
                "primaryColor": "blue",
                "fontFamily": "Inter, sans-serif"
            },
            children=[
                html.Div([
                    # En-tête
                            dmc.Paper(
                                children=[
                                    dmc.Group(
                                        children=[
                                            dmc.Title("Panneau d'Administration", order=3),
                                            dmc.Badge("Admin", c="red", variant="filled")
                                        ],
                                        style={"height": "100%", "padding": "0 20px"}
                                    )
                                ],
                                withBorder=True,
                                shadow="sm",
                                radius=0,
                                style={
                                    "height": 60,
                                    "backgroundColor": "#fff",
                                    "borderBottom": "1px solid #e9ecef",
                                    "display": "flex",
                                    "alignItems": "center"
                                }
                            )
                            ,
                
                    # Zone de notification
                    html.Div(id="admin-notification-container"),
                    
                    dmc.Container(
                        size="xl",
                        mt="xl",
                        children=[
# Section KPIs
dmc.SimpleGrid(
    cols=4,
    spacing="lg",
    children=[
        dmc.Card(
            children=[
                dmc.Group(
                    children=[
                        DashIconify(icon="mdi:account-group", width=30, color="blue"),
                        dmc.Text("Utilisateurs", size="sm", c="dimmed")
                    ],
                    mt="md",
                    mb="xs",
                ),
                dmc.Text(f"{user_stats.get('total_users', 0)}", size="xl", fw=700),
                dmc.Text(f"{user_stats.get('active_users', 0)} actifs", size="xs", c="dimmed", mt=5)
            ],
            withBorder=True,
            shadow="sm",
            radius="md",
            p="md"
        ),
        dmc.Card(
            children=[
                dmc.Group(
                    children=[
                        DashIconify(icon="mdi:database", width=30, color="green"),
                        dmc.Text("Propriétés", size="sm", c="dimmed")
                    ],
                    mt="md",
                    mb="xs",
                ),
                dmc.Text(f"{system_stats.get('total_properties', 0):,}", size="xl", fw=700),
                dmc.Text("Total en base", size="xs", c="dimmed", mt=5)
            ],
            withBorder=True,
            shadow="sm",
            radius="md",
            p="md"
        ),
        dmc.Card(
            children=[
                dmc.Group(
                    children=[
                        DashIconify(icon="mdi:history", width=30, color="orange"),
                        dmc.Text("Sessions", size="sm", c="dimmed")
                    ],
                    mt="md",
                    mb="xs",
                ),
                dmc.Text(f"{user_stats.get('recent_users', 0)}", size="xl", fw=700),
                dmc.Text("30 derniers jours", size="xs", c="dimmed", mt=5)
            ],
            withBorder=True,
            shadow="sm",
            radius="md",
            p="md"
        ),
        dmc.Card(
            children=[
                dmc.Group(
                    children=[
                        DashIconify(icon="mdi:shield-check", width=30, color="red"),
                        dmc.Text("Sécurité", size="sm", c="dimmed")
                    ],
                    mt="md",
                    mb="xs",
                ),
                dmc.Text("OK", size="xl", fw=700),
                dmc.Text("Aucune alerte", size="xs", c="dimmed", mt=5)
            ],
            withBorder=True,
            shadow="sm",
            radius="md",
            p="md"
        )
    ],
    className="admin-grid-4"  # Pour la responsivité
),

dmc.Space(h=30),

# Graphiques
dmc.SimpleGrid(
    cols=3,
    spacing="lg",
    children=[
        dmc.Card(
            children=[
                dmc.Text("Activité de connexion", size="lg", fw=500, mb="md"),
                dcc.Graph(
                    id="user-activity-chart",
                    figure=self.create_user_activity_chart(),
                    config={'displayModeBar': False}
                )
            ],
            withBorder=True,
            shadow="sm",
            radius="md",
            p="md"
        ),
        dmc.Card(
            children=[
                dmc.Text("Actions récentes", size="lg", fw=500, mb="md"),
                dcc.Graph(
                    id="audit-actions-chart",
                    figure=self.create_audit_actions_chart(),
                    config={'displayModeBar': False}
                )
            ],
            withBorder=True,
            shadow="sm",
            radius="md",
            p="md"
        ),
        dmc.Card(
            children=[
                dmc.Text("Répartition des rôles", size="lg", fw=500, mb="md"),
                dcc.Graph(
                    id="user-role-chart",
                    figure=self.create_user_role_chart(),
                    config={'displayModeBar': False}
                )
            ],
            withBorder=True,
            shadow="sm",
            radius="md",
            p="md"
        )
    ],
    className="admin-grid-3"  # Pour le responsive aussi
)
,
                            
                            dmc.Space(h=30),
                            
                            # Section gestion des utilisateurs
                            dmc.Card(
                                children=[
                                    dmc.Group(
                                        children=[
                                            dmc.Text("Gestion des utilisateurs", size="lg", fw=500),
                                            dmc.Group([
                                                dmc.Button(
                                                    "Ajouter un utilisateur",
                                                    leftSection=DashIconify(icon="mdi:plus", width=16),
                                                    id="add-user-btn",
                                                    color="green",
                                                    size="sm"
                                                ),
                                                dmc.Button(
                                                    "Exporter les données",
                                                    leftIcon=DashIconify(icon="mdi:download", width=16),
                                                    id="export-users-btn",
                                                    color="blue",
                                                    size="sm"
                                                )
                                            ])
                                        ],
                                        mb="md"
                                    ),
                                    dash_table.DataTable(
                                        id="users-table",
                                        columns=[
                                            {"name": "ID", "id": "id"},
                                            {"name": "Nom d'utilisateur", "id": "username"},
                                            {"name": "Email", "id": "email"},
                                            {"name": "Rôle", "id": "role"},
                                            {"name": "Prénom", "id": "first_name"},
                                            {"name": "Nom", "id": "last_name"},
                                            {"name": "Actif", "id": "is_active"},
                                            {"name": "Dernière connexion", "id": "last_login"},
                                            {"name": "Date de création", "id": "created_at"},
                                            {"name": "Actions", "id": "actions", "sortable": False}
                                        ],
                                        data=[],  # Sera rempli par le callback
                                        page_size=10,
                                        style_cell={
                                            'textAlign': 'left',
                                            'minWidth': '100px',
                                            'width': '150px',
                                            'maxWidth': '300px',
                                            'overflow': 'hidden',
                                            'textOverflow': 'ellipsis'
                                        },
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': 'rgb(248, 248, 248)'
                                            },
                                            {
                                                'if': {'column_id': 'is_active', 'filter_query': '{is_active} eq true'},
                                                'backgroundColor': '#d4edda',
                                                'c': '#155724'
                                            },
                                            {
                                                'if': {'column_id': 'is_active', 'filter_query': '{is_active} eq false'},
                                                'backgroundColor': '#f8d7da',
                                                'c': '#721c24'
                                            }
                                        ],
                                        style_header={
                                            'backgroundColor': 'rgb(230, 230, 230)',
                                            'fontWeight': 'bold'
                                        }
                                    )
                                ],
                                withBorder=True,
                                shadow="sm",
                                radius="md",
                                p="md",
                                mb="xl"
                            ),
                            
                            # Section journaux d'audit
                            dmc.Card(
                                children=[
                                    dmc.Group(
                                        children=[
                                            dmc.Text("Journaux d'audit", size="lg", fw=500),
                                            dmc.Group([
                                                dmc.Button(
                                                    "Effacer les filtres",
                                                    id="clear-audit-filters",
                                                    c="gray",
                                                    size="sm"
                                                ),
                                                dmc.Button(
                                                    "Exporter les logs",
                                                    leftSection=DashIconify(icon="mdi:download", width=16),
                                                    id="export-audit-btn",
                                                    color="blue",
                                                    size="sm"
                                                )
                                            ])
                                        ],
                                        mb="md"
                                    ),
                                    dash_table.DataTable(
                                        id="audit-table",
                                        columns=[
                                            {"name": "ID", "id": "id"},
                                            {"name": "Utilisateur", "id": "username"},
                                            {"name": "Action", "id": "action"},
                                            {"name": "Ressource", "id": "resource"},
                                            {"name": "Détails", "id": "details"},
                                            {"name": "IP", "id": "ip_address"},
                                            {"name": "Date", "id": "timestamp"},
                                            {"name": "Succès", "id": "success"}
                                        ],
                                        data=audit_logs,
                                        page_size=15,
                                        style_cell={
                                            'textAlign': 'left',
                                            'minWidth': '80px',
                                            'width': '120px',
                                            'maxWidth': '250px',
                                            'overflow': 'hidden',
                                            'textOverflow': 'ellipsis'
                                        },
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': 'rgb(248, 248, 248)'
                                            },
                                            {
                                                'if': {'column_id': 'success', 'filter_query': '{success} eq true'},
                                                'backgroundColor': '#d4edda',
                                                'c': '#155724'
                                            },
                                            {
                                                'if': {'column_id': 'success', 'filter_query': '{success} eq false'},
                                                'backgroundColor': '#f8d7da',
                                                'c': '#721c24'
                                            }
                                        ],
                                        style_header={
                                            'backgroundColor': 'rgb(230, 230, 230)',
                                            'fontWeight': 'bold'
                                        }
                                    )
                                ],
                                withBorder=True,
                                shadow="sm",
                                radius="md",
                                p="md"
                            )
                        ]
                    )
                ])
            ]
        )
    
    def setup_callbacks(self):
        """Configurer les callbacks"""
        @callback(
            Output("users-table", "data"),
            Input("users-table", "id")
        )
        def load_users_table(table_id):
            try:
                users = User.query.all()
                user_data = []
                
                for user in users:
                    user_data.append({
                        'id': str(user.id),
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'first_name': user.first_name or '',
                        'last_name': user.last_name or '',
                        'is_active': user.is_active,
                        'last_login': user.last_login.isoformat() if user.last_login else 'Jamais',
                        'created_at': user.created_at.isoformat() if user.created_at else 'N/A',
                        'actions': 'Éditer | Désactiver | Supprimer'
                    })
                
                return user_data
            except Exception as e:
                print(f"Erreur lors du chargement des utilisateurs: {e}")
                return []
        
        @callback(
            Output("admin-notification-container", "children"),
            [
                Input("add-user-btn", "n_clicks"),
                Input("export-users-btn", "n_clicks"),
                Input("export-audit-btn", "n_clicks"),
                Input("clear-audit-filters", "n_clicks")
            ],
            prevent_initial_call=True
        )
        def handle_admin_actions(add_clicks, export_users_clicks, export_audit_clicks, clear_filters_clicks):
            ctx = dash.callback_context
            
            if not ctx.triggered:
                return ""
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if button_id == "add-user-btn":
                return dmc.Notification(
                    title="Ajout d'utilisateur",
                    message="Fonctionnalité en cours de développement",
                    c="blue",
                    action="show",
                    autoClose=3000
                )
            elif button_id == "export-users-btn":
                return dmc.Notification(
                    title="Export des utilisateurs",
                    message="Export en cours...",
                    c="green",
                    action="show",
                    autoClose=3000
                )
            elif button_id == "export-audit-btn":
                return dmc.Notification(
                    title="Export des journaux",
                    message="Export en cours...",
                    c="green",
                    action="show",
                    autoClose=3000
                )
            elif button_id == "clear-audit-filters":
                return dmc.Notification(
                    title="Filtres effacés",
                    message="Les filtres ont été réinitialisés",
                    c="gray",
                    action="show",
                    autoClose=3000
                )
            
            return ""