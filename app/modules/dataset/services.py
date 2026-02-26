import hashlib
import logging
import os
import re
import shutil
import tempfile
import uuid
import zipfile
from typing import List, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request
from zipfile import ZipFile

import bleach
from flask import current_app, request

from app import db
from app.modules.auth.models import User
from app.modules.dataset.forms import AuthorForm, DataSetForm, FeatureModelForm
from app.modules.dataset.models import DataSet, DSDownloadRecord, DSMetaData, DSViewRecord, PublicationType
from app.modules.dataset.repositories import (
    AuthorRepository,
    DataSetRepository,
    DOIMappingRepository,
    DSDownloadRecordRepository,
    DSMetaDataRepository,
    DSViewRecordRepository,
)
from app.modules.featuremodel.repositories import FeatureModelRepository
from app.modules.hubfile.repositories import (
    HubfileDownloadRecordRepository,
    HubfileRepository,
    HubfileViewRecordRepository,
)
from app.modules.hubfile.services import UploadIngestService
from app.modules.statistics.services import StatisticsService
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)
ORCID_REGEX = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$")


class DatasetMetadataValidationError(Exception):
    pass


class DatasetMetadataUpdateError(Exception):
    pass


def calculate_checksum_and_size(file_path):
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as file:
        content = file.read()
        hash_md5 = hashlib.md5(content).hexdigest()
        return hash_md5, file_size


