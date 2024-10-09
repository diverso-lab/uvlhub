from datetime import datetime
import logging
import pytz
import redis
from rq import Queue

logger = logging.getLogger(__name__)


class EventService:

    def __init__(self):
        self.redis = redis.from_url('redis://redis:6379')
        self.queue = Queue(connection=self.redis)

    def publish(self, event_type: str, event_data: dict[str, str]):
        event = {
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.now(pytz.utc).isoformat(),
        }
        logger.info(f"Publishing event: {event}")
        path = event_data.get("path")
        self.queue.enqueue("app.modules.event.process.process_event_worker", path)
