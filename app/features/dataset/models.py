from datetime import datetime
from datetime import timedelta
from enum import Enum
from typing import List

import pytz
from flask import request
from flask_login import current_user
from sqlalchemy import Boolean
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import event

from app import db


class PublicationType(Enum):
    ANNOTATION_COLLECTION = "annotationcollection"
    BOOK = "book"
    BOOK_SECTION = "section"
    CONFERENCE_PAPER = "conferencepaper"
    DATA_MANAGEMENT_PLAN = "datamanagementplan"
    JOURNAL_ARTICLE = "article"
    PATENT = "patent"
    PREPRINT = "preprint"
    PROJECT_DELIVERABLE = "deliverable"
    PROJECT_MILESTONE = "milestone"
    PROPOSAL = "proposal"
    REPORT = "report"
    SOFTWARE_DOCUMENTATION = "softwaredocumentation"
    TAXONOMIC_TREATMENT = "taxonomictreatment"
    TECHNICAL_NOTE = "technicalnote"
    THESIS = "thesis"
    WORKING_PAPER = "workingpaper"
    OTHER = "other"


PUBLICATION_TYPE_LABELS = {
    PublicationType.ANNOTATION_COLLECTION: "Annotation Collection",
    PublicationType.BOOK: "Book",
    PublicationType.BOOK_SECTION: "Book Section",
    PublicationType.CONFERENCE_PAPER: "Conference Paper",
    PublicationType.DATA_MANAGEMENT_PLAN: "Data Management Plan",
    PublicationType.JOURNAL_ARTICLE: "Journal Article",
    PublicationType.PATENT: "Patent",
    PublicationType.PREPRINT: "Preprint",
    PublicationType.PROJECT_DELIVERABLE: "Project Deliverable",
    PublicationType.PROJECT_MILESTONE: "Project Milestone",
    PublicationType.PROPOSAL: "Proposal",
    PublicationType.REPORT: "Report",
    PublicationType.SOFTWARE_DOCUMENTATION: "Software Documentation",
    PublicationType.TAXONOMIC_TREATMENT: "Taxonomic Treatment",
    PublicationType.TECHNICAL_NOTE: "Technical Note",
    PublicationType.THESIS: "Thesis",
    PublicationType.WORKING_PAPER: "Working Paper",
    PublicationType.OTHER: "Other",
}


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    affiliation = db.Column(db.String(120))
    orcid = db.Column(db.String(19))
    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"))

    def to_dict(self):
        return {"name": self.name, "affiliation": self.affiliation, "orcid": self.orcid}


class DSMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number_of_models = db.Column(db.Integer)
    number_of_features = db.Column(db.Integer)

    def __repr__(self):
        return f"DSMetrics<models={self.number_of_models}, features={self.number_of_features}>"


class DSMetaData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deposition_id = db.Column(db.Integer)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    publication_type = db.Column(SQLAlchemyEnum(PublicationType))
    publication_doi = db.Column(db.String(120))
    dataset_doi = db.Column(db.String(120))
    # Zenodo's "conceptdoi": the permanent identifier of the whole version
    # lineage, which always resolves to its newest version. Every version of a
    # dataset shares it. Nullable: records published before this column existed,
    # and depositions for which Zenodo returns no conceptdoi, keep it empty.
    dataset_concept_doi = db.Column(db.String(120), index=True)
    # Provenance for records created through the API. The author credit an API
    # client sends is a claim about someone else, so the account whose key made
    # the claim is recorded here and surfaced in the Zenodo metadata. Ownership
    # can be transferred later, which is why user_id on the dataset is not a
    # substitute. NULL for everything created through the web interface.
    api_publisher_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    api_publisher = db.relationship("User", foreign_keys=[api_publisher_user_id])
    tags = db.Column(db.String(120))
    ds_metrics_id = db.Column(db.Integer, db.ForeignKey("ds_metrics.id"))
    ds_metrics = db.relationship("DSMetrics", uselist=False, backref="ds_meta_data", cascade="all, delete")
    authors = db.relationship("Author", backref="ds_meta_data", lazy=True, cascade="all, delete")
    dataset_anonymous = db.Column(Boolean, default=False)
    metadata_synced = db.Column(Boolean, nullable=False, default=True)


