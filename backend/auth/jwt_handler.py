from flask_jwt_extended import JWTManager
from backend.models.user import User

jwt_handler = JWTManager()


@jwt_handler.user_identity_loader
def user_identity_lookup(user):
    """Return user identity for JWT token."""
    return str(user.id)


@jwt_handler.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Load user from JWT token."""
    identity = jwt_data["sub"]
    return User.query.filter_by(id=int(identity)).one_or_none()


@jwt_handler.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired token."""
    return {'message': 'Token has expired'}, 401


@jwt_handler.invalid_token_loader
def invalid_token_callback(error):
    """Handle invalid token."""
    return {'message': 'Invalid token'}, 401


@jwt_handler.unauthorized_loader
def missing_token_callback(error):
    """Handle missing token."""
    return {'message': 'Authorization token is missing'}, 401
