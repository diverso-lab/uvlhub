from datetime import datetime

from app import db
from enum import Enum
from sqlalchemy import Enum as SQLAlchemyEnum


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
    ds_metrics = db.relationship('DSMetrics', uselist=False, backref='ds_meta_data')
    authors = db.relationship('Author', backref='ds_meta_data', lazy=True)


class DataSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey('ds_meta_data.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ds_meta_data = db.relationship('DSMetaData', backref='data_set', lazy=True)
    feature_models = db.relationship('FeatureModel', backref='data_set', lazy=True)

    def __repr__(self):
        return f'DataSet<{self.id}>'


class FeatureModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_set_id = db.Column(db.Integer, db.ForeignKey('data_set.id'), nullable=False)
    fm_meta_data_id = db.Column(db.Integer, db.ForeignKey('fm_meta_data.id'))
    files = db.relationship('File', backref='feature_model', lazy=True)
    fm_meta_data = db.relationship('FMMetaData', uselist=False, backref='feature_model')

    def __repr__(self):
        return f'FeatureModel<{self.id}>'


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    checksum = db.Column(db.String(120), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    feature_model_id = db.Column(db.Integer, db.ForeignKey('feature_model.id'), nullable=False)

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
    authors = db.relationship('Author', backref='fm_metadata', lazy=True, foreign_keys=[Author.fm_meta_data_id])

    def __repr__(self):
        return f'FMMetaData<{self.title}'


class FMMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solver = db.Column(db.Text)
    not_solver = db.Column(db.Text)

    def __repr__(self):
        return f'FMMetrics<solver={self.solver}, not_solver={self.not_solver}>'
