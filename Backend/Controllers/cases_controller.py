from flask import Blueprint, request, jsonify
from Service.security import security_service
from Service.repository import case_repo, user_repo
from Models.case import Case, CaseStatus, CasePriority
import logging

cases_bp = Blueprint('cases', __name__, url_prefix='/api/cases')

@cases_bp.route('', methods=['GET'])
@security_service.require_auth
def get_cases():
    """Get all cases with filtering and pagination"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status')
        priority = request.args.get('priority')
        search = request.args.get('search')
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get cases based on user role
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        
        if user_role == 'admin':
            cases = case_repo.get_all()
        else:
            cases = case_repo.get_by_user(user_id)
        
        # Apply filters
        if status:
            cases = [c for c in cases if c.status.value == status]
        
        if priority:
            cases = [c for c in cases if c.priority.value == priority]
        
        if search:
            search_lower = search.lower()
            cases = [c for c in cases if 
                    search_lower in c.product_name.lower() or 
                    search_lower in c.product_description.lower() or
                    search_lower in c.case_number.lower()]
        
        # Apply pagination
        total_cases = len(cases)
        paginated_cases = cases[offset:offset + per_page]
        
        return jsonify({
            'cases': [c.to_dict() for c in paginated_cases],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_cases,
                'pages': (total_cases + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get cases error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@cases_bp.route('', methods=['POST'])
@security_service.require_auth
def create_case():
    """Create a new case"""
    try:
        data = request.get_json()
        user_id = request.current_user['user_id']
        
        # Validate required fields
        required_fields = ['product_name', 'product_description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create case
        case_data = {
            'user_id': user_id,
            'title': data.get('title', f'Case: {data["product_name"]}'),
            'description': data.get('description'),
            'product_name': data['product_name'],
            'product_description': data['product_description'],
            'brand': data.get('brand'),
            'model': data.get('model'),
            'origin_country': data.get('origin_country'),
            'destination_country': data.get('destination_country'),
            'status': CaseStatus.DRAFT,
            'priority': data.get('priority', 'medium'),
            'notes': data.get('notes')
        }
        
        case = case_repo.create(case_data)
        
        return jsonify({
            'message': 'Case created successfully',
            'case': case.to_dict()
        }), 201
        
    except Exception as e:
        logging.error(f"Create case error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@cases_bp.route('/<int:case_id>', methods=['GET'])
@security_service.require_auth
def get_case(case_id):
    """Get a specific case"""
    try:
        case = case_repo.get_by_id(case_id)
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        # Check permissions
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        
        if user_role != 'admin' and case.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'case': case.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Get case error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@cases_bp.route('/<int:case_id>', methods=['PUT'])
@security_service.require_auth
def update_case(case_id):
    """Update a case"""
    try:
        case = case_repo.get_by_id(case_id)
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        # Check permissions
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        
        if user_role != 'admin' and case.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Allow updating certain fields
        allowed_fields = [
            'title', 'description', 'product_name', 'product_description',
            'brand', 'model', 'origin_country', 'destination_country',
            'priority', 'notes'
        ]
        
        update_data = {}
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # Update case
        updated_case = case_repo.update(case_id, update_data)
        
        return jsonify({
            'message': 'Case updated successfully',
            'case': updated_case.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Update case error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@cases_bp.route('/<int:case_id>', methods=['DELETE'])
@security_service.require_auth
def delete_case(case_id):
    """Delete a case"""
    try:
        case = case_repo.get_by_id(case_id)
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        # Check permissions
        user_id = request.current_user['user_id']
        user_role = request.current_user['role']
        
        if user_role != 'admin' and case.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Delete case
        case_repo.delete(case_id)
        
        return jsonify({
            'message': 'Case deleted successfully'
        }), 200
        
    except Exception as e:
        logging.error(f"Delete case error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@cases_bp.route('/<int:case_id>/submit', methods=['POST'])
@security_service.require_auth
def submit_case(case_id):
    """Submit a case for review"""
    try:
        case = case_repo.get_by_id(case_id)
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        # Check permissions
        user_id = request.current_user['user_id']
        if case.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Submit case
        case.submit()
        case_repo.update(case_id, {'status': CaseStatus.PENDING})
        
        return jsonify({
            'message': 'Case submitted successfully',
            'case': case.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Submit case error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@cases_bp.route('/<int:case_id>/assign', methods=['POST'])
@security_service.require_role('admin')
def assign_case(case_id):
    """Assign a case to a reviewer"""
    try:
        data = request.get_json()
        reviewer_id = data.get('reviewer_id')
        
        if not reviewer_id:
            return jsonify({'error': 'Reviewer ID is required'}), 400
        
        # Check if reviewer exists
        reviewer = user_repo.get_by_id(reviewer_id)
        if not reviewer:
            return jsonify({'error': 'Reviewer not found'}), 404
        
        case = case_repo.get_by_id(case_id)
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        # Assign case
        case.assign_review(reviewer_id)
        case_repo.update(case_id, {
            'status': CaseStatus.IN_REVIEW,
            'assigned_to': reviewer_id
        })
        
        return jsonify({
            'message': 'Case assigned successfully',
            'case': case.to_dict(),
            'reviewer': reviewer.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Assign case error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
