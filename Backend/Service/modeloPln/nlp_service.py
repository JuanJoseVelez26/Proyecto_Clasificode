import re
import nltk
from typing import List, Dict, Any
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tokenize import word_tokenize, sent_tokenize
import logging

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

class NLPService:
    """Natural Language Processing service for text preprocessing"""
    
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        
        # Custom stop words for HS classification
        self.custom_stops = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'within',
            'without', 'against', 'toward', 'towards', 'upon', 'over', 'under',
            'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now'
        }
        
        self.stop_words.update(self.custom_stops)
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces and hyphens
        text = re.sub(r'[^\w\s\-]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        return word_tokenize(text)
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Remove stop words from tokens"""
        return [token for token in tokens if token.lower() not in self.stop_words]
    
    def lemmatize(self, tokens: List[str]) -> List[str]:
        """Lemmatize tokens"""
        return [self.lemmatizer.lemmatize(token) for token in tokens]
    
    def stem(self, tokens: List[str]) -> List[str]:
        """Stem tokens"""
        return [self.stemmer.stem(token) for token in tokens]
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text"""
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        # Tokenize
        tokens = self.tokenize(processed_text)
        
        # Remove stopwords
        tokens = self.remove_stopwords(tokens)
        
        # Lemmatize
        tokens = self.lemmatize(tokens)
        
        # Count frequencies
        word_freq = {}
        for token in tokens:
            if len(token) > 2:  # Filter out very short words
                word_freq[token] = word_freq.get(token, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def extract_phrases(self, text: str) -> List[str]:
        """Extract meaningful phrases from text"""
        # Split into sentences
        sentences = sent_tokenize(text)
        
        phrases = []
        for sentence in sentences:
            # Extract noun phrases (simple approach)
            words = self.tokenize(sentence)
            pos_tags = nltk.pos_tag(words)
            
            # Find noun phrases (NP)
            current_phrase = []
            for word, tag in pos_tags:
                if tag.startswith('NN'):  # Noun
                    current_phrase.append(word)
                else:
                    if current_phrase:
                        phrases.append(' '.join(current_phrase))
                        current_phrase = []
            
            # Add last phrase if exists
            if current_phrase:
                phrases.append(' '.join(current_phrase))
        
        return phrases
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        # Preprocess
        text = self.preprocess_text(text)
        
        # Tokenize and remove stopwords
        tokens = self.tokenize(text)
        tokens = self.remove_stopwords(tokens)
        
        # Lemmatize
        tokens = self.lemmatize(tokens)
        
        # Join back
        return ' '.join(tokens)
    
    def extract_materials(self, text: str) -> List[str]:
        """Extract material terms from text"""
        materials = {
            'cotton', 'wool', 'silk', 'leather', 'plastic', 'metal', 'steel', 'iron',
            'aluminum', 'copper', 'wood', 'glass', 'ceramic', 'paper', 'cardboard',
            'rubber', 'synthetic', 'polyester', 'nylon', 'acrylic', 'linen', 'jute',
            'bamboo', 'cork', 'marble', 'granite', 'concrete', 'fabric', 'textile'
        }
        
        processed_text = self.preprocess_text(text)
        tokens = self.tokenize(processed_text)
        tokens = self.lemmatize(tokens)
        
        found_materials = []
        for token in tokens:
            if token in materials:
                found_materials.append(token)
        
        return found_materials
    
    def extract_functions(self, text: str) -> List[str]:
        """Extract function/use terms from text"""
        functions = {
            'machine', 'tool', 'equipment', 'instrument', 'device', 'apparatus',
            'appliance', 'motor', 'engine', 'pump', 'valve', 'sensor', 'controller',
            'processor', 'computer', 'phone', 'camera', 'speaker', 'display',
            'medical', 'surgical', 'agricultural', 'industrial', 'domestic',
            'commercial', 'residential', 'automotive', 'aviation', 'marine'
        }
        
        processed_text = self.preprocess_text(text)
        tokens = self.tokenize(processed_text)
        tokens = self.lemmatize(tokens)
        
        found_functions = []
        for token in tokens:
            if token in functions:
                found_functions.append(token)
        
        return found_functions
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Normalize both texts
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)
        
        # Get keywords
        keywords1 = set(self.extract_keywords(norm1))
        keywords2 = set(self.extract_keywords(norm2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Comprehensive text analysis"""
        return {
            'original_text': text,
            'preprocessed_text': self.preprocess_text(text),
            'normalized_text': self.normalize_text(text),
            'keywords': self.extract_keywords(text),
            'phrases': self.extract_phrases(text),
            'materials': self.extract_materials(text),
            'functions': self.extract_functions(text),
            'word_count': len(self.tokenize(text)),
            'unique_words': len(set(self.tokenize(self.preprocess_text(text))))
        }

# Global NLP service instance
nlp_service = NLPService()
