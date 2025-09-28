from app import db


class FeatureModel(db.Model):
    __tablename__ = "feature_model"

    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id"), nullable=False, index=True)

    # Relaciones
    hubfiles = db.relationship("Hubfile", back_populates="feature_model", lazy=True, cascade="all, delete")
    dataset = db.relationship("DataSet", back_populates="feature_models")

    def __repr__(self):
        return f"FeatureModel<{self.id}>"
