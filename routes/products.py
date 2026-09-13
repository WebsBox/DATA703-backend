from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from extensions import db
from models import Product
from utils.response import ok, fail
from utils.auth_helpers import get_current_user_id, get_current_user_role

products_bp = Blueprint('products', __name__, url_prefix='/api/products')


@products_bp.route('', methods=['GET'])
def list_products():
    """列出所有可用产品，支持搜索和筛选"""
    keyword = request.args.get('keyword', '').strip()
    category = request.args.get('category', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    owner_id = request.args.get('owner_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    query = Product.query

    if keyword:
        like = f'%{keyword}%'
        query = query.filter(or_(Product.name.ilike(like), Product.description.ilike(like)))
    if category:
        query = query.filter(Product.category == category)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if owner_id is not None:
        query = query.filter(Product.owner_id == owner_id)

    query = query.order_by(Product.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return ok({
        'items': [p.to_dict() for p in pagination.items],
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'pages': pagination.pages,
    })


@products_bp.route('/categories', methods=['GET'])
def list_categories():
    """获取所有不重复的产品分类"""
    categories = db.session.query(Product.category).filter(
        Product.category.isnot(None), Product.category != ''
    ).distinct().order_by(Product.category.asc()).all()
    return ok([c[0] for c in categories])


@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return fail('Product not found', 404)
    return ok(product.to_dict())


@products_bp.route('', methods=['POST'])
@jwt_required()
def create_product():
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}

    name = data.get('name', '').strip()
    if not name:
        return fail('Product name is required', 400)

    product = Product(
        name=name,
        description=data.get('description', '').strip() or None,
        price=float(data.get('price', 0) or 0),
        category=data.get('category', '').strip() or None,
        image_id=int(data.get('image_id')) if data.get('image_id') else None,
        stock=int(data.get('stock', 0) or 0),
        owner_id=user_id,
    )
    db.session.add(product)
    db.session.commit()
    return ok(product.to_dict(), 'Created successfully', 201)


@products_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    user_id = get_current_user_id()
    user_role = get_current_user_role()
    product = Product.query.get(product_id)
    if not product:
        return fail('Product not found', 404)

    # Only owner or admin can edit
    if product.owner_id != user_id and user_role != 'admin':
        return fail('You are not allowed to edit this product', 403)

    data = request.get_json(silent=True) or {}
    if 'name' in data:
        name = str(data['name']).strip()
        if not name:
            return fail('Product name is required', 400)
        product.name = name
    if 'description' in data:
        product.description = str(data['description']).strip() or None
    if 'price' in data:
        product.price = float(data['price'] or 0)
    if 'category' in data:
        product.category = str(data['category']).strip() or None
    if 'image_id' in data:
        product.image_id = int(data['image_id']) if data['image_id'] else None
    if 'stock' in data:
        product.stock = int(data['stock'] or 0)

    db.session.commit()
    return ok(product.to_dict(), 'Updated successfully')


@products_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    user_id = get_current_user_id()
    user_role = get_current_user_role()
    product = Product.query.get(product_id)
    if not product:
        return fail('Product not found', 404)

    if product.owner_id != user_id and user_role != 'admin':
        return fail('You are not allowed to delete this product', 403)

    db.session.delete(product)
    db.session.commit()
    return ok(message='Deleted successfully')
