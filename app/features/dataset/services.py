import hashlib
import json
import logging
import os
import re
import shutil
import tempfile
import unicodedata
import uuid
import zipfile
from datetime import datetime
from typing import List, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request
from zipfile import ZipFile

import bleach
import pytz
from flask import current_app, request
from splent_framework.services.BaseService import BaseService
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.datastructures import MultiDict
from werkzeug.utils import secure_filename

from app import db
from app.features.auth.models import User
from app.features.dataset.forms import AuthorForm, DataSetForm, FeatureModelForm
from app.features.dataset.models import (
    DataSet,
    DatasetTransferRequest,
    DatasetTransferStatus,
    DSDownloadRecord,
    DSMetaData,
    DSViewRecord,
    PublicationType,
)
from app.features.dataset.repositories import (
    AuthorRepository,
    DataSetRepository,
    DatasetTransferRequestRepository,
    DOIMappingRepository,
    DSDownloadRecordRepository,
    DSMetaDataRepository,
    DSViewRecordRepository,
)
from app.features.featuremodel.repositories import FeatureModelRepository
from app.features.hubfile.repositories import (
    HubfileDownloadRecordRepository,
    HubfileRepository,
    HubfileViewRecordRepository,
)
from app.features.hubfile.services import UploadIngestService
from app.features.statistics.services import StatisticsService
from app.features.zenodo.services import ZenodoUnavailableError

logger = logging.getLogger(__name__)
ORCID_REGEX = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$")

# Upper bound for author lists accepted by the API. Author name/affiliation are
# 120-char columns, so oversized payloads are rejected before any DB write.
MAX_API_AUTHORS = 25
AUTHOR_FIELD_MAX_LENGTH = 120


class DatasetMetadataValidationError(Exception):
    pass


class DatasetMetadataUpdateError(Exception):
    pass


class DatasetOwnershipError(Exception):
    """Raised when a dataset (or its lineage) cannot change owner."""


def calculate_checksum_and_size(file_path):
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as file:
        content = file.read()
        hash_md5 = hashlib.md5(content).hexdigest()
        return hash_md5, file_size


