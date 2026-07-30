from flask import request, g
import logging
import time

logger = logging.getLogger(__name__)


def request_logger(app):
    """Register request logging middleware."""
    
    @app.before_request
    def before_request():
        """Log request details before processing."""
        g.start_time = time.time()
        
        logger.info(
            f"Incoming request: {request.method} {request.path} "
            f"from {request.remote_addr}"
        )
    
    @app.after_request
    def after_request(response):
        """Log response details after processing."""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            logger.info(
                f"Response: {request.method} {request.path} "
                f"Status: {response.status_code} "
                f"Duration: {duration:.3f}s"
            )
        
        return response
    
    @app.teardown_request
    def teardown_request(exception):
        """Clean up after request."""
        if exception:
            logger.error(f"Request teardown with exception: {exception}")