class DataSetService(BaseService):
    def __init__(self):
        super().__init__(DataSetRepository())
        self.feature_model_repository = FeatureModelRepository()
        self.author_repository = AuthorRepository()
        self.dsmetadata_repository = DSMetaDataRepository()
        self.dsdownloadrecord_repository = DSDownloadRecordRepository()
        self.hubfiledownloadrecord_repository = HubfileDownloadRecordRepository()
        self.hubfilerepository = HubfileRepository()
        self.dsviewrecord_repostory = DSViewRecordRepository()
        self.hubfileviewrecord_repository = HubfileViewRecordRepository()

    def create_basic_dataset(self, user: User) -> DataSet:
        dataset = self.create(commit=False, user_id=user.id, ds_meta_data_id=None)
        return dataset

    def is_synchronized(self, dataset_id: int) -> bool:
        return self.repository.is_synchronized(dataset_id)

    """
        Synchronised dataset
    """

    def get_synchronized_datasets(self) -> List[DataSet]:
        return self.repository.get_synchronized_datasets()

    def get_synchronized_datasets_by_user(self, current_user_id: int) -> List[DataSet]:
        return self.repository.get_synchronized_datasets_by_user(current_user_id)

    def get_synchronized_dataset_by_user(self, current_user_id: int, dataset_id: int) -> DataSet:
        return self.repository.get_synchronized_dataset_by_user(current_user_id, dataset_id)

    def count_synchronized_datasets(self) -> int:
        return self.repository.count_synchronized_datasets()

    """
        Unsynchronised dataset
    """

    def get_unsynchronized_datasets(self) -> List[DataSet]:
        return self.repository.get_unsynchronized_datasets()

    def get_unsynchronized_datasets_by_user(self, current_user_id: int) -> List[DataSet]:
        return self.repository.get_unsynchronized_datasets_by_user(current_user_id)

    def get_unsynchronized_dataset_by_user(self, current_user_id: int, dataset_id: int) -> DataSet:
        return self.repository.get_unsynchronized_dataset_by_user(current_user_id, dataset_id)

    def count_unsynchronized_datasets(self) -> int:
        return self.repository.count_unsynchronized_datasets()

    """
        Top X datasets...
    """

    def latest_synchronized(self) -> List[DataSet]:
        return self.repository.latest_synchronized()

    def get_top_5_datasets_by_feature_model_count(self) -> List[DataSet]:
        return self.repository.get_top_5_datasets_by_feature_model_count()

    def count_feature_models(self, dataset_id: int) -> int:
        dataset = self.repository.get_by_id(dataset_id)
        return dataset.feature_model_count

    def count_authors(self) -> int:
        return self.author_repository.count()

    def count_dsmetadata(self) -> int:
        return self.dsmetadata_repository.count()

    def _normalize_text(self, value: str) -> str:
        return " ".join((value or "").strip().lower().split())

    def _normalize_orcid(self, value: str) -> str:
        raw = (value or "").strip()
        if not raw:
            return ""
        raw = re.sub(r"^https?://orcid\.org/", "", raw, flags=re.IGNORECASE)
        return raw.upper()

    def _is_valid_orcid_checksum(self, orcid: str) -> bool:
        digits = orcid.replace("-", "")
        if not re.match(r"^\d{15}[\dX]$", digits):
            return False
        total = 0
        for idx in range(15):
            total = (total + int(digits[idx])) * 2
        remainder = total % 11
        result = (12 - remainder) % 11
        check_digit = "X" if result == 10 else str(result)
        return digits[15] == check_digit

    def _validate_orcid(self, orcid: str) -> str:
        normalized = self._normalize_orcid(orcid)
        if not normalized:
            return ""

        if not ORCID_REGEX.match(normalized):
            raise DatasetMetadataValidationError("Invalid ORCID format. Expected: 0000-0000-0000-0000.")

        if not self._is_valid_orcid_checksum(normalized):
            raise DatasetMetadataValidationError("Invalid ORCID checksum.")

        try:
            req = urllib_request.Request(
                f"https://pub.orcid.org/v3.0/{normalized}",
                headers={"Accept": "application/json"},
                method="GET",
            )
            with urllib_request.urlopen(req, timeout=5) as response:
                if response.status != 200:
                    raise DatasetMetadataValidationError(f"Could not validate ORCID (status {response.status}).")
        except urllib_error.HTTPError as exc:
            if exc.code == 404:
                raise DatasetMetadataValidationError("ORCID not found.")
            raise DatasetMetadataValidationError(f"Could not validate ORCID (status {exc.code}).")
        except DatasetMetadataValidationError:
            raise
        except Exception:
            raise DatasetMetadataValidationError("Could not validate ORCID due to network error.")

        return normalized

    def _parse_tags_from_form(self, form_data) -> str:
        tags = form_data.getlist("tags[]")
        if not tags:
            raw_tags = form_data.get("tags", "")
            tags = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
        return ",".join(tags)

    def _parse_authors_from_form(self, form_data) -> list[dict]:
        authors = []
        idx = 0
        while True:
            name = form_data.get(f"authors[{idx}][name]")
            if name is None:
                break
            authors.append(
                {
                    "name": name,
                    "affiliation": form_data.get(f"authors[{idx}][affiliation]", ""),
                    "orcid": form_data.get(f"authors[{idx}][orcid]", ""),
                }
            )
            idx += 1

        if authors:
            return authors

        author_names = form_data.getlist("author_names[]")
        author_affiliations = form_data.getlist("author_affiliations[]")
        author_orcids = form_data.getlist("author_orcids[]")
        return [
            {
                "name": name,
                "affiliation": aff,
                "orcid": orcid,
            }
            for name, aff, orcid in zip(author_names, author_affiliations, author_orcids)
        ]

    def _apply_metadata_from_form(self, dataset: DataSet, form_data) -> None:
        dataset.ds_meta_data.title = form_data.get("title", "").strip()
        dataset.ds_meta_data.description = form_data.get("description", "")
        dataset.ds_meta_data.publication_doi = (form_data.get("publication_doi", "") or "").strip()
        dataset.ds_meta_data.tags = self._parse_tags_from_form(form_data)
        dataset.ds_meta_data.dataset_anonymous = form_data.get("dataset_type", "draft") == "zenodo_anonymous"

        pub_type = form_data.get("publication_type")
        if not pub_type:
            dataset.ds_meta_data.publication_type = None
            return

        try:
            dataset.ds_meta_data.publication_type = PublicationType(pub_type)
        except ValueError:
            dataset.ds_meta_data.publication_type = PublicationType.OTHER

    def _get_requested_dataset_type(self, form_data) -> str:
        dataset_type = (form_data.get("dataset_type") or "draft").strip()
        allowed_types = {"draft", "zenodo", "zenodo_anonymous"}
        if dataset_type not in allowed_types:
            raise DatasetMetadataValidationError(
                f"Invalid dataset type '{dataset_type}'. Allowed values: draft, zenodo, zenodo_anonymous."
            )
        return dataset_type

    def _replace_authors_from_form(self, dataset: DataSet, form_data) -> None:
        authors = self._parse_authors_from_form(form_data)
        seen_author_keys = set()
        seen_orcids = set()

        dataset.ds_meta_data.authors.clear()

        for author in authors:
            name = (author.get("name") or "").strip()
            if not name:
                continue

            affiliation = (author.get("affiliation") or "").strip()
            normalized_name = self._normalize_text(name)
            normalized_affiliation = self._normalize_text(affiliation)
            normalized_orcid = self._normalize_orcid(author.get("orcid"))

            if normalized_orcid:
                if normalized_orcid in seen_orcids:
                    raise DatasetMetadataValidationError(
                        f"Duplicate author detected: ORCID {normalized_orcid} is already in the list."
                    )
                seen_orcids.add(normalized_orcid)
            else:
                author_key = (normalized_name, normalized_affiliation)
                if author_key in seen_author_keys:
                    raise DatasetMetadataValidationError("Duplicate author detected: same name and affiliation.")
                seen_author_keys.add(author_key)

            try:
                sanitized_orcid = self._validate_orcid(author.get("orcid"))
            except DatasetMetadataValidationError as exc:
                raise DatasetMetadataValidationError(f"Invalid ORCID for author '{name}': {exc}")

            new_author = self.author_repository.create(
                commit=False,
                name=name,
                affiliation=affiliation,
                orcid=sanitized_orcid,
                ds_meta_data_id=dataset.ds_meta_data.id,
            )
            dataset.ds_meta_data.authors.append(new_author)

    def _sync_metadata_in_zenodo_if_needed(self, dataset: DataSet, zenodo_service) -> None:
        if not dataset.ds_meta_data.dataset_doi:
            return

        deposition_id = dataset.ds_meta_data.deposition_id
        if not deposition_id:
            raise DatasetMetadataUpdateError("Dataset is synchronized but missing Zenodo deposition_id.")

        metadata = zenodo_service.build_metadata(dataset, anonymous=dataset.ds_meta_data.dataset_anonymous)
        zenodo_service.update_deposition(deposition_id, metadata)

    def _publish_dataset_to_zenodo(self, dataset: DataSet, zenodo_service) -> None:
        anonymous = bool(dataset.ds_meta_data.dataset_anonymous)
        deposition = zenodo_service.create_new_deposition(dataset, anonymous=anonymous)
        deposition_id = deposition.get("id")
        if not deposition_id:
            raise DatasetMetadataUpdateError("Zenodo did not return a deposition id.")

        zip_path = self.zip_dataset(dataset)
        try:
            zenodo_service.upload_zip(dataset, deposition_id, zip_path)
        finally:
            if zip_path and os.path.exists(zip_path):
                temp_dir = os.path.dirname(zip_path)
                shutil.rmtree(temp_dir, ignore_errors=True)

        zenodo_service.publish_deposition(deposition_id)
        doi = zenodo_service.get_doi(deposition_id)
        if not doi:
            raise DatasetMetadataUpdateError("Zenodo did not return a DOI after publishing.")

        dataset.ds_meta_data.deposition_id = deposition_id
        dataset.ds_meta_data.dataset_doi = doi

    def _transition_dataset_state_if_needed(self, dataset: DataSet, dataset_type: str, zenodo_service) -> None:
        wants_sync = dataset_type in {"zenodo", "zenodo_anonymous"}
        is_synced = bool(dataset.ds_meta_data.dataset_doi)

        if not wants_sync:
            dataset.ds_meta_data.dataset_doi = None
            dataset.ds_meta_data.deposition_id = None
            return

        if zenodo_service is None:
            raise DatasetMetadataUpdateError("Zenodo service is required to synchronize the dataset.")

        if is_synced:
            self._sync_metadata_in_zenodo_if_needed(dataset, zenodo_service)
            return

        self._publish_dataset_to_zenodo(dataset, zenodo_service)

    def update_metadata_from_request(self, dataset: DataSet, form_data, zenodo_service=None) -> None:
        try:
            dataset_type = self._get_requested_dataset_type(form_data)
            self._apply_metadata_from_form(dataset, form_data)
            self._replace_authors_from_form(dataset, form_data)
            self._transition_dataset_state_if_needed(dataset, dataset_type, zenodo_service)
            self.repository.session.commit()
        except DatasetMetadataValidationError:
            self.repository.session.rollback()
            raise
        except DatasetMetadataUpdateError:
            self.repository.session.rollback()
            raise
        except Exception as exc:
            self.repository.session.rollback()
            raise DatasetMetadataUpdateError(str(exc))

    def create_from_form(self, form: DataSetForm, current_user: User) -> DataSet:

        dataset = None

        main_author = {
            "name": f"{current_user.profile.surname}, {current_user.profile.name}",
            "affiliation": current_user.profile.affiliation,
            "orcid": current_user.profile.get_orcid(),
        }
        try:
            dsmetadata_data = form.get_dsmetadata()

            # Limpiar HTML en el campo description
            raw_description = dsmetadata_data.get("description", "")
            clean_description = bleach.clean(
                raw_description,
                tags=["b", "i", "u", "a", "p", "br"],
                attributes={"a": ["href", "title", "target"]},
                strip=True,
            )
            dsmetadata_data["description"] = clean_description

            logger.info(f"Creating dsmetadata...: {dsmetadata_data}")
            dsmetadata = self.dsmetadata_repository.create(**dsmetadata_data)

            dsmetadata_info = form.get_dsmetadata()
            is_anonymous = dsmetadata_info.get("dataset_anonymous", False)

            if is_anonymous:
                author_list = form.get_anonymous_authors()
            else:
                other_authors = form.get_authors()
                if other_authors:
                    author_list = other_authors
                else:
                    author_list = [main_author]

            for author_data in author_list:
                author = self.author_repository.create(commit=False, ds_meta_data_id=dsmetadata.id, **author_data)
                dsmetadata.authors.append(author)

            dataset = self.create(commit=False, user_id=current_user.id, ds_meta_data_id=dsmetadata.id)

            feature_model_count = 0
            for feature_model in form.feature_models:
                uvl_filename = feature_model.uvl_filename.data
                fmmetadata = self.fmmetadata_repository.create(commit=False, **feature_model.get_fmmetadata())
                for author_data in feature_model.get_authors():
                    author = self.author_repository.create(commit=False, fm_meta_data_id=fmmetadata.id, **author_data)
                    fmmetadata.authors.append(author)

                fm = self.feature_model_repository.create(
                    commit=False, dataset_id=dataset.id, fm_meta_data_id=fmmetadata.id
                )

                feature_model_count += 1

                # associated files in feature model
                file_path = os.path.join(current_user.temp_folder(), uvl_filename)
                checksum, size = calculate_checksum_and_size(file_path)

                file = self.hubfilerepository.create(
                    commit=False,
                    name=uvl_filename,
                    checksum=checksum,
                    size=size,
                    feature_model_id=fm.id,
                )
                fm.hubfiles.append(file)

            dataset.feature_model_count = feature_model_count
            self.repository.session.commit()
        except Exception as exc:
            logger.info(f"Exception creating dataset from form...: {exc}")
            self.repository.session.rollback()
            raise exc

        return dataset

    def populate_form_from_dataset(self, form: DataSetForm, dataset: DataSet):
        ds_meta_data = dataset.ds_meta_data

        form.title.data = ds_meta_data.title
        form.desc.data = ds_meta_data.description
        form.publication_type.data = ds_meta_data.publication_type.value
        form.publication_doi.data = ds_meta_data.publication_doi
        form.dataset_doi.data = ds_meta_data.dataset_doi
        form.tags.data = ds_meta_data.tags
        form.dataset_anonymous.data = ds_meta_data.dataset_anonymous

        # Populate authors
        form.authors.entries = []  # Clear existing entries
        for author in ds_meta_data.authors:
            author_form = AuthorForm()
            author_form.name.data = author.name
            author_form.affiliation.data = author.affiliation
            author_form.orcid.data = author.orcid
            form.authors.append_entry(author_form)

        # Populate feature models
        form.feature_models.entries = []  # Clear existing entries
        for fm in dataset.feature_models:
            fm_meta_data = fm.fm_meta_data
            fm_form = FeatureModelForm()
            fm_form.uvl_filename.data = fm_meta_data.uvl_filename
            fm_form.title.data = fm_meta_data.title
            fm_form.desc.data = fm_meta_data.description
            fm_form.publication_type.data = fm_meta_data.publication_type.value
            fm_form.publication_doi.data = fm_meta_data.publication_doi
            fm_form.tags.data = fm_meta_data.tags
            fm_form.version.data = fm_meta_data.uvl_version

            # Populate authors for feature model
            fm_form.authors.entries = []  # Clear existing entries
            for author in fm_meta_data.authors:
                author_form = AuthorForm()
                author_form.name.data = author.name
                author_form.affiliation.data = author.affiliation
                author_form.orcid.data = author.orcid
                fm_form.authors.append_entry(author_form)

            form.feature_models.append_entry(fm_form)

        return form

    def update_dsmetadata(self, id, **kwargs):
        return self.dsmetadata_repository.update(id, **kwargs)

    def get_uvlhub_doi(self, dataset: DataSet) -> str:
        server_name = current_app.config.get("SERVER_NAME")
        preferred_url_scheme = current_app.config.get("PREFERRED_URL_SCHEME")
        return f"{preferred_url_scheme}://{server_name}/doi/{dataset.ds_meta_data.dataset_doi}"

    def zip_dataset(self, dataset: DataSet) -> str:
        working_dir = os.getenv("WORKING_DIR", "")
        dataset_dir = os.path.join(working_dir, "uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}")

        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"dataset_{dataset.id}.zip")

        with ZipFile(zip_path, "w") as zipf:
            for subdir, _, files in os.walk(dataset_dir):
                for file in files:
                    full_path = os.path.join(subdir, file)
                    relative_path = os.path.relpath(full_path, dataset_dir)
                    zipf.write(full_path, arcname=relative_path)

        return zip_path

    def zip_all_datasets(self, zip_path: str):
        with ZipFile(zip_path, "w") as zipf:
            for user_dir in os.listdir("uploads"):
                user_path = os.path.join("uploads", user_dir)

                if os.path.isdir(user_path) and user_dir.startswith("user_"):
                    for dataset_dir in os.listdir(user_path):
                        dataset_path = os.path.join(user_path, dataset_dir)

                        if os.path.isdir(dataset_path) and dataset_dir.startswith("dataset_"):
                            dataset_id = int(dataset_dir.split("_")[1])

                            if self.is_synchronized(dataset_id):
                                for subdir, dirs, files in os.walk(dataset_path):
                                    for file in files:
                                        full_path = os.path.join(subdir, file)

                                        relative_path = os.path.relpath(full_path, dataset_path)
                                        zipf.write(
                                            full_path,
                                            arcname=os.path.join(dataset_dir, relative_path),
                                        )

    def zip_from_storage(self, dataset):
        dataset_folder = os.path.join(
            os.getenv("WORKING_DIR", ""),
            "uploads",
            f"user_{dataset.user_id}",
            f"dataset_{dataset.id}",
            "uvl",
        )

        if not os.path.exists(dataset_folder):
            current_app.logger.warning(f"[ZIP] Dataset folder not found: {dataset_folder}")
            return None  # Lo manejarás con abort(404) fuera

        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"dataset_{dataset.id}.zip")

        with zipfile.ZipFile(zip_path, "w") as zipf:
            for filename in os.listdir(dataset_folder):
                file_path = os.path.join(dataset_folder, filename)
                arcname = filename
                zipf.write(file_path, arcname=arcname)

        return zip_path


