import logging
import os
from datetime import datetime

import pytz
from dotenv import load_dotenv
from flask import url_for
from sqlalchemy import event
from sqlalchemy.orm import joinedload, object_session

from app import db
from app.features.auth.models import User
from app.features.dataset.models import DataSet
from app.features.hubfile.signals import hubfile_created

logger = logging.getLogger(__name__)
load_dotenv()


class Hubfile(db.Model):
    __tablename__ = "hubfiles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    checksum = db.Column(db.String(120), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    feature_model_id = db.Column(db.Integer, db.ForeignKey("feature_model.id"), nullable=False)
    # Generic anchor: a hubfile belongs to its dataset (the container) directly.
    # feature_model_id is kept as the UVL-domain grouping link.
    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id"), nullable=False, index=True)

    feature_model = db.relationship("FeatureModel", back_populates="hubfiles")
    dataset = db.relationship("DataSet")

    def get_formatted_size(self):
        from app.features.dataset.services import SizeService

        return SizeService().get_human_readable_size(self.size)

    def get_owner_user(self) -> User:
        from app.features.hubfile.services import HubfileService

        return HubfileService().get_owner_user_by_hubfile(self)

    def get_dataset(self) -> DataSet:
        from app.features.hubfile.services import HubfileService

        return HubfileService().get_dataset_by_hubfile(self)

    def get_path(self) -> str:
        from app.features.hubfile.services import HubfileService

        return HubfileService().get_path_by_hubfile(self)

    def get_url(self) -> str:
        from app.features.hubfile.services import HubfileService

        return HubfileService().get_hubfile_url(self)

    def get_full_path(self) -> str:
        return os.path.join(
            os.getenv("WORKING_DIR", ""),
            "uploads",
            f"user_{self.dataset.user_id}",
            f"dataset_{self.dataset_id}",
            "uvl",
            self.name,
        )

    def _public_raw_url(self) -> str:
        """Build the public raw-UVL URL for this hubfile (https outside local).

        Shared between the Flamapy IDE and FactLabel helpers so a future
        tweak (e.g. hostname rewrite) only needs to happen in one place.
        """
        from urllib.parse import quote

        raw_url = url_for("hubfile.raw_uvl", file_id=self.id, filename=self.name, _external=True)
        if "localhost" not in raw_url and "127.0.0.1" not in raw_url:
            raw_url = raw_url.replace("http://", "https://", 1)
        # Percent-encode before injecting into another URL's query string,
        # otherwise a filename containing "&", "#" or "?" would corrupt the
        # outer URL. `safe=""` means even "/" and ":" get encoded — the
        # consumer (FactLabel / IDE) URL-decodes the value before fetching.
        return quote(raw_url, safe="")

    def get_ide_url(self) -> str:
        """Return the URL that opens this hubfile in Flamapy IDE."""
        return f"https://ide.flamapy.org/?import={self._public_raw_url()}"

    def get_factlabel_url(self) -> str:
        """Return the URL that opens this hubfile in FactLabel.

        Note: we deliberately don't pass `?v=<version>`. FactLabel's JS
        compares the URL's `v` against its own version.json and redirects
        to /error_version.html (which is a 404 on GitHub Pages) when they
        don't match. Hardcoding `v=1.8.0` here broke as soon as FactLabel
        bumped to 1.8.1. Omitting the param skips the check entirely and
        lets FactLabel pick up whatever version it's currently serving.
        """
        return f"https://fmfactlabel.github.io/app/?file={self._public_raw_url()}"

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

    hubfile_with_dataset = (
        session.query(Hubfile).options(joinedload(Hubfile.dataset)).filter(Hubfile.id == target.id).first()
    )
    path = hubfile_with_dataset.get_full_path()

    # Announce the creation; domain features (flamapy, factlabel) subscribe and
    # enqueue their own processing. The hub stays unaware of the UVL domain.
    hubfile_created.send(target, hubfile_id=target.id, path=path)
