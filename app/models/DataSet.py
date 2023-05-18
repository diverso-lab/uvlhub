from app import db


class DataSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    files = db.relationship('File', backref='data_set', lazy=True)
    meta_data_id = db.Column(db.Integer, db.ForeignKey('meta_data.id'), nullable=False)
    feature_models = db.relationship('FeatureModel', backref='data_set', lazy=True)

    def __repr__(self):
        return f'DataSet<{self.id}>'
