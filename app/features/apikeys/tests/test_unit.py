import pytest

from app.features.apikeys.models import ApiKey

pytestmark = pytest.mark.unit


def test_scope_list_splits_comma_separated_scopes():
    assert ApiKey(scopes="read_dataset,write_dataset").scope_list == ["read_dataset", "write_dataset"]


def test_scope_list_is_empty_for_a_blank_value():
    assert ApiKey(scopes="").scope_list == []
