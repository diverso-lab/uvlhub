import os
import secrets

from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_migrate import Migrate

# Load environment variables
load_dotenv()

# Instances
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_name=None):
    """
    Factory function to create the Flask application.
    :param config_name: The name of the configuration to use.
    :return: A Flask application object.
    """
    app = Flask(__name__)
    app.secret_key = secrets.token_bytes()

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('MYSQL_USER', 'default_user')}:{os.getenv('MYSQL_PASSWORD', 'default_password')}"
        f"@{os.getenv('MYSQL_HOSTNAME', 'localhost')}:3306/{os.getenv('MYSQL_DATABASE', 'default_db')}"
    )

    # Templates configuration
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Login configuration
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Initialize SQLAlchemy with the app
    db.init_app(app)

    # Initialize Migrate with the app
    migrate.init_app(app, db)

    # Register routes
    from app.tests.routes import test_routes
    app.register_blueprint(test_routes)

    # Register blueprints
    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    # Register blueprints
    from .dataset import dataset_bp
    app.register_blueprint(dataset_bp)

    from .public import public_bp
    app.register_blueprint(public_bp)

    # Custom error handlers
    register_error_handlers(app)

    # Injecting FLASK_APP_NAME environment variable into jinja context
    @app.context_processor
    def inject_flask_app_name():
        return dict(FLASK_APP_NAME=os.getenv('FLASK_APP_NAME'))

    return app



if __name__ == '__main__':
    app = create_app()
    app.run()


def register_error_handlers(app):

    @app.errorhandler(500)
    def base_error_handler(e):
        return render_template('500.html'), 500

    @app.errorhandler(404)
    def error_404_handler(e):
        return render_template('404.html'), 404

    @app.errorhandler(401)
    def error_404_handler(e):
        return render_template('401.html'), 401

    @app.errorhandler(400)
    def error_400_handler(e):
        return render_template('400.html'), 400

def get_test_client():
    """
    Function to get the test client of the application.
    :return: A Flask application test client.
    """
    return create_app().test_client()
