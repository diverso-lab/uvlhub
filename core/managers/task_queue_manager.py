import logging
from datetime import datetime

import pytz
from flask import current_app
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
        self.queue = Queue(connection=current_app.config["SESSION_REDIS"])
        self.redis_worker_timeout = current_app.config["REDIS_WORKER_TIMEOUT"]
        logger.info("TaskQueueManager initialized with Redis connection.")

    def enqueue_task(self, task_name: str, *args, timeout=None, **kwargs):
        """
        Method to queue a custom task.

        :param task_name: Full name of the method or function to queue (e.g. ‘app.modules.hubfile.process_task_worker’).
        :param args: Positional arguments required by the task.
        :param timeout: Maximum task execution time in seconds (default: 180s).
        :param kwargs: Named arguments required by the task.
        """
        if timeout is None:
            timeout = self.redis_worker_timeout  # Asigna el timeout de la instancia si no se provee uno.

        task_metadata = {
            "task_name": task_name,
            "args": args,
            "kwargs": kwargs,
            "timestamp": datetime.now(pytz.utc).isoformat(),
        }
        logger.info(f"Enqueueing task: {task_metadata}")

        # Bind the custom task to RQ with timeout
        self.queue.enqueue(task_name, *args, **kwargs, job_timeout=timeout)
        logger.info(f"Task '{task_name}' enqueued with arguments: {args}, {kwargs} and timeout: {timeout}")
