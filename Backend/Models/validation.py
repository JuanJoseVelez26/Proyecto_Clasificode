from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import DeclarativeBase

class Validation(DeclarativeBase):
    """Validation model for case validations"""
    
    __tablename__ = 'validations'
    
    # Validation information
    validation_type = Column(String(50), nullable=False)  # RULE_CHECK, SEMANTIC_CHECK, MANUAL
    status = Column(String(20), nullable=False)  # PASSED, FAILED, WARNING
    message = Column(Text)
    
    # Details
    details = Column(Text)  # JSON string with validation details
    score = Column(String(10))  # Validation score if applicable
    
    # Relationships
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    case = relationship("Case", back_populates="validations")
    
    def __repr__(self):
        return f"<Validation(type='{self.validation_type}', status='{self.status}')>"
