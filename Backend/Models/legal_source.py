from sqlalchemy import Column, String, Text, Integer, Boolean
from .base import DeclarativeBase

class LegalSource(DeclarativeBase):
    """Legal Source model for legal references"""
    
    __tablename__ = 'legal_sources'
    
    # Source information
    source_type = Column(String(50), nullable=False)  # LAW, REGULATION, DECISION, RULING
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Reference details
    reference_number = Column(String(100))
    publication_date = Column(String(50))  # Store as string
    effective_date = Column(String(50))    # Store as string
    
    # Content
    content = Column(Text)
    url = Column(String(500))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<LegalSource(type='{self.source_type}', title='{self.title}')>"
