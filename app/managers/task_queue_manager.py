"""Product-local task queue manager.

Kept in the product (not from splent_framework) because diverso needs two
behaviours the framework's TaskQueueManager does not yet provide:
  * it returns the RQ ``job`` (flamapy reads ``job.id`` for ``check_uvl_async``);
  * it falls back to fakeredis under TESTING so the suite runs without Redis.
"""

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
        redis_conn = current_app.config.get("SESSION_REDIS")

        # If we're in testing mode or there's no real connection, fall back to fakeredis.
        if current_app.config.get("TESTING") or redis_conn is None:
            try:
                import fakeredis

                redis_conn = fakeredis.FakeStrictRedis()
                logger.info("Using FakeRedis for TaskQueueManager (testing mode).")
            except ImportError:
                logger.warning("fakeredis not installed, tests may fail without Redis.")
        else:
            # If the config value is a string, turn it into a real Redis connection.
            import redis

            if isinstance(redis_conn, str):
                redis_conn = redis.from_url(redis_conn)

        # Create the RQ queue with the appropriate connection.
        self.queue = Queue(connection=redis_conn)
        self.redis_worker_timeout = current_app.config.get("REDIS_WORKER_TIMEOUT", 180)
        logger.info("TaskQueueManager initialized with Redis connection.")

    def enqueue_task(self, task_name: str, *args, timeout=None, **kwargs):
        if timeout is None:
            timeout = self.redis_worker_timeout

        task_metadata = {
            "task_name": task_name,
            "args": args,
            "kwargs": kwargs,
            "timestamp": datetime.now(pytz.utc).isoformat(),
        }
        logger.info(f"Enqueueing task: {task_metadata}")

        job = self.queue.enqueue(task_name, *args, **kwargs, job_timeout=timeout)
        logger.info(f"Task '{task_name}' enqueued with id={job.id}, args={args}, kwargs={kwargs}, timeout={timeout}")

        return job
