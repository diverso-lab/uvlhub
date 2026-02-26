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

        # 🔹 Si estamos en modo testing o no hay conexión real, usar fakeredis
        if current_app.config.get("TESTING") or redis_conn is None:
            try:
                import fakeredis

                redis_conn = fakeredis.FakeStrictRedis()
                logger.info("Using FakeRedis for TaskQueueManager (testing mode).")
            except ImportError:
                logger.warning("fakeredis not installed, tests may fail without Redis.")
        else:
            # Si es un string, convierte a conexión redis real
            import redis

            if isinstance(redis_conn, str):
                redis_conn = redis.from_url(redis_conn)

        # ✅ Crear la cola RQ con la conexión apropiada
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
