from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

DEMO_USERNAME = 'demo'


def get_or_create_demo_user():
    """Return the seeded demo user, creating it if missing.

    Used while the frontend has no login: unauthenticated requests are
    attributed to this user. Remove once the frontend performs real login.
    """
    from backend.database import db
    from backend.models.user import User

    user = User.query.filter_by(username=DEMO_USERNAME).first()
    if user is None:
        user = User(
            username=DEMO_USERNAME,
            email='demo@incidentiq.local',
            first_name='Demo',
            last_name='User',
            role='analyst',
            is_active=True,
        )
        user.set_password('demo-password-change-me')
        db.session.add(user)
        db.session.commit()
    return user


def jwt_optional(f):
    """Allow the endpoint with or without a JWT.

    With a valid token the request runs as that user; without one it runs as
    the seeded demo user. Sets g.current_user_id either way. This keeps the
    auth routes/JWT machinery intact so the frontend can add login later
    without backend changes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
        except Exception:
            identity = None

        if identity is not None:
            g.current_user_id = int(identity)
        else:
            g.current_user_id = get_or_create_demo_user().id

        return f(*args, **kwargs)
    return decorated_function


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
