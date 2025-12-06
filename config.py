import os
from datetime import timedelta
from sqlalchemy.pool import NullPool

class Config:
    """Configuration de base pour l'application"""
    
    # Base de données
    # For Render free tier: disable SSL to avoid connection drops
    _db_url = os.environ.get('DATABASE_URL') or 'postgresql://neondb_owner:npg_9vrYBWUeT7js@ep-raspy-dust-a4a9f62f-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require'
    SQLALCHEMY_DATABASE_URI = _db_url.replace('?sslmode=require', '?sslmode=disable').replace('&sslmode=require', '&sslmode=disable')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': NullPool,  # Use NullPool to create fresh connection for each query
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'dash_immo'
        }
    }
    
    # Sécurité
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'votre-secret-key-tres-securise'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'votre-jwt-secret-key-tres-securise'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'app/static/uploads'
    
    # Pagination
    POSTS_PER_PAGE = 20
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}