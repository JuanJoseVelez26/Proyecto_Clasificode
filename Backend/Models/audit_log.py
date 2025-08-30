from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import DeclarativeBase

class AuditLog(DeclarativeBase):
    """Audit Log model for system audit trail"""
    
    __tablename__ = 'audit_logs'
    
    # Audit information
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    entity_type = Column(String(50), nullable=False)  # USER, CASE, HS_ITEM, etc.
    entity_id = Column(String(50))  # ID of the affected entity
    
    # User information
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="audit_logs")
    
    # Details
    details = Column(Text)  # JSON string with action details
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(String(500))
    
    # Relationships
    case_id = Column(Integer, ForeignKey('cases.id'))
    case = relationship("Case", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(action='{self.action}', entity='{self.entity_type}', user_id={self.user_id})>"
