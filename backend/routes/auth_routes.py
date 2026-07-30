from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from backend.models.user import User, db
from backend.utils.schemas import user_schema, user_login_schema
from marshmallow import ValidationError

auth_ns = Namespace('auth', description='Authentication operations')

# DTOs
user_register_model = auth_ns.model('UserRegister', {
    'username': fields.String(required=True, description='Username'),
    'email': fields.String(required=True, description='Email address'),
    'password': fields.String(required=True, description='Password'),
    'first_name': fields.String(description='First name'),
    'last_name': fields.String(description='Last name')
})

user_login_model = auth_ns.model('UserLogin', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

token_model = auth_ns.model('Token', {
    'access_token': fields.String(description='Access token'),
    'refresh_token': fields.String(description='Refresh token'),
    'user': fields.Nested(auth_ns.model('User', {
        'id': fields.Integer,
        'username': fields.String,
        'email': fields.String,
        'first_name': fields.String,
        'last_name': fields.String,
        'role': fields.String
    }))
})


@auth_ns.route('/register')
class UserRegister(Resource):
    @auth_ns.doc('register_user')
    @auth_ns.expect(user_register_model)
    @auth_ns.response(201, 'Created', token_model)
    def post(self):
        """Register a new user."""
        try:
            data = user_schema.load(request.json)
        except ValidationError as err:
            return {'message': 'Validation error', 'errors': err.messages}, 400
        
        # Check if user exists
        if User.query.filter_by(username=data['username']).first():
            return {'message': 'Username already exists'}, 400
        
        if User.query.filter_by(email=data['email']).first():
            return {'message': 'Email already exists'}, 400
        
        # Create user
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(identity=user)
        refresh_token = create_refresh_token(identity=user)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }, 201


@auth_ns.route('/login')
class UserLogin(Resource):
    @auth_ns.doc('login_user')
    @auth_ns.expect(user_login_model)
    @auth_ns.response(200, 'Success', token_model)
    def post(self):
        """Login user."""
        try:
            data = user_login_schema.load(request.json)
        except ValidationError as err:
            return {'message': 'Validation error', 'errors': err.messages}, 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return {'message': 'Invalid credentials'}, 401
        
        if not user.is_active:
            return {'message': 'Account is inactive'}, 403
        
        # Generate tokens
        access_token = create_access_token(identity=user)
        refresh_token = create_refresh_token(identity=user)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }


@auth_ns.route('/refresh')
class TokenRefresh(Resource):
    @auth_ns.doc('refresh_token')
    @jwt_required(refresh=True)
    @auth_ns.response(200, 'Success', token_model)
    def post(self):
        """Refresh access token."""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return {'message': 'User not found'}, 404
        
        access_token = create_access_token(identity=user)
        refresh_token = create_refresh_token(identity=user)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }


@auth_ns.route('/me')
class UserProfile(Resource):
    @auth_ns.doc('get_current_user')
    @jwt_required()
    @auth_ns.marshal_with(auth_ns.model('User', {
        'id': fields.Integer,
        'username': fields.String,
        'email': fields.String,
        'first_name': fields.String,
        'last_name': fields.String,
        'role': fields.String,
        'is_active': fields.Boolean,
        'created_at': fields.String,
        'updated_at': fields.String
    }))
    def get(self):
        """Get current user profile."""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return {'message': 'User not found'}, 404
        
        return user.to_dict()
