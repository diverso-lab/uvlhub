from app import db


class MetaData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    authors = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(120), nullable=False)
    publication_type = db.Column(db.String(120))
    publication_doi = db.Column(db.String(120))
    dataset_doi = db.Column(db.String(120))
    tags = db.Column(db.String(120))
    ds_metrics_id = db.Column(db.Integer, db.ForeignKey('ds_metrics.id'))
    ds_metrics = db.relationship('DSMetrics', uselist=False, backref='meta_data')

    def __repr__(self):
        return f'MetaData<{self.title}>'
