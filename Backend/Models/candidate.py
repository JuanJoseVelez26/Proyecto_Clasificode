from sqlalchemy import Column, String, Text, Integer, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from .base import DeclarativeBase

class Candidate(DeclarativeBase):
    """Candidate model for classification candidates"""
    
    __tablename__ = 'candidates'
    
    # Candidate information
    hs_code = Column(String(20), nullable=False, index=True)
    description = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    ranking_position = Column(Integer, default=1)
    
    # Classification method
    classification_method = Column(String(50), nullable=False)  # RGI, SEMANTIC, HYBRID
    rule_applied = Column(String(100))  # Which RGI rule was applied
    semantic_similarity = Column(Float)  # Semantic similarity score
    
    # Reasoning
    reasoning = Column(Text)  # Explanation of why this candidate was selected
    evidence = Column(Text)   # Supporting evidence
    
    # Status
    is_selected = Column(Boolean, default=False)
    is_rejected = Column(Boolean, default=False)
    
    # Relationships
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    case = relationship("Case", back_populates="candidates")
    hs_item_id = Column(Integer, ForeignKey('hs_items.id'))
    hs_item = relationship("HSItem")
    
    def __repr__(self):
        return f"<Candidate(hs_code='{self.hs_code}', confidence={self.confidence_score}, method='{self.classification_method}')>"
