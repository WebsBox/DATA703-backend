import os
from flask import Blueprint, request, send_file, Response
from flask_jwt_extended import jwt_required
from extensions import db
from models import Image
from utils.response import ok, fail
from utils.auth_helpers import get_current_user_id, get_current_user_role

images_bp = Blueprint('images', __name__, url_prefix='/api/images')

ALLOWED_MIME = {'image/jpeg', 'image/jpg', 'image/png'}
ALLOWED_EXTS = {'.jpg', '.jpeg', '.png'}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB


@images_bp.route('', methods=['POST'])
@jwt_required()
def upload_image():
    """上传图片，返回 image_id"""
    user_id = get_current_user_id()

    if 'file' not in request.files:
        return fail('No upload file found', 400)

    file = request.files['file']
    if not file or not file.filename:
        return fail('No file selected', 400)

    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTS:
        return fail('Only JPG / PNG formats are supported', 400)

    mime = (file.mimetype or '').lower()
    if mime and mime not in ALLOWED_MIME and mime not in {'image/jpg'}:
        return fail('Only JPG / PNG formats are supported', 400)

    data = file.read()
    size = len(data)
    if size == 0:
        return fail('File is empty', 400)
    if size > MAX_SIZE:
        return fail(f'Image size must not exceed {MAX_SIZE // (1024 * 1024)}MB', 413)

    # 规范化 mime_type
    mime_type = 'image/jpeg' if ext in ('.jpg', '.jpeg') else 'image/png'

    img = Image(
        filename=filename,
        mime_type=mime_type,
        size=size,
        image_data=data,
        owner_id=user_id,
    )
    db.session.add(img)
    db.session.commit()

    return ok({
        'id': img.id,
        'image_url': f'/api/images/{img.id}',
        'filename': img.filename,
        'size': size,
    }, 'Uploaded successfully', 201)


@images_bp.route('/<int:image_id>', methods=['GET'])
def get_image(image_id):
    """返回图片二进制，浏览器可直接渲染"""
    img = Image.query.get(image_id)
    if not img:
        return fail('Image not found', 404)

    # 直接用 Response 返回二进制，设置正确的 Content-Type
    return Response(
        img.image_data,
        mimetype=img.mime_type,
        headers={
            'Content-Disposition': f'inline; filename="{img.filename}"',
            'Cache-Control': 'public, max-age=86400',  # 缓存 24h
        },
    )


@images_bp.route('/<int:image_id>', methods=['DELETE'])
@jwt_required()
def delete_image(image_id):
    """删除图片（仅作者或管理员）"""
    user_id = get_current_user_id()
    user_role = get_current_user_role()
    img = Image.query.get(image_id)
    if not img:
        return fail('Image not found', 404)

    if img.owner_id != user_id and user_role != 'admin':
        return fail('You are not allowed to delete this image', 403)

    db.session.delete(img)
    db.session.commit()
    return ok(message='Deleted successfully')
