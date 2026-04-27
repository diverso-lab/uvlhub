from app import db


class Statistics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datasets_counter = db.Column(db.Integer, default=0)
    feature_models_counter = db.Column(db.Integer, default=0)
    datasets_viewed = db.Column(db.Integer, default=0)
    feature_models_viewed = db.Column(db.Integer, default=0)
    datasets_downloaded = db.Column(db.Integer, default=0)
    feature_models_downloaded = db.Column(db.Integer, default=0)

    def __repr__(self):
        return (
            f"Statistics<id={self.id}, datasets_counter={self.datasets_counter}, "
            f"feature_models_counter={self.feature_models_counter}, "
            f"datasets_viewed={self.datasets_viewed}, "
            f"feature_models_viewed={self.feature_models_viewed}, "
            f"datasets_downloaded={self.datasets_downloaded}, "
            f"feature_models_downloaded={self.feature_models_downloaded}>"
        )
