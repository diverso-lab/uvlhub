from datetime import datetime, timezone
from flask import request
from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet


class Hubfile(db.Model):
    __tablename__ = 'file'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    checksum = db.Column(db.String(120), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    feature_model_id = db.Column(db.Integer, db.ForeignKey('feature_model.id'), nullable=False)

    def get_formatted_size(self):
        from app.modules.dataset.services import SizeService
        return SizeService().get_human_readable_size(self.size)

    def get_owner_user(self) -> User:
        from app.modules.hubfile.services import HubfileService
        return HubfileService().get_owner_user_by_hubfile(self)

    def get_dataset(self) -> DataSet:
        from app.modules.hubfile.services import HubfileService
        return HubfileService().get_dataset_by_hubfile(self)

    def get_path(self) -> DataSet:
        from app.modules.hubfile.services import HubfileService
        return HubfileService().get_path_by_hubfile(self)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'checksum': self.checksum,
            'size_in_bytes': self.size,
            'size_in_human_format': self.get_formatted_size(),
            'url': f'{request.host_url.rstrip("/")}/file/download/{self.id}',
        }

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
