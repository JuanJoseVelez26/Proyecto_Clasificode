from typing import List, Tuple, Optional
from sqlalchemy import text
from Service.db import db
from Service.repository import hs_item_repo
from Service.modeloPln.embedding_service import embedding_service
from Models.hs_item import HSItem
import logging

class PgVectorIndex:
    """PostgreSQL vector index for semantic search using pgvector"""
    
    def __init__(self):
        self.embedding_service = embedding_service
    
    def search_similar(self, query_embedding: List[float], limit: int = 10, 
                      threshold: float = 0.5) -> List[Tuple[HSItem, float]]:
        """Search for similar HS items using vector similarity"""
        try:
            # Convert embedding to PostgreSQL vector format
            vector_str = self._embedding_to_vector_string(query_embedding)
            
            # SQL query using pgvector cosine similarity
            query = text("""
                SELECT h.id, h.hs_code, h.description, h.chapter, h.heading, h.subheading,
                       h.full_code, h.level, h.parent_code, h.is_leaf,
                       h.general_rate, h.preferential_rate, h.unit_of_measure,
                       h.notes, h.exclusions, h.inclusions,
                       h.created_at, h.updated_at,
                       e.embedding_vector <=> :query_vector as similarity
                FROM hs_items h
                JOIN embeddings e ON h.id = e.hs_item_id
                WHERE e.model_name = :model_name
                AND e.content_type = 'DESCRIPTION'
                AND e.embedding_vector <=> :query_vector < :threshold
                ORDER BY e.embedding_vector <=> :query_vector
                LIMIT :limit
            """)
            
            result = db.session.execute(query, {
                'query_vector': vector_str,
                'model_name': self.embedding_service.model_name,
                'threshold': 1 - threshold,  # pgvector uses distance, not similarity
                'limit': limit
            })
            
            similar_items = []
            for row in result:
                # Create HSItem object from row
                hs_item = HSItem(
                    id=row.id,
                    hs_code=row.hs_code,
                    description=row.description,
                    chapter=row.chapter,
                    heading=row.heading,
                    subheading=row.subheading,
                    full_code=row.full_code,
                    level=row.level,
                    parent_code=row.parent_code,
                    is_leaf=row.is_leaf,
                    general_rate=row.general_rate,
                    preferential_rate=row.preferential_rate,
                    unit_of_measure=row.unit_of_measure,
                    notes=row.notes,
                    exclusions=row.exclusions,
                    inclusions=row.inclusions
                )
                
                # Convert distance to similarity (1 - distance)
                similarity = 1 - row.similarity
                similar_items.append((hs_item, similarity))
            
            return similar_items
            
        except Exception as e:
            logging.error(f"Error in vector search: {e}")
            return []
    
    def search_by_text(self, query_text: str, limit: int = 10, 
                      threshold: float = 0.5) -> List[Tuple[HSItem, float]]:
        """Search for similar HS items using text query"""
        try:
            # Get embedding for query text
            query_embedding = self.embedding_service.get_embedding(query_text)
            if not query_embedding:
                return []
            
            return self.search_similar(query_embedding, limit, threshold)
            
        except Exception as e:
            logging.error(f"Error in text-based vector search: {e}")
            return []
    
    def find_related_items(self, hs_code: str, limit: int = 5) -> List[Tuple[HSItem, float]]:
        """Find related HS items based on semantic similarity"""
        try:
            # Get HS item
            hs_item = hs_item_repo.get_by_hs_code(hs_code)
            if not hs_item:
                return []
            
            # Get embedding for the HS item description
            item_embedding = self.embedding_service.get_embedding(hs_item.description)
            if not item_embedding:
                return []
            
            # Search for similar items, excluding the original
            similar_items = self.search_similar(item_embedding, limit + 1, 0.3)
            
            # Filter out the original item
            filtered_items = [(item, sim) for item, sim in similar_items 
                            if item.hs_code != hs_code]
            
            return filtered_items[:limit]
            
        except Exception as e:
            logging.error(f"Error finding related items: {e}")
            return []
    
    def get_semantic_clusters(self, chapter: str = None, limit: int = 20) -> List[dict]:
        """Get semantically similar HS items grouped by similarity"""
        try:
            # Get HS items for the chapter
            if chapter:
                hs_items = hs_item_repo.get_by_chapter(chapter)
            else:
                hs_items = hs_item_repo.get_all(limit=100)
            
            if not hs_items:
                return []
            
            clusters = []
            processed_items = set()
            
            for item in hs_items:
                if item.id in processed_items:
                    continue
                
                # Get embedding for this item
                item_embedding = self.embedding_service.get_embedding(item.description)
                if not item_embedding:
                    continue
                
                # Find similar items
                similar_items = self.search_similar(item_embedding, limit, 0.7)
                
                if len(similar_items) > 1:  # Only create clusters with multiple items
                    cluster = {
                        'center_item': item,
                        'similar_items': [item for item, _ in similar_items],
                        'avg_similarity': sum(sim for _, sim in similar_items) / len(similar_items)
                    }
                    clusters.append(cluster)
                    
                    # Mark items as processed
                    for similar_item, _ in similar_items:
                        processed_items.add(similar_item.id)
            
            return clusters
            
        except Exception as e:
            logging.error(f"Error getting semantic clusters: {e}")
            return []
    
    def _embedding_to_vector_string(self, embedding: List[float]) -> str:
        """Convert embedding list to PostgreSQL vector string format"""
        return f"[{','.join(map(str, embedding))}]"
    
    def create_embeddings_for_hs_catalog(self, batch_size: int = 100) -> int:
        """Create embeddings for all HS items in the catalog"""
        try:
            # Get all HS items
            hs_items = hs_item_repo.get_all()
            
            created_count = 0
            for i in range(0, len(hs_items), batch_size):
                batch = hs_items[i:i + batch_size]
                
                for item in batch:
                    try:
                        # Check if embedding already exists
                        existing_embedding = self._get_existing_embedding(item.id)
                        if existing_embedding:
                            continue
                        
                        # Create embedding for description
                        embedding = self.embedding_service.get_embedding(item.description)
                        if embedding:
                            self._save_embedding(item.id, embedding, 'DESCRIPTION')
                            created_count += 1
                        
                        # Create embedding for notes if available
                        if item.notes:
                            notes_embedding = self.embedding_service.get_embedding(item.notes)
                            if notes_embedding:
                                self._save_embedding(item.id, notes_embedding, 'NOTE')
                                created_count += 1
                    
                    except Exception as e:
                        logging.error(f"Error creating embedding for HS item {item.hs_code}: {e}")
                        continue
                
                logging.info(f"Processed batch {i//batch_size + 1}, created {created_count} embeddings so far")
            
            return created_count
            
        except Exception as e:
            logging.error(f"Error creating embeddings for HS catalog: {e}")
            return 0
    
    def _get_existing_embedding(self, hs_item_id: int) -> Optional[List[float]]:
        """Get existing embedding for HS item"""
        try:
            query = text("""
                SELECT embedding_vector 
                FROM embeddings 
                WHERE hs_item_id = :hs_item_id 
                AND content_type = 'DESCRIPTION'
                LIMIT 1
            """)
            
            result = db.session.execute(query, {'hs_item_id': hs_item_id})
            row = result.fetchone()
            
            if row:
                # Convert PostgreSQL vector to list
                vector_str = row[0]
                return self._vector_string_to_embedding(vector_str)
            
            return None
            
        except Exception as e:
            logging.error(f"Error getting existing embedding: {e}")
            return None
    
    def _save_embedding(self, hs_item_id: int, embedding: List[float], content_type: str):
        """Save embedding to database"""
        try:
            vector_str = self._embedding_to_vector_string(embedding)
            
            query = text("""
                INSERT INTO embeddings (hs_item_id, model_name, vector_dimension, 
                                      embedding_vector, text_content, content_type)
                VALUES (:hs_item_id, :model_name, :vector_dimension, 
                       :embedding_vector, :text_content, :content_type)
            """)
            
            db.session.execute(query, {
                'hs_item_id': hs_item_id,
                'model_name': self.embedding_service.model_name,
                'vector_dimension': len(embedding),
                'embedding_vector': vector_str,
                'text_content': '',  # Will be filled by the calling function
                'content_type': content_type
            })
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saving embedding: {e}")
            raise
    
    def _vector_string_to_embedding(self, vector_str: str) -> List[float]:
        """Convert PostgreSQL vector string to embedding list"""
        # Remove brackets and split by comma
        vector_str = vector_str.strip('[]')
        return [float(x) for x in vector_str.split(',')]

# Global vector index instance
vector_index = PgVectorIndex()
