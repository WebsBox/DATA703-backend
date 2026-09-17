import os

# Neon 云数据库连接串（默认）
NEON_DATABASE_URL = (
    "postgresql://neondb_owner:npg_F8QbLDW4HTVO"
    "@ep-divine-brook-auz0jhq8-pooler.c-10.us-east-1.aws.neon.tech/neondb"
    "?sslmode=require&channel_binding=require"
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    # 优先使用环境变量 DATABASE_URL，否则使用 Neon PostgreSQL，最后 fallback 到本地 SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        NEON_DATABASE_URL,
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # PostgreSQL 连接池配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
