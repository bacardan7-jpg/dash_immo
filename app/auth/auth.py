import bcrypt
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import redis
import json
from ..database.models import db, User, AuditLog
from sqlalchemy.exc import ProgrammingError, OperationalError

auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()

# Configuration Redis pour la gestion de session
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(uuid.UUID(user_id))
    except:
        return None

@login_manager.unauthorized_handler
def unauthorized():
    if request.is_json:
        return jsonify({'error': 'Authentification requise'}), 401
    return redirect(url_for('auth.login'))

def hash_password(password):
    """Hacher le mot de passe avec bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    """Vérifier le mot de passe"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def log_audit_action(user_id, action, resource, details=None, success=True):
    """Enregistrer une action d'audit"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        success=success
    )
    db.session.add(audit_log)
    db.session.commit()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        
        if not username or not password:
            if request.is_json:
                return jsonify({'error': 'Nom d\'utilisateur et mot de passe requis'}), 400
            flash('Nom d\'utilisateur et mot de passe requis', 'error')
            return render_template('auth/login.html')
        
        # Rechercher l'utilisateur
        try:
            user = User.query.filter_by(username=username).first()
        except (ProgrammingError, OperationalError) as e:
            # Database schema may be out-of-sync (missing columns/tables).
            print(f"DB error during login lookup: {e}")
            if request.is_json:
                return jsonify({'error': 'Service indisponible, base de données inaccessible'}), 503
            flash('Service indisponible, veuillez réessayer plus tard', 'error')
            return render_template('auth/login.html'), 503
        
        if user and verify_password(password, user.password_hash):
            if not user.is_active:
                if request.is_json:
                    return jsonify({'error': 'Compte désactivé'}), 403
                flash('Votre compte est désactivé', 'error')
                return render_template('auth/login.html')
            
            # Mettre à jour la dernière connexion
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Connecter l'utilisateur
            login_user(user, remember=True)
            
            # Journaliser la connexion
            log_audit_action(user.id, 'LOGIN', 'AUTHENTICATION', success=True)
            
            # Créer un token JWT pour les requêtes API
            access_token = create_access_token(identity=str(user.id))
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'access_token': access_token,
                    'user': {
                        'id': str(user.id),
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    }
                })
            
            flash('Connexion réussie!', 'success')
            next_page = request.args.get('next')
            
            # REDIRECTION SELON LE RÔLE
            if user.role == 'viewer':
                return redirect(url_for('viewer'))  # Espace viewer dédié
            elif user.role in ['analyst', 'admin']:
                return redirect(next_page or url_for('dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            # Journaliser l'échec de connexion
            if user:
                log_audit_action(user.id, 'LOGIN_FAILED', 'AUTHENTICATION', success=False)
            
            if request.is_json:
                return jsonify({'error': 'Nom d\'utilisateur ou mot de passe incorrect'}), 401
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    user_id = current_user.id
    logout_user()
    
    # Journaliser la déconnexion
    log_audit_action(user_id, 'LOGOUT', 'AUTHENTICATION', success=True)
    
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
        else:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
        
        # Validation
        if not all([username, email, password]):
            if request.is_json:
                return jsonify({'error': 'Tous les champs obligatoires doivent être remplis'}), 400
            flash('Tous les champs obligatoires doivent être remplis', 'error')
            return render_template('auth/register.html')
        
        # Vérifier si l'utilisateur existe déjà
        try:
            username_exists = User.query.filter_by(username=username).first()
        except (ProgrammingError, OperationalError) as e:
            print(f"DB error during register username check: {e}")
            if request.is_json:
                return jsonify({'error': 'Service indisponible, base de données inaccessible'}), 503
            flash('Service indisponible, veuillez réessayer plus tard', 'error')
            return render_template('auth/register.html'), 503

        if username_exists:
            if request.is_json:
                return jsonify({'error': 'Nom d\'utilisateur déjà pris'}), 400
            flash('Nom d\'utilisateur déjà pris', 'error')
            return render_template('auth/register.html')

        try:
            email_exists = User.query.filter_by(email=email).first()
        except (ProgrammingError, OperationalError) as e:
            print(f"DB error during register email check: {e}")
            if request.is_json:
                return jsonify({'error': 'Service indisponible, base de données inaccessible'}), 503
            flash('Service indisponible, veuillez réessayer plus tard', 'error')
            return render_template('auth/register.html'), 503

        if email_exists:
            if request.is_json:
                return jsonify({'error': 'Email déjà utilisé'}), 400
            flash('Email déjà utilisé', 'error')
            return render_template('auth/register.html')
        
        # Créer le nouvel utilisateur
        password_hash = hash_password(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role='viewer'  # Rôle par défaut
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Journaliser l'inscription
        log_audit_action(new_user.id, 'REGISTER', 'USER_MANAGEMENT', success=True)
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Compte créé avec succès'})
        
        flash('Compte créé avec succès!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    if request.method == 'PUT':
        data = request.get_json()
        
        # Mise à jour du profil
        if 'first_name' in data:
            current_user.first_name = data['first_name']
        if 'last_name' in data:
            current_user.last_name = data['last_name']
        if 'email' in data:
            # Vérifier si l'email est déjà utilisé
            try:
                existing_user = User.query.filter_by(email=data['email']).first()
            except (ProgrammingError, OperationalError) as e:
                print(f"DB error during profile email check: {e}")
                return jsonify({'error': 'Service indisponible, base de données inaccessible'}), 503
            if existing_user and existing_user.id != current_user.id:
                return jsonify({'error': 'Email déjà utilisé'}), 400
            current_user.email = data['email']
        
        db.session.commit()
        
        # Journaliser la mise à jour
        log_audit_action(current_user.id, 'PROFILE_UPDATE', 'USER_MANAGEMENT', success=True)
        
        return jsonify({
            'success': True,
            'user': {
                'id': str(current_user.id),
                'username': current_user.username,
                'email': current_user.email,
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'role': current_user.role
            }
        })
    
    return jsonify({
        'user': {
            'id': str(current_user.id),
            'username': current_user.username,
            'email': current_user.email,
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'role': current_user.role
        }
    })

@auth_bp.route('/settings')
@login_required
def settings():
    """Page des paramètres utilisateur"""
    return render_template('auth/settings.html')

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Mot de passe actuel et nouveau mot de passe requis'}), 400
    
    # Vérifier le mot de passe actuel
    if not verify_password(current_password, current_user.password_hash):
        log_audit_action(current_user.id, 'PASSWORD_CHANGE_FAILED', 'SECURITY', success=False)
        return jsonify({'error': 'Mot de passe actuel incorrect'}), 400
    
    # Mettre à jour le mot de passe
    current_user.password_hash = hash_password(new_password)
    db.session.commit()
    
    # Journaliser le changement
    log_audit_action(current_user.id, 'PASSWORD_CHANGE', 'SECURITY', success=True)
    
    return jsonify({'success': True, 'message': 'Mot de passe modifié avec succès'})

@auth_bp.route('/api/token')
@login_required
def get_api_token():
    """Obtenir un token JWT pour les requêtes API"""
    access_token = create_access_token(identity=str(current_user.id))
    return jsonify({'access_token': access_token})

@auth_bp.route('/health')
def health_check():
    """Endpoint de vérification de santé"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})