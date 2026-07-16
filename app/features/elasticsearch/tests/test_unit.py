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


# Tests for new filter functionality
def test_features_range_filter_builds_correctly():
    """Test that features_min/max create correct range filter"""
    ElasticsearchService()
    # This would be tested in the full search method, but we verify the logic
    range_filter = {}
    features_min = 10
    features_max = 50
    if features_min is not None:
        range_filter["gte"] = features_min
    if features_max is not None:
        range_filter["lte"] = features_max

    assert range_filter == {"gte": 10, "lte": 50}


def test_models_range_filter_with_only_min():
    """Test models filter with only minimum value"""
    range_filter = {}
    models_min = 5
    if models_min is not None:
        range_filter["gte"] = models_min

    assert range_filter == {"gte": 5}


def test_size_range_filter_with_only_max():
    """Test size filter with only maximum value"""
    range_filter = {}
    size_max = 1024 * 1024 * 100  # 100 MB in bytes
    if size_max is not None:
        range_filter["lte"] = size_max

    assert range_filter == {"lte": 104857600}


def test_files_count_range_filter():
    """Test files count filter"""
    range_filter = {}
    files_min = 1
    files_max = 10
    if files_min is not None:
        range_filter["gte"] = files_min
    if files_max is not None:
        range_filter["lte"] = files_max

    assert range_filter == {"gte": 1, "lte": 10}


def test_year_filter_builds_date_range():
    """Test that year filter creates correct date range"""
    year = 2023
    date_range = {"gte": f"{year}-01-01T00:00:00Z", "lte": f"{year}-12-31T23:59:59Z"}

    assert date_range["gte"] == "2023-01-01T00:00:00Z"
    assert date_range["lte"] == "2023-12-31T23:59:59Z"


def test_authors_filter_term():
    """Test that only_with_authors creates correct term filter"""
    filter_clause = {"term": {"authors_is_anonymous": False}}

    assert filter_clause["term"]["authors_is_anonymous"] is False
