from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import DeclarativeBase

class HSNote(DeclarativeBase):
    """HS Note model for explanatory notes"""
    
    __tablename__ = 'hs_notes'
    
    # Note information
    note_type = Column(String(50), nullable=False)  # SECTION, CHAPTER, HEADING
    note_number = Column(String(20))
    title = Column(String(200))
    content = Column(Text, nullable=False)
    
    # Language
    language = Column(String(10), default='en')  # en, es
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    hs_item_id = Column(Integer, ForeignKey('hs_items.id'), nullable=False)
    hs_item = relationship("HSItem", back_populates="notes_rel")
    
    def __repr__(self):
        return f"<HSNote(type='{self.note_type}', title='{self.title[:50]}...')>"
