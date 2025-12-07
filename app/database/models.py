from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modèle utilisateur pour l'authentification"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    role = Column(String(20), default='viewer', nullable=False)  # admin, analyst, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relations
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def has_role(self, role):
        return self.role == role
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_analyst(self):
        return self.role in ['admin', 'analyst']

class CoinAfrique(db.Model):
    """Modèle pour les propriétés CoinAfrique (créées par pipeline Scrapy)"""
    __tablename__ = 'coinafrique'
    
    id = Column(String(32), primary_key=True)
    url = Column(Text, unique=True)
    title = Column(Text)
    price = Column(Integer)
    surface_area = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    city = Column(String(100))
    description = Column(Text)
    source = Column(String(50))
    latitude = Column(Float)
    longitude = Column(Float)
    scraped_at = Column(DateTime)
    statut = Column(String(50))
    nb_annonces = Column(Integer)
    posted_time = Column(String(100))
    adresse = Column(String(100))
    property_type = Column(String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'price': self.price,
            'surface_area': self.surface_area,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'city': self.city,
            'description': self.description,
            'source': self.source,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'statut': self.statut,
            'nb_annonces': self.nb_annonces,
            'posted_time': self.posted_time,
            'adresse': self.adresse,
            'property_type': self.property_type
        }

class ExpatDakarProperty(db.Model):
    """Modèle pour les propriétés ExpatDakar (créées par pipeline Scrapy)"""
    __tablename__ = 'expat_dakar_properties'
    
    id = Column(String(32), primary_key=True)
    url = Column(Text, unique=True)
    title = Column(Text)
    price = Column(Integer)
    surface_area = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    city = Column(String(100))
    region = Column(String(100))
    description = Column(Text)
    source = Column(String(50))
    scraped_at = Column(DateTime)
    statut = Column(String(50))
    posted_time = Column(String(100))
    adresse = Column(String(100))
    property_type = Column(String(100))
    member_since = Column(String(50))
    
    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'price': self.price,
            'surface_area': self.surface_area,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'city': self.city,
            'region': self.region,
            'description': self.description,
            'source': self.source,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'statut': self.statut,
            'posted_time': self.posted_time,
            'adresse': self.adresse,
            'property_type': self.property_type,
            'member_since': self.member_since
        }

class LogerDakarProperty(db.Model):
    """Modèle pour les propriétés Loger Dakar (créées par pipeline Scrapy)"""
    __tablename__ = 'loger_dakar_properties'
    
    id = Column(String(32), primary_key=True)
    url = Column(Text, unique=True)
    title = Column(Text)
    price = Column(Integer)
    surface_area = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    city = Column(String(100))
    region = Column(String(100))
    description = Column(Text)
    source = Column(String(50))
    scraped_at = Column(DateTime)
    statut = Column(String(50))
    posted_time = Column(String(100))
    adresse = Column(String(100))
    property_type = Column(String(100))
    listing_id = Column(String(50))
    
    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'price': self.price,
            'surface_area': self.surface_area,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'city': self.city,
            'region': self.region,
            'description': self.description,
            'source': self.source,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'statut': self.statut,
            'posted_time': self.posted_time,
            'adresse': self.adresse,
            'property_type': self.property_type,
            'listing_id': self.listing_id
        }


class ProprietesConsolidees(db.Model):
    """Table consolidée des propriétés de tous les sources (créée par Airflow)"""
    __tablename__ = 'proprietes_consolidees'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False, index=True)  # coinafrique, expatdakar, logerdakar
    original_id = Column(Integer, nullable=True)  # ID original de la source
    url = Column(String(500), nullable=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    price = Column(Float, nullable=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    property_type = Column(String(100), nullable=False, index=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    surface_area = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    posted_time = Column(DateTime, nullable=True)
    adresse = Column(String(500), nullable=True)
    statut = Column(String(50), nullable=True)
    scraped_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour améliorer les performances
    __table_args__ = (
        Index('idx_proprietes_source_url', 'source', 'url'),
        Index('idx_proprietes_city_type', 'city', 'property_type'),
        Index('idx_proprietes_date', 'scraped_at'),
    )
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'source': self.source,
            'original_id': self.original_id,
            'url': self.url,
            'title': self.title,
            'price': self.price,
            'city': self.city,
            'description': self.description,
            'property_type': self.property_type,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'surface_area': self.surface_area,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'posted_time': self.posted_time.isoformat() if self.posted_time else None,
            'adresse': self.adresse,
            'statut': self.statut,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class AuditLog(db.Model):
    """Journal d'audit pour les actions sensibles"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    success = Column(Boolean, default=True)
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_id}>'

class DashboardConfig(db.Model):
    """Configuration des dashboards"""
    __tablename__ = 'dashboard_configs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    config_data = Column(Text, nullable=False)  # JSON string
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f'<DashboardConfig {self.name}>'