class DataSet(db.Model):
    __tablename__ = "datasets"

    # A dataset can only be deleted by its owner within this many days of creation.
    DELETE_WINDOW_DAYS = 30

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))

    ds_meta_data = db.relationship("DSMetaData", backref=db.backref("dataset", uselist=False))

    feature_models = db.relationship(
        "FeatureModel",
        back_populates="dataset",
        cascade="all, delete-orphan",
        lazy=True,
    )

    feature_model_count = db.Column(db.Integer, nullable=False, default=0)

    # Versioning / lineage: replacing a UVL on a published dataset creates a new
    # dataset (a new version) that points at the one it was derived from via
    # dataset_origin_id, so the history stays navigable (mirrors Zenodo's
    # concept-DOI version chain). Version 1 with origin=None is an original.
    dataset_version = db.Column(db.Integer, nullable=False, default=1)
    dataset_origin_id = db.Column(db.Integer, db.ForeignKey("datasets.id"), nullable=True)
    dataset_origin = db.relationship(
        "DataSet",
        remote_side=[id],
        backref=db.backref("dataset_versions", lazy=True),
    )

    def version_root(self) -> "DataSet":
        """Walk back up the lineage to the first version (origin=None)."""
        node = self
        seen = {node.id}
        while node.dataset_origin is not None and node.dataset_origin.id not in seen:
            node = node.dataset_origin
            seen.add(node.id)
        return node

    def all_versions(self) -> List["DataSet"]:
        """Return every version of this lineage, oldest first.

        The walk covers the whole tree hanging off the root, not just the first
        child of each node. Versioning a node that is already superseded is
        refused by the service layer, so new lineages stay linear, but rows
        created before that guard existed (or by direct DB writes) can have a
        node with several children. Following a single branch would silently
        drop versions, and every caller here answers a question that has to be
        exhaustive: which datasets move on a transfer, which rows get the
        concept DOI, and what the API reports as the full history.

        Ordering is deterministic: version number first, then id, which for a
        linear chain is exactly oldest to newest.
        """
        root = self.version_root()
        collected = {root.id: root}
        pending = [root]
        while pending:
            node = pending.pop()
            for child in node.dataset_versions:
                if child.id in collected:
                    continue
                collected[child.id] = child
                pending.append(child)
        return sorted(collected.values(), key=lambda version: (version.dataset_version or 1, version.id))

    def has_versions(self) -> bool:
        return self.dataset_origin_id is not None or bool(self.dataset_versions)

    def is_superseded(self) -> bool:
        """True when another dataset already claims this one as its origin."""
        return bool(self.dataset_versions)

    def latest_version(self) -> "DataSet":
        """Return the newest version of this dataset's lineage.

        Published versions win over unpublished ones. A version with no DOI is
        useless as an answer to "where do I find the newest record", and an
        unpublished row inside a published lineage only ever happens when
        something went wrong, so it must never shadow a real Zenodo record.
        """
        versions = self.all_versions()
        published = [version for version in versions if version.ds_meta_data.dataset_doi]
        return (published or versions)[-1]

    def is_latest_version(self) -> bool:
        return self.latest_version().id == self.id

    def get_concept_doi(self) -> str | None:
        """Concept DOI of the lineage, falling back to any sibling version.

        Records published before the concept DOI was stored keep a NULL column,
        so a version that does know it answers for the whole chain.
        """
        own = self.ds_meta_data.dataset_concept_doi
        if own:
            return own
        for version in self.all_versions():
            if version.ds_meta_data.dataset_concept_doi:
                return version.ds_meta_data.dataset_concept_doi
        return None

    def name(self) -> str:
        return self.ds_meta_data.title

    def description(self) -> str:
        return self.ds_meta_data.description

    def files(self) -> List[any]:
        return [file for fm in self.feature_models for file in fm.hubfiles]

    def is_synchronized(self) -> bool:
        from app.features.dataset.services import DataSetService

        return DataSetService.is_synchronized(self.id)

    def get_cleaned_publication_type(self) -> str | None:
        if not self.ds_meta_data.publication_type:
            return None
        return PUBLICATION_TYPE_LABELS.get(self.ds_meta_data.publication_type, None)

    def get_zenodo_url(self) -> str:
        return f"https://zenodo.org/record/{self.ds_meta_data.deposition_id}" if self.ds_meta_data.dataset_doi else None

    def count_feature_models(self) -> int:
        from app.features.dataset.services import DataSetService

        dataservice = DataSetService()
        return dataservice.count_feature_models(self.id)

    def get_files_count(self) -> int:
        return sum(len(fm.hubfiles) for fm in self.feature_models)

    def get_file_total_size(self) -> int:
        return sum(file.size for fm in self.feature_models for file in fm.hubfiles)

    def get_file_total_size_for_human(self) -> str:
        from app.features.dataset.services import SizeService

        return SizeService().get_human_readable_size(self.get_file_total_size())

    def get_uvlhub_doi(self) -> str:
        from app.features.dataset.services import DataSetService

        return DataSetService().get_uvlhub_doi(self)

    def get_uvlhub_doi_path(self) -> str:
        doi = self.get_uvlhub_doi()
        # If "/doi" is present, return the substring starting there.
        idx = doi.find("/doi")
        if idx != -1:
            return doi[idx:]
        return doi  # fallback: return the full value if no "/doi" segment

    def is_anonymous(self) -> bool:
        return self.ds_meta_data.dataset_anonymous

    def is_metadata_synchronized(self) -> bool:
        return bool(self.ds_meta_data.metadata_synced)

    def get_publication(self) -> str | None:
        if not self.ds_meta_data.publication_type:
            return None
        return self.ds_meta_data.publication_type.name.replace("_", " ").title()

    def to_dict(self):
        return {
            "title": self.ds_meta_data.title,
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_at_timestamp": int(self.created_at.timestamp()),
            "description": self.ds_meta_data.description,
            "authors": [author.to_dict() for author in self.ds_meta_data.authors],
            "publication_type": self.get_cleaned_publication_type(),
            "publication_doi": self.ds_meta_data.publication_doi,
            "dataset_doi": self.ds_meta_data.dataset_doi,
            "dataset_concept_doi": self.ds_meta_data.dataset_concept_doi,
            "dataset_version": self.dataset_version,
            "dataset_origin_id": self.dataset_origin_id,
            "metadata_synced": self.ds_meta_data.metadata_synced,
            "tags": self.ds_meta_data.tags.split(",") if self.ds_meta_data.tags else [],
            "url": self.get_uvlhub_doi(),
            "download": f'{request.host_url.rstrip("/")}/dataset/download/{self.id}',
            "zenodo": self.get_zenodo_url(),
            "files": [file.to_dict() for fm in self.feature_models for file in fm.hubfiles],
            "files_count": self.get_files_count(),
            "total_size_in_bytes": self.get_file_total_size(),
            "total_size_in_human_format": self.get_file_total_size_for_human(),
        }

    def get_zenodo_deposition(self) -> int:
        return self.ds_meta_data.deposition_id

    def get_zenodo_metadata(self):
        metadata = {
            "title": self.ds_meta_data.title,
            "description": self.ds_meta_data.description,
            "creators": [author.to_dict() for author in self.ds_meta_data.authors],
            "upload_type": "publication",
            "tags": self.ds_meta_data.tags.split(",") if self.ds_meta_data.tags else [],
        }

        if self.ds_meta_data.publication_type:
            metadata["publication_type"] = self.ds_meta_data.publication_type.value

        return metadata

    def is_mine(self):
        if not current_user.is_authenticated:
            return False
        return self.user_id == current_user.id

    def is_deletable(self) -> bool:
        """Whether this dataset is still within its deletion window.

        Datasets can only be deleted within DELETE_WINDOW_DAYS of creation,
        regardless of who is asking — ownership is checked separately.
        """
        created_at = self.created_at
        if created_at.tzinfo is None:
            created_at = pytz.utc.localize(created_at)
        return datetime.now(pytz.utc) - created_at <= timedelta(days=self.DELETE_WINDOW_DAYS)

    def can_be_deleted_by(self, user) -> bool:
        """Whether `user` is allowed to delete this dataset right now."""
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return self.user_id == user.id and self.is_deletable()

    def __repr__(self):
        return f"DataSet<{self.id}>"


class DatasetTransferStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class DatasetTransferRequest(db.Model):
    """An offer to hand a dataset lineage over to another account.

    Ownership never moves without the receiving account saying yes. A dataset
    carries a permanent Zenodo DOI and shows up in its owner's public listings,
    so pushing one onto somebody unannounced would let any key holder plant a
    record under a name that cannot refuse it. The offer sits here until the
    recipient accepts or declines, or the sender cancels.
    """

    __tablename__ = "dataset_transfer_request"

    id = db.Column(db.Integer, primary_key=True)
    # ON DELETE CASCADE: an offer is meaningless without the dataset it offers.
    # Without it the constraint blocked every deletion of a dataset that had
    # ever been offered, including the admin cleanup command, with a bare
    # foreign key error and no way to proceed.
    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    to_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    status = db.Column(
        SQLAlchemyEnum(DatasetTransferStatus),
        nullable=False,
        default=DatasetTransferStatus.PENDING,
    )
    message = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))
    resolved_at = db.Column(db.DateTime)

    dataset = db.relationship("DataSet", foreign_keys=[dataset_id])
    from_user = db.relationship("User", foreign_keys=[from_user_id])
    to_user = db.relationship("User", foreign_keys=[to_user_id])

    def is_pending(self) -> bool:
        return self.status == DatasetTransferStatus.PENDING

    def to_dict(self) -> dict:
        return {
            "transfer_id": self.id,
            "dataset_id": self.dataset_id,
            "from_user_id": self.from_user_id,
            "to_user_id": self.to_user_id,
            "status": self.status.value if self.status else None,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

    def __repr__(self):
        return f"DatasetTransferRequest<{self.id} dataset={self.dataset_id} status={self.status}>"


class DSDownloadRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id"))
    download_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))
    download_cookie = db.Column(db.String(36), nullable=False)

    def __repr__(self):
        return (
            f"<Download id={self.id} "
            f"dataset_id={self.dataset_id} "
            f"date={self.download_date} "
            f"cookie={self.download_cookie}>"
        )


class DSViewRecord(db.Model):
    __tablename__ = "ds_view_record"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id"), nullable=False)

    view_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))

    view_cookie = db.Column(db.String(36), nullable=False)


class DOIMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_doi_old = db.Column(db.String(120))
    dataset_doi_new = db.Column(db.String(120))


# Evento: Crear automáticamente ds_metrics cuando se crea un nuevo dataset
@event.listens_for(DSMetaData, "after_insert")
def create_ds_metrics_on_metadata_create(mapper, connection, target):
    """Crea automáticamente DSMetrics cuando se crea DSMetaData sin métricas"""
    if target.ds_metrics is None:
        metrics = DSMetrics(number_of_features=0, number_of_models=0)
        db.session.add(metrics)
        target.ds_metrics = metrics
