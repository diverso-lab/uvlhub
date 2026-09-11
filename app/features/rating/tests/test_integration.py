from unittest.mock import patch

import pytest

from app.features.auth.repositories import UserRepository
from app.features.dataset.models import PublicationType
from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository
from app.features.profile.repositories import UserProfileRepository
from app.features.rating.services import RatingService

pytestmark = pytest.mark.integration


def _user_with_profile(email, password="pw-123456"):
    user = UserRepository().create(email=email, password=password)
    UserProfileRepository().create(user_id=user.id, name="T", surname="U")
    return user


@pytest.fixture(autouse=True)
def _no_reindex():
    with patch.object(RatingService, "_reindex_lineage"):
        yield


def _voter(email="voter@example.com", password="pw-123456"):
    return _user_with_profile(email, password)


def _login(test_client, email="voter@example.com", password="pw-123456"):
    test_client.post("/login", data=dict(email=email, password=password), follow_redirects=True)


def _owner():
    return _user_with_profile("owner@example.com")


def _published_dataset(doi="10.5072/zenodo.rating.1"):
    meta = DSMetaDataRepository().create(
        title="Rated", description="d", publication_type=PublicationType.BOOK, dataset_doi=doi, tags=""
    )
    return DataSetRepository().create(user_id=_owner().id, ds_meta_data_id=meta.id)


def _draft_dataset():
    meta = DSMetaDataRepository().create(title="Draft", description="d", publication_type=PublicationType.BOOK, tags="")
    return DataSetRepository().create(user_id=_owner().id, ds_meta_data_id=meta.id)


def test_posting_a_vote_requires_authentication(test_client, clean_database):
    dataset = _published_dataset()
    test_client.get("/logout", follow_redirects=True)

    response = test_client.post(f"/datasets/{dataset.id}/rating", json={"vote": "like"})

    assert response.status_code in (302, 401)


def test_full_vote_cycle_over_http(test_client, clean_database):
    dataset = _published_dataset()
    _voter()
    _login(test_client)

    liked = test_client.post(f"/datasets/{dataset.id}/rating", json={"vote": "like"}).get_json()
    assert liked == {"likes": 1, "dislikes": 0, "my_vote": "like"}

    switched = test_client.post(f"/datasets/{dataset.id}/rating", json={"vote": "dislike"}).get_json()
    assert switched == {"likes": 0, "dislikes": 1, "my_vote": "dislike"}

    cleared = test_client.post(f"/datasets/{dataset.id}/rating", json={"vote": "none"}).get_json()
    assert cleared == {"likes": 0, "dislikes": 0, "my_vote": None}

    test_client.get("/logout", follow_redirects=True)


def test_get_rating_is_public_and_reports_counts(test_client, clean_database):
    dataset = _published_dataset()
    _voter()
    _login(test_client)
    test_client.post(f"/datasets/{dataset.id}/rating", json={"vote": "like"})
    test_client.get("/logout", follow_redirects=True)

    response = test_client.get(f"/datasets/{dataset.id}/rating")

    assert response.status_code == 200
    assert response.get_json() == {"likes": 1, "dislikes": 0, "my_vote": None}


def test_a_draft_dataset_cannot_be_rated(test_client, clean_database):
    dataset = _draft_dataset()
    _voter()
    _login(test_client)

    response = test_client.post(f"/datasets/{dataset.id}/rating", json={"vote": "like"})

    assert response.status_code == 403
    test_client.get("/logout", follow_redirects=True)


def test_an_unknown_vote_value_is_rejected(test_client, clean_database):
    dataset = _published_dataset()
    _voter()
    _login(test_client)

    response = test_client.post(f"/datasets/{dataset.id}/rating", json={"vote": "sideways"})

    assert response.status_code == 400
    test_client.get("/logout", follow_redirects=True)


def test_view_page_embeds_the_rating_widget(test_client, clean_database):
    dataset = _published_dataset(doi="10.5072/zenodo.rating.widget")

    response = test_client.get(f"/doi/{dataset.ds_meta_data.dataset_doi}/")

    assert response.status_code == 200
    body = response.data.decode()
    assert 'id="dataset-rating"' in body
    assert f'data-dataset-id="{dataset.id}"' in body


def test_home_page_shows_the_rating_counters(test_client, clean_database):
    dataset = _published_dataset(doi="10.5072/zenodo.rating.home")
    voter = _voter()
    RatingService().set_vote(dataset, voter, "like")

    response = test_client.get("/")

    assert response.status_code == 200
    body = response.data.decode()
    assert "Community rating" in body
    assert "ki-like" in body
