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
    from models import User
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('[seed] Default admin created: admin / admin123')


# Vercel Python Runtime needs the app exposed at module level
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3031, debug=True)
