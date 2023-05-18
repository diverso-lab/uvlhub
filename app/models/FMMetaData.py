from app import db


class FMMetaData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    authors = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(120), nullable=False)
    publication_type = db.Column(db.String(120))
    publication_doi = db.Column(db.String(120))
    dataset_doi = db.Column(db.String(120))
    tags = db.Column(db.String(120))
    uvl_version = db.Column(db.String(120))
    fm_metrics_id = db.Column(db.Integer, db.ForeignKey('fm_metrics.id'))
    fm_metrics = db.relationship('FMMetrics', uselist=False, backref='fm_meta_data')

    def __repr__(self):
        return f'FMMetaData<{self.title}>'
