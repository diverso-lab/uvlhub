import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_migrate import Migrate

# Load environment variables
load_dotenv()

# Instance of SQLAlchemy
db = SQLAlchemy()


def create_app(config_name=None):
    """
    Factory function to create the Flask application.
    :param config_name: The name of the configuration to use.
    :return: A Flask application object.
    """
    app = Flask(__name__)
    app.secret_key = {os.getenv('SECRET_KEY', '')}

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('MYSQL_USER', 'default_user')}:{os.getenv('MYSQL_PASSWORD', 'default_password')}"
        f"@{os.getenv('MYSQL_HOSTNAME', 'localhost')}:3306/{os.getenv('MYSQL_DATABASE', 'default_db')}"
    )

    # Initialize SQLAlchemy with the app
    db.init_app(app)

    # Register routes
    from app.tests.routes import test_routes
    app.register_blueprint(test_routes)

    @app.route('/')
    def hello_world():
        return 'Hello, World!'

    # Register models and migration
    from app.models import User, DataSet, File, MetaData, DSMetrics, FeatureModel, FMMetaData, FMMetrics
    Migrate(app, db)

    return app


def get_test_client():
    """
    Function to get the test client of the application.
    :return: A Flask application test client.
    """
    return create_app().test_client()
