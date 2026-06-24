from datetime import datetime

import pytz
from flask_login import current_user
from splent_framework.repositories.BaseRepository import BaseRepository

from app import db
from app.features.auth.models import User
from app.features.dataset.models import DataSet
from app.features.hubfile.models import Hubfile, HubfileDownloadRecord, HubfileViewRecord


class HubfileRepository(BaseRepository):
    def __init__(self):
        super().__init__(Hubfile)

    def get_owner_user_by_hubfile(self, hubfile: Hubfile) -> User:
        return (
            db.session.query(User)
            .join(DataSet, DataSet.user_id == User.id)
            .join(Hubfile, Hubfile.dataset_id == DataSet.id)
            .filter(Hubfile.id == hubfile.id)
            .first()
        )

    def get_dataset_by_hubfile(self, hubfile: Hubfile) -> DataSet:
        return db.session.get(DataSet, hubfile.dataset_id)

    def get_by_ids(self, ids: list[int]) -> list[Hubfile]:
        return self.model.query.filter(self.model.id.in_(ids)).all()


class HubfileViewRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(HubfileViewRecord)

    def the_record_exists(self, hubfile: Hubfile, user_cookie: str):
        return self.model.query.filter_by(
            user_id=current_user.id if current_user.is_authenticated else None,
            file_id=hubfile.id,
            view_cookie=user_cookie,
        ).first()

    def create_new_record(self, hubfile: Hubfile, user_cookie: str) -> HubfileViewRecord:
        return self.create(
            user_id=current_user.id if current_user.is_authenticated else None,
            file_id=hubfile.id,
            view_date=datetime.now(pytz.utc),
            view_cookie=user_cookie,
        )


class HubfileDownloadRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(HubfileDownloadRecord)

    def the_record_exists(self, hubfile: Hubfile, user_cookie: str):
        return self.model.query.filter_by(
            user_id=current_user.id if current_user.is_authenticated else None,
            file_id=hubfile.id,
            download_cookie=user_cookie,
        ).first()

    def create_new_record(self, hubfile: Hubfile, user_cookie: str) -> HubfileViewRecord:
        return self.create(
            user_id=current_user.id if current_user.is_authenticated else None,
            file_id=hubfile.id,
            download_date=datetime.now(pytz.utc),
            download_cookie=user_cookie,
        )
