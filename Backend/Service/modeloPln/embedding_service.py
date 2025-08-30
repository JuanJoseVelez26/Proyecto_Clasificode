import os
import numpy as np
from typing import List, Optional, Union
import openai
from sentence_transformers import SentenceTransformer
import logging

class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self):
        self.model_name = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
        
        # Initialize OpenAI client if API key is available
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.openai_client = openai
        else:
            self.openai_client = None
            logging.warning("OpenAI API key not found. Using local models.")
        
        # Initialize local model as fallback
        self.local_model = None
        self._init_local_model()
    
    def _init_local_model(self):
        """Initialize local embedding model"""
        try:
            # Use a smaller, efficient model for local use
            self.local_model = SentenceTransformer('all-MiniLM-L6-v2')
            logging.info("Local embedding model initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize local embedding model: {e}")
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text using best available method"""
        if not text:
            return None
        
        # Try OpenAI first if available
        if self.openai_client:
            try:
                return self._get_openai_embedding(text)
            except Exception as e:
                logging.warning(f"OpenAI embedding failed: {e}. Falling back to local model.")
        
        # Fallback to local model
        if self.local_model:
            try:
                return self._get_local_embedding(text)
            except Exception as e:
                logging.error(f"Local embedding failed: {e}")
                return None
        
        return None
    
    def _get_openai_embedding(self, text: str) -> List[float]:
        """Get embedding using OpenAI API"""
        try:
            response = self.openai_client.Embedding.create(
                input=text,
                model=self.model_name
            )
            return response['data'][0]['embedding']
        except Exception as e:
            logging.error(f"OpenAI embedding error: {e}")
            raise
    
    def _get_local_embedding(self, text: str) -> List[float]:
        """Get embedding using local model"""
        try:
            embedding = self.local_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logging.error(f"Local embedding error: {e}")
            raise
    
    def get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Get embeddings for multiple texts"""
        embeddings = []
        
        for text in texts:
            embedding = self.get_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Normalize vectors
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            return float(similarity)
        
        except Exception as e:
            logging.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], 
                         candidate_embeddings: List[List[float]], 
                         top_k: int = 5) -> List[tuple]:
        """Find most similar embeddings"""
        similarities = []
        
        for i, candidate_embedding in enumerate(candidate_embeddings):
            if candidate_embedding is not None:
                similarity = self.calculate_similarity(query_embedding, candidate_embedding)
                similarities.append((i, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        if self.model_name == 'text-embedding-ada-002':
            return 1536
        elif self.local_model:
            return self.local_model.get_sentence_embedding_dimension()
        else:
            return 384  # Default for all-MiniLM-L6-v2
    
    def is_available(self) -> bool:
        """Check if embedding service is available"""
        return self.openai_client is not None or self.local_model is not None
    
    def get_service_info(self) -> dict:
        """Get information about the embedding service"""
        return {
            'model_name': self.model_name,
            'openai_available': self.openai_client is not None,
            'local_model_available': self.local_model is not None,
            'embedding_dimension': self.get_embedding_dimension(),
            'service_available': self.is_available()
        }

# Global embedding service instance
embedding_service = EmbeddingService()
