import os
import logging
from dotenv import load_dotenv
from rq import Worker, Queue
from splent_framework.managers.config_manager import ConfigManager
from app import create_app, mail_service

# Load environment variables from .env
load_dotenv()

# Set up the base logger
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Build the Flask app with the base configuration
    config_name = os.getenv("FLASK_ENV", "development")
    app = create_app(config_name=config_name)

    # Load the full configuration via ConfigManager (same path as create_app)
    config_manager = ConfigManager(app)
    config_manager.load_config(config_name=config_name)

    # Run the worker inside the app context
    with app.app_context():
        # Initialize the mail service (needed for external URLs, templates, etc.)
        mail_service.init_app(app)

        # Get the Redis connection from the Flask config
        redis_connection = app.config.get("SESSION_REDIS")

        if not redis_connection:
            raise RuntimeError("Redis connection not found in configuration (SESSION_REDIS).")

        # Queues to listen on
        listen = os.getenv("RQ_QUEUES", "default").split(",")

        # Build the RQ queues
        queues = [Queue(name.strip(), connection=redis_connection) for name in listen]

        # Start the worker
        logger.info(f"Starting RQ worker for queues: {listen}")
        worker = Worker(queues, connection=redis_connection)
        worker.work()