class DataSetService(BaseService):
    AVAILABLE_DOWNLOAD_FORMATS = ("uvl", "glencoe", "dimacs", "splot")

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
        self.transfer_request_repository = DatasetTransferRequestRepository()

    def paginate(self, page: int = 1, per_page: int = 5):
        return self.repository.model.query.paginate(page=page, per_page=per_page, error_out=False)

    def mark_metadata_synced(self, dataset: DataSet) -> None:
        dataset.ds_meta_data.metadata_synced = True
        self.repository.session.commit()

    def create_basic_dataset(self, user: User) -> DataSet:
        dataset = self.create(commit=False, user_id=user.id, ds_meta_data_id=None)
        return dataset

    def create_draft_from_uvl_import(
        self,
        current_user: User,
        title: str,
        uvl_content: str,
        filename: str = None,
        description: str = "",
        authors: Optional[List[dict]] = None,
        api_publisher: Optional[User] = None,
    ) -> tuple[DataSet, list]:
        """Create a draft dataset from raw UVL content.

        ``authors`` is optional. When given (already normalized by
        ``normalize_authors``) it becomes the dataset credit, which lets a
        service account publish on behalf of the real developer. When omitted
        the draft is credited to the uploading account's profile, exactly as
        before.

        ``api_publisher`` is the account whose API key made the request. It is
        recorded on the metadata so a credit given to somebody else stays
        traceable back to whoever made the claim.
        """
        clean_title = self._sanitize_person_field(title)
        if not clean_title:
            raise DatasetMetadataValidationError("Title is required.")

        if not (uvl_content or "").strip():
            raise DatasetMetadataValidationError("UVL content is required.")

        # The dataset page renders the description with |safe, and the web
        # upload already runs it through bleach. This entry point feeds the
        # same column from an API request, so it has to clean it the same way
        # or an API key turns a public DOI landing page into a script sink.
        clean_description = self.sanitize_description(description) or "Imported from flamapyIDE."

        base_filename = filename or f"{clean_title}.uvl"
        safe_filename = secure_filename(base_filename) or "model.uvl"
        if not safe_filename.lower().endswith(".uvl"):
            safe_filename = f"{safe_filename}.uvl"

        temp_root = current_user.temp_folder()
        os.makedirs(temp_root, exist_ok=True)
        import_dir = tempfile.mkdtemp(prefix="flamapy_", dir=temp_root)
        import_path = os.path.join(import_dir, safe_filename)

        try:
            with open(import_path, "w", encoding="utf-8", newline="\n") as imported_file:
                imported_file.write(uvl_content)

            import_form = MultiDict(
                [
                    ("title", clean_title),
                    ("description", clean_description),
                    ("publication_type", ""),
                    ("publication_doi", ""),
                ]
            )
            if authors:
                for index, author in enumerate(authors):
                    import_form.add(f"authors[{index}][name]", author["name"])
                    import_form.add(f"authors[{index}][affiliation]", author.get("affiliation") or "")
                    import_form.add(f"authors[{index}][orcid]", author.get("orcid") or "")
            else:
                profile = getattr(current_user, "profile", None)
                if profile and (profile.name or profile.surname):
                    author_parts = [part.strip() for part in [profile.surname, profile.name] if part and part.strip()]
                    author_name = ", ".join(author_parts) if len(author_parts) > 1 else author_parts[0]
                    import_form.add("authors[0][name]", author_name)
                    import_form.add("authors[0][affiliation]", (profile.affiliation or "").strip())
                    import_form.add("authors[0][orcid]", profile.get_orcid() if hasattr(profile, "get_orcid") else "")

            from app.features.featuremodel.services import FeatureModelService

            local_service = LocalDatasetService(
                dsmetadata_service=DSMetaDataService(),
                dataset_service=self,
                author_service=AuthorService(),
                feature_model_service=FeatureModelService(),
                logger=logger,
            )
            dataset, ds_meta, created_fms = local_service.create_local_dataset(
                import_form,
                current_user,
                temp_root=import_dir,
            )
            if api_publisher is not None:
                ds_meta.api_publisher_user_id = api_publisher.id
                self.repository.session.commit()
            return dataset, created_fms
        except Exception:
            self.repository.session.rollback()
            raise
        finally:
            shutil.rmtree(import_dir, ignore_errors=True)

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

    def _normalize_orcid(self, value) -> str:
        """Normalize an ORCID coming from JSON, where the type is not a given.

        The web form only ever sends strings, but an API client can put any
        JSON value in this field. ``(value or "").strip()`` raised
        AttributeError on an int, a float, a list or a dict, and the upload
        route only catches DatasetMetadataValidationError, so the request came
        back as a 500 instead of the documented 400. Rejected explicitly here
        rather than coerced with str(), so the message names the real problem
        instead of complaining about the shape of "12345".
        """
        if value is not None and not isinstance(value, str):
            raise DatasetMetadataValidationError("ORCID must be a text value.")
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

    def _validate_orcid_format(self, orcid: str) -> str:
        """Offline ORCID validation: shape plus check digit, no network call."""
        normalized = self._normalize_orcid(orcid)
        if not normalized:
            return ""

        if not ORCID_REGEX.match(normalized):
            raise DatasetMetadataValidationError("Invalid ORCID format. Expected: 0000-0000-0000-0000.")

        if not self._is_valid_orcid_checksum(normalized):
            raise DatasetMetadataValidationError("Invalid ORCID checksum.")

        return normalized

    def _validate_orcid(self, orcid: str) -> str:
        normalized = self._validate_orcid_format(orcid)
        if not normalized:
            return ""

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

    def extract_authors_from_request(self, payload: Optional[dict], form_data) -> Optional[List[dict]]:
        """Collect optional author data from an API request.

        Three shapes are accepted, in this order of precedence:
        JSON ``{"authors": [{"name": ..., "affiliation": ..., "orcid": ...}]}``,
        a form field ``authors`` holding that same JSON array, and the
        ``authors[0][name]`` form fields the web upload already uses.

        Returns None when the request carries no author data at all, which
        callers read as "keep the default behaviour".
        """
        if payload and "authors" in payload:
            return self.normalize_authors(payload.get("authors"))

        raw_authors = form_data.get("authors") if form_data is not None else None
        if raw_authors:
            try:
                decoded = json.loads(raw_authors)
            except ValueError:
                raise DatasetMetadataValidationError("The authors field must be a JSON array of author objects.")
            return self.normalize_authors(decoded)

        if form_data is not None:
            form_authors = self._parse_authors_from_form(form_data)
            if form_authors:
                return self.normalize_authors(form_authors)

        return None

    @staticmethod
    def sanitize_description(raw_description: str) -> str:
        """Clean a dataset description down to the formatting uvlhub renders.

        ``view_dataset.html`` prints the description with the ``safe`` filter,
        so whatever survives here is live HTML on a public page. The allowlist
        matches the one the web upload has always used.
        """
        return bleach.clean(
            raw_description or "",
            tags=["b", "i", "u", "a", "p", "br"],
            attributes={"a": ["href", "title", "target"]},
            strip=True,
        ).strip()

    @staticmethod
    def _sanitize_person_field(value) -> str:
        """Strip anything that could make a rendered name lie.

        Author names travel to a permanent, public Zenodo record and to the
        dataset page. Unicode control and format characters are removed, which
        covers the bidirectional overrides that let "Bad‮Name" render as
        something else entirely, plus newlines and tabs that break a one-line
        credit into several. Whitespace is collapsed and the result normalized
        to NFC so visually identical names compare equal.
        """
        text = unicodedata.normalize("NFC", str(value or ""))
        cleaned = "".join(
            # Whitespace is turned into a plain space before anything is
            # dropped: a newline or a tab is a control character, and removing
            # it outright would glue "Ada\nLovelace" into "AdaLovelace".
            " " if character.isspace() else character
            for character in text
            if character.isspace() or unicodedata.category(character) not in {"Cc", "Cf", "Co", "Cs", "Cn"}
        )
        return " ".join(cleaned.split())

    def _assert_orcid_is_claimable(self, orcid: str, name: str) -> None:
        """Only let an API client attach an ORCID that uvlhub can vouch for.

        An ORCID is machine resolvable: Zenodo turns it into a link to that
        researcher's profile, permanently. Accepting one on the word of
        whoever holds an API key is enough to attribute an arbitrary record to
        a real named person. uvlhub cannot ask ORCID for consent, but it does
        know which ORCIDs have signed in here through ORCID's own OAuth flow,
        which proves the holder controls that identifier and gives them an
        account where they can see and contest the record. Anything else is
        refused, and the author can still be credited by name.
        """
        from app.features.orcid.models import Orcid

        if Orcid.query.filter_by(orcid_id=orcid).first() is not None:
            return
        raise DatasetMetadataValidationError(
            f"ORCID {orcid} cannot be credited for author '{name}': it is not linked to any uvlhub account. "
            "Ask the author to sign in with ORCID once, or send the author without an orcid field."
        )

    def normalize_authors(self, raw_authors, verify_orcid_ownership: bool = True) -> List[dict]:
        """Validate and clean author data coming from an API client.

        Names and affiliations are sanitized before anything else, so nothing
        that reaches Zenodo can carry control or bidi characters. ORCIDs are
        checked offline (shape plus check digit) so a publication never depends
        on orcid.org being reachable, and then checked against the ORCIDs that
        have actually authenticated on uvlhub, so a key holder cannot pin a
        record on a researcher who has no relationship with it. Duplicates are
        rejected the same way the web form rejects them.
        """
        if raw_authors is None:
            return []
        if not isinstance(raw_authors, list):
            raise DatasetMetadataValidationError("The authors field must be a list of author objects.")
        if len(raw_authors) > MAX_API_AUTHORS:
            raise DatasetMetadataValidationError(f"Too many authors (max {MAX_API_AUTHORS}).")

        authors = []
        seen_author_keys = set()
        seen_orcids = set()

        for entry in raw_authors:
            if isinstance(entry, str):
                entry = {"name": entry}
            if not isinstance(entry, dict):
                raise DatasetMetadataValidationError("Each author must be an object with a name.")

            name = self._sanitize_person_field(entry.get("name"))
            if not name:
                raise DatasetMetadataValidationError("Each author must have a name.")
            if len(name) > AUTHOR_FIELD_MAX_LENGTH:
                raise DatasetMetadataValidationError(
                    f"Author name is too long (max {AUTHOR_FIELD_MAX_LENGTH} characters)."
                )

            affiliation = self._sanitize_person_field(entry.get("affiliation"))
            if len(affiliation) > AUTHOR_FIELD_MAX_LENGTH:
                raise DatasetMetadataValidationError(
                    f"Author affiliation is too long (max {AUTHOR_FIELD_MAX_LENGTH} characters)."
                )

            try:
                orcid = self._validate_orcid_format(entry.get("orcid"))
            except DatasetMetadataValidationError as exc:
                raise DatasetMetadataValidationError(f"Invalid ORCID for author '{name}': {exc}")

            if orcid and verify_orcid_ownership:
                self._assert_orcid_is_claimable(orcid, name)

            if orcid:
                if orcid in seen_orcids:
                    raise DatasetMetadataValidationError(
                        f"Duplicate author detected: ORCID {orcid} is already in the list."
                    )
                seen_orcids.add(orcid)
            else:
                author_key = (self._normalize_text(name), self._normalize_text(affiliation))
                if author_key in seen_author_keys:
                    raise DatasetMetadataValidationError("Duplicate author detected: same name and affiliation.")
                seen_author_keys.add(author_key)

            authors.append({"name": name, "affiliation": affiliation, "orcid": orcid})

        return authors

    def _apply_metadata_from_form(self, dataset: DataSet, form_data) -> None:
        dataset.ds_meta_data.title = form_data.get("title", "").strip()
        # Same sink as the creation paths: the description is rendered with
        # |safe on the public dataset page.
        dataset.ds_meta_data.description = self.sanitize_description(form_data.get("description", ""))
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

    def _get_requested_dataset_type(self, form_data, default: str = "draft") -> str:
        dataset_type = (form_data.get("dataset_type") or default).strip()
        allowed_types = {"draft", "zenodo", "zenodo_anonymous"}
        if dataset_type not in allowed_types:
            raise DatasetMetadataValidationError(
                f"Invalid dataset type '{dataset_type}'. Allowed values: draft, zenodo, zenodo_anonymous."
            )
        return dataset_type

    @staticmethod
    def _current_dataset_type(dataset: DataSet) -> str:
        """The dataset_type that reflects a dataset's current published state.

        Used as the default when editing so a request that omits dataset_type
        never silently downgrades a synchronized dataset to draft (which would
        clear its Zenodo DOI). Only an explicit dataset_type=draft downgrades.
        """
        meta = dataset.ds_meta_data
        if meta.dataset_doi:
            return "zenodo_anonymous" if meta.dataset_anonymous else "zenodo"
        return "draft"

    @staticmethod
    def _find_dataset_hubfile(dataset: DataSet, hubfile_id):
        """Return the hubfile with ``hubfile_id`` if it belongs to ``dataset``."""
        target = int(hubfile_id)
        for feature_model in dataset.feature_models:
            for hubfile in feature_model.hubfiles:
                if hubfile.id == target:
                    return hubfile
        return None

    def replace_hubfile(self, dataset: DataSet, hubfile_id, file_storage):
        """Swap the content of a draft dataset's UVL file with a new upload.

        Published datasets are versioned instead (a new linked dataset), so this
        refuses to edit them in place — that would desync the Zenodo deposition.
        The file keeps its stored name; only its content (and checksum/size) and
        the derived domain artefacts (fact label, flamapy transform) change.
        """
        from app.features.hubfile.services import HubfileService
        from app.features.hubfile.signals import hubfile_created

        if dataset.ds_meta_data.dataset_doi:
            raise DatasetMetadataUpdateError(
                "Published datasets are versioned, not edited in place. Create a new version instead."
            )

        hubfile = self._find_dataset_hubfile(dataset, hubfile_id)
        if hubfile is None:
            raise DatasetMetadataValidationError("The file does not belong to this dataset.")

        if not (file_storage and file_storage.filename and file_storage.filename.lower().endswith(".uvl")):
            raise DatasetMetadataValidationError("A .uvl file is required.")

        dest_path = hubfile.get_full_path()
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        file_storage.save(dest_path)

        hubfile.checksum = HubfileService._calculate_checksum(dest_path)
        hubfile.size = os.path.getsize(dest_path)
        self.repository.session.commit()

        # Re-run the domain processing the creation signal would have triggered,
        # now against the replaced content (fact label + flamapy transform).
        hubfile_created.send(hubfile, hubfile_id=hubfile.id, path=dest_path)
        return hubfile

    def create_new_version(self, dataset: DataSet, file_storage, current_user, zenodo_service):
        """Publish a new version of a published dataset with a replaced UVL.

        Uses Zenodo's newversion action so the new version gets its own DOI within
        the same concept lineage, and records a new local dataset linked to the
        previous one via dataset_origin_id. Drafts are replaced in place instead.
        """
        meta = dataset.ds_meta_data
        if not (meta.dataset_doi and meta.deposition_id):
            raise DatasetMetadataUpdateError(
                "Only published datasets are versioned. Replace the file directly for drafts."
            )
        self._reject_if_superseded(dataset)
        if not (file_storage and file_storage.filename and file_storage.filename.lower().endswith(".uvl")):
            raise DatasetMetadataValidationError("A .uvl file is required.")

        # The clone is committed before Zenodo is touched (the file ingest needs
        # a real dataset id on disk), so every failure past this point has to
        # remove it again. An abandoned clone would sit in the lineage forever,
        # with no DOI, and the lineage endpoints would advertise it.
        #
        # Only up to the point of no return, though. publish_deposition mints a
        # permanent public DOI that nobody can withdraw, so once it has been
        # called the clone is the only local trace of a real Zenodo record and
        # deleting it would strand that record forever.
        new_dataset = self._clone_as_new_version(dataset, current_user)
        published = False
        new_deposition_id = None
        try:
            self._claim_sole_successor(dataset, new_dataset)
            self._attach_uvl_file(new_dataset, file_storage)

            new_deposition_id = zenodo_service.create_new_version_draft(meta.deposition_id)
            zenodo_service.delete_all_deposition_files(new_deposition_id)
            zip_path = self.zip_dataset(new_dataset)
            try:
                zenodo_service.upload_zip(new_dataset, new_deposition_id, zip_path)
            finally:
                if zip_path and os.path.exists(zip_path):
                    shutil.rmtree(os.path.dirname(zip_path), ignore_errors=True)

            new_metadata = zenodo_service.build_metadata(
                new_dataset, anonymous=bool(meta.dataset_anonymous), version=new_dataset.dataset_version
            )
            zenodo_service.update_draft_metadata(new_deposition_id, new_metadata)

            # Committed before the irreversible call, not after it. The
            # deposition id is the only handle that ties the local row to the
            # Zenodo record, and everything between here and the DOI commit can
            # fail. Writing it first means a crash at any point leaves a row
            # that names the deposition, which is what makes reconciliation
            # possible at all.
            new_dataset.ds_meta_data.deposition_id = new_deposition_id
            self.repository.session.commit()

            zenodo_service.publish_deposition(new_deposition_id)
            published = True

            new_doi = zenodo_service.get_doi(new_deposition_id)
            if not new_doi:
                raise DatasetMetadataUpdateError("Zenodo did not return a DOI for the new version.")

            new_dataset.ds_meta_data.dataset_doi = new_doi
            new_dataset.ds_meta_data.metadata_synced = True
            self.repository.session.commit()
        except Exception:
            if published:
                self._preserve_published_version(new_dataset, new_deposition_id)
            else:
                self._discard_unpublished_version(new_dataset)
            raise

        # Same lineage, same concept DOI. Zenodo returns it on the new version
        # too; the previous version's value is the fallback when it does not.
        # Deliberately after the commit above and deliberately non-fatal: the
        # DOI is already minted and stored, so nothing here may turn a
        # successful publication into an error for the client.
        self.resolve_and_store_concept_doi(
            new_dataset,
            zenodo_service,
            new_deposition_id,
            fallback=dataset.get_concept_doi(),
            propagate=True,
        )
        return new_dataset

    @staticmethod
    def _reject_if_superseded(dataset: DataSet, exclude_id: Optional[int] = None) -> None:
        """Refuse to branch a lineage.

        Zenodo versions are a chain, not a tree, and so is the local mirror.
        Versioning a node that already has a successor (a client retrying after
        a timeout, a duplicated job, a stale dataset id) would create two
        siblings claiming the same predecessor. Nothing downstream can then
        answer "which one is the newest version" honestly, and a transfer would
        move one branch and leave the other behind.
        """
        successors = sorted(
            (version for version in dataset.dataset_versions if version.id != exclude_id),
            key=lambda version: ((version.dataset_version or 1), version.id),
        )
        if not successors:
            return
        newest = successors[-1]
        raise DatasetMetadataUpdateError(
            f"Dataset {dataset.id} has already been superseded by version {newest.dataset_version} "
            f"(dataset {newest.id}). Create the new version from the newest one."
        )

    def _claim_sole_successor(self, origin: DataSet, candidate: DataSet) -> None:
        """Re-run the branch check once the clone row is visible to everyone.

        The pre-check runs before the clone is committed, so two concurrent
        requests can both pass it. After the commit each of them can see the
        other, and the lowest id wins: a rival clone created before ours makes
        us back off, while one created after ours will back off itself. Exactly
        one request goes on to mint a Zenodo version.
        """
        self.repository.session.expire(origin, ["dataset_versions"])
        rivals = [
            version for version in origin.dataset_versions if version.id != candidate.id and version.id < candidate.id
        ]
        if not rivals:
            return
        newest = max(rivals, key=lambda version: ((version.dataset_version or 1), version.id))
        raise DatasetMetadataUpdateError(
            f"Dataset {origin.id} has already been superseded by version {newest.dataset_version} "
            f"(dataset {newest.id}). Create the new version from the newest one."
        )

    def _preserve_published_version(self, dataset: DataSet, deposition_id: Optional[int]) -> None:
        """Keep a clone whose Zenodo deposition was already published.

        The counterpart of _discard_unpublished_version, for the window between
        publish_deposition and the DOI commit. A public DOI exists by now and
        holds the user's files, so the local row must survive even though the
        request is about to fail: it is the only thing that records which
        deposition the record lives in. The row is left with its deposition id
        and no DOI, which is exactly the shape an operator can reconcile.

        Never raises, for the same reason as the discard path.
        """
        dataset_id = getattr(dataset, "id", None)
        try:
            self.repository.session.rollback()
            fresh = self.repository.get_by_id(dataset_id) if dataset_id else None
            if fresh is not None and fresh.ds_meta_data and not fresh.ds_meta_data.deposition_id and deposition_id:
                # The pre-publication commit is expected to have stored this
                # already. Restore it if anything rolled it back, because
                # losing it is what makes the record unreconcilable.
                fresh.ds_meta_data.deposition_id = deposition_id
                self.repository.session.commit()
        except Exception as exc:  # noqa: BLE001 - the original failure matters more
            self.repository.session.rollback()
            logger.error("[VERSION] Could not record deposition %s on version %s: %s", deposition_id, dataset_id, exc)

        logger.error(
            "[VERSION] Deposition %s was PUBLISHED at Zenodo but version %s could not be completed. "
            "The DOI is permanent and the local row was kept on purpose so the two can be reconciled. "
            "Do not delete dataset %s.",
            deposition_id,
            dataset_id,
            dataset_id,
        )

    def _discard_unpublished_version(self, dataset: DataSet) -> None:
        """Remove a version clone that never made it to Zenodo.

        Best effort and never raises: the caller is already propagating the
        real failure, and leaving the half-created row behind is worse than a
        failed cleanup because it becomes a permanent phantom in the lineage.

        Refuses to delete anything that carries a deposition id or a DOI. Both
        mean Zenodo already knows about this row, and a Zenodo record whose
        local trace has been erased can never be reconciled. The check is
        deliberately made against freshly read, committed state: the rollback
        below throws away every uncommitted attribute, so reading the in-memory
        object here would answer about values that no longer exist.
        """
        dataset_id = getattr(dataset, "id", None)
        owner_id = getattr(dataset, "user_id", None)
        try:
            self.repository.session.rollback()
            fresh = self.repository.get_by_id(dataset_id) if dataset_id else None
            if fresh is None:
                return
            if fresh.ds_meta_data and (fresh.ds_meta_data.dataset_doi or fresh.ds_meta_data.deposition_id):
                # Zenodo has seen this one. Keeping a phantom in the lineage is
                # recoverable; erasing the only pointer to a public record is not.
                logger.error(
                    "[VERSION] Refusing to discard version %s: it already points at deposition %s (DOI %s).",
                    dataset_id,
                    fresh.ds_meta_data.deposition_id,
                    fresh.ds_meta_data.dataset_doi,
                )
                return
            meta = fresh.ds_meta_data
            self.repository.session.delete(fresh)
            if meta is not None:
                self.repository.session.delete(meta)
            self.repository.session.commit()
            logger.info("[VERSION] Discarded unpublished version %s after a failed publication", dataset_id)
        except Exception as exc:  # noqa: BLE001 - cleanup must not mask the original failure
            self.repository.session.rollback()
            logger.error("[VERSION] Could not discard unpublished version %s: %s", dataset_id, exc)
            return

        if dataset_id and owner_id:
            shutil.rmtree(self._dataset_storage_dir(owner_id, dataset_id), ignore_errors=True)

    """
        Concept DOI (Zenodo lineage identifier)
    """

    def resolve_and_store_concept_doi(
        self,
        dataset: DataSet,
        zenodo_service,
        deposition_id: int,
        fallback: Optional[str] = None,
        propagate: bool = False,
    ) -> Optional[str]:
        """Read the concept DOI from Zenodo and persist it.

        Never fatal, for real: by the time this runs the version DOI is already
        minted at Zenodo and already committed locally, so no failure here may
        reach the client. A Zenodo hiccup, a deposition without a conceptdoi, a
        lock timeout on the UPDATE, a dropped connection: all of them leave the
        column null and everything else keeps working. Every exit path that
        touched the session leaves it clean for the caller.

        ``propagate`` backfills the rest of the lineage. It is only true when
        the deposition really belongs to the lineage's Zenodo concept, which is
        the case for the newversion action. A first publication creates a brand
        new deposition in its own concept, so it speaks only for itself.
        """
        concept_doi = None
        try:
            concept_doi = zenodo_service.get_concept_doi(deposition_id)
        except Exception as exc:  # noqa: BLE001 - the DOI is already minted, do not fail the publish
            logger.warning("[ZENODO] Could not read the concept DOI of deposition %s: %s", deposition_id, exc)

        if not isinstance(concept_doi, str) or not concept_doi.strip():
            concept_doi = fallback

        if not isinstance(concept_doi, str) or not concept_doi.strip():
            logger.info("[ZENODO] No concept DOI available for deposition %s", deposition_id)
            return None

        try:
            return self.store_concept_doi(dataset, concept_doi.strip(), propagate=propagate)
        except Exception as exc:  # noqa: BLE001 - the version DOI is already committed, never fail here
            logger.error(
                "[ZENODO] Could not persist the concept DOI of deposition %s: %s",
                deposition_id,
                exc,
            )
            try:
                self.repository.session.rollback()
            except Exception:  # noqa: BLE001 - a broken session must not surface either
                logger.exception("[ZENODO] Could not roll back after a failed concept DOI write")
            return None

    def store_concept_doi(self, dataset: DataSet, concept_doi: str, propagate: bool = True) -> str:
        """Persist the concept DOI on a dataset, optionally across its lineage.

        The value always lands on ``dataset`` itself, overwriting whatever was
        there. It comes from the deposition that dataset actually points at, so
        it is the authoritative answer for that row: a stale value inherited
        from somewhere else would advertise a Zenodo concept the record is not
        in, and nothing would ever correct it.

        Other versions of the lineage are only backfilled when they have none.
        A version that already carries a different value belongs to a different
        Zenodo concept, which is a real (if unusual) state, so it is logged
        rather than silently rewritten.
        """
        concept_doi = (concept_doi or "").strip()
        if not concept_doi:
            return concept_doi

        previous = dataset.ds_meta_data.dataset_concept_doi
        if previous and previous != concept_doi:
            logger.warning(
                "[ZENODO] Dataset %s changed concept DOI from %s to %s",
                dataset.id,
                previous,
                concept_doi,
            )
        dataset.ds_meta_data.dataset_concept_doi = concept_doi

        if propagate:
            for version in dataset.all_versions():
                if version.id == dataset.id:
                    continue
                current = version.ds_meta_data.dataset_concept_doi
                if not current:
                    version.ds_meta_data.dataset_concept_doi = concept_doi
                elif current != concept_doi:
                    logger.warning(
                        "[ZENODO] Version %s of the lineage carries concept DOI %s, not %s; left untouched",
                        version.id,
                        current,
                        concept_doi,
                    )

        self.repository.session.commit()
        return concept_doi

    """
        Version lineage
    """

    def get_lineage(self, dataset: DataSet) -> List[DataSet]:
        """The whole version chain of a dataset, oldest first."""
        return dataset.all_versions()

    def get_lineage_by_concept_doi(self, concept_doi: str) -> List[DataSet]:
        """Resolve a version chain from the stable concept DOI.

        The lineage is walked from any member that carries the concept DOI, so
        it stays complete even when older versions predate the column and have
        it empty.

        A version that carries a *different* concept DOI is left out. Zenodo
        decides which concept a deposition belongs to, and resolving this
        concept DOI at Zenodo will never return that version, so answering with
        it (or worse, naming it the latest) would contradict the record this
        endpoint exists to point at.
        """
        wanted = (concept_doi or "").strip()
        entry_point = self.repository.get_by_concept_doi(wanted)
        if entry_point is None:
            return []
        return [
            version
            for version in entry_point.all_versions()
            if (version.ds_meta_data.dataset_concept_doi or wanted) == wanted
        ]

    """
        Ownership
    """

    @staticmethod
    def _dataset_storage_dir(user_id: int, dataset_id: int) -> str:
        return os.path.join(os.getenv("WORKING_DIR", ""), "uploads", f"user_{user_id}", f"dataset_{dataset_id}")

    def request_ownership_transfer(
        self,
        dataset: DataSet,
        current_owner: User,
        new_owner: User,
        message: Optional[str] = None,
    ) -> DatasetTransferRequest:
        """Offer a dataset lineage to another account, pending their answer.

        Nothing moves here. A published dataset carries a permanent Zenodo DOI
        and appears in its owner's public listings, so an account that never
        asked for it must be able to say no; otherwise any key holder could
        publish a record crediting a real person and then drop it on them.
        The offer is created, the recipient is told, and ownership moves only
        when they accept.
        """
        lineage = self.get_lineage(dataset)
        self._assert_lineage_is_transferable(dataset, lineage, current_owner, new_owner)

        blocking = self.transfer_request_repository.get_pending_for_datasets([version.id for version in lineage])
        if blocking:
            raise DatasetOwnershipError(
                f"A transfer of this dataset is already pending (transfer {blocking[0].id}). "
                "Cancel it before opening another one."
            )

        clean_message = self._sanitize_person_field(message)[:500] if message else None
        transfer = self.transfer_request_repository.create(
            dataset_id=dataset.id,
            from_user_id=current_owner.id,
            to_user_id=new_owner.id,
            status=DatasetTransferStatus.PENDING,
            message=clean_message,
        )
        logger.info(
            "[TRANSFER] Offer %s created for lineage %s from user %s to user %s",
            transfer.id,
            [version.id for version in lineage],
            current_owner.id,
            new_owner.id,
        )
        self._notify_transfer_offer(transfer, dataset, current_owner, new_owner)
        return transfer

    def accept_ownership_transfer(self, transfer: DatasetTransferRequest, recipient: User) -> List[DataSet]:
        """Accept a pending offer and move the whole lineage."""
        if not transfer.is_pending():
            raise DatasetOwnershipError(f"This transfer is already {transfer.status.value}.")
        if transfer.to_user_id != recipient.id:
            raise DatasetOwnershipError("Only the account the dataset was offered to can accept it.")

        dataset = self.repository.get_by_id(transfer.dataset_id)
        if dataset is None:
            raise DatasetOwnershipError("The dataset offered no longer exists.")

        sender = dataset.user
        if dataset.user_id != transfer.from_user_id:
            raise DatasetOwnershipError("The dataset changed owner after the offer was made.")

        lineage = self.transfer_ownership(dataset, recipient)
        transfer.status = DatasetTransferStatus.ACCEPTED
        transfer.resolved_at = datetime.now(pytz.utc)
        self.transfer_request_repository.session.commit()
        self._notify_transfer_resolution(transfer, dataset, sender, recipient, "accepted")
        return lineage

    def decline_ownership_transfer(self, transfer: DatasetTransferRequest, recipient: User) -> DatasetTransferRequest:
        """Refuse a pending offer. Nothing changes owner."""
        if not transfer.is_pending():
            raise DatasetOwnershipError(f"This transfer is already {transfer.status.value}.")
        if transfer.to_user_id != recipient.id:
            raise DatasetOwnershipError("Only the account the dataset was offered to can decline it.")

        transfer.status = DatasetTransferStatus.DECLINED
        transfer.resolved_at = datetime.now(pytz.utc)
        self.transfer_request_repository.session.commit()
        dataset = self.repository.get_by_id(transfer.dataset_id)
        self._notify_transfer_resolution(transfer, dataset, transfer.from_user, recipient, "declined")
        return transfer

    def cancel_ownership_transfer(self, transfer: DatasetTransferRequest, sender: User) -> DatasetTransferRequest:
        """Withdraw an offer that has not been answered yet."""
        if not transfer.is_pending():
            raise DatasetOwnershipError(f"This transfer is already {transfer.status.value}.")
        if transfer.from_user_id != sender.id:
            raise DatasetOwnershipError("Only the account that offered the dataset can cancel the transfer.")

        transfer.status = DatasetTransferStatus.CANCELLED
        transfer.resolved_at = datetime.now(pytz.utc)
        self.transfer_request_repository.session.commit()
        return transfer

    def get_transfer_request(self, transfer_id: int) -> Optional[DatasetTransferRequest]:
        return self.transfer_request_repository.get_by_id(transfer_id)

    def get_transfer_requests_for_user(self, user_id: int, status: Optional[str] = None):
        parsed_status = None
        if status:
            try:
                parsed_status = DatasetTransferStatus(status)
            except ValueError:
                raise DatasetOwnershipError(
                    "Unknown transfer status. Use one of: "
                    + ", ".join(member.value for member in DatasetTransferStatus)
                )
        return self.transfer_request_repository.get_involving_user(user_id, parsed_status)

    def _assert_lineage_is_transferable(
        self,
        dataset: DataSet,
        lineage: List[DataSet],
        current_owner: User,
        new_owner: User,
    ) -> None:
        if new_owner.id == current_owner.id:
            raise DatasetOwnershipError("The dataset already belongs to that account.")
        if not any(version.id == dataset.id for version in lineage):
            # all_versions walks the whole tree from the root, so this cannot
            # happen; if it ever did, moving a lineage the dataset is not part
            # of would move the wrong rows and report success.
            raise DatasetOwnershipError("The dataset is not part of the lineage it resolves to.")
        foreign = [version.id for version in lineage if version.user_id != current_owner.id]
        if foreign:
            raise DatasetOwnershipError(
                f"This version lineage is split across several accounts (datasets {foreign}) "
                "and cannot be transferred automatically."
            )

    def _notify_transfer_offer(
        self,
        transfer: DatasetTransferRequest,
        dataset: DataSet,
        sender: User,
        recipient: User,
    ) -> None:
        """Tell the recipient a dataset is waiting for their answer.

        Best effort. A mail outage must not block the offer, which is visible
        through the transfers endpoint either way.
        """
        body = (
            f"uvlhub account {sender.id} wants to transfer the dataset "
            f'"{dataset.ds_meta_data.title}" (dataset {dataset.id}) and all of its versions to you.\n\n'
            f"Nothing has changed yet. Accept or decline transfer {transfer.id} "
            "through the uvlhub API to answer."
        )
        self._send_transfer_email(recipient, "A uvlhub dataset has been offered to you", body)

    def _notify_transfer_resolution(
        self,
        transfer: DatasetTransferRequest,
        dataset: Optional[DataSet],
        sender: Optional[User],
        recipient: User,
        outcome: str,
    ) -> None:
        if sender is None:
            return
        title = dataset.ds_meta_data.title if dataset is not None else f"dataset {transfer.dataset_id}"
        body = f'Account {recipient.id} {outcome} the transfer of "{title}" (transfer {transfer.id}).'
        self._send_transfer_email(sender, f"Your uvlhub dataset transfer was {outcome}", body)

    @staticmethod
    def _send_transfer_email(user: Optional[User], subject: str, body: str) -> None:
        recipient_email = getattr(user, "email", None)
        if not recipient_email:
            return
        try:
            from app.features.mail.services import MailService

            MailService().send_email(subject, [recipient_email], body)
        except Exception as exc:  # noqa: BLE001 - notification is not part of the transaction
            logger.warning("[TRANSFER] Could not notify %s: %s", recipient_email, exc)

    def transfer_ownership(self, dataset: DataSet, new_owner: User) -> List[DataSet]:
        """Move a dataset and its whole version lineage to another account.

        The lineage moves as a unit on purpose. Versioning requires owning the
        node being versioned, and every file lives under
        ``uploads/user_<owner>/dataset_<id>``, so moving a single node would
        scatter one logical record across two accounts and leave the rest of
        the chain unversionable by either of them.

        Returns the moved lineage, oldest first.
        """
        lineage = self.get_lineage(dataset)
        previous_owner = dataset.user
        previous_owner_id = dataset.user_id
        self._assert_lineage_is_transferable(dataset, lineage, previous_owner, new_owner)

        moved_directories = []
        try:
            for version in lineage:
                source_dir = self._dataset_storage_dir(previous_owner_id, version.id)
                target_dir = self._dataset_storage_dir(new_owner.id, version.id)
                if not os.path.isdir(source_dir):
                    continue
                if os.path.exists(target_dir):
                    raise DatasetOwnershipError(f"The target account already has storage for dataset {version.id}.")
                os.makedirs(os.path.dirname(target_dir), exist_ok=True)
                shutil.move(source_dir, target_dir)
                moved_directories.append((source_dir, target_dir))

            for version in lineage:
                version.user_id = new_owner.id
            self.repository.session.commit()
        except Exception:
            self.repository.session.rollback()
            self._undo_directory_moves(moved_directories)
            raise

        logger.info(
            "[TRANSFER] Lineage %s moved from user %s to user %s",
            [version.id for version in lineage],
            previous_owner_id,
            new_owner.id,
        )
        return lineage

    @staticmethod
    def _undo_directory_moves(moved_directories) -> None:
        for source_dir, target_dir in reversed(moved_directories):
            try:
                shutil.move(target_dir, source_dir)
            except OSError as exc:  # noqa: PERF203 - best effort, the original error matters more
                logger.error("[TRANSFER] Could not restore %s after a failed transfer: %s", source_dir, exc)

    def _clone_as_new_version(self, source: DataSet, current_user) -> DataSet:
        src = source.ds_meta_data
        # dataset_concept_doi is deliberately not copied. Zenodo decides which
        # concept a deposition belongs to, and it has not been asked yet; the
        # value is written after publication from the deposition the clone
        # actually got. Copying it up front would leave a wrong, permanent
        # concept DOI behind on any clone that ends up in its own deposition.
        new_meta = DSMetaDataService().create(
            title=src.title,
            description=src.description,
            publication_type=src.publication_type,
            publication_doi=src.publication_doi,
            api_publisher_user_id=src.api_publisher_user_id,
            tags=src.tags,
            dataset_anonymous=src.dataset_anonymous,
            metadata_synced=True,
        )
        author_service = AuthorService()
        for author in src.authors:
            author_service.create(
                ds_meta_data_id=new_meta.id, name=author.name, affiliation=author.affiliation, orcid=author.orcid
            )
        return self.repository.create(
            user_id=current_user.id,
            ds_meta_data_id=new_meta.id,
            dataset_version=(source.dataset_version or 1) + 1,
            dataset_origin_id=source.id,
        )

    def _attach_uvl_file(self, dataset: DataSet, file_storage) -> None:
        from app.features.featuremodel.services import FeatureModelService

        stage_dir = tempfile.mkdtemp()
        try:
            file_storage.save(os.path.join(stage_dir, secure_filename(file_storage.filename)))
            created = FeatureModelService().create_from_uvl_files(dataset, base_dir=stage_dir)
            dataset.feature_model_count = len(created)
            self.repository.session.commit()
        finally:
            shutil.rmtree(stage_dir, ignore_errors=True)

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
        self._set_concept_doi_from_zenodo(dataset, zenodo_service, deposition_id)

    def _set_concept_doi_from_zenodo(self, dataset: DataSet, zenodo_service, deposition_id: int) -> None:
        """Read the concept DOI and stage it on the metadata being written.

        Used inside flows that own their own commit, hence no commit here.
        """
        try:
            concept_doi = zenodo_service.get_concept_doi(deposition_id)
        except Exception as exc:  # noqa: BLE001 - the DOI is already minted, do not fail the publish
            logger.warning("[ZENODO] Could not read the concept DOI of deposition %s: %s", deposition_id, exc)
            return
        if isinstance(concept_doi, str) and concept_doi.strip():
            dataset.ds_meta_data.dataset_concept_doi = concept_doi.strip()

    def _transition_dataset_state_if_needed(self, dataset: DataSet, dataset_type: str, zenodo_service) -> None:
        wants_sync = dataset_type in {"zenodo", "zenodo_anonymous"}
        is_synced = bool(dataset.ds_meta_data.dataset_doi)

        if not wants_sync:
            dataset.ds_meta_data.dataset_doi = None
            dataset.ds_meta_data.deposition_id = None
            dataset.ds_meta_data.metadata_synced = True
            return

        if zenodo_service is None:
            raise DatasetMetadataUpdateError("Zenodo service is required to synchronize the dataset.")

        if is_synced:
            self._sync_metadata_in_zenodo_if_needed(dataset, zenodo_service)
            dataset.ds_meta_data.metadata_synced = True
            return

        self._publish_dataset_to_zenodo(dataset, zenodo_service)
        dataset.ds_meta_data.metadata_synced = True

    def update_metadata_from_request(self, dataset: DataSet, form_data, zenodo_service=None) -> dict:
        was_synchronized = bool(dataset.ds_meta_data.dataset_doi)
        sync_deferred = False
        try:
            dataset_type = self._get_requested_dataset_type(form_data, default=self._current_dataset_type(dataset))
            self._apply_metadata_from_form(dataset, form_data)
            self._replace_authors_from_form(dataset, form_data)
            try:
                self._transition_dataset_state_if_needed(dataset, dataset_type, zenodo_service)
            except ZenodoUnavailableError as exc:
                if was_synchronized and dataset_type in {"zenodo", "zenodo_anonymous"}:
                    dataset.ds_meta_data.metadata_synced = False
                    sync_deferred = True
                    logger.warning(
                        "Zenodo unavailable while updating metadata for dataset %s. Changes saved locally.",
                        getattr(dataset, "id", "unknown"),
                    )
                else:
                    raise DatasetMetadataUpdateError(str(exc))
            self.repository.session.commit()
            return {
                "metadata_synced": bool(dataset.ds_meta_data.metadata_synced),
                "sync_deferred": sync_deferred,
            }
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

            # Clean the HTML in the description field
            dsmetadata_data["description"] = self.sanitize_description(dsmetadata_data.get("description", ""))

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

    def resolve_download_formats(self, formats: Optional[List[str]]) -> List[str]:
        if formats is None:
            return list(self.AVAILABLE_DOWNLOAD_FORMATS)

        normalized_formats = [fmt.strip().lower() for fmt in formats if fmt and fmt.strip()]
        invalid_formats = sorted(set(normalized_formats) - set(self.AVAILABLE_DOWNLOAD_FORMATS))
        if invalid_formats:
            raise ValueError(f"Invalid format(s): {', '.join(invalid_formats)}")

        selected_formats = [fmt for fmt in self.AVAILABLE_DOWNLOAD_FORMATS if fmt in normalized_formats]
        if not selected_formats:
            raise ValueError("No download formats selected.")

        return selected_formats

    def zip_all_datasets(self, zip_path: str):
        self.zip_all_datasets_by_formats(zip_path, self.AVAILABLE_DOWNLOAD_FORMATS)

    def zip_all_datasets_by_formats(self, zip_path: str, formats: Optional[List[str]] = None):
        selected_formats = self.resolve_download_formats(formats)
        with ZipFile(zip_path, "w") as zipf:
            for user_dir in os.listdir("uploads"):
                user_path = os.path.join("uploads", user_dir)

                if os.path.isdir(user_path) and user_dir.startswith("user_"):
                    for dataset_dir in os.listdir(user_path):
                        dataset_path = os.path.join(user_path, dataset_dir)

                        if os.path.isdir(dataset_path) and dataset_dir.startswith("dataset_"):
                            dataset_id = int(dataset_dir.split("_")[1])

                            if self.is_synchronized(dataset_id):
                                for fmt in selected_formats:
                                    format_path = os.path.join(dataset_path, fmt)
                                    if not os.path.isdir(format_path):
                                        continue

                                    for subdir, _, files in os.walk(format_path):
                                        for file in files:
                                            full_path = os.path.join(subdir, file)
                                            relative_path = os.path.relpath(full_path, format_path)
                                            zipf.write(
                                                full_path,
                                                arcname=os.path.join(dataset_dir, fmt, relative_path),
                                            )

    def zip_from_storage(self, dataset, formats: Optional[List[str]] = None):
        dataset_base_path = os.path.join(
            os.getenv("WORKING_DIR", ""), "uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}"
        )
        selected_formats = self.resolve_download_formats(formats)

        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"dataset_{dataset.id}.zip")
        written_files = 0

        with zipfile.ZipFile(zip_path, "w") as zipf:
            for fmt in selected_formats:
                format_path = os.path.join(dataset_base_path, fmt)
                if not os.path.isdir(format_path):
                    continue

                for subdir, _, files in os.walk(format_path):
                    for filename in files:
                        file_path = os.path.join(subdir, filename)
                        arcname = os.path.join(fmt, os.path.relpath(file_path, format_path))
                        zipf.write(file_path, arcname=arcname)
                        written_files += 1

        if written_files == 0:
            current_app.logger.warning(f"[ZIP] No files found for selected formats in dataset {dataset.id}")
            return None

        return zip_path

    def delete_dataset(self, dataset: DataSet) -> None:
        """Delete a dataset and all its related files."""
        import shutil

        from app.features.hubfile.models import HubfileDownloadRecord, HubfileViewRecord

        dataset_id = dataset.id
        user_id = dataset.user_id

        try:
            dataset_dir = os.path.join("uploads", f"user_{user_id}", f"dataset_{dataset_id}")
            parent_dir = os.path.dirname(current_app.root_path)
            full_path = os.path.join(parent_dir, dataset_dir)

            if os.path.exists(full_path):
                shutil.rmtree(full_path, ignore_errors=True)
                current_app.logger.info(f"Deleted dataset directory for dataset {dataset_id}: {full_path}")

            # Delete view and download records for all hubfiles in this dataset
            hubfile_ids = [hf.id for hf in dataset.feature_models for hf in hf.hubfiles]
            if hubfile_ids:
                db.session.query(HubfileViewRecord).filter(HubfileViewRecord.file_id.in_(hubfile_ids)).delete(
                    synchronize_session=False
                )
                db.session.query(HubfileDownloadRecord).filter(HubfileDownloadRecord.file_id.in_(hubfile_ids)).delete(
                    synchronize_session=False
                )

            # Delete dataset view and download records
            db.session.query(DSViewRecord).filter(DSViewRecord.dataset_id == dataset_id).delete(
                synchronize_session=False
            )
            db.session.query(DSDownloadRecord).filter(DSDownloadRecord.dataset_id == dataset_id).delete(
                synchronize_session=False
            )

            # Delete all related feature models, hubfiles, and their records
            for feature_model in dataset.feature_models:
                for hubfile in feature_model.hubfiles:
                    db.session.delete(hubfile)
                db.session.delete(feature_model)

            db.session.delete(dataset)
            db.session.commit()
            current_app.logger.info(f"Dataset {dataset_id} deleted successfully")

        except SQLAlchemyError as exc:
            db.session.rollback()
            current_app.logger.exception(f"Database error deleting dataset {dataset_id}: {exc}")
            raise DatasetMetadataUpdateError(f"Could not delete dataset: {str(exc)}")
        except Exception as exc:
            db.session.rollback()
            current_app.logger.exception(f"Error deleting dataset {dataset_id}: {exc}")
            raise DatasetMetadataUpdateError(f"Could not delete dataset: {str(exc)}")


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

    def create_local_dataset(self, form, current_user, temp_root: str = None):
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

            # Create DSMetaData
            ds_meta = self.dsmetadata_service.create(
                title=title,
                description=description,
                publication_type=publication_type,
                publication_doi=publication_doi,
                tags=",".join(tags) if tags else "",
                metadata_synced=True,
            )
            self.logger.info(f"[LOCAL] DSMetaData created with ID: {ds_meta.id}")

            # Create DataSet
            dataset = self.dataset_service.create(commit=False, user_id=current_user.id, ds_meta_data_id=ds_meta.id)
            self.logger.info(f"[LOCAL] DataSet created with ID: {dataset.id}")

            # Create authors
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

            # Commit to DB
            db.session.commit()
            self.logger.info(f"[LOCAL] Dataset {dataset.id} committed to DB")

            ingest = UploadIngestService(self.logger)
            ingest_root = temp_root or current_user.temp_folder()
            stage_dir, staged_uvls = ingest.prepare_uvls(ingest_root)
            self.logger.info(f"[LOCAL] {len(staged_uvls)} UVLs listos en {stage_dir}")

            created_fms = self.feature_model_service.create_from_uvl_files(dataset, base_dir=stage_dir)
            dataset.feature_model_count = len(created_fms)
            db.session.commit()

            return dataset, ds_meta, created_fms

        except Exception as exc:
            db.session.rollback()
            self.logger.exception(f"[LOCAL ERROR] {exc}")
            raise
