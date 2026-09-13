from flask import Blueprint, request
from flask_jwt_extended import create_access_token, jwt_required
from extensions import db
from models import User
from utils.response import ok, fail
from utils.auth_helpers import get_current_user_id

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def generate_token_for_user(user: User) -> str:
    """Generate a JWT access token for a user."""
    additional_claims = {'username': user.username, 'role': user.role}
    return create_access_token(identity=str(user.id), additional_claims=additional_claims)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not username or not email or not password:
        return fail('Username, email and password are required', 400)
    if len(username) < 3:
        return fail('Username must be at least 3 characters', 400)
    if len(password) < 6:
        return fail('Password must be at least 6 characters', 400)
    if User.query.filter_by(username=username).first():
        return fail('Username already taken', 400)
    if User.query.filter_by(email=email).first():
        return fail('Email already registered', 400)

    user = User(username=username, email=email, role='user')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    access_token = generate_token_for_user(user)
    return ok({
        'token': access_token,
        'user': user.to_dict(),
    }, 'Registered successfully', 201)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    identifier = data.get('username', '') or data.get('email', '')
    password = data.get('password', '')

    if not identifier or not password:
        return fail('Please provide username/email and password', 400)

    # Try username first, then email
    user = User.query.filter_by(username=identifier).first()
    if not user:
        user = User.query.filter_by(email=identifier).first()

    if not user or not user.check_password(password):
        return fail('Invalid username or password', 401)

    access_token = generate_token_for_user(user)
    return ok({
        'token': access_token,
        'user': user.to_dict(),
    }, 'Login successful')


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user = User.query.get(get_current_user_id())
    if not user:
        return fail('User not found', 404)
    return ok(user.to_dict())


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """修改自己的密码"""
    user_id = get_current_user_id()
    user = User.query.get(user_id)
    if not user:
        return fail('User not found', 404)

    data = request.get_json(silent=True) or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return fail('Old and new password are required', 400)
    if not user.check_password(old_password):
        return fail('Old password is incorrect', 401)
    if len(new_password) < 6:
        return fail('New password must be at least 6 characters', 400)

    user.set_password(new_password)
    db.session.commit()
    return ok(message='Password changed successfully')
