import os
import uuid

from flask import request
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet
from app.modules.hubfile.models import Hubfile
from app.modules.hubfile.repositories import (
    HubfileDownloadRecordRepository,
    HubfileRepository,
    HubfileViewRecordRepository,
)
from app.modules.statistics.services import StatisticsService
from core.services.BaseService import BaseService


class HubfileService(BaseService):
    def __init__(self):
        super().__init__(HubfileRepository())
        self.hubfile_view_record_repository = HubfileViewRecordRepository()
        self.hubfile_download_record_repository = HubfileDownloadRecordRepository()

    def get_owner_user_by_hubfile(self, hubfile: Hubfile) -> User:
        return self.repository.get_owner_user_by_hubfile(hubfile)

    def get_dataset_by_hubfile(self, hubfile: Hubfile) -> DataSet:
        return self.repository.get_dataset_by_hubfile(hubfile)

    def get_path_by_hubfile(self, hubfile: Hubfile) -> str:

        hubfile_user = self.get_owner_user_by_hubfile(hubfile)
        hubfile_dataset = self.get_dataset_by_hubfile(hubfile)
        working_dir = os.getenv("WORKING_DIR")

        path = os.path.join(
            working_dir,
            "uploads",
            f"user_{hubfile_user.id}",
            f"dataset_{hubfile_dataset.id}",
            "uvl",
            hubfile.name,
        )

        return path

    def get_by_ids(self, ids: list[int]) -> list[Hubfile]:
        return self.repository.get_by_ids(ids)


class HubfileDownloadRecordService(BaseService):
    def __init__(self):
        super().__init__(HubfileDownloadRecordRepository())
        self.statistics_service = StatisticsService()

    def the_record_exists(self, hubfile: Hubfile, user_cookie: str):
        return self.repository.the_record_exists(hubfile, user_cookie)

    def create_new_record(self, hubfile: Hubfile, user_cookie: str) -> Hubfile:
        return self.repository.create_new_record(hubfile, user_cookie)

    def create_cookie(self, hubfile: Hubfile):

        user_cookie = request.cookies.get("file_download_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing_record = self.the_record_exists(
            hubfile=hubfile, user_cookie=user_cookie
        )

        if not existing_record:
            self.create_new_record(hubfile=hubfile, user_cookie=user_cookie)
            self.statistics_service.increment_feature_models_downloaded()

        return user_cookie
