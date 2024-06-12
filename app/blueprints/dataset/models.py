from datetime import datetime

from flask import request

from app import db
from enum import Enum
from sqlalchemy import Enum as SQLAlchemyEnum

import os


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
        return get_human_readable_size(self.get_file_total_size())

    def get_uvlhub_doi(self):
        domain = os.getenv('DOMAIN', 'localhost')
        return f'http://{domain}/doi/{self.ds_meta_data.dataset_doi}'

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
            'url': f'{request.host_url.rstrip("/")}/dataset/view/{self.id}',
            'download': f'{request.host_url.rstrip("/")}/dataset/download/{self.id}',
            'zenodo': self.get_zenodo_url(),
            'files': [file.to_dict() for fm in self.feature_models for file in fm.files],
            'files_count': self.get_files_count(),
            'total_size_in_bytes': self.get_file_total_size(),
            'total_size_in_human_format': self.get_file_total_size_for_human(),
        }

    def __repr__(self):
        return f'DataSet<{self.id}>'


class FeatureModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_set_id = db.Column(db.Integer, db.ForeignKey('data_set.id'), nullable=False)
    fm_meta_data_id = db.Column(db.Integer, db.ForeignKey('fm_meta_data.id'))
    files = db.relationship('File', backref='feature_model', lazy=True, cascade="all, delete")
    fm_meta_data = db.relationship('FMMetaData', uselist=False, backref='feature_model', cascade="all, delete")

    def __repr__(self):
        return f'FeatureModel<{self.id}>'


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    checksum = db.Column(db.String(120), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    feature_model_id = db.Column(db.Integer, db.ForeignKey('feature_model.id'), nullable=False)

    def get_formatted_size(self):
        return get_human_readable_size(self.size)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'checksum': self.checksum,
            'size_in_bytes': self.size,
            'size_in_human_format': get_human_readable_size(self.size),
            'url': f'{request.host_url.rstrip("/")}/file/download/{self.id}',
        }

    def __repr__(self):
        return f'File<{self.id}>'


class FMMetaData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uvl_filename = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    publication_type = db.Column(SQLAlchemyEnum(PublicationType), nullable=False)
    publication_doi = db.Column(db.String(120))
    tags = db.Column(db.String(120))
    uvl_version = db.Column(db.String(120))
    fm_metrics_id = db.Column(db.Integer, db.ForeignKey('fm_metrics.id'))
    fm_metrics = db.relationship('FMMetrics', uselist=False, backref='fm_meta_data')
    authors = db.relationship('Author', backref='fm_metadata', lazy=True, cascade="all, delete",
                              foreign_keys=[Author.fm_meta_data_id])

    def __repr__(self):
        return f'FMMetaData<{self.title}'


class FMMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solver = db.Column(db.Text)
    not_solver = db.Column(db.Text)

    def __repr__(self):
        return f'FMMetrics<solver={self.solver}, not_solver={self.not_solver}>'


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


class FileViewRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    view_date = db.Column(db.DateTime, default=datetime.utcnow)
    view_cookie = db.Column(db.String(36))

    def __repr__(self):
        return '<FileViewRecord {}>'.format(self.id)


class FileDownloadRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'))
    download_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    download_cookie = db.Column(db.String(36), nullable=False)  # Assuming UUID4 strings

    def __repr__(self):
        return (
            f'<FileDownload id={self.id} '
            f'file_id={self.file_id} '
            f'date={self.download_date} '
            f'cookie={self.download_cookie}>'
        )


def get_human_readable_size(size):
    if size < 1024:
        return f'{size} bytes'
    elif size < 1024 ** 2:
        return f'{round(size / 1024, 2)} KB'
    elif size < 1024 ** 3:
        return f'{round(size / (1024 ** 2), 2)} MB'
    else:
        return f'{round(size / (1024 ** 3), 2)} GB'
