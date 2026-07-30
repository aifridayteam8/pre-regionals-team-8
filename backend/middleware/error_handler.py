from flask import jsonify
from werkzeug.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)


def error_handler(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(400)
    def bad_request(error):
        logger.warning(f"Bad request: {error.description}")
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description) if error.description else 'Invalid request'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        logger.warning(f"Unauthorized access: {error.description}")
        return jsonify({
            'error': 'Unauthorized',
            'message': str(error.description) if error.description else 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        logger.warning(f"Forbidden access: {error.description}")
        return jsonify({
            'error': 'Forbidden',
            'message': str(error.description) if error.description else 'Access denied'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        logger.info(f"Resource not found: {error.description}")
        return jsonify({
            'error': 'Not Found',
            'message': str(error.description) if error.description else 'Resource not found'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        logger.warning(f"Method not allowed: {error.description}")
        return jsonify({
            'error': 'Method Not Allowed',
            'message': str(error.description) if error.description else 'Method not allowed'
        }), 405
    
    @app.errorhandler(413)
    def payload_too_large(error):
        logger.warning(f"Payload too large: {error.description}")
        return jsonify({
            'error': 'Payload Too Large',
            'message': str(error.description) if error.description else 'File too large'
        }), 413
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        logger.error(f"HTTP exception: {error.code} - {error.description}")
        return jsonify({
            'error': error.name,
            'message': str(error.description) if error.description else error.name
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.exception(f"Unhandled exception: {error}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
