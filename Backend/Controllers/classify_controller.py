from flask import Blueprint, request, jsonify
from Service.security import security_service
from Service.repository import case_repo, candidate_repo
from Service.Agente.re_rank import re_rank_service
from Service.modeloPln.nlp_service import nlp_service
from Models.case import Case, CaseStatus
from Models.candidate import Candidate
import logging

classify_bp = Blueprint('classify', __name__, url_prefix='/api/classify')

@classify_bp.route('', methods=['POST'])
@security_service.require_auth
def classify_product():
    """Classify a product using AI/ML algorithms"""
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
            'title': data.get('title', f'Classification: {data["product_name"]}'),
            'product_name': data['product_name'],
            'product_description': data['product_description'],
            'brand': data.get('brand'),
            'model': data.get('model'),
            'origin_country': data.get('origin_country'),
            'destination_country': data.get('destination_country'),
            'status': CaseStatus.DRAFT,
            'priority': data.get('priority', 'medium')
        }
        
        case = case_repo.create(case_data)
        
        # Perform classification
        candidates = re_rank_service.classify_product(case)
        
        # Save candidates to database
        for candidate in candidates:
            candidate_repo.create(candidate.__dict__)
        
        # Get classification summary
        summary = re_rank_service.get_classification_summary(candidates)
        
        # Update case with best candidate
        if candidates:
            best_candidate = candidates[0]
            case.proposed_hs_code = best_candidate.hs_code
            case.confidence_score = best_candidate.confidence_score
            case.classification_method = best_candidate.classification_method
            case_repo.update(case.id, {
                'proposed_hs_code': best_candidate.hs_code,
                'confidence_score': best_candidate.confidence_score,
                'classification_method': best_candidate.classification_method
            })
        
        # Perform NLP analysis
        nlp_analysis = nlp_service.analyze_text(data['product_description'])
        
        return jsonify({
            'message': 'Classification completed successfully',
            'case_id': case.id,
            'case_number': case.case_number,
            'classification_summary': summary,
            'candidates': [c.to_dict() for c in candidates],
            'nlp_analysis': nlp_analysis
        }), 200
        
    except Exception as e:
        logging.error(f"Classification error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@classify_bp.route('/<int:case_id>', methods=['GET'])
@security_service.require_auth
def get_classification(case_id):
    """Get classification results for a specific case"""
    try:
        case = case_repo.get_by_id(case_id)
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        # Get candidates for this case
        candidates = candidate_repo.get_by_case(case_id)
        
        # Get classification summary
        summary = re_rank_service.get_classification_summary(candidates)
        
        return jsonify({
            'case': case.to_dict(),
            'candidates': [c.to_dict() for c in candidates],
            'classification_summary': summary
        }), 200
        
    except Exception as e:
        logging.error(f"Get classification error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@classify_bp.route('/history', methods=['GET'])
@security_service.require_auth
def get_classification_history():
    """Get classification history for current user"""
    try:
        user_id = request.current_user['user_id']
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status')
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get cases for user
        cases = case_repo.get_by_user(user_id)
        
        # Filter by status if provided
        if status:
            cases = [c for c in cases if c.status.value == status]
        
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
        logging.error(f"Get classification history error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@classify_bp.route('/<int:case_id>/candidates', methods=['GET'])
@security_service.require_auth
def get_candidates(case_id):
    """Get all candidates for a specific case"""
    try:
        case = case_repo.get_by_id(case_id)
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        candidates = candidate_repo.get_by_case(case_id)
        
        return jsonify({
            'case_id': case_id,
            'candidates': [c.to_dict() for c in candidates]
        }), 200
        
    except Exception as e:
        logging.error(f"Get candidates error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@classify_bp.route('/<int:case_id>/select', methods=['POST'])
@security_service.require_auth
def select_candidate(case_id):
    """Select a candidate as the final classification"""
    try:
        data = request.get_json()
        candidate_id = data.get('candidate_id')
        
        if not candidate_id:
            return jsonify({'error': 'Candidate ID is required'}), 400
        
        # Get case and candidate
        case = case_repo.get_by_id(case_id)
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        candidate = candidate_repo.get_by_id(candidate_id)
        if not candidate or candidate.case_id != case_id:
            return jsonify({'error': 'Candidate not found'}), 404
        
        # Update case with selected candidate
        case.final_hs_code = candidate.hs_code
        case.confidence_score = candidate.confidence_score
        case.classification_method = candidate.classification_method
        case.status = CaseStatus.APPROVED
        
        case_repo.update(case.id, {
            'final_hs_code': candidate.hs_code,
            'confidence_score': candidate.confidence_score,
            'classification_method': candidate.classification_method,
            'status': CaseStatus.APPROVED
        })
        
        # Mark candidate as selected
        candidate_repo.update(candidate.id, {'is_selected': True})
        
        return jsonify({
            'message': 'Candidate selected successfully',
            'case': case.to_dict(),
            'selected_candidate': candidate.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Select candidate error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@classify_bp.route('/analyze', methods=['POST'])
@security_service.require_auth
def analyze_text():
    """Analyze text using NLP services"""
    try:
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Perform NLP analysis
        analysis = nlp_service.analyze_text(text)
        
        return jsonify({
            'analysis': analysis
        }), 200
        
    except Exception as e:
        logging.error(f"Text analysis error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@classify_bp.route('/similarity', methods=['POST'])
@security_service.require_auth
def calculate_similarity():
    """Calculate similarity between two texts"""
    try:
        data = request.get_json()
        text1 = data.get('text1')
        text2 = data.get('text2')
        
        if not text1 or not text2:
            return jsonify({'error': 'Both texts are required'}), 400
        
        # Calculate similarity
        similarity = nlp_service.calculate_similarity(text1, text2)
        
        return jsonify({
            'text1': text1,
            'text2': text2,
            'similarity': similarity
        }), 200
        
    except Exception as e:
        logging.error(f"Similarity calculation error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@classify_bp.route('/stats', methods=['GET'])
@security_service.require_auth
def get_classification_stats():
    """Get classification statistics for current user"""
    try:
        user_id = request.current_user['user_id']
        
        # Get user's cases
        cases = case_repo.get_by_user(user_id)
        
        # Calculate statistics
        total_cases = len(cases)
        approved_cases = len([c for c in cases if c.status.value == 'approved'])
        pending_cases = len([c for c in cases if c.status.value == 'pending'])
        draft_cases = len([c for c in cases if c.status.value == 'draft'])
        
        # Calculate average confidence score
        confidence_scores = [c.confidence_score for c in cases if c.confidence_score]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Method distribution
        method_counts = {}
        for case in cases:
            method = case.classification_method
            if method:
                method_counts[method] = method_counts.get(method, 0) + 1
        
        return jsonify({
            'total_cases': total_cases,
            'approved_cases': approved_cases,
            'pending_cases': pending_cases,
            'draft_cases': draft_cases,
            'average_confidence': round(avg_confidence, 2),
            'method_distribution': method_counts
        }), 200
        
    except Exception as e:
        logging.error(f"Get classification stats error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
