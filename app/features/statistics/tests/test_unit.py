import pytest

from app.features.dataset.models import PublicationType
from app.features.statistics.services import (
    DashboardService,
    _bucket,
    _format_top_value,
    _linear_bucket,
    _summarize,
)

pytestmark = pytest.mark.unit


def test_summarize_handles_empty_input():
    summary = _summarize([])

    assert summary.count == 0
    assert summary.mean is None


def test_summarize_computes_basic_statistics():
    summary = _summarize([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    assert summary.count == 10
    assert summary.min == 1.0
    assert summary.max == 10.0
    assert summary.mean == 5.5


def test_format_top_value_keeps_small_integers():
    assert _format_top_value(1024) == 1024
    assert _format_top_value(None) == 0


def test_format_top_value_uses_scientific_notation_for_huge_numbers():
    assert _format_top_value(1e20) == "1.00e+20"


def test_bucket_counts_into_half_open_ranges():
    buckets = [("low", 0, 10), ("high", 10, None)]

    result = _bucket([1, 5, 10, 20], buckets)

    assert result[0].count == 2
    assert result[1].count == 2


def test_linear_bucket_groups_by_integer_with_overflow_bin():
    result = _linear_bucket([0, 1, 1, 5, 20], max_bucket=3)

    assert [b.count for b in result] == [1, 2, 0, 2]


def test_pretty_enum_titlecases_the_name():
    assert DashboardService._pretty_enum(PublicationType.JOURNAL_ARTICLE) == "Journal Article"
    assert DashboardService._pretty_enum(None) == "—"


def test_align_to_months_fills_gaps_with_zero():
    aligned = DashboardService._align_to_months(["2020-01", "2020-02"], [("2020-01", 5)])

    assert aligned == [5, 0]
