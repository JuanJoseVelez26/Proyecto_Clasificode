from sqlalchemy import Column, String, Text, Integer, Float, Boolean, Index
from sqlalchemy.orm import relationship
from .base import DeclarativeBase

class HSItem(DeclarativeBase):
    """HS Item model for Harmonized System catalog"""
    
    __tablename__ = 'hs_items'
    
    # HS Code information
    hs_code = Column(String(20), unique=True, nullable=False, index=True)
    chapter = Column(String(2), nullable=False, index=True)
    heading = Column(String(4), nullable=False, index=True)
    subheading = Column(String(6), nullable=False, index=True)
    full_code = Column(String(12), nullable=False, index=True)
    
    # Description
    description = Column(Text, nullable=False)
    english_description = Column(Text)
    spanish_description = Column(Text)
    
    # Classification details
    level = Column(Integer, default=1)  # 1=Chapter, 2=Heading, 3=Subheading, 4=Full
    parent_code = Column(String(20), index=True)
    is_leaf = Column(Boolean, default=False)  # True if no children
    
    # Tariff information
    general_rate = Column(Float)
    preferential_rate = Column(Float)
    unit_of_measure = Column(String(20))
    
    # Additional information
    notes = Column(Text)
    exclusions = Column(Text)
    inclusions = Column(Text)
    
    # Relationships
    children = relationship("HSItem", 
                          backref="parent",
                          remote_side=[full_code],
                          foreign_keys=[parent_code])
    notes_rel = relationship("HSNote", back_populates="hs_item", cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="hs_item", cascade="all, delete-orphan")
    
    # Indexes for better performance
    __table_args__ = (
        Index('idx_hs_chapter_heading', 'chapter', 'heading'),
        Index('idx_hs_parent_children', 'parent_code', 'level'),
        Index('idx_hs_description', 'description'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.full_code:
            self.full_code = self.hs_code
    
    @property
    def is_chapter(self):
        """Check if this is a chapter level item"""
        return self.level == 1
    
    @property
    def is_heading(self):
        """Check if this is a heading level item"""
        return self.level == 2
    
    @property
    def is_subheading(self):
        """Check if this is a subheading level item"""
        return self.level == 3
    
    @property
    def is_full_code(self):
        """Check if this is a full code level item"""
        return self.level == 4
    
    def get_ancestors(self):
        """Get all ancestor codes"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors
    
    def get_descendants(self):
        """Get all descendant codes"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def get_siblings(self):
        """Get sibling codes (same parent)"""
        if not self.parent_code:
            return []
        return [item for item in self.parent.children if item.id != self.id]
    
    def get_path(self):
        """Get full path from root to this item"""
        path = [self]
        current = self.parent
        while current:
            path.append(current)
            current = current.parent
        return list(reversed(path))
    
    def matches_search(self, search_term):
        """Check if item matches search term"""
        search_lower = search_term.lower()
        return (search_lower in self.description.lower() or
                search_lower in self.english_description.lower() or
                search_lower in self.spanish_description.lower() or
                search_lower in self.hs_code.lower())
    
    def to_dict(self):
        """Convert HS item to dictionary"""
        data = super().to_dict()
        # Add computed fields
        data['is_chapter'] = self.is_chapter
        data['is_heading'] = self.is_heading
        data['is_subheading'] = self.is_subheading
        data['is_full_code'] = self.is_full_code
        data['has_children'] = len(self.children) > 0
        return data
    
    def __repr__(self):
        return f"<HSItem(hs_code='{self.hs_code}', description='{self.description[:50]}...')>"
