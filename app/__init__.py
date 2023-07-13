import os
import secrets
import logging

from flask import Flask, render_template
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_wtf import CSRFProtect

# Load environment variables
load_dotenv()

# Create the instances
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name=None):
    app = Flask(__name__)
    app.secret_key = secrets.token_bytes()

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('MYSQL_USER', 'default_user')}:{os.getenv('MYSQL_PASSWORD', 'default_password')}"
        f"@{os.getenv('MYSQL_HOSTNAME', 'localhost')}:3306/{os.getenv('MYSQL_DATABASE', 'default_db')}"
    )

    # Timezone
    app.config['TIMEZONE'] = 'Europe/Madrid'

    # Templates configuration
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Uploads feature models configuration
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')

    # Initialize SQLAlchemy and Migrate with the app
    db.init_app(app)
    migrate.init_app(app, db)

    # Import blueprints
    from app.tests.routes import test_routes
    from .auth import auth_bp
    from .dataset import dataset_bp
    from .explore import explore_bp
    from .profile import profile_bp
    from .team import team_bp
    from .public import public_bp

    # Register blueprints
    app.register_blueprint(test_routes)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dataset_bp)
    app.register_blueprint(explore_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(public_bp)

    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        from app.auth.models import User
        return User.query.get(int(user_id))

    # Logging
    logging.basicConfig(filename='app.log', level=logging.DEBUG)

    # Custom error handlers
    register_error_handlers(app)

    # Injecting FLASK_APP_NAME environment variable into jinja context
    @app.context_processor
    def inject_flask_app_name():
        return dict(FLASK_APP_NAME=os.getenv('FLASK_APP_NAME'))

    return app


def register_error_handlers(app):
    @app.errorhandler(500)
    def base_error_handler(e):
        app.logger.error('Internal Server Error: %s', str(e))  # Error logging
        return render_template('500.html'), 500

    @app.errorhandler(404)
    def error_404_handler(e):
        app.logger.warning('Page Not Found: %s', str(e))  # Warning logging
        return render_template('404.html'), 404

    @app.errorhandler(401)
    def error_401_handler(e):
        app.logger.warning('Unauthorized Access: %s', str(e))  # Warning logging
        return render_template('401.html'), 401

    @app.errorhandler(400)
    def error_400_handler(e):
        app.logger.warning('Bad Request: %s', str(e))  # Warning logging
        return render_template('400.html'), 400


def get_test_client():
    """
    Function to get the test client of the application.
    :return: A Flask application test client.
    """
    return create_app().test_client()


def upload_folder_name():
    return 'uploads'


def get_user_by_token(token):
    # TODO
    from app.auth.models import User
    return User.query.first()


def get_authenticated_user_profile():
    if current_user.is_authenticated:
        return current_user.profile
    return None


def datasets_counter() -> int:
    from app.dataset.models import DataSet
    count = DataSet.query.count()
    return count


def feature_models_counter() -> int:
    from app.dataset.models import FeatureModel
    count = FeatureModel.query.count()
    return count


app = create_app()
