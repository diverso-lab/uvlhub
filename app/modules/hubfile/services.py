import os
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet
from app.modules.hubfile.models import Hubfile
from app.modules.hubfile.repositories import HubfileDownloadRecordRepository, HubfileRepository
from core.services.BaseService import BaseService


class HubfileService(BaseService):
    def __init__(self):
        super().__init__(HubfileRepository())

    def get_owner_user_by_hubfile(self, hubfile: Hubfile) -> User:
        return self.repository.get_owner_user_by_hubfile(hubfile)

    def get_dataset_by_hubfile(self, hubfile: Hubfile) -> DataSet:
        return self.repository.get_dataset_by_hubfile(hubfile)

    def get_path_by_hubfile(self, hubfile: Hubfile) -> str:

        hubfile_user = self.get_owner_user_by_hubfile(hubfile)
        hubfile_dataset = self.get_dataset_by_hubfile(hubfile)
        working_dir = os.getenv('WORKING_DIR')

        path = os.path.join(working_dir,
                            'uploads',
                            f'user_{hubfile_user.id}',
                            f'dataset_{hubfile_dataset.id}',
                            hubfile.name)

        return path


class HubfileDownloadRecordService(BaseService):
    def __init__(self):
        super().__init__(HubfileDownloadRecordRepository())
