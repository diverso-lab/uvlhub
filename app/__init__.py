import os
import secrets
import logging
import importlib.util

from flask import Flask, render_template, Blueprint
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_migrate import Migrate

# Load environment variables
load_dotenv()

# Create the instances
db = SQLAlchemy()
migrate = Migrate()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_bytes())
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('MARIADB_USER', 'default_user')}:"
        f"{os.getenv('MARIADB_PASSWORD', 'default_password')}@"
        f"{os.getenv('MARIADB_HOSTNAME', 'localhost')}:"
        f"{os.getenv('MARIADB_PORT', '3306')}/"
        f"{os.getenv('MARIADB_DATABASE', 'default_db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TIMEZONE = 'Europe/Madrid'
    TEMPLATES_AUTO_RELOAD = True
    UPLOAD_FOLDER = 'uploads'


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('MARIADB_USER', 'default_user')}:"
        f"{os.getenv('MARIADB_PASSWORD', 'default_password')}@"
        f"{os.getenv('MARIADB_HOSTNAME', 'localhost')}:"
        f"{os.getenv('MARIADB_PORT', '3306')}/"
        f"{os.getenv('MARIADB_TEST_DATABASE', 'default_db')}"
    )
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    pass


def create_app(config_name='development'):
    app = Flask(__name__)

    # If config_name is not provided, use the environment variable FLASK_ENV
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    # Load configuration
    if config_name == 'testing':
        app.config.from_object(TestingConfig)
    elif config_name == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # Initialize SQLAlchemy and Migrate with the app
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    register_blueprints(app)
    if config_name == 'development':
        print_registered_blueprints(app)

    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        from app.blueprints.auth.models import User
        return User.query.get(int(user_id))

    # Logging
    logging.basicConfig(filename='app.log', level=logging.ERROR,
                        format='%(asctime)s:%(levelname)s:%(message)s')

    # Custom error handlers
    register_error_handlers(app)

    # Injecting environment variables into jinja context
    @app.context_processor
    def inject_vars_into_jinja():
        return {
            'FLASK_APP_NAME': os.getenv('FLASK_APP_NAME'),
            'FLASK_ENV': os.getenv('FLASK_ENV'),
            'DOMAIN': os.getenv('DOMAIN', 'localhost')
        }

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
    from app.blueprints.auth.models import User
    return User.query.first()


def get_authenticated_user_profile():
    if current_user.is_authenticated:
        return current_user.profile
    return None


def get_authenticated_user():
    if current_user.is_authenticated:
        return current_user
    return None


def datasets_counter() -> int:
    from app.blueprints.dataset.models import DataSet
    count = DataSet.query.count()
    return count


def feature_models_counter() -> int:
    from app.blueprints.dataset.models import FeatureModel
    count = FeatureModel.query.count()
    return count


def register_blueprints(app):
    app.blueprint_url_prefixes = {}
    base_dir = os.path.abspath(os.path.dirname(__file__))
    blueprints_dir = os.path.join(base_dir, 'blueprints')
    for blueprint_name in os.listdir(blueprints_dir):
        blueprint_path = os.path.join(blueprints_dir, blueprint_name)
        if os.path.isdir(blueprint_path) and not blueprint_name.startswith('__'):
            try:
                routes_module = importlib.import_module(f'app.blueprints.{blueprint_name}.routes')
                for item in dir(routes_module):
                    if isinstance(getattr(routes_module, item), Blueprint):
                        blueprint = getattr(routes_module, item)
                        app.register_blueprint(blueprint)
            except ModuleNotFoundError as e:
                print(f"Could not load the module for Blueprint '{blueprint_name}': {e}")


def print_registered_blueprints(app):
    print("Registered blueprints")
    for name, blueprint in app.blueprints.items():
        url_prefix = app.blueprint_url_prefixes.get(name, 'No URL prefix set')
        print(f"Name: {name}, URL prefix: {url_prefix}")


app = create_app()
