from sqlalchemy import Column, String, Text, Integer, Boolean
from .base import DeclarativeBase

class RGIRule(DeclarativeBase):
    """RGI Rule model for General Rules of Interpretation"""
    
    __tablename__ = 'rgi_rules'
    
    # Rule information
    rule_number = Column(Integer, nullable=False, unique=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Rule content
    rule_text = Column(Text, nullable=False)
    examples = Column(Text)
    exceptions = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<RGIRule(rule_number={self.rule_number}, title='{self.title}')>"