class AuthorService(BaseService):
    def __init__(self):
        super().__init__(AuthorRepository())


class DSDownloadRecordService(BaseService):
    def __init__(self):
        super().__init__(DSDownloadRecordRepository())
        self.statistics_service = StatisticsService()

    def the_record_exists(self, dataset: DataSet, user_cookie: str):
        return self.repository.the_record_exists(dataset, user_cookie)

    def create_new_record(self, dataset: DataSet, user_cookie: str) -> DSDownloadRecord:
        return self.repository.create_new_record(dataset, user_cookie)

    def create_cookie(self, dataset: DataSet) -> str:

        user_cookie = request.cookies.get("download_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing_record = self.the_record_exists(dataset=dataset, user_cookie=user_cookie)

        if not existing_record:
            self.create_new_record(dataset=dataset, user_cookie=user_cookie)
            self.statistics_service.increment_datasets_downloaded()

        return user_cookie


class DSMetaDataService(BaseService):
    def __init__(self):
        super().__init__(DSMetaDataRepository())

    def update(self, id, **kwargs):
        return self.repository.update(id, **kwargs)

    def filter_by_doi(self, doi: str) -> Optional[DSMetaData]:
        return self.repository.filter_by_doi(doi)


class DSViewRecordService(BaseService):
    def __init__(self):
        super().__init__(DSViewRecordRepository())
        self.statistics_service = StatisticsService()

    def the_record_exists(self, dataset: DataSet, user_cookie: str):
        return self.repository.the_record_exists(dataset, user_cookie)

    def create_new_record(self, dataset: DataSet, user_cookie: str) -> DSViewRecord:
        return self.repository.create_new_record(dataset, user_cookie)

    def create_cookie(self, dataset: DataSet) -> str:

        user_cookie = request.cookies.get("view_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing_record = self.the_record_exists(dataset=dataset, user_cookie=user_cookie)

        if not existing_record:
            self.create_new_record(dataset=dataset, user_cookie=user_cookie)
            self.statistics_service.increment_datasets_viewed()

        return user_cookie


class DOIMappingService(BaseService):
    def __init__(self):
        super().__init__(DOIMappingRepository())

    def get_new_doi(self, old_doi: str) -> str:
        doi_mapping = self.repository.get_new_doi(old_doi)
        if doi_mapping:
            return doi_mapping.dataset_doi_new
        else:
            return None


class SizeService:

    def __init__(self):
        pass

    def get_human_readable_size(self, size: int) -> str:
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024**2:
            return f"{round(size / 1024, 2)} KB"
        elif size < 1024**3:
            return f"{round(size / (1024 ** 2), 2)} MB"
        else:
            return f"{round(size / (1024 ** 3), 2)} GB"


class LocalDatasetService:
    def __init__(
        self,
        dsmetadata_service,
        dataset_service,
        author_service,
        feature_model_service,
        logger,
    ):
        self.dsmetadata_service = dsmetadata_service
        self.dataset_service = dataset_service
        self.author_service = author_service
        self.feature_model_service = feature_model_service
        self.logger = logger

    def create_local_dataset(self, form, current_user):
        try:
            title = form.get("title")
            description = form.get("description")
            publication_type_id = form.get("publication_type")
            publication_doi = form.get("publication_doi")
            tags = form.getlist("tags[]")

            self.logger.info(
                f"[LOCAL] Metadata - title: {title}, description: {description}, "
                f"publication_type_id: {publication_type_id}, publication_doi: {publication_doi}, tags: {tags}"
            )

            publication_type = PublicationType(publication_type_id) if publication_type_id else None

            # Crear DSMetaData
            ds_meta = self.dsmetadata_service.create(
                title=title,
                description=description,
                publication_type=publication_type,
                publication_doi=publication_doi,
                tags=",".join(tags) if tags else "",
            )
            self.logger.info(f"[LOCAL] DSMetaData created with ID: {ds_meta.id}")

            # Crear DataSet
            dataset = self.dataset_service.create(commit=False, user_id=current_user.id, ds_meta_data_id=ds_meta.id)
            self.logger.info(f"[LOCAL] DataSet created with ID: {dataset.id}")

            # Crear autores
            i = 0
            while True:
                name = form.get(f"authors[{i}][name]")
                if not name:
                    break
                affiliation = form.get(f"authors[{i}][affiliation]")
                orcid = form.get(f"authors[{i}][orcid]")

                self.author_service.create(
                    ds_meta_data_id=ds_meta.id,
                    name=name,
                    affiliation=affiliation,
                    orcid=orcid,
                )
                self.logger.info(f"[LOCAL] Author #{i} added: {name}, {affiliation}, {orcid}")
                i += 1

            # Guardar en DB
            db.session.commit()
            self.logger.info(f"[LOCAL] Dataset {dataset.id} committed to DB")

            ingest = UploadIngestService(self.logger)
            stage_dir, staged_uvls = ingest.prepare_uvls(current_user.temp_folder())
            self.logger.info(f"[LOCAL] {len(staged_uvls)} UVLs listos en {stage_dir}")

            created_fms = self.feature_model_service.create_from_uvl_files(dataset, base_dir=stage_dir)

            return dataset, ds_meta, created_fms

        except Exception as exc:
            db.session.rollback()
            self.logger.exception(f"[LOCAL ERROR] {exc}")
            raise
