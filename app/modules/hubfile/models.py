import logging
import os
from datetime import datetime

import pytz
from dotenv import load_dotenv
from flask import url_for
from sqlalchemy import Text, event
from sqlalchemy.orm import joinedload, object_session

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet
from core.managers.task_queue_manager import TaskQueueManager

logger = logging.getLogger(__name__)
load_dotenv()


class Hubfile(db.Model):
    __tablename__ = "hubfiles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    checksum = db.Column(db.String(120), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    feature_model_id = db.Column(db.Integer, db.ForeignKey("feature_model.id"), nullable=False)

    feature_model = db.relationship("FeatureModel", back_populates="hubfiles")
    factlabel_json = db.Column(Text, nullable=True)

    def get_formatted_size(self):
        from app.modules.dataset.services import SizeService

        return SizeService().get_human_readable_size(self.size)

    def get_owner_user(self) -> User:
        from app.modules.hubfile.services import HubfileService

        return HubfileService().get_owner_user_by_hubfile(self)

    def get_dataset(self) -> DataSet:
        from app.modules.hubfile.services import HubfileService

        return HubfileService().get_dataset_by_hubfile(self)

    def get_path(self) -> str:
        from app.modules.hubfile.services import HubfileService

        return HubfileService().get_path_by_hubfile(self)

    def get_url(self) -> str:
        from app.modules.hubfile.services import HubfileService

        return HubfileService().get_hubfile_url(self)

    def get_full_path(self) -> str:
        return os.path.join(
            os.getenv("WORKING_DIR", ""),
            "uploads",
            f"user_{self.feature_model.dataset.user_id}",
            f"dataset_{self.feature_model.dataset_id}",
            "uvl",
            self.name,
        )

    def get_ide_url(self) -> str:
        """
        Returns the URL ready to open this hubfile in Flamapy IDE,
        with the import correctly encoded.
        On localhost, leave http; on any other host, force https.
        """
        raw_url = url_for("hubfile.raw_uvl", file_id=self.id, _external=True)
        if "localhost" not in raw_url and "127.0.0.1" not in raw_url:
            raw_url = raw_url.replace("http://", "https://", 1)
        return f"https://ide.flamapy.org/?import={raw_url}"

    def to_dict(self):
        from flask import url_for

        return {
            "id": self.id,
            "name": self.name,
            "checksum": self.checksum,
            "size_in_bytes": self.size,
            "size_in_human_format": self.get_formatted_size(),
            "url": url_for("hubfile.download_file", file_id=self.id, _external=True),
        }

    def __repr__(self):
        return f"<Hubfile id={self.id}, name={self.name}>"


class HubfileViewRecord(db.Model):
    __tablename__ = "hubfile_view_record"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey("hubfiles.id"), nullable=False)
    view_date = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    view_cookie = db.Column(db.String(36))

    def __repr__(self):
        return f"<HubfileViewRecord id={self.id} file_id={self.file_id}>"


class HubfileDownloadRecord(db.Model):
    __tablename__ = "hubfile_download_record"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey("hubfiles.id"), nullable=False)
    download_date = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc), nullable=False)
    download_cookie = db.Column(db.String(36), nullable=False)

    def __repr__(self):
        return f"<HubfileDownloadRecord id={self.id} file_id={self.file_id} date={self.download_date}>"


@event.listens_for(Hubfile, "after_insert")
def hubfile_after_insert_listener(mapper, connection, target):
    session = object_session(target)

    hubfile_with_fm = (
        session.query(Hubfile).options(joinedload(Hubfile.feature_model)).filter(Hubfile.id == target.id).first()
    )
    path = hubfile_with_fm.get_full_path()

    task_manager = TaskQueueManager()

    # Transformación UVL
    task_manager.enqueue_task("app.modules.hubfile.tasks.transform_uvl", path=path, timeout=5)

    # Fact Label
    task_manager.enqueue_task("app.modules.hubfile.tasks.compute_factlabel", hubfile_id=target.id, timeout=5)
