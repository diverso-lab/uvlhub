from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.features.auth.repositories import UserRepository
from app.features.dataset.models import PublicationType
from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository
from app.features.rating.models import DatasetRating
from app.features.rating.repositories import DatasetRatingRepository
from app.features.rating.services import RatingService

pytestmark = pytest.mark.service


def _user(email):
    return UserRepository().create(email=email, password="pw-123456")


def _dataset(owner, doi="10.5072/zenodo.1", version=1, origin_id=None):
    meta = DSMetaDataRepository().create(
        title="t", description="d", publication_type=PublicationType.BOOK, dataset_doi=doi
    )
    return DataSetRepository().create(
        user_id=owner.id, ds_meta_data_id=meta.id, dataset_version=version, dataset_origin_id=origin_id
    )


@pytest.fixture(autouse=True)
def _no_reindex():
    with patch.object(RatingService, "_reindex_lineage"):
        yield


def test_set_vote_creates_a_like_and_reports_it_back(test_app, clean_database):
    owner, voter = _user("o@example.com"), _user("v@example.com")
    dataset = _dataset(owner)

    state = RatingService().set_vote(dataset, voter, "like")

    assert state == {"likes": 1, "dislikes": 0, "my_vote": "like"}
    assert DatasetRatingRepository().count() == 1


def test_clicking_the_same_vote_again_removes_it(test_app, clean_database):
    owner, voter = _user("o@example.com"), _user("v@example.com")
    dataset = _dataset(owner)
    service = RatingService()

    service.set_vote(dataset, voter, "like")
    state = service.set_vote(dataset, voter, "none")

    assert state == {"likes": 0, "dislikes": 0, "my_vote": None}
    assert DatasetRatingRepository().count() == 0


def test_switching_from_like_to_dislike_keeps_a_single_row(test_app, clean_database):
    owner, voter = _user("o@example.com"), _user("v@example.com")
    dataset = _dataset(owner)
    service = RatingService()

    service.set_vote(dataset, voter, "like")
    state = service.set_vote(dataset, voter, "dislike")

    assert state == {"likes": 0, "dislikes": 1, "my_vote": "dislike"}
    assert DatasetRatingRepository().count() == 1


def test_owner_can_vote_their_own_dataset(test_app, clean_database):
    owner = _user("o@example.com")
    dataset = _dataset(owner)

    state = RatingService().set_vote(dataset, owner, "like")

    assert state["likes"] == 1


def test_a_vote_counts_for_every_version_of_the_lineage(test_app, clean_database):
    owner, voter = _user("o@example.com"), _user("v@example.com")
    v1 = _dataset(owner, doi="10.5072/zenodo.10.1", version=1)
    v2 = _dataset(owner, doi="10.5072/zenodo.10.2", version=2, origin_id=v1.id)
    service = RatingService()

    service.set_vote(v2, voter, "like")  # vote from the v2 page

    # both version pages show the same aggregate, and the row is on the root
    assert service.get_state(v1, voter)["likes"] == 1
    assert service.get_state(v2, voter)["my_vote"] == "like"
    assert DatasetRating.query.one().dataset_id == v1.id


def test_rating_counts_returns_just_the_lineage_totals(test_app, clean_database):
    owner, voter = _user("o@example.com"), _user("v@example.com")
    v1 = _dataset(owner, doi="10.5072/zenodo.20.1", version=1)
    v2 = _dataset(owner, doi="10.5072/zenodo.20.2", version=2, origin_id=v1.id)
    RatingService().set_vote(v1, voter, "like")

    assert RatingService().rating_counts(v2) == {"likes": 1, "dislikes": 0}


def test_get_state_without_a_user_omits_my_vote(test_app, clean_database):
    owner, voter = _user("o@example.com"), _user("v@example.com")
    dataset = _dataset(owner)
    RatingService().set_vote(dataset, voter, "dislike")

    anon = SimpleNamespace(is_authenticated=False)
    state = RatingService().get_state(dataset, anon)

    assert state == {"likes": 0, "dislikes": 1, "my_vote": None}


def test_set_vote_rejects_an_unknown_value(test_app, clean_database):
    owner, voter = _user("o@example.com"), _user("v@example.com")
    dataset = _dataset(owner)

    with pytest.raises(ValueError):
        RatingService().set_vote(dataset, voter, "meh")


def test_set_vote_triggers_a_reindex_of_the_lineage(test_app, clean_database):
    owner, voter = _user("o@example.com"), _user("v@example.com")
    dataset = _dataset(owner)

    with patch.object(RatingService, "_reindex_lineage") as reindex:
        RatingService().set_vote(dataset, voter, "like")

    reindex.assert_called_once()
