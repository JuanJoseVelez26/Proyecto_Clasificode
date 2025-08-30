from typing import List, Dict, Any
from rapidfuzz import fuzz
from Service.Agente.rule_engine import rgi_engine
from Service.modeloPln.embedding_service import embedding_service
from Service.modeloPln.vector_index import vector_index
from Models.candidate import Candidate
from Models.case import Case
import logging

class ReRankService:
    """Re-ranking service that combines RGI rules with semantic similarity"""
    
    def __init__(self):
        self.rgi_weight = 0.6  # Weight for RGI-based classification
        self.semantic_weight = 0.4  # Weight for semantic similarity
        
    def classify_product(self, case: Case) -> List[Candidate]:
        """Classify product using hybrid approach (RGI + Semantic)"""
        candidates = []
        
        # Step 1: Get RGI-based candidates
        rgi_candidates = rgi_engine.classify_product(case)
        
        # Step 2: Get semantic-based candidates
        semantic_candidates = self._get_semantic_candidates(case)
        
        # Step 3: Combine and re-rank candidates
        combined_candidates = self._combine_candidates(rgi_candidates, semantic_candidates, case)
        
        # Step 4: Apply final ranking
        final_candidates = self._apply_final_ranking(combined_candidates, case)
        
        return final_candidates
    
    def _get_semantic_candidates(self, case: Case) -> List[Candidate]:
        """Get candidates using semantic similarity"""
        try:
            # Get embedding for product description
            product_embedding = embedding_service.get_embedding(case.product_description)
            
            # Search similar HS items using vector similarity
            similar_items = vector_index.search_similar(product_embedding, limit=20)
            
            candidates = []
            for item, similarity in similar_items:
                candidate = Candidate(
                    case_id=case.id,
                    hs_code=item.hs_code,
                    description=item.description,
                    confidence_score=similarity,
                    classification_method="SEMANTIC",
                    rule_applied="Vector Similarity",
                    semantic_similarity=similarity,
                    reasoning=f"Semantic similarity: {similarity:.2f}"
                )
                candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            logging.error(f"Error getting semantic candidates: {e}")
            return []
    
    def _combine_candidates(self, rgi_candidates: List[Candidate], 
                          semantic_candidates: List[Candidate], 
                          case: Case) -> List[Candidate]:
        """Combine RGI and semantic candidates"""
        combined = {}
        
        # Process RGI candidates
        for candidate in rgi_candidates:
            key = candidate.hs_code
            if key not in combined:
                combined[key] = {
                    'candidate': candidate,
                    'rgi_score': candidate.confidence_score,
                    'semantic_score': 0.0,
                    'combined_score': 0.0
                }
            else:
                # Update with better RGI score
                if candidate.confidence_score > combined[key]['rgi_score']:
                    combined[key]['candidate'] = candidate
                    combined[key]['rgi_score'] = candidate.confidence_score
        
        # Process semantic candidates
        for candidate in semantic_candidates:
            key = candidate.hs_code
            if key not in combined:
                combined[key] = {
                    'candidate': candidate,
                    'rgi_score': 0.0,
                    'semantic_score': candidate.confidence_score,
                    'combined_score': 0.0
                }
            else:
                # Update semantic score
                combined[key]['semantic_score'] = candidate.confidence_score
                combined[key]['candidate'].semantic_similarity = candidate.confidence_score
        
        # Calculate combined scores
        for key, data in combined.items():
            rgi_score = data['rgi_score'] * self.rgi_weight
            semantic_score = data['semantic_score'] * self.semantic_weight
            combined_score = rgi_score + semantic_score
            
            data['combined_score'] = combined_score
            data['candidate'].confidence_score = combined_score
            
            # Update reasoning
            if data['rgi_score'] > 0 and data['semantic_score'] > 0:
                data['candidate'].classification_method = "HYBRID"
                data['candidate'].reasoning = f"Combined RGI ({data['rgi_score']:.2f}) and semantic ({data['semantic_score']:.2f}) scores"
            elif data['rgi_score'] > 0:
                data['candidate'].classification_method = "RGI"
            else:
                data['candidate'].classification_method = "SEMANTIC"
        
        return [data['candidate'] for data in combined.values()]
    
    def _apply_final_ranking(self, candidates: List[Candidate], case: Case) -> List[Candidate]:
        """Apply final ranking and filtering"""
        if not candidates:
            return []
        
        # Sort by combined confidence score
        candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Apply additional ranking factors
        for i, candidate in enumerate(candidates):
            # Boost score for exact matches
            if self._is_exact_match(case.product_description, candidate.description):
                candidate.confidence_score = min(1.0, candidate.confidence_score + 0.1)
            
            # Boost score for material matches
            if self._has_material_match(case.product_description, candidate.description):
                candidate.confidence_score = min(1.0, candidate.confidence_score + 0.05)
            
            # Set ranking position
            candidate.ranking_position = i + 1
        
        # Filter out low-confidence candidates
        threshold = 0.3
        filtered_candidates = [c for c in candidates if c.confidence_score >= threshold]
        
        # Limit to top 10 candidates
        return filtered_candidates[:10]
    
    def _is_exact_match(self, product_desc: str, hs_desc: str) -> bool:
        """Check if there's an exact match between product and HS descriptions"""
        product_words = set(product_desc.lower().split())
        hs_words = set(hs_desc.lower().split())
        
        # Check for significant word overlap
        common_words = product_words.intersection(hs_words)
        if len(common_words) >= min(len(product_words), len(hs_words)) * 0.7:
            return True
        
        return False
    
    def _has_material_match(self, product_desc: str, hs_desc: str) -> bool:
        """Check if there's a material match between descriptions"""
        materials = ['cotton', 'wool', 'silk', 'leather', 'plastic', 'metal', 'wood', 'glass', 'ceramic']
        
        product_materials = [m for m in materials if m in product_desc.lower()]
        hs_materials = [m for m in materials if m in hs_desc.lower()]
        
        return bool(set(product_materials).intersection(set(hs_materials)))
    
    def get_classification_summary(self, candidates: List[Candidate]) -> Dict[str, Any]:
        """Get summary of classification results"""
        if not candidates:
            return {
                'total_candidates': 0,
                'best_candidate': None,
                'confidence_distribution': {},
                'method_distribution': {}
            }
        
        # Best candidate
        best_candidate = candidates[0]
        
        # Confidence distribution
        confidence_ranges = {
            'high': len([c for c in candidates if c.confidence_score >= 0.8]),
            'medium': len([c for c in candidates if 0.5 <= c.confidence_score < 0.8]),
            'low': len([c for c in candidates if c.confidence_score < 0.5])
        }
        
        # Method distribution
        method_counts = {}
        for candidate in candidates:
            method = candidate.classification_method
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return {
            'total_candidates': len(candidates),
            'best_candidate': {
                'hs_code': best_candidate.hs_code,
                'description': best_candidate.description,
                'confidence_score': best_candidate.confidence_score,
                'classification_method': best_candidate.classification_method
            },
            'confidence_distribution': confidence_ranges,
            'method_distribution': method_counts
        }

# Global re-rank service instance
re_rank_service = ReRankService()
