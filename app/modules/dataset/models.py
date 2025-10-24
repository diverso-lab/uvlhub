from datetime import datetime
from enum import Enum
from typing import List

import pytz
from flask import request
from flask_login import current_user
from sqlalchemy import Boolean
from sqlalchemy import Enum as SQLAlchemyEnum

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
    tags = db.Column(db.String(120))
    ds_metrics_id = db.Column(db.Integer, db.ForeignKey("ds_metrics.id"))
    ds_metrics = db.relationship("DSMetrics", uselist=False, backref="ds_meta_data", cascade="all, delete")
    authors = db.relationship("Author", backref="ds_meta_data", lazy=True, cascade="all, delete")
    dataset_anonymous = db.Column(Boolean, default=False)


class DataSet(db.Model):
    __tablename__ = "datasets"
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

    def name(self) -> str:
        return self.ds_meta_data.title

    def description(self) -> str:
        return self.ds_meta_data.description

    def files(self) -> List[any]:
        return [file for fm in self.feature_models for file in fm.hubfiles]

    def is_synchronized(self) -> bool:
        from app.modules.dataset.services import DataSetService

        return DataSetService.is_synchronized(self.id)

    def get_cleaned_publication_type(self) -> str | None:
        if not self.ds_meta_data.publication_type:
            return None
        return PUBLICATION_TYPE_LABELS.get(self.ds_meta_data.publication_type, None)

    def get_zenodo_url(self) -> str:
        return f"https://zenodo.org/record/{self.ds_meta_data.deposition_id}" if self.ds_meta_data.dataset_doi else None

    def count_feature_models(self) -> int:
        from app.modules.dataset.services import DataSetService

        dataservice = DataSetService()
        return dataservice.count_feature_models(self.id)

    def get_files_count(self) -> int:
        return sum(len(fm.hubfiles) for fm in self.feature_models)

    def get_file_total_size(self) -> int:
        return sum(file.size for fm in self.feature_models for file in fm.hubfiles)

    def get_file_total_size_for_human(self) -> str:
        from app.modules.dataset.services import SizeService

        return SizeService().get_human_readable_size(self.get_file_total_size())

    def get_uvlhub_doi(self) -> str:
        from app.modules.dataset.services import DataSetService

        return DataSetService().get_uvlhub_doi(self)

    def get_uvlhub_doi_path(self) -> str:
        doi = self.get_uvlhub_doi()
        # Si encuentra "/doi", devolver desde ahí
        idx = doi.find("/doi")
        if idx != -1:
            return doi[idx:]
        return doi  # fallback: devuelve completo si no hay /doi

    def is_anonymous(self) -> bool:
        return self.ds_meta_data.dataset_anonymous

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

    def __repr__(self):
        return f"DataSet<{self.id}>"


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
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id"))
    view_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))
    view_cookie = db.Column(db.String(36), nullable=False)

    def __repr__(self):
        return f"<View id={self.id} dataset_id={self.dataset_id} date={self.view_date} cookie={self.view_cookie}>"


class DOIMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_doi_old = db.Column(db.String(120))
    dataset_doi_new = db.Column(db.String(120))
