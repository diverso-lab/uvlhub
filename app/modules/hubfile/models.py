import os
from datetime import datetime, timezone

from sqlalchemy import event

from app import db
from app import event_service
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet


class Hubfile(db.Model):
    __tablename__ = 'file'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    checksum = db.Column(db.String(120), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    feature_model_id = db.Column(db.Integer, db.ForeignKey('feature_model.id'), nullable=False)

    feature_model = db.relationship('FeatureModel', back_populates='hubfiles')

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

    def to_dict(self):

        # Get the current FLASK_ENV environment and the domain of the DOMAIN environment variable
        flask_env = os.getenv('FLASK_ENV', 'development')
        domain = os.getenv('DOMAIN', 'localhost')

        # If the domain looks like a subdomain (contains more than one dot), do not add ‘www’.
        if domain.count('.') == 1:
            domain = f"www.{domain}"

        # If in production, use https, otherwise use http
        protocol = 'https' if flask_env == 'production' else 'http'

        # Construct the URL using the appropriate protocol and domain.
        url = f"{protocol}://{domain}/hubfile/download/{self.id}"

        return {
            "id": self.id,
            "name": self.name,
            "checksum": self.checksum,
            "size_in_bytes": self.size,
            "size_in_human_format": self.get_formatted_size(),
            "url": url,
        }

    def get_full_path(self) -> str:
        return os.path.join(
            os.getenv("WORKING_DIR"),
            "uploads",
            f"user_{self.feature_model.data_set.user_id}",
            f"dataset_{self.feature_model.data_set_id}",
            self.name,
        )

    def __repr__(self):
        return f'File<{self.id}>'


class HubfileViewRecord(db.Model):
    __tablename__ = 'file_view_record'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    view_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    view_cookie = db.Column(db.String(36))

    def __repr__(self):
        return '<FileViewRecord {}>'.format(self.id)


class HubfileDownloadRecord(db.Model):
    __tablename__ = 'file_download_record'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'))
    download_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    download_cookie = db.Column(db.String(36), nullable=False)

    def __repr__(self):
        return (
            f'<FileDownload id={self.id} '
            f'file_id={self.file_id} '
            f'date={self.download_date} '
            f'cookie={self.download_cookie}>'
        )


@event.listens_for(Hubfile, "after_insert")
def hubfile_aupdated_listener(mapper, connection, target):
    event_service.publish(
        "events",
        "hubfile_created",
        {
            "path": target.get_full_path(),
        },
    )
