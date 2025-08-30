from flask import Blueprint, request, jsonify
from Service.security import security_service
from Service.repository import user_repo, case_repo, hs_item_repo
from Service.modeloPln.vector_index import vector_index
from Service.modeloPln.embedding_service import embedding_service
from Models.user import UserRole
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/users', methods=['GET'])
@security_service.require_role('admin')
def get_users():
    """Get all users"""
    try:
        users = user_repo.get_all()
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
    except Exception as e:
        logging.error(f"Get users error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@security_service.require_role('admin')
def update_user(user_id):
    """Update user role and status"""
    try:
        user = user_repo.get_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Allow updating role and status
        update_data = {}
        if 'role' in data:
            update_data['role'] = UserRole(data['role'])
        if 'status' in data:
            update_data['status'] = data['status']
        if 'is_active' in data:
            update_data['is_active'] = data['is_active']
        
        updated_user = user_repo.update(user_id, update_data)
        
        return jsonify({
            'message': 'User updated successfully',
            'user': updated_user.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Update user error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/stats', methods=['GET'])
@security_service.require_role('admin')
def get_system_stats():
    """Get system statistics"""
    try:
        # User statistics
        total_users = user_repo.count()
        active_users = user_repo.count(is_active=True)
        
        # Case statistics
        total_cases = case_repo.count()
        pending_cases = len(case_repo.get_pending_cases())
        
        # HS catalog statistics
        total_hs_items = hs_item_repo.count()
        
        # Embedding service info
        embedding_info = embedding_service.get_service_info()
        
        return jsonify({
            'users': {
                'total': total_users,
                'active': active_users
            },
            'cases': {
                'total': total_cases,
                'pending': pending_cases
            },
            'hs_catalog': {
                'total_items': total_hs_items
            },
            'embedding_service': embedding_info
        }), 200
        
    except Exception as e:
        logging.error(f"Get system stats error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/embed-catalog', methods=['POST'])
@security_service.require_role('admin')
def embed_hs_catalog():
    """Generate embeddings for HS catalog"""
    try:
        batch_size = request.json.get('batch_size', 100)
        
        # Create embeddings
        created_count = vector_index.create_embeddings_for_hs_catalog(batch_size)
        
        return jsonify({
            'message': f'Created {created_count} embeddings successfully',
            'created_count': created_count
        }), 200
        
    except Exception as e:
        logging.error(f"Embed HS catalog error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/health', methods=['GET'])
@security_service.require_role('admin')
def system_health():
    """Check system health"""
    try:
        from Service.db import db
        
        # Database health
        db_healthy = db.session.execute("SELECT 1").fetchone() is not None
        
        # Embedding service health
        embedding_healthy = embedding_service.is_available()
        
        return jsonify({
            'database': {
                'status': 'healthy' if db_healthy else 'unhealthy',
                'connected': db_healthy
            },
            'embedding_service': {
                'status': 'healthy' if embedding_healthy else 'unhealthy',
                'available': embedding_healthy
            },
            'overall_status': 'healthy' if db_healthy and embedding_healthy else 'unhealthy'
        }), 200
        
    except Exception as e:
        logging.error(f"System health check error: {e}")
        return jsonify({
            'database': {'status': 'unhealthy', 'connected': False},
            'embedding_service': {'status': 'unhealthy', 'available': False},
            'overall_status': 'unhealthy',
            'error': str(e)
        }), 500
