from datetime import datetime
from enum import Enum

from flask import request
from sqlalchemy import Enum as SQLAlchemyEnum

from app import db


class PublicationType(Enum):
    NONE = 'none'
    ANNOTATION_COLLECTION = 'annotationcollection'
    BOOK = 'book'
    BOOK_SECTION = 'section'
    CONFERENCE_PAPER = 'conferencepaper'
    DATA_MANAGEMENT_PLAN = 'datamanagementplan'
    JOURNAL_ARTICLE = 'article'
    PATENT = 'patent'
    PREPRINT = 'preprint'
    PROJECT_DELIVERABLE = 'deliverable'
    PROJECT_MILESTONE = 'milestone'
    PROPOSAL = 'proposal'
    REPORT = 'report'
    SOFTWARE_DOCUMENTATION = 'softwaredocumentation'
    TAXONOMIC_TREATMENT = 'taxonomictreatment'
    TECHNICAL_NOTE = 'technicalnote'
    THESIS = 'thesis'
    WORKING_PAPER = 'workingpaper'
    OTHER = 'other'


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    affiliation = db.Column(db.String(120))
    orcid = db.Column(db.String(120))
    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey('ds_meta_data.id'))
    fm_meta_data_id = db.Column(db.Integer, db.ForeignKey('fm_meta_data.id'))

    def to_dict(self):
        return {
            'name': self.name,
            'affiliation': self.affiliation,
            'orcid': self.orcid
        }


class DSMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number_of_models = db.Column(db.String(120))
    number_of_features = db.Column(db.String(120))

    def __repr__(self):
        return f'DSMetrics<models={self.number_of_models}, features={self.number_of_features}>'


class DSMetaData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deposition_id = db.Column(db.Integer)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    publication_type = db.Column(SQLAlchemyEnum(PublicationType), nullable=False)
    publication_doi = db.Column(db.String(120))
    dataset_doi = db.Column(db.String(120))
    tags = db.Column(db.String(120))
    ds_metrics_id = db.Column(db.Integer, db.ForeignKey('ds_metrics.id'))
    ds_metrics = db.relationship('DSMetrics', uselist=False, backref='ds_meta_data', cascade="all, delete")
    authors = db.relationship('Author', backref='ds_meta_data', lazy=True, cascade="all, delete")


class DataSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey('ds_meta_data.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    ds_meta_data = db.relationship('DSMetaData', backref=db.backref('data_set', uselist=False))
    feature_models = db.relationship('FeatureModel', backref='data_set', lazy=True, cascade="all, delete")

    def name(self):
        return self.ds_meta_data.title

    def files(self):
        return [file for fm in self.feature_models for file in fm.files]

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def get_cleaned_publication_type(self):
        return self.ds_meta_data.publication_type.name.replace('_', ' ').title()

    def get_zenodo_url(self):
        return f'https://zenodo.org/record/{self.ds_meta_data.deposition_id}' if self.ds_meta_data.dataset_doi else None

    def get_files_count(self):
        return sum(len(fm.files) for fm in self.feature_models)

    def get_file_total_size(self):
        return sum(file.size for fm in self.feature_models for file in fm.files)

    def get_file_total_size_for_human(self):
        from app.modules.dataset.services import SizeService
        return SizeService().get_human_readable_size(self.get_file_total_size())

    def get_uvlhub_doi(self):
        from app.modules.dataset.services import DataSetService
        return DataSetService().get_uvlhub_doi(self)

    def to_dict(self):
        return {
            'title': self.ds_meta_data.title,
            'id': self.id,
            'created_at': self.created_at,
            'created_at_timestamp': int(self.created_at.timestamp()),
            'description': self.ds_meta_data.description,
            'authors': [author.to_dict() for author in self.ds_meta_data.authors],
            'publication_type': self.get_cleaned_publication_type(),
            'publication_doi': self.ds_meta_data.publication_doi,
            'dataset_doi': self.ds_meta_data.dataset_doi,
            'tags': self.ds_meta_data.tags.split(",") if self.ds_meta_data.tags else [],
            'url': self.get_uvlhub_doi(),
            'download': f'{request.host_url.rstrip("/")}/dataset/download/{self.id}',
            'zenodo': self.get_zenodo_url(),
            'files': [file.to_dict() for fm in self.feature_models for file in fm.files],
            'files_count': self.get_files_count(),
            'total_size_in_bytes': self.get_file_total_size(),
            'total_size_in_human_format': self.get_file_total_size_for_human(),
        }

    def __repr__(self):
        return f'DataSet<{self.id}>'


class DSDownloadRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('data_set.id'))
    download_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    download_cookie = db.Column(db.String(36), nullable=False)  # Assuming UUID4 strings

    def __repr__(self):
        return (
            f'<Download id={self.id} '
            f'dataset_id={self.dataset_id} '
            f'date={self.download_date} '
            f'cookie={self.download_cookie}>'
        )


class DSViewRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('data_set.id'))
    view_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    view_cookie = db.Column(db.String(36), nullable=False)  # Assuming UUID4 strings

    def __repr__(self):
        return f'<View id={self.id} dataset_id={self.dataset_id} date={self.view_date} cookie={self.view_cookie}>'


class DOIMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_doi_old = db.Column(db.String(120))
    dataset_doi_new = db.Column(db.String(120))
