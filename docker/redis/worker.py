import logging
from rq import Worker, Queue
from dotenv import load_dotenv
from app import create_app

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Create Flask application and load configuration
    app = create_app()

    with app.app_context():
        # Create Flask application and load configuration
        redis_connection = app.config["SESSION_REDIS"]

        # Define the queues to be listened to
        listen = ["default"]

        # Create queue list
        queues = [Queue(name, connection=redis_connection) for name in listen]

        # Initialise the worker
        logger.info(f"Starting worker for queues: {listen}")
        worker = Worker(queues)
        worker.work()
