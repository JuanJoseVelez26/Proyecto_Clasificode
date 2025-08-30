from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from .db import db
import logging

class BaseRepository:
    """Base repository with common CRUD operations"""
    
    def __init__(self, model_class):
        self.model = model_class
    
    def create(self, data: Dict[str, Any]) -> Any:
        """Create new record"""
        try:
            instance = self.model(**data)
            db.session.add(instance)
            db.session.commit()
            return instance
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating {self.model.__name__}: {e}")
            raise
    
    def get_by_id(self, id: int) -> Optional[Any]:
        """Get record by ID"""
        return db.session.get(self.model, id)
    
    def get_all(self, limit: int = None, offset: int = None) -> List[Any]:
        """Get all records with optional pagination"""
        query = db.session.query(self.model)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def update(self, id: int, data: Dict[str, Any]) -> Optional[Any]:
        """Update record by ID"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None
            
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            db.session.commit()
            return instance
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating {self.model.__name__}: {e}")
            raise
    
    def delete(self, id: int) -> bool:
        """Delete record by ID"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return False
            
            db.session.delete(instance)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting {self.model.__name__}: {e}")
            raise
    
    def find_by(self, **kwargs) -> List[Any]:
        """Find records by multiple criteria"""
        query = db.session.query(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.all()
    
    def find_one_by(self, **kwargs) -> Optional[Any]:
        """Find single record by criteria"""
        query = db.session.query(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.first()
    
    def count(self, **kwargs) -> int:
        """Count records by criteria"""
        query = db.session.query(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.count()
    
    def exists(self, **kwargs) -> bool:
        """Check if record exists"""
        return self.count(**kwargs) > 0

class UserRepository(BaseRepository):
    """User repository with specific operations"""
    
    def __init__(self):
        from Models.user import User
        super().__init__(User)
    
    def get_by_username(self, username: str):
        """Get user by username"""
        return self.find_one_by(username=username)
    
    def get_by_email(self, email: str):
        """Get user by email"""
        return self.find_one_by(email=email)
    
    def get_active_users(self):
        """Get all active users"""
        return self.find_by(is_active=True)

class CaseRepository(BaseRepository):
    """Case repository with specific operations"""
    
    def __init__(self):
        from Models.case import Case
        super().__init__(Case)
    
    def get_by_case_number(self, case_number: str):
        """Get case by case number"""
        return self.find_one_by(case_number=case_number)
    
    def get_by_status(self, status: str):
        """Get cases by status"""
        return self.find_by(status=status)
    
    def get_by_user(self, user_id: int):
        """Get cases by user"""
        return self.find_by(user_id=user_id)
    
    def get_pending_cases(self):
        """Get all pending cases"""
        return self.get_by_status('pending')
    
    def get_cases_for_review(self, reviewer_id: int):
        """Get cases assigned for review"""
        return self.find_by(assigned_to=reviewer_id, status='in_review')

class HSItemRepository(BaseRepository):
    """HS Item repository with specific operations"""
    
    def __init__(self):
        from Models.hs_item import HSItem
        super().__init__(HSItem)
    
    def get_by_hs_code(self, hs_code: str):
        """Get HS item by code"""
        return self.find_one_by(hs_code=hs_code)
    
    def search_by_description(self, description: str, limit: int = 10):
        """Search HS items by description"""
        query = db.session.query(self.model)
        query = query.filter(self.model.description.ilike(f'%{description}%'))
        return query.limit(limit).all()
    
    def get_by_chapter(self, chapter: str):
        """Get HS items by chapter"""
        return self.find_by(chapter=chapter)
    
    def get_by_heading(self, heading: str):
        """Get HS items by heading"""
        return self.find_by(heading=heading)
    
    def get_children(self, parent_code: str):
        """Get child HS items"""
        return self.find_by(parent_code=parent_code)

class CandidateRepository(BaseRepository):
    """Candidate repository with specific operations"""
    
    def __init__(self):
        from Models.candidate import Candidate
        super().__init__(Candidate)
    
    def get_by_case(self, case_id: int):
        """Get candidates by case"""
        return self.find_by(case_id=case_id)
    
    def get_best_candidate(self, case_id: int):
        """Get best candidate for case"""
        candidates = self.get_by_case(case_id)
        if not candidates:
            return None
        return max(candidates, key=lambda c: c.confidence_score or 0)
    
    def get_by_method(self, case_id: int, method: str):
        """Get candidates by classification method"""
        return self.find_by(case_id=case_id, classification_method=method)

# Repository instances
user_repo = UserRepository()
case_repo = CaseRepository()
hs_item_repo = HSItemRepository()
candidate_repo = CandidateRepository()
