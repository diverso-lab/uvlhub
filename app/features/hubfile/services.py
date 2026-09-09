import hashlib
import os
import re
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import List, Tuple

from flask import request
from flask_login import current_user
from splent_framework.services.BaseService import BaseService
from werkzeug.utils import secure_filename

from app.features.auth.models import User
from app.features.dataset.models import DataSet
from app.features.hubfile.models import Hubfile, HubfileViewRecord
from app.features.hubfile.repositories import (
    HubfileDownloadRecordRepository,
    HubfileRepository,
    HubfileViewRecordRepository,
)
from app.features.statistics.services import StatisticsService

UUID_PREFIX_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}_")


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
            *(hubfile.directory_path.split("/") if hubfile.directory_path else ()),
            hubfile.name,
        )

        return path

    def get_by_ids(self, ids: list[int]) -> list[Hubfile]:
        return self.repository.get_by_ids(ids)

    def create_from_file(
        self, feature_model_id: int, dataset_id: int, filepath: str, directory_path: str = ""
    ) -> Hubfile:
        """Create a Hubfile from a .uvl file already placed in the destination directory.

        Args:
            feature_model_id (int): ID of the FeatureModel the file belongs to.
            dataset_id (int): ID of the dataset (container) the file belongs to.
            filepath (str): Full path to the UVL file.
            directory_path (str): POSIX relative folder inside the dataset's uvl
                tree ("" for the root).

        Returns:
            Hubfile: The created instance.
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        return self.repository.create(
            commit=False,
            feature_model_id=feature_model_id,
            dataset_id=dataset_id,
            name=os.path.basename(filepath),
            directory_path=directory_path,
            size=os.path.getsize(filepath),
            checksum=self._calculate_checksum(filepath),
        )

    @staticmethod
    def _calculate_checksum(filepath: str) -> str:
        """Compute the SHA256 hash of the file."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_hubfile_url(self, hubfile: Hubfile) -> str:
        dataset = self.get_dataset_by_hubfile(hubfile)
        ds_meta = dataset.ds_meta_data
        if not ds_meta or not ds_meta.dataset_doi:
            return None

        path = f"/doi/{ds_meta.dataset_doi}/files/{hubfile.name}"

        return path

    def clear_temp(self):
        """Wipe and recreate the current user's temp folder. Raises on I/O error;
        the route maps the outcome to an HTTP response."""
        temp_folder = current_user.temp_folder()
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder, ignore_errors=True)
        os.makedirs(temp_folder, exist_ok=True)


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

        existing_record = self.the_record_exists(hubfile=hubfile, user_cookie=user_cookie)

        if not existing_record:
            self.create_new_record(hubfile=hubfile, user_cookie=user_cookie)
            self.statistics_service.increment_feature_models_downloaded()

        return user_cookie


