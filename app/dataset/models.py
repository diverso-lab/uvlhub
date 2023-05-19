from app import db


class DataSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    files = db.relationship('File', backref='data_set', lazy=True)
    meta_data_id = db.Column(db.Integer, db.ForeignKey('meta_data.id'), nullable=False)
    feature_models = db.relationship('FeatureModel', backref='data_set', lazy=True)

    def __repr__(self):
        return f'DataSet<{self.id}>'


class DSMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number_of_models = db.Column(db.String(120))
    number_of_features = db.Column(db.String(120))

    def __repr__(self):
        return f'DSMetrics<models={self.number_of_models}, features={self.number_of_features}>'


class FeatureModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_set_id = db.Column(db.Integer, db.ForeignKey('data_set.id'), nullable=False)
    fm_meta_data_id = db.Column(db.Integer, db.ForeignKey('fm_meta_data.id'))
    fm_meta_data = db.relationship('FMMetaData', uselist=False, backref='feature_model')

    def __repr__(self):
        return f'FeatureModel<{self.id}>'


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    checksum = db.Column(db.String(120), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    data_set_id = db.Column(db.Integer, db.ForeignKey('data_set.id'), nullable=False)

    def __repr__(self):
        return f'File<{self.name}>'


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
        return f'FMMetaData<{self.title}'


class FMMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solver = db.Column(db.Text)
    not_solver = db.Column(db.Text)

    def __repr__(self):
        return f'FMMetrics<solver={self.solver}, not_solver={self.not_solver}>'


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
