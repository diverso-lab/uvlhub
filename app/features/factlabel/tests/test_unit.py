import pytest

from app.features.factlabel.services import FactlabelNotReady, FactlabelService, InvalidFactlabel

pytestmark = pytest.mark.unit


class _FakeFactLabel:
    def __init__(self, factlabel_json):
        self.factlabel_json = factlabel_json


class _FakeHubfile:
    def __init__(self, factlabel_json):
        self.factlabel = _FakeFactLabel(factlabel_json) if factlabel_json is not None else None


def test_parse_factlabel_returns_the_decoded_content():
    assert FactlabelService().parse_factlabel(_FakeHubfile('{"name": "demo"}')) == {"name": "demo"}


def test_parse_factlabel_raises_when_not_ready():
    with pytest.raises(FactlabelNotReady):
        FactlabelService().parse_factlabel(_FakeHubfile(None))


def test_parse_factlabel_raises_on_corrupted_json():
    with pytest.raises(InvalidFactlabel):
        FactlabelService().parse_factlabel(_FakeHubfile("{not valid json"))
