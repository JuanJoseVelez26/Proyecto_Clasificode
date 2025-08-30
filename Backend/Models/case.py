from datetime import datetime
from sqlalchemy import Column, String, Text, Enum, Integer, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
import enum
from .base import DeclarativeBase

class CaseStatus(enum.Enum):
    """Case status enumeration"""
    DRAFT = "draft"
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"

class CasePriority(enum.Enum):
    """Case priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Case(DeclarativeBase):
    """Case model for classification requests"""
    
    __tablename__ = 'cases'
    
    # Case identification
    case_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Product information
    product_name = Column(String(200), nullable=False)
    product_description = Column(Text, nullable=False)
    brand = Column(String(100))
    model = Column(String(100))
    origin_country = Column(String(100))
    destination_country = Column(String(100))
    
    # Classification details
    proposed_hs_code = Column(String(20))
    final_hs_code = Column(String(20))
    confidence_score = Column(Float)
    classification_method = Column(String(50))  # RGI, SEMANTIC, HYBRID
    
    # Case management
    status = Column(Enum(CaseStatus), default=CaseStatus.DRAFT, nullable=False)
    priority = Column(Enum(CasePriority), default=CasePriority.MEDIUM, nullable=False)
    assigned_to = Column(Integer, ForeignKey('users.id'))
    reviewed_by = Column(Integer, ForeignKey('users.id'))
    
    # Timestamps
    submitted_at = Column(String(50))  # Store as string
    reviewed_at = Column(String(50))   # Store as string
    closed_at = Column(String(50))     # Store as string
    
    # Additional information
    notes = Column(Text)
    attachments = Column(Text)  # JSON string of file paths
    tags = Column(Text)         # JSON string of tags
    
    # Relationships
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="cases")
    candidates = relationship("Candidate", back_populates="case", cascade="all, delete-orphan")
    validations = relationship("Validation", back_populates="case", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="case", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.case_number:
            self.case_number = self.generate_case_number()
    
    @staticmethod
    def generate_case_number():
        """Generate unique case number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"CASE-{timestamp}"
    
    @property
    def is_draft(self):
        """Check if case is in draft status"""
        return self.status == CaseStatus.DRAFT
    
    @property
    def is_pending(self):
        """Check if case is pending"""
        return self.status == CaseStatus.PENDING
    
    @property
    def is_in_review(self):
        """Check if case is in review"""
        return self.status == CaseStatus.IN_REVIEW
    
    @property
    def is_approved(self):
        """Check if case is approved"""
        return self.status == CaseStatus.APPROVED
    
    @property
    def is_rejected(self):
        """Check if case is rejected"""
        return self.status == CaseStatus.REJECTED
    
    @property
    def is_closed(self):
        """Check if case is closed"""
        return self.status == CaseStatus.CLOSED
    
    def submit(self):
        """Submit case for review"""
        self.status = CaseStatus.PENDING
        self.submitted_at = datetime.utcnow().isoformat()
    
    def assign_review(self, reviewer_id):
        """Assign case for review"""
        self.status = CaseStatus.IN_REVIEW
        self.assigned_to = reviewer_id
    
    def approve(self, reviewer_id, hs_code=None):
        """Approve case"""
        self.status = CaseStatus.APPROVED
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow().isoformat()
        if hs_code:
            self.final_hs_code = hs_code
    
    def reject(self, reviewer_id, reason=None):
        """Reject case"""
        self.status = CaseStatus.REJECTED
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow().isoformat()
        if reason:
            self.notes = f"Rejected: {reason}"
    
    def close(self):
        """Close case"""
        self.status = CaseStatus.CLOSED
        self.closed_at = datetime.utcnow().isoformat()
    
    def get_best_candidate(self):
        """Get the best candidate based on confidence score"""
        if not self.candidates:
            return None
        return max(self.candidates, key=lambda c: c.confidence_score or 0)
    
    def to_dict(self):
        """Convert case to dictionary"""
        data = super().to_dict()
        # Add relationships
        data['candidates'] = [c.to_dict() for c in self.candidates]
        data['validations'] = [v.to_dict() for v in self.validations]
        return data
    
    def __repr__(self):
        return f"<Case(case_number='{self.case_number}', title='{self.title}', status='{self.status.value}')>"
