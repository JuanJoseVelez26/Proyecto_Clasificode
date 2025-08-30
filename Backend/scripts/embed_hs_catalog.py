#!/usr/bin/env python3
"""
Script to generate embeddings for HS catalog
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import create_app
from Service.db import db
from Service.modeloPln.vector_index import vector_index
from Service.modeloPln.embedding_service import embedding_service
from Models.hs_item import HSItem
import logging
import time

def generate_embeddings_for_hs_catalog():
    """Generate embeddings for all HS items in the catalog"""
    try:
        print("Starting HS catalog embedding generation...")
        
        # Check if embedding service is available
        if not embedding_service.is_available():
            print("ERROR: Embedding service is not available!")
            return 0
        
        # Get all HS items
        hs_items = db.session.query(HSItem).all()
        print(f"Found {len(hs_items)} HS items to process")
        
        if not hs_items:
            print("No HS items found in database")
            return 0
        
        # Generate embeddings
        created_count = vector_index.create_embeddings_for_hs_catalog(batch_size=50)
        
        print(f"Successfully created {created_count} embeddings")
        return created_count
        
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        logging.error(f"Error generating embeddings: {e}")
        return 0

def verify_embeddings():
    """Verify that embeddings were created correctly"""
    try:
        print("\nVerifying embeddings...")
        
        # Count embeddings in database
        from Models.embedding import Embedding
        embedding_count = db.session.query(Embedding).count()
        hs_item_count = db.session.query(HSItem).count()
        
        print(f"Total HS items: {hs_item_count}")
        print(f"Total embeddings: {embedding_count}")
        
        if embedding_count > 0:
            print("✅ Embeddings verification successful")
            return True
        else:
            print("❌ No embeddings found")
            return False
            
    except Exception as e:
        print(f"Error verifying embeddings: {e}")
        return False

def main():
    """Main function"""
    app = create_app()
    
    with app.app_context():
        start_time = time.time()
        
        print("=== HS Catalog Embedding Generation ===")
        print(f"Embedding service: {embedding_service.get_service_info()}")
        
        # Generate embeddings
        created_count = generate_embeddings_for_hs_catalog()
        
        # Verify embeddings
        verification_success = verify_embeddings()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n=== Summary ===")
        print(f"Embeddings created: {created_count}")
        print(f"Verification: {'✅ Success' if verification_success else '❌ Failed'}")
        print(f"Duration: {duration:.2f} seconds")
        
        if created_count > 0 and verification_success:
            print("🎉 HS catalog embedding generation completed successfully!")
        else:
            print("⚠️  HS catalog embedding generation completed with issues")

if __name__ == '__main__':
    main()
