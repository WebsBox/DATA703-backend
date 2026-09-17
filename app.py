import os
from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db, jwt


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Import models so SQLAlchemy knows about them
    import models  # noqa: F401

    # Register blueprints
    from routes.auth import auth_bp
    from routes.products import products_bp
    from routes.admin import admin_bp
    from routes.images import images_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(images_bp)

    @app.route('/api/health')
    def health():
        return {'status': 'ok'}

    # Create tables and seed default admin
    with app.app_context():
        db.create_all()
        seed_default_admin()

    return app


def seed_default_admin():
    """从环境变量读取管理员凭据，首次启动时自动创建"""
    from models import User
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.environ.get('ADMIN_PASSWORD')

    if not User.query.filter_by(username=admin_username).first():
        if not admin_password:
            print('[seed] ADMIN_PASSWORD not set, skipping default admin creation')
            return
        admin = User(username=admin_username, email=admin_email, role='admin')
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f'[seed] Default admin created: {admin_username}')


# Vercel Python Runtime needs the app exposed at module level
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3031, debug=True)