class HubfileViewRecordService(BaseService):
    def __init__(self):
        super().__init__(HubfileViewRecordRepository())
        self.statistics_service = StatisticsService()

    def the_record_exists(self, hubfile: Hubfile, user_cookie: str):
        return self.repository.the_record_exists(hubfile=hubfile, user_cookie=user_cookie)

    def create_new_record(self, hubfile: Hubfile, user_cookie: str) -> HubfileViewRecord:
        return self.repository.create_new_record(hubfile=hubfile, user_cookie=user_cookie)

    def create_cookie(self, hubfile: Hubfile) -> str:
        user_cookie = request.cookies.get("file_view_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing = self.the_record_exists(hubfile=hubfile, user_cookie=user_cookie)
        if not existing:
            self.create_new_record(hubfile=hubfile, user_cookie=user_cookie)
            self.statistics_service.increment_feature_models_viewed()

        return user_cookie


class UploadIngestService:
    """
    Prepare UVL files for processing:
      - Extract zips safely.
      - Collect every .uvl (from zips and loose).
      - Stage them, keeping the folder structure found inside each zip.
    """

    def __init__(self, logger):
        self.logger = logger

    def _strip_uuid_prefix(self, name: str) -> str:
        """Remove UUID_ prefixes from file names, if present."""
        return UUID_PREFIX_RE.sub("", name)

    # -------- utils -------- #

    def _safe_extract_zip(self, zip_path: str, dest_dir: str) -> None:
        """Extract while preventing path traversal."""
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.infolist():
                # Normalize and reject absolute or .. paths.
                member_path = Path(member.filename)
                if member.is_dir():
                    continue
                target_path = Path(dest_dir) / member_path
                # Containment check.
                target_path_resolved = target_path.resolve()
                if not str(target_path_resolved).startswith(str(Path(dest_dir).resolve())):
                    raise ValueError(f"[INGEST] Zip slip detected in {zip_path}: {member.filename}")
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member, "r") as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

    def _unique_dest(self, dest_dir: str, filename: str) -> str:
        """Produce a unique name if the target already exists."""
        base = Path(filename).stem
        ext = Path(filename).suffix
        candidate = Path(dest_dir) / f"{base}{ext}"
        i = 1
        while candidate.exists():
            candidate = Path(dest_dir) / f"{base} ({i}){ext}"
            i += 1
        return str(candidate)

    @staticmethod
    def _sanitize_rel_dir(rel_dir: str) -> str:
        """Normalize a relative folder to a safe POSIX path with no leading/
        trailing slash and no ``.``/``..`` segments. Returns "" for the root."""
        parts = []
        for segment in Path(rel_dir).as_posix().split("/"):
            segment = segment.strip()
            if not segment or segment in (".", ".."):
                continue
            parts.append(secure_filename(segment) or "folder")
        return "/".join(parts)

    @staticmethod
    def _strip_common_root(rel_dirs: List[str]) -> str | None:
        """If every file in a zip lives under the same single wrapper folder
        (the common "I zipped the folder, not its contents" case), return that
        folder so the caller can drop it. Otherwise return None."""
        firsts = {d.split("/", 1)[0] for d in rel_dirs if d}
        if len(firsts) == 1 and all(d for d in rel_dirs):
            return firsts.pop()
        return None

    # -------- public -------- #

    def prepare_uvls(self, temp_root: str) -> Tuple[str, List[str]]:
        """Stage every uploaded UVL under ``_uvl_stage`` preserving the folder
        structure found inside uploaded ZIPs. Loose (individually attached)
        files land at the stage root."""
        stage_dir = str(Path(temp_root) / "_uvl_stage")
        extract_root = str(Path(temp_root) / "_extracted_zips")

        # Previous cleanup.
        shutil.rmtree(stage_dir, ignore_errors=True)
        shutil.rmtree(extract_root, ignore_errors=True)
        Path(stage_dir).mkdir(parents=True, exist_ok=True)
        Path(extract_root).mkdir(parents=True, exist_ok=True)

        def file_hash(path: Path) -> str:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            return h.hexdigest()

        # (relative_dir, source_path) pairs.
        sources: List[Tuple[str, Path]] = []

        # 1) Loose .uvl files sitting directly in temp_root -> dataset root.
        for p in Path(temp_root).rglob("*.uvl"):
            if not p.is_file():
                continue
            if str(p).startswith(extract_root) or str(p).startswith(stage_dir):
                continue
            sources.append(("", p))

        # 2) Every ZIP, keeping its internal folders.
        zip_paths = [str(p) for p in Path(temp_root).glob("*.zip")]
        self.logger.info(f"[INGEST] Zips detected: {len(zip_paths)}")
        for zp in zip_paths:
            subdir = Path(extract_root) / f"{Path(zp).stem}_{uuid.uuid4().hex[:8]}"
            subdir.mkdir(parents=True, exist_ok=True)
            self._safe_extract_zip(zp, str(subdir))

            zip_uvls = [p for p in subdir.rglob("*.uvl") if p.is_file()]
            rel_dirs = [self._sanitize_rel_dir(str(p.parent.relative_to(subdir))) for p in zip_uvls]
            wrapper = self._strip_common_root(rel_dirs)
            for p, rel_dir in zip(zip_uvls, rel_dirs):
                if wrapper and (rel_dir == wrapper or rel_dir.startswith(wrapper + "/")):
                    rel_dir = rel_dir[len(wrapper) :].lstrip("/")
                sources.append((rel_dir, p))
            self.logger.info(f"[INGEST] Extracted {zp}: {len(zip_uvls)} UVLs (wrapper={wrapper})")

        # 3) Deduplicate by (relative_path, hash) and stage keeping the folders.
        seen = set()
        staged_paths: List[str] = []

        for rel_dir, src in sources:
            h = file_hash(src)
            dest_name = self._strip_uuid_prefix(src.name)
            dedup_key = (rel_dir, dest_name, h)
            if dedup_key in seen:
                self.logger.info(f"[INGEST] Duplicate ignored: {rel_dir}/{src.name}")
                continue
            seen.add(dedup_key)

            dest_folder = Path(stage_dir) / rel_dir if rel_dir else Path(stage_dir)
            dest_folder.mkdir(parents=True, exist_ok=True)

            # Only disambiguate a name clash inside the SAME folder.
            if (dest_folder / dest_name).exists():
                dest_name = f"{Path(dest_name).stem}_{h[:8]}{Path(dest_name).suffix}"

            dest = dest_folder / dest_name
            shutil.copy2(src, dest)
            staged_paths.append(str(dest))

        if not staged_paths:
            raise ValueError("No .uvl files were found after processing the uploaded zips and loose files.")

        self.logger.info(f"[INGEST] UVLs in staging: {len(staged_paths)} (dir: {stage_dir})")
        return stage_dir, sorted(staged_paths)
