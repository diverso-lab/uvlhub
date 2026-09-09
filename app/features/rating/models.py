from datetime import datetime

import pytz

from app import db


class DatasetRating(db.Model):
    """A single like / dislike vote by a user on a dataset.

    The vote is stored against the *lineage root* dataset (the first version),
    so it counts for every version of the same dataset and does not fragment
    when a new version is published.
    """

    __tablename__ = "dataset_rating"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    is_like = db.Column(db.Boolean, nullable=False)  # True = like, False = dislike
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(pytz.utc),
        onupdate=lambda: datetime.now(pytz.utc),
    )

    __table_args__ = (db.UniqueConstraint("user_id", "dataset_id", name="uq_rating_user_dataset"),)

    def __repr__(self):
        return f"<DatasetRating user={self.user_id} dataset={self.dataset_id} like={self.is_like}>"
