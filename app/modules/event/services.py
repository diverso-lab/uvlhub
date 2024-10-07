import json
from datetime import datetime

import redis

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, GlencoeWriter, SPLOTWriter
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat, DimacsWriter


class EventService:
    def __init__(self):
        self.redis = None

    def init_app(self, app):
        self.redis = app.config.get("SESSION_REDIS")

    def publish(self, channel: str, event_type: str, event_data: dict[str, str]):
        event = {
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.now(datetime.timezone.utc).isoformat(),
        }
        self.redis.publish(channel, json.dumps(event))

    def _new_hubfile(self, event):
        path = event.get("event_data").get("path")

        fm = UVLReader(path).transform()
        json_path = path.replace(".uvl", ".json")
        GlencoeWriter(json_path, fm).transform()

        cnf_path = path.replace(".uvl", ".cnf")
        sat = FmToPysat(fm).transform()
        DimacsWriter(cnf_path, sat).transform()

        splx_path = path.replace(".uvl", ".splx")
        SPLOTWriter(splx_path, fm).transform()

    def consume(self, channel: str):
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(channel)
        for message in self.pubsub.listen():
            try:
                event = json.loads(message["data"])

                if event["event_type"] == "hubfile_created":
                    self._new_hubfile(event)
            except json.JSONDecodeError:
                print(f"Error decoding JSON: {message['data']}")
