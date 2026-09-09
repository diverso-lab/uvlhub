from splent_framework.repositories.BaseRepository import BaseRepository
from sqlalchemy import func

from app.features.rating.models import DatasetRating


class DatasetRatingRepository(BaseRepository):
    def __init__(self):
        super().__init__(DatasetRating)

    def get_vote(self, dataset_id: int, user_id: int) -> DatasetRating | None:
        return self.model.query.filter_by(dataset_id=dataset_id, user_id=user_id).first()

    def counts_for(self, dataset_id: int) -> dict:
        rows = (
            self.session.query(DatasetRating.is_like, func.count())
            .filter(DatasetRating.dataset_id == dataset_id)
            .group_by(DatasetRating.is_like)
            .all()
        )
        by_flag = dict(rows)
        return {"likes": int(by_flag.get(True, 0)), "dislikes": int(by_flag.get(False, 0))}

    def counts_for_many(self, dataset_ids: list[int]) -> dict[int, dict]:
        result = {ds_id: {"likes": 0, "dislikes": 0} for ds_id in dataset_ids}
        if not dataset_ids:
            return result
        rows = (
            self.session.query(DatasetRating.dataset_id, DatasetRating.is_like, func.count())
            .filter(DatasetRating.dataset_id.in_(dataset_ids))
            .group_by(DatasetRating.dataset_id, DatasetRating.is_like)
            .all()
        )
        for dataset_id, is_like, count in rows:
            result[dataset_id]["likes" if is_like else "dislikes"] = int(count)
        return result
