from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity


def token_required(f):
    """Decorator to require JWT token for endpoint access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Token is invalid or expired'}), 401
    return decorated_function


def admin_required(f):
    """Decorator to require admin role for endpoint access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            from backend.models.user import User
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or user.role != 'admin':
                return jsonify({'message': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Authorization failed'}), 401
    return decorated_function
