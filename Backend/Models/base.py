from datetime import datetime
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr

class Base:
    """Base class for all models"""
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name"""
        return cls.__name__.lower()
    
    # Common columns for all models
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result
    
    def update(self, **kwargs):
        """Update model instance with provided attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def get_by_id(cls, db, id):
        """Get model instance by ID"""
        return db.session.get(cls, id)
    
    def save(self, db):
        """Save model instance to database"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self, db):
        """Delete model instance from database"""
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        """String representation of model instance"""
        return f"<{self.__class__.__name__}(id={self.id})>"

# Create declarative base
DeclarativeBase = declarative_base(cls=Base)
