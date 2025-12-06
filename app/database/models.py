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
    """Modèle pour les propriétés CoinAfrique"""
    __tablename__ = 'coinafriqure'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    price = Column(Float, nullable=False, index=True)
    price_unit = Column(String(50), default='FCFA')
    city = Column(String(100), nullable=False, index=True)
    country = Column(String(100), default='Sénégal')
    bedrooms = Column(Integer, nullable=True, index=True)
    bathrooms = Column(Integer, nullable=True, index=True)
    surface_area = Column(Float, nullable=True, index=True)
    surface_unit = Column(String(20), default='m²')
    property_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    contact_info = Column(String(200), nullable=True)
    images = Column(Text, nullable=True)  # JSON string for multiple images
    listing_url = Column(String(500), nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String(50), default='coinafrique')
    
    # Index pour améliorer les performances
    __table_args__ = (
        Index('idx_coinafrique_price_city', 'price', 'city'),
        Index('idx_coinafrique_type_city', 'property_type', 'city'),
        Index('idx_coinafrique_date', 'scraped_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'price_unit': self.price_unit,
            'city': self.city,
            'country': self.country,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'surface_area': self.surface_area,
            'surface_unit': self.surface_unit,
            'property_type': self.property_type,
            'description': self.description,
            'contact_info': self.contact_info,
            'images': self.images,
            'listing_url': self.listing_url,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'source': self.source
        }

class ExpatDakarProperty(db.Model):
    """Modèle pour les propriétés ExpatDakar"""
    __tablename__ = 'expat_dakar_properties'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    price = Column(Float, nullable=False, index=True)
    price_unit = Column(String(50), default='FCFA')
    city = Column(String(100), nullable=False, index=True)
    country = Column(String(100), default='Sénégal')
    region = Column(String(100), nullable=True, index=True)
    bedrooms = Column(Integer, nullable=True, index=True)
    bathrooms = Column(Integer, nullable=True, index=True)
    surface_area = Column(Float, nullable=True, index=True)
    surface_unit = Column(String(20), default='m²')
    property_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    contact_info = Column(String(200), nullable=True)
    images = Column(Text, nullable=True)  # JSON string for multiple images
    listing_url = Column(String(500), nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String(50), default='expat_dakar')
    
    # Index pour améliorer les performances
    __table_args__ = (
        Index('idx_expat_price_region', 'price', 'region'),
        Index('idx_expat_type_region', 'property_type', 'region'),
        Index('idx_expat_date', 'scraped_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'price_unit': self.price_unit,
            'city': self.city,
            'country': self.country,
            'region': self.region,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'surface_area': self.surface_area,
            'surface_unit': self.surface_unit,
            'property_type': self.property_type,
            'description': self.description,
            'contact_info': self.contact_info,
            'images': self.images,
            'listing_url': self.listing_url,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'source': self.source
        }

class LogerDakarProperty(db.Model):
    """Modèle pour les propriétés Loger Dakar"""
    __tablename__ = 'loger_dakar_properties'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    price = Column(Float, nullable=False, index=True)
    price_unit = Column(String(50), default='FCFA')
    city = Column(String(100), nullable=False, index=True)
    country = Column(String(100), default='Sénégal')
    district = Column(String(100), nullable=True, index=True)
    bedrooms = Column(Integer, nullable=True, index=True)
    bathrooms = Column(Integer, nullable=True, index=True)
    surface_area = Column(Float, nullable=True, index=True)
    surface_unit = Column(String(20), default='m²')
    property_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    contact_info = Column(String(200), nullable=True)
    images = Column(Text, nullable=True)  # JSON string for multiple images
    listing_url = Column(String(500), nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String(50), default='loger_dakar')
    
    # Index pour améliorer les performances
    __table_args__ = (
        Index('idx_loger_price_district', 'price', 'district'),
        Index('idx_loger_type_district', 'property_type', 'district'),
        Index('idx_loger_date', 'scraped_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'price_unit': self.price_unit,
            'city': self.city,
            'country': self.country,
            'district': self.district,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'surface_area': self.surface_area,
            'surface_unit': self.surface_unit,
            'property_type': self.property_type,
            'description': self.description,
            'contact_info': self.contact_info,
            'images': self.images,
            'listing_url': self.listing_url,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'source': self.source
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