from flask import Flask, jsonify
from flask_cors import CORS
from Config.settings import get_config
from Service.db import init_db
from Service.security import security_service
from Controllers.auth_controller import auth_bp
from Controllers.classify_controller import classify_bp
from Controllers.cases_controller import cases_bp
from Controllers.admin_controller import admin_bp
from Controllers.health_controller import health_bp
import logging
import os

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config()
    app.config.from_object(config)
    config.init_app(app)
    
    # Initialize extensions
    init_db(app)
    security_service.init_app(app)
    
    # Enable CORS
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(app.config.get('LOG_FILE', 'logs/clasificode.log')),
            logging.StreamHandler()
        ]
    )
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(classify_bp)
    app.register_blueprint(cases_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(health_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403
    
    # Root endpoint
    @app.route('/')
    def root():
        return jsonify({
            'message': 'ClasifiCode API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'auth': '/api/auth',
                'classify': '/api/classify',
                'cases': '/api/cases',
                'admin': '/api/admin',
                'health': '/api/health'
            }
        })
    
    # API info endpoint
    @app.route('/api')
    def api_info():
        return jsonify({
            'name': 'ClasifiCode API',
            'version': '1.0.0',
            'description': 'Sistema de Clasificación Arancelaria con IA/ML',
            'endpoints': {
                'authentication': {
                    'login': 'POST /api/auth/login',
                    'register': 'POST /api/auth/register',
                    'refresh': 'POST /api/auth/refresh',
                    'profile': 'GET /api/auth/profile'
                },
                'classification': {
                    'classify': 'POST /api/classify',
                    'history': 'GET /api/classify/history',
                    'analysis': 'POST /api/classify/analyze'
                },
                'cases': {
                    'list': 'GET /api/cases',
                    'create': 'POST /api/cases',
                    'detail': 'GET /api/cases/{id}',
                    'update': 'PUT /api/cases/{id}'
                },
                'admin': {
                    'users': 'GET /api/admin/users',
                    'stats': 'GET /api/admin/stats',
                    'health': 'GET /api/admin/health'
                }
            }
        })
    
    return app

def main():
    """Main application entry point"""
    app = create_app()
    
    # Get configuration
    host = app.config.get('API_HOST', '0.0.0.0')
    port = app.config.get('API_PORT', 8000)
    debug = app.config.get('DEBUG', False)
    
    # Create logs directory if it doesn't exist
    log_file = app.config.get('LOG_FILE', 'logs/clasificode.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Log startup information
    logging.info(f"Starting ClasifiCode API on {host}:{port}")
    logging.info(f"Debug mode: {debug}")
    logging.info(f"Environment: {app.config.get('FLASK_ENV', 'development')}")
    
    # Run the application
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

if __name__ == '__main__':
    main()