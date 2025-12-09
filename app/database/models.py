from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Date, Boolean, ForeignKey, Index, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modèle utilisateur premium"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    role = Column(String(20), default='viewer', nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    preferences = Column(JSONB, default=lambda: {})
    
    # Relations
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    saved_configs = db.relationship('DashboardConfig', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def has_role(self, role):
        return self.role == role
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_analyst(self):
        return self.role in ['admin', 'analyst']

class ProprietesConsolidees(db.Model):
    """Table consolidée premium"""
    __tablename__ = 'proprietes_consolidees'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False, index=True)
    original_id = Column(String(100), nullable=True, index=True)
    url = Column(String(500), nullable=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    price = Column(Numeric(15, 2), nullable=True, index=True)
    currency = Column(String(3), default='XOF')
    price_per_m2 = Column(Numeric(15, 2), nullable=True, index=True)
    
    # Localisation
    city = Column(String(100), nullable=False, index=True)
    region = Column(String(100), nullable=True, index=True)
    district = Column(String(100), nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geohash = Column(String(20), nullable=True, index=True)
    
    # Caractéristiques
    property_type = Column(String(100), nullable=False, index=True)
    property_subtype = Column(String(100), nullable=True, index=True)
    bedrooms = Column(Integer, nullable=True, index=True)
    bathrooms = Column(Integer, nullable=True)
    surface_area = Column(Float, nullable=True, index=True)
    land_area = Column(Float, nullable=True)
    year_built = Column(Integer, nullable=True)
    floor = Column(Integer, nullable=True)
    total_floors = Column(Integer, nullable=True)
    furnishing = Column(String(50), nullable=True)
    condition = Column(String(50), nullable=True)
    
    # Description & Médias
    description = Column(Text, nullable=True)
    description_lang = Column(String(10), default='fr')
    description_sentiment = Column(Float, nullable=True)
    description_length = Column(Integer, nullable=True)
    image_urls = Column(JSONB, default=list)
    video_urls = Column(JSONB, default=list)
    
    # Contact & Auteur
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(100), nullable=True)
    author_name = Column(String(100), nullable=True)
    author_type = Column(String(50), nullable=True)  # particulier, professionnel
    listing_id = Column(String(50), nullable=True, index=True)
    
    # Statut & Dates
    statut = Column(String(50), nullable=True, index=True)
    posted_time = Column(DateTime, nullable=True, index=True)
    scraped_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Métadonnées & Scoring
    # NOTE: 'metadata' is a reserved attribute name in SQLAlchemy's Declarative API,
    # so use a different column attribute name and expose it as 'metadata' in the
    # `to_dict` output to preserve external contract.
    metadata_json = Column(JSONB, default=dict)
    quality_score = Column(Float, default=0.0, index=True)
    completeness_score = Column(Float, default=0.0)
    duplication_score = Column(Float, default=0.0)
    
    # Analytique
    view_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    contact_count = Column(Integer, default=0)
    
    # Index avancés
    __table_args__ = (
        Index('idx_proprietes_location', 'latitude', 'longitude'),
        Index('idx_proprietes_price_surface', 'price', 'surface_area'),
        Index('idx_proprietes_quality', 'quality_score'),
        Index('idx_proprietes_date_city', 'scraped_at', 'city'),
        Index('idx_proprietes_sentiment', 'description_sentiment'),
        # GIST index pour géospatial (à activer si PostGIS)
        # Index('idx_proprietes_geohash', 'geohash', postgresql_using='gist'),
    )
    
    def calculate_quality_score(self):
        """Calculer le score de qualité de l'annonce"""
        score = 0
        max_score = 100
        
        # Complétude des champs (40 points)
        if self.price: score += 10
        if self.surface_area: score += 10
        if self.description and len(self.description) > 50: score += 10
        if self.image_urls and len(self.image_urls) > 0: score += 10
        
        # Qualité des données (30 points)
        if self.price_per_m2 and self.price_per_m2 > 0: score += 10
        if self.description_sentiment is not None: score += 10
        if self.geohash or (self.latitude and self.longitude): score += 10
        
        # Fraîcheur (20 points)
        if self.posted_time:
            days_old = (datetime.utcnow() - self.posted_time).days
            score += max(0, 20 - days_old)
        
        # Intéractions (10 points)
        score += min(10, (self.view_count or 0) / 10)
        
        self.quality_score = score
        return score
    
    def to_dict(self, include_metadata=False):
        data = {
            'id': str(self.id),
            'source': self.source,
            'url': self.url,
            'title': self.title,
            'price': float(self.price) if self.price else None,
            'currency': self.currency,
            'price_per_m2': float(self.price_per_m2) if self.price_per_m2 else None,
            'city': self.city,
            'region': self.region,
            'district': self.district,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'property_type': self.property_type,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'surface_area': self.surface_area,
            'description': self.description,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'quality_score': self.quality_score,
        }
        
        if include_metadata:
            data.update({
                'metadata': self.metadata_json,
                'image_urls': self.image_urls,
                'contact_phone': self.contact_phone,
                'author_name': self.author_name,
                'view_count': self.view_count
            })
        
        return data

class AuditLog(db.Model):
    """Journal d'audit détaillé"""
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSONB, default=dict)
    
    # Contexte
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    referer = Column(String(500), nullable=True)
    
    # Géolocalisation
    country = Column(String(50), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Performance
    response_time = Column(Float, nullable=True)
    status_code = Column(Integer, nullable=True)
    
    # Flags
    success = Column(Boolean, default=True)
    is_api_call = Column(Boolean, default=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'action': self.action,
            'resource': self.resource,
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'details': self.details,
            'ip_address': self.ip_address
        }

class DashboardConfig(db.Model):
    """Configuration des dashboards"""
    __tablename__ = 'dashboard_configs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    config_data = Column(JSONB, nullable=False)
    
    # Propriétaire
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Permissions
    is_public = Column(Boolean, default=False)
    is_template = Column(Boolean, default=False)
    
    # Versioning
    version = Column(Integer, default=1)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('dashboard_configs.id'), nullable=True)
    
    # Statut
    is_active = Column(Boolean, default=True)
    is_favorite = Column(Boolean, default=False)
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_viewed = Column(DateTime, nullable=True)
    
    # Relations
    children = db.relationship('DashboardConfig', backref='parent', remote_side=[id])
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'config_data': self.config_data,
            'version': self.version,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat()
        }

class MarketIndex(db.Model):
    """Index du marché immobilier (calculé quotidiennement)"""
    __tablename__ = 'market_indices'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    index_name = Column(String(50), nullable=False)  # price_index, volume_index, volatility_index
    index_value = Column(Float, nullable=False)
    base_value = Column(Float, default=100.0)
    
    # Période
    date = Column(Date, nullable=False, index=True)
    period = Column(String(10), nullable=False)  # daily, weekly, monthly
    
    # Métadonnées
    calculation_method = Column(String(100), nullable=True)
    sample_size = Column(Integer, nullable=True)
    confidence_interval = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_market_index_composite', 'index_name', 'date', 'period', unique=True),
    )

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
