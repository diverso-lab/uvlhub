import pytest

from app.features.elasticsearch.services import ElasticsearchService

pytestmark = pytest.mark.unit


# Invalid index names are rejected before any connection is attempted.
@pytest.mark.parametrize("bad_name", ["", "Bad Name", "UPPER", "_leading", "name,with,commas"])
def test_constructor_rejects_invalid_index_names(bad_name):
    with pytest.raises(ValueError):
        ElasticsearchService(index_name=bad_name)


def test_human_readable_size_formats_bytes():
    assert ElasticsearchService._human_readable_size(0) == "0 B"
    assert ElasticsearchService._human_readable_size(None) == ""
    assert ElasticsearchService._human_readable_size(1024) == "1.0 KB"


def test_date_range_filter_builds_bounds():
    result = ElasticsearchService._date_range_filter("2020-01-01", "2020-12-31")

    created_at = result[0]["range"]["created_at"]
    assert created_at["gte"] == "2020-01-01T00:00:00Z"
    assert created_at["lte"] == "2020-12-31T23:59:59Z"


def test_date_range_filter_is_empty_without_bounds():
    assert ElasticsearchService._date_range_filter(None, None) == []


def test_date_range_filter_ignores_invalid_dates():
    assert ElasticsearchService._date_range_filter("not-a-date", None) == []


def test_format_hit_humanises_date_and_size():
    hit = {"_source": {"created_at": "2020-01-01T12:30:00", "total_size_in_bytes": 1024}}

    source = ElasticsearchService._format_hit(hit)

    assert source["total_size_in_human_format"] == "1.0 KB"
    assert source["created_at"] == "01 Jan 2020, 12:30"
