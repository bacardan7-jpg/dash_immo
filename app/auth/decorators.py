from functools import wraps
from flask import jsonify
from flask_login import current_user

def role_required(role):
    """Décorateur pour vérifier le rôle de l'utilisateur"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentification requise'}), 401
            
            if not current_user.has_role(role):
                return jsonify({'error': 'Permissions insuffisantes'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Décorateur pour les administrateurs uniquement"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentification requise'}), 401
        
        if not current_user.is_admin():
            return jsonify({'error': 'Accès réservé aux administrateurs'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def analyst_required(f):
    """Décorateur pour les analystes et administrateurs"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentification requise'}), 401
        
        if not current_user.is_analyst():
            return jsonify({'error': 'Accès réservé aux analystes'}), 403
        
        return f(*args, **kwargs)
    return decorated_function