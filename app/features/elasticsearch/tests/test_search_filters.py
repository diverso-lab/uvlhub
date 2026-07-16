from unittest.mock import MagicMock, patch

import pytest

from app.features.elasticsearch.services import ElasticsearchService

pytestmark = pytest.mark.unit


class TestSearchFilters:
    """Tests for new filter functionality in ElasticsearchService"""

    @patch("app.features.elasticsearch.services.Elasticsearch")
    def test_search_with_features_min_filter(self, mock_es_class):
        """Test that features_min parameter adds correct range filter"""
        mock_es = MagicMock()
        mock_es_class.return_value = mock_es
        mock_es.search.return_value = {"hits": {"hits": [], "total": {"value": 0}}}

        service = ElasticsearchService()
        service.search(query="", features_min=10)

        # Verify search was called
        assert mock_es.search.called
        call_kwargs = mock_es.search.call_args[1]
        body = call_kwargs["body"]

        # Verify features filter is in the query
        filters = body["query"]["bool"]["filter"]
        assert any("number_of_features" in str(f) for f in filters)

    @patch("app.features.elasticsearch.services.Elasticsearch")
    def test_search_with_features_max_filter(self, mock_es_class):
        """Test that features_max parameter adds correct range filter"""
        mock_es = MagicMock()
        mock_es_class.return_value = mock_es
        mock_es.search.return_value = {"hits": {"hits": [], "total": {"value": 0}}}

        service = ElasticsearchService()
        service.search(query="", features_max=100)

        call_kwargs = mock_es.search.call_args[1]
        body = call_kwargs["body"]
        filters = body["query"]["bool"]["filter"]
        assert any("number_of_features" in str(f) for f in filters)

    @patch("app.features.elasticsearch.services.Elasticsearch")
    def test_search_with_models_filter(self, mock_es_class):
        """Test that models_min/max parameters add correct range filter"""
        mock_es = MagicMock()
        mock_es_class.return_value = mock_es
        mock_es.search.return_value = {"hits": {"hits": [], "total": {"value": 0}}}

        service = ElasticsearchService()
        service.search(query="", models_min=1, models_max=5)

        call_kwargs = mock_es.search.call_args[1]
        body = call_kwargs["body"]
        filters = body["query"]["bool"]["filter"]
        assert any("number_of_models" in str(f) for f in filters)

    @patch("app.features.elasticsearch.services.Elasticsearch")
    def test_search_with_size_filter(self, mock_es_class):
        """Test that size_min/max parameters add correct range filter"""
        mock_es = MagicMock()
        mock_es_class.return_value = mock_es
        mock_es.search.return_value = {"hits": {"hits": [], "total": {"value": 0}}}

        service = ElasticsearchService()
        service.search(query="", size_min=1048576, size_max=104857600)

        call_kwargs = mock_es.search.call_args[1]
        body = call_kwargs["body"]
        filters = body["query"]["bool"]["filter"]
        assert any("total_size_in_bytes" in str(f) for f in filters)

    @patch("app.features.elasticsearch.services.Elasticsearch")
    def test_search_with_files_filter(self, mock_es_class):
        """Test that files_min/max parameters add correct range filter"""
        mock_es = MagicMock()
        mock_es_class.return_value = mock_es
        mock_es.search.return_value = {"hits": {"hits": [], "total": {"value": 0}}}

        service = ElasticsearchService()
        service.search(query="", files_min=1, files_max=10)

        call_kwargs = mock_es.search.call_args[1]
        body = call_kwargs["body"]
        filters = body["query"]["bool"]["filter"]
        assert any("files_count" in str(f) for f in filters)

    @patch("app.features.elasticsearch.services.Elasticsearch")
    def test_search_with_year_filter(self, mock_es_class):
        """Test that year parameter adds correct date range filter"""
        mock_es = MagicMock()
        mock_es_class.return_value = mock_es
        mock_es.search.return_value = {"hits": {"hits": [], "total": {"value": 0}}}

        service = ElasticsearchService()
        service.search(query="", year=2023)

        call_kwargs = mock_es.search.call_args[1]
        body = call_kwargs["body"]
        filters = body["query"]["bool"]["filter"]
        assert any("created_at" in str(f) for f in filters)

    @patch("app.features.elasticsearch.services.Elasticsearch")
    def test_search_with_only_with_authors_filter(self, mock_es_class):
        """Test that only_with_authors parameter adds correct term filter"""
        mock_es = MagicMock()
        mock_es_class.return_value = mock_es
        mock_es.search.return_value = {"hits": {"hits": [], "total": {"value": 0}}}

        service = ElasticsearchService()
        service.search(query="", only_with_authors=True)

        call_kwargs = mock_es.search.call_args[1]
        body = call_kwargs["body"]
        filters = body["query"]["bool"]["filter"]
        assert any("authors_is_anonymous" in str(f) for f in filters)

    @patch("app.features.elasticsearch.services.Elasticsearch")
    def test_search_with_all_filters_combined(self, mock_es_class):
        """Test that all filters work together"""
        mock_es = MagicMock()
        mock_es_class.return_value = mock_es
        mock_es.search.return_value = {"hits": {"hits": [], "total": {"value": 0}}}

        service = ElasticsearchService()
        service.search(
            query="test",
            features_min=5,
            features_max=100,
            models_min=1,
            models_max=10,
            size_min=1024,
            size_max=1048576,
            files_min=1,
            files_max=50,
            year=2023,
            only_with_authors=True,
        )

        call_kwargs = mock_es.search.call_args[1]
        body = call_kwargs["body"]

        # Verify search was called with correct structure
        assert "query" in body
        assert "bool" in body["query"]
        assert "filter" in body["query"]["bool"]

        filters_str = str(body["query"]["bool"]["filter"])
        assert "number_of_features" in filters_str
        assert "number_of_models" in filters_str
        assert "total_size_in_bytes" in filters_str
        assert "files_count" in filters_str
        assert "created_at" in filters_str
        assert "authors_is_anonymous" in filters_str

    @patch("app.features.elasticsearch.services.Elasticsearch")
    def test_search_with_only_min_values(self, mock_es_class):
        """Test that only minimum values work correctly"""
        mock_es = MagicMock()
        mock_es_class.return_value = mock_es
        mock_es.search.return_value = {"hits": {"hits": [], "total": {"value": 0}}}

        service = ElasticsearchService()
        service.search(query="", features_min=10, models_min=1, files_min=1)

        call_kwargs = mock_es.search.call_args[1]
        body = call_kwargs["body"]
        filters = body["query"]["bool"]["filter"]

        # Should have filters for features, models, and files
        assert len(filters) >= 3

    @patch("app.features.elasticsearch.services.Elasticsearch")
    def test_search_with_only_max_values(self, mock_es_class):
        """Test that only maximum values work correctly"""
        mock_es = MagicMock()
        mock_es_class.return_value = mock_es
        mock_es.search.return_value = {"hits": {"hits": [], "total": {"value": 0}}}

        service = ElasticsearchService()
        service.search(query="", features_max=50, models_max=10, size_max=1000000)

        call_kwargs = mock_es.search.call_args[1]
        body = call_kwargs["body"]
        filters = body["query"]["bool"]["filter"]

        # Should have filters for features, models, and size
        assert len(filters) >= 3

    @patch("app.features.elasticsearch.services.Elasticsearch")
    def test_search_with_none_filters(self, mock_es_class):
        """Test that None filter values don't add unnecessary filters"""
        mock_es = MagicMock()
        mock_es_class.return_value = mock_es
        mock_es.search.return_value = {"hits": {"hits": [], "total": {"value": 0}}}

        service = ElasticsearchService()
        service.search(query="", features_min=None, features_max=None)

        call_kwargs = mock_es.search.call_args[1]
        body = call_kwargs["body"]
        filters = body["query"]["bool"]["filter"]

        # Should not have number_of_features filter
        assert not any("number_of_features" in str(f) for f in filters)
