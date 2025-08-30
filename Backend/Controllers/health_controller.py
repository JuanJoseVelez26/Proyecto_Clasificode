from flask import Blueprint, jsonify
from Service.db import db
from Service.modeloPln.embedding_service import embedding_service
import logging

health_bp = Blueprint('health', __name__, url_prefix='/api/health')

@health_bp.route('', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    try:
        # Check database connection
        db_healthy = False
        try:
            db.session.execute("SELECT 1")
            db_healthy = True
        except Exception as e:
            logging.error(f"Database health check failed: {e}")
        
        # Check embedding service
        embedding_healthy = embedding_service.is_available()
        
        # Overall health
        overall_healthy = db_healthy and embedding_healthy
        
        status_code = 200 if overall_healthy else 503
        
        return jsonify({
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'services': {
                'database': {
                    'status': 'healthy' if db_healthy else 'unhealthy',
                    'connected': db_healthy
                },
                'embedding_service': {
                    'status': 'healthy' if embedding_healthy else 'unhealthy',
                    'available': embedding_healthy
                }
            },
            'timestamp': '2024-01-01T00:00:00Z'  # You can use datetime.utcnow().isoformat()
        }), status_code
        
    except Exception as e:
        logging.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'services': {
                'database': {'status': 'unknown', 'connected': False},
                'embedding_service': {'status': 'unknown', 'available': False}
            }
        }), 503

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check for Kubernetes"""
    try:
        # Check if all critical services are ready
        db_ready = False
        try:
            db.session.execute("SELECT 1")
            db_ready = True
        except Exception as e:
            logging.error(f"Database readiness check failed: {e}")
        
        embedding_ready = embedding_service.is_available()
        
        # All services must be ready
        ready = db_ready and embedding_ready
        
        status_code = 200 if ready else 503
        
        return jsonify({
            'ready': ready,
            'services': {
                'database': db_ready,
                'embedding_service': embedding_ready
            }
        }), status_code
        
    except Exception as e:
        logging.error(f"Readiness check error: {e}")
        return jsonify({
            'ready': False,
            'error': str(e)
        }), 503

@health_bp.route('/live', methods=['GET'])
def liveness_check():
    """Liveness check for Kubernetes"""
    try:
        # Simple check that the application is running
        return jsonify({
            'alive': True,
            'timestamp': '2024-01-01T00:00:00Z'
        }), 200
        
    except Exception as e:
        logging.error(f"Liveness check error: {e}")
        return jsonify({
            'alive': False,
            'error': str(e)
        }), 503
