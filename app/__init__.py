import os
import logging

from flask import Flask, render_template
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_migrate import Migrate

from app.managers.blueprint_manager import BlueprintManager
from app.managers.config_manager import ConfigManager

# Load environment variables
load_dotenv()

# Create the instances
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name='development'):
    app = Flask(__name__)

    # Load configuration according to environment
    config_manager = ConfigManager(app)
    config_manager.load_config(config_name=config_name)

    # Initialize SQLAlchemy and Migrate with the app
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    blueprint_manager = BlueprintManager(app)
    blueprint_manager.register_blueprints()

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


app = create_app()
