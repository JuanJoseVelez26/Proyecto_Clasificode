from sqlalchemy import Column, String, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import VECTOR
from .base import DeclarativeBase

class Embedding(DeclarativeBase):
    """Embedding model for semantic vectors"""
    
    __tablename__ = 'embeddings'
    
    # Embedding information
    model_name = Column(String(100), nullable=False)
    vector_dimension = Column(Integer, nullable=False)
    embedding_vector = Column(VECTOR(1536))  # OpenAI ada-002 dimension
    
    # Metadata
    text_content = Column(String, nullable=False)  # Text that was embedded
    content_type = Column(String(50), nullable=False)  # DESCRIPTION, NOTE, RULE
    
    # Relationships
    hs_item_id = Column(Integer, ForeignKey('hs_items.id'), nullable=False)
    hs_item = relationship("HSItem", back_populates="embeddings")
    
    def __repr__(self):
        return f"<Embedding(model='{self.model_name}', content_type='{self.content_type}')>"
