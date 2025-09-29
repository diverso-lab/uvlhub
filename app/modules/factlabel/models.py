from typing import Any, Optional

from flamapy.core.operations import Metrics

from app import db


class Factlabel(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return f"Factlabel<{self.id}>"
