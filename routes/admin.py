from functools import wraps
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from extensions import db
from models import User, Product
from utils.response import ok, fail
from utils.auth_helpers import get_current_user_id, get_current_user_role

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if get_current_user_role() != 'admin':
            return fail('Admin privilege required', 403)
        return fn(*args, **kwargs)
    return wrapper


@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()

    query = User.query
    if keyword:
        like = f'%{keyword}%'
        query = query.filter(User.username.ilike(like) | User.email.ilike(like))

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return ok({
        'items': [u.to_dict() for u in pagination.items],
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'pages': pagination.pages,
    })


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return fail('User not found', 404)

    data = request.get_json(silent=True) or {}
    if 'role' in data:
        if data['role'] not in ('user', 'admin'):
            return fail('Invalid role', 400)
        user.role = data['role']
    if 'password' in data and data['password']:
        user.set_password(data['password'])

    db.session.commit()
    return ok(user.to_dict(), 'Updated successfully')


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    current_id = get_current_user_id()
    if current_id == user_id:
        return fail('Cannot delete yourself', 400)

    user = User.query.get(user_id)
    if not user:
        return fail('User not found', 404)

    db.session.delete(user)
    db.session.commit()
    return ok(message='Deleted successfully')


@admin_bp.route('/products', methods=['GET'])
@admin_required
def admin_list_products():
    """管理员查看所有产品，可筛选"""
    keyword = request.args.get('keyword', '').strip()
    owner_id = request.args.get('owner_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Product.query
    if keyword:
        like = f'%{keyword}%'
        query = query.filter(Product.name.ilike(like))
    if owner_id:
        query = query.filter(Product.owner_id == owner_id)

    pagination = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return ok({
        'items': [p.to_dict() for p in pagination.items],
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'pages': pagination.pages,
    })


@admin_bp.route('/stats', methods=['GET'])
@admin_required
def stats():
    return ok({
        'user_count': User.query.count(),
        'admin_count': User.query.filter_by(role='admin').count(),
        'product_count': Product.query.count(),
    })
