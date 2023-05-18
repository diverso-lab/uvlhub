from app import db


class FeatureModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_set_id = db.Column(db.Integer, db.ForeignKey('data_set.id'), nullable=False)
    fm_meta_data_id = db.Column(db.Integer, db.ForeignKey('fm_meta_data.id'))
    fm_meta_data = db.relationship('FMMetaData', uselist=False, backref='feature_model')

    def __repr__(self):
        return f'FeatureModel<{self.id}>'
