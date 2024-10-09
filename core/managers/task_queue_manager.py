from datetime import datetime
import logging
import pytz
import redis
from rq import Queue

logger = logging.getLogger(__name__)


class TaskQueueManager:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TaskQueueManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.redis = redis.from_url('redis://redis:6379')
        self.queue = Queue(connection=self.redis)
        logger.info("TaskQueueManager initialized with Redis connection.")

    def enqueue_task(self, task_name: str, *args, **kwargs):
        """
        Método para encolar una tarea personalizada.

        :param task_name: Nombre completo del método o función a encolar (ej. "app.modules.hubfile.process_task_worker")
        :param args: Argumentos posicionales que requiere la tarea.
        :param kwargs: Argumentos nombrados que requiere la tarea.
        """
        task_metadata = {
            "task_name": task_name,
            "args": args,
            "kwargs": kwargs,
            "timestamp": datetime.now(pytz.utc).isoformat(),
        }
        logger.info(f"Enqueueing task: {task_metadata}")

        # Encolar la tarea personalizada en RQ
        self.queue.enqueue(task_name, *args, **kwargs)
        logger.info(f"Task '{task_name}' enqueued with arguments: {args}, {kwargs}")
