from flask import Flask
from flask_restx import Api
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import get_config
from backend.database import db
from backend.auth.jwt_handler import jwt_handler
from backend.middleware.error_handler import error_handler
from backend.routes.auth_routes import auth_ns
from backend.routes.incident_routes import incident_ns
from backend.routes.report_routes import report_ns
from backend.routes.analytics_routes import analytics_ns

# Initialize extensions
migrate = Migrate()


def create_app(config_name=None):
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Ensure upload and reports directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt_handler.init_app(app)
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Configure logging
    setup_logging(app)
    
    # Register error handlers
    error_handler(app)
    
    # Initialize API
    api = Api(
        app,
        version='1.0',
        title='AI-Powered Incident Report Generator API',
        description='Backend API for AI-powered incident report generation using local LLMs',
        doc='/api/docs',
        prefix='/api'
    )
    
    # Register namespaces
    api.add_namespace(auth_ns, path='/auth')
    api.add_namespace(incident_ns, path='/incidents')
    api.add_namespace(report_ns, path='/reports')
    api.add_namespace(analytics_ns, path='/analytics')
    
    # Create tables and seed the demo user used by unauthenticated requests
    # (the frontend has no login yet — see auth/decorators.jwt_optional).
    with app.app_context():
        from backend.models import user, incident, report  # noqa: F401  (register models)
        from backend.auth.decorators import get_or_create_demo_user

        db.create_all()
        get_or_create_demo_user()

    # Health check endpoints. /api/health is what the frontend polls; /health
    # is kept for existing container/orchestration probes.
    @app.route('/api/health')
    def api_health_check():
        return {'status': 'ok', 'service': 'incidentiq'}, 200

    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'incident-report-generator'}, 200

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'message': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'message': 'Internal server error'}, 500
    
    return app


def setup_logging(app):
    """Configure application logging."""
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper())
    log_file = app.config.get('LOG_FILE', 'app.log')
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    app.logger.setLevel(log_level)


# Create application instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
