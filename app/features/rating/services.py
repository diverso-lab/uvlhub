import logging

from splent_framework.services.BaseService import BaseService

from app.features.rating.repositories import DatasetRatingRepository

logger = logging.getLogger(__name__)

VOTES = {"like", "dislike", "none"}


class RatingService(BaseService):
    def __init__(self):
        super().__init__(DatasetRatingRepository())

    @staticmethod
    def _root_id(dataset) -> int:
        return dataset.version_root().id

    def rating_counts(self, dataset) -> dict:
        """Just the like/dislike counts for a dataset's lineage (no user vote).
        Exposed to templates as the `dataset_rating_counts` global."""
        return self.repository.counts_for(self._root_id(dataset))

    def get_state(self, dataset, user) -> dict:
        """Like/dislike counts for a dataset's lineage plus this user's own vote
        ("like" | "dislike" | None)."""
        root_id = self._root_id(dataset)
        state = self.repository.counts_for(root_id)
        state["my_vote"] = None
        if user is not None and getattr(user, "is_authenticated", False):
            vote = self.repository.get_vote(root_id, user.id)
            if vote is not None:
                state["my_vote"] = "like" if vote.is_like else "dislike"
        return state

    def set_vote(self, dataset, user, vote: str) -> dict:
        """Apply the user's vote ("like"/"dislike" to set it, "none" to clear it)
        and return the fresh state. Re-indexes the lineage so search stays sorted."""
        if vote not in VOTES:
            raise ValueError(f"vote must be one of {sorted(VOTES)}")

        root = dataset.version_root()
        existing = self.repository.get_vote(root.id, user.id)

        if vote == "none":
            if existing is not None:
                self.repository.delete(existing.id)
        else:
            is_like = vote == "like"
            if existing is None:
                self.repository.create(dataset_id=root.id, user_id=user.id, is_like=is_like)
            elif existing.is_like != is_like:
                self.repository.update(existing.id, is_like=is_like)

        self._reindex_lineage(root)
        return self.get_state(dataset, user)

    @staticmethod
    def _reindex_lineage(root) -> None:
        """Refresh the search document of every version so the like counts used
        for the 'most liked' sort stay current. Best effort: a search outage
        must not fail the vote."""
        try:
            from app.features.elasticsearch.utils import index_dataset

            for version in root.all_versions():
                index_dataset(version)
        except Exception as exc:  # pragma: no cover - depends on ES availability
            logger.warning("Could not re-index lineage %s after a rating change: %s", root.id, exc)
