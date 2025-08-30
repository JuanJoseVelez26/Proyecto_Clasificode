import re
from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz, process
from Service.repository import hs_item_repo, candidate_repo
from Models.candidate import Candidate
from Models.case import Case
import logging

class RGIRuleEngine:
    """RGI (Reglas Generales de Interpretación) Rule Engine"""
    
    def __init__(self):
        self.rules = {
            1: self._rule_1,
            2: self._rule_2,
            3: self._rule_3,
            4: self._rule_4,
            5: self._rule_5,
            6: self._rule_6
        }
    
    def classify_product(self, case: Case) -> List[Candidate]:
        """Classify product using RGI rules"""
        candidates = []
        
        # Apply each RGI rule in order
        for rule_number in range(1, 7):
            try:
                rule_candidates = self.rules[rule_number](case)
                if rule_candidates:
                    candidates.extend(rule_candidates)
                    # If we found candidates with this rule, stop (RGI is hierarchical)
                    break
            except Exception as e:
                logging.error(f"Error applying RGI rule {rule_number}: {e}")
                continue
        
        # Sort candidates by confidence score
        candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return candidates
    
    def _rule_1(self, case: Case) -> List[Candidate]:
        """RGI Rule 1: Specific descriptions take precedence"""
        candidates = []
        product_desc = case.product_description.lower()
        
        # Search for exact matches in HS descriptions
        hs_items = hs_item_repo.search_by_description(product_desc, limit=50)
        
        for hs_item in hs_items:
            # Calculate similarity score
            similarity = fuzz.ratio(product_desc, hs_item.description.lower())
            
            if similarity >= 80:  # High confidence threshold for RGI 1
                candidate = Candidate(
                    case_id=case.id,
                    hs_code=hs_item.hs_code,
                    description=hs_item.description,
                    confidence_score=similarity / 100.0,
                    classification_method="RGI",
                    rule_applied="RGI Rule 1",
                    reasoning=f"Exact or very close match found in HS description. Similarity: {similarity}%"
                )
                candidates.append(candidate)
        
        return candidates
    
    def _rule_2(self, case: Case) -> List[Candidate]:
        """RGI Rule 2: Most specific description"""
        candidates = []
        product_desc = case.product_description.lower()
        
        # Search for specific terms in the description
        specific_terms = self._extract_specific_terms(product_desc)
        
        for term in specific_terms:
            hs_items = hs_item_repo.search_by_description(term, limit=20)
            
            for hs_item in hs_items:
                # Check if the specific term is prominent in the HS description
                if term in hs_item.description.lower():
                    similarity = fuzz.partial_ratio(product_desc, hs_item.description.lower())
                    
                    if similarity >= 70:
                        candidate = Candidate(
                            case_id=case.id,
                            hs_code=hs_item.hs_code,
                            description=hs_item.description,
                            confidence_score=similarity / 100.0,
                            classification_method="RGI",
                            rule_applied="RGI Rule 2",
                            reasoning=f"Specific term '{term}' found in HS description. Similarity: {similarity}%"
                        )
                        candidates.append(candidate)
        
        return candidates
    
    def _rule_3(self, case: Case) -> List[Candidate]:
        """RGI Rule 3: Essential character"""
        candidates = []
        product_desc = case.product_description.lower()
        
        # Identify essential characteristics
        essential_chars = self._identify_essential_characteristics(product_desc)
        
        for char in essential_chars:
            hs_items = hs_item_repo.search_by_description(char, limit=30)
            
            for hs_item in hs_items:
                # Check if the essential characteristic is present
                if char in hs_item.description.lower():
                    similarity = fuzz.token_sort_ratio(product_desc, hs_item.description.lower())
                    
                    if similarity >= 60:
                        candidate = Candidate(
                            case_id=case.id,
                            hs_code=hs_item.hs_code,
                            description=hs_item.description,
                            confidence_score=similarity / 100.0,
                            classification_method="RGI",
                            rule_applied="RGI Rule 3",
                            reasoning=f"Essential characteristic '{char}' identified. Similarity: {similarity}%"
                        )
                        candidates.append(candidate)
        
        return candidates
    
    def _rule_4(self, case: Case) -> List[Candidate]:
        """RGI Rule 4: Most appropriate heading"""
        candidates = []
        product_desc = case.product_description.lower()
        
        # Search for broader categories
        broad_terms = self._extract_broad_terms(product_desc)
        
        for term in broad_terms:
            hs_items = hs_item_repo.search_by_description(term, limit=25)
            
            for hs_item in hs_items:
                # Check if it's a heading level item
                if hs_item.is_heading:
                    similarity = fuzz.token_set_ratio(product_desc, hs_item.description.lower())
                    
                    if similarity >= 50:
                        candidate = Candidate(
                            case_id=case.id,
                            hs_code=hs_item.hs_code,
                            description=hs_item.description,
                            confidence_score=similarity / 100.0,
                            classification_method="RGI",
                            rule_applied="RGI Rule 4",
                            reasoning=f"Most appropriate heading found for '{term}'. Similarity: {similarity}%"
                        )
                        candidates.append(candidate)
        
        return candidates
    
    def _rule_5(self, case: Case) -> List[Candidate]:
        """RGI Rule 5: Packaging and containers"""
        candidates = []
        product_desc = case.product_description.lower()
        
        # Check if product is a container or packaging
        container_terms = ['container', 'package', 'box', 'bottle', 'can', 'jar', 'bag']
        
        for term in container_terms:
            if term in product_desc:
                hs_items = hs_item_repo.search_by_description(term, limit=15)
                
                for hs_item in hs_items:
                    similarity = fuzz.ratio(product_desc, hs_item.description.lower())
                    
                    if similarity >= 65:
                        candidate = Candidate(
                            case_id=case.id,
                            hs_code=hs_item.hs_code,
                            description=hs_item.description,
                            confidence_score=similarity / 100.0,
                            classification_method="RGI",
                            rule_applied="RGI Rule 5",
                            reasoning=f"Container/packaging classification. Similarity: {similarity}%"
                        )
                        candidates.append(candidate)
        
        return candidates
    
    def _rule_6(self, case: Case) -> List[Candidate]:
        """RGI Rule 6: Subordinate classification"""
        candidates = []
        product_desc = case.product_description.lower()
        
        # This rule is applied when no other rules match
        # Search for any relevant HS codes
        hs_items = hs_item_repo.search_by_description(product_desc, limit=40)
        
        for hs_item in hs_items:
            similarity = fuzz.ratio(product_desc, hs_item.description.lower())
            
            if similarity >= 40:  # Lower threshold for RGI 6
                candidate = Candidate(
                    case_id=case.id,
                    hs_code=hs_item.hs_code,
                    description=hs_item.description,
                    confidence_score=similarity / 100.0,
                    classification_method="RGI",
                    rule_applied="RGI Rule 6",
                    reasoning=f"Subordinate classification. Similarity: {similarity}%"
                )
                candidates.append(candidate)
        
        return candidates
    
    def _extract_specific_terms(self, description: str) -> List[str]:
        """Extract specific terms from product description"""
        # Common specific terms in HS classification
        specific_terms = []
        
        # Look for material terms
        materials = ['cotton', 'wool', 'silk', 'leather', 'plastic', 'metal', 'wood', 'glass', 'ceramic']
        for material in materials:
            if material in description:
                specific_terms.append(material)
        
        # Look for function terms
        functions = ['machine', 'tool', 'equipment', 'instrument', 'device', 'apparatus']
        for func in functions:
            if func in description:
                specific_terms.append(func)
        
        # Look for use terms
        uses = ['medical', 'surgical', 'agricultural', 'industrial', 'domestic', 'commercial']
        for use in uses:
            if use in description:
                specific_terms.append(use)
        
        return specific_terms
    
    def _identify_essential_characteristics(self, description: str) -> List[str]:
        """Identify essential characteristics of the product"""
        characteristics = []
        
        # Material characteristics
        if any(material in description for material in ['cotton', 'wool', 'silk']):
            characteristics.append('textile')
        
        if 'electronic' in description or 'electric' in description:
            characteristics.append('electronic')
        
        if 'mechanical' in description:
            characteristics.append('mechanical')
        
        if 'chemical' in description:
            characteristics.append('chemical')
        
        return characteristics
    
    def _extract_broad_terms(self, description: str) -> List[str]:
        """Extract broad category terms"""
        broad_terms = []
        
        # Product categories
        categories = ['textile', 'machinery', 'chemical', 'food', 'beverage', 'vehicle', 'weapon']
        for category in categories:
            if category in description:
                broad_terms.append(category)
        
        return broad_terms

# Global RGI rule engine instance
rgi_engine = RGIRuleEngine()
