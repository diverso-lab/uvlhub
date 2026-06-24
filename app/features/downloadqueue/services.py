import logging
import os
import zipfile
from io import BytesIO

from app.features.hubfile.services import HubfileService

logger = logging.getLogger(__name__)


class DownloadqueueService:
    """Builds on-the-fly ZIP bundles from a set of hubfiles.

    Entity-less by design: it composes the hubfile domain instead of owning a
    repository of its own.
    """

    def __init__(self):
        self.hubfile_service = HubfileService()

    @staticmethod
    def parse_file_ids(raw: str) -> list[int]:
        return [int(token) for token in raw.split(",") if token.strip()]

    def get_hubfiles(self, file_ids: list[int]):
        return self.hubfile_service.get_by_ids(file_ids)

    @staticmethod
    def build_zip(hubfiles) -> BytesIO:
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as archive:
            for hubfile in hubfiles:
                file_path = hubfile.get_full_path()
                if os.path.exists(file_path):
                    archive.write(file_path, os.path.basename(file_path))
                else:
                    logger.warning("Skipping missing file in download bundle: %s", file_path)
        memory_file.seek(0)
        return memory_file

    def build_zip_for_ids(self, file_ids: list[int]) -> BytesIO:
        return self.build_zip(self.get_hubfiles(file_ids))
