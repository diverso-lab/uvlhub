import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_session import Session

from app.modules.mail.services import MailService
from core.configuration.configuration import get_app_version
from core.managers.module_manager import ModuleManager
from core.managers.config_manager import ConfigManager
from core.managers.error_handler_manager import ErrorHandlerManager
from core.managers.logging_manager import LoggingManager

# Load environment variables
load_dotenv()

# Create the instances
db = SQLAlchemy()
migrate = Migrate()
mail_service = MailService()
sess = Session()

def create_app(config_name="development"):
    app = Flask(__name__, static_folder='static')

    # Load configuration according to environment
    config_manager = ConfigManager(app)
    config_manager.load_config(config_name=config_name)

    # --- MODIFICACIÓN CLAVE: Configura sesiones usando Redis si REDIS_URL está presente ---
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        app.config["SESSION_TYPE"] = "redis"
        import redis
        app.config["SESSION_REDIS"] = redis.from_url(redis_url)
    else:
        # Fallback: usa sesiones en el sistema de archivos
        app.config["SESSION_TYPE"] = "filesystem"

    # Initialize SQLAlchemy and Migrate with the app
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize session with the app
    sess.init_app(app)

    # ... (el resto igual)
    # Register modules
    module_manager = ModuleManager(app)
    module_manager.register_modules()

    from flask_login import LoginManager

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        from app.modules.auth.models import User
        return User.query.get(int(user_id))

    logging_manager = LoggingManager(app)
    logging_manager.setup_logging()

    error_handler_manager = ErrorHandlerManager(app)
    error_handler_manager.register_error_handlers()

    mail_service.init_app(app)

    @app.context_processor
    def inject_vars_into_jinja():
        env_vars = {key: os.getenv(key) for key in os.environ}
        env_vars["APP_VERSION"] = get_app_version()
        env_vars["DOMAIN"] = os.getenv("DOMAIN", "localhost")
        flask_env = os.getenv("FLASK_ENV")
        env_vars["DEVELOPMENT"] = flask_env == "development"
        env_vars["PRODUCTION"] = flask_env == "production"
        return env_vars

    return app

app = create_app()
