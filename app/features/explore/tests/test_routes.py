import pytest

pytestmark = pytest.mark.integration


class TestExploreRoutes:
    """Tests for explore routes and parameter handling"""

    def test_api_search_returns_json(self, test_client):
        """Test that /api/v1/search returns valid JSON"""
        response = test_client.get("/api/v1/search")
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_api_search_returns_required_fields(self, test_client):
        """Test that response contains required fields"""
        response = test_client.get("/api/v1/search")
        data = response.get_json()
        assert "results" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

    def test_features_min_parameter_accepted(self, test_client):
        """Test that features_min parameter is accepted without error"""
        response = test_client.get("/api/v1/search?features_min=10")
        assert response.status_code == 200

    def test_features_max_parameter_accepted(self, test_client):
        """Test that features_max parameter is accepted without error"""
        response = test_client.get("/api/v1/search?features_max=100")
        assert response.status_code == 200

    def test_models_min_parameter_accepted(self, test_client):
        """Test that models_min parameter is accepted without error"""
        response = test_client.get("/api/v1/search?models_min=1")
        assert response.status_code == 200

    def test_models_max_parameter_accepted(self, test_client):
        """Test that models_max parameter is accepted without error"""
        response = test_client.get("/api/v1/search?models_max=20")
        assert response.status_code == 200

    def test_size_min_parameter_accepted(self, test_client):
        """Test that size_min parameter (in bytes) is accepted"""
        response = test_client.get("/api/v1/search?size_min=1048576")
        assert response.status_code == 200

    def test_size_max_parameter_accepted(self, test_client):
        """Test that size_max parameter (in bytes) is accepted"""
        response = test_client.get("/api/v1/search?size_max=1073741824")
        assert response.status_code == 200

    def test_files_min_parameter_accepted(self, test_client):
        """Test that files_min parameter is accepted"""
        response = test_client.get("/api/v1/search?files_min=1")
        assert response.status_code == 200

    def test_files_max_parameter_accepted(self, test_client):
        """Test that files_max parameter is accepted"""
        response = test_client.get("/api/v1/search?files_max=50")
        assert response.status_code == 200

    def test_year_parameter_accepted(self, test_client):
        """Test that year parameter is accepted"""
        response = test_client.get("/api/v1/search?year=2023")
        assert response.status_code == 200

    def test_only_with_authors_true_accepted(self, test_client):
        """Test that only_with_authors=true is accepted"""
        response = test_client.get("/api/v1/search?only_with_authors=true")
        assert response.status_code == 200

    def test_only_with_authors_false_accepted(self, test_client):
        """Test that only_with_authors=false is accepted"""
        response = test_client.get("/api/v1/search?only_with_authors=false")
        assert response.status_code == 200

    def test_combined_filters(self, test_client):
        """Test that multiple filters work together"""
        response = test_client.get(
            "/api/v1/search?features_min=5&features_max=50&models_min=1&year=2023"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data["results"], list)

    def test_multiple_filters_simultaneously(self, test_client):
        """Test that multiple filters can be used together"""
        response = test_client.get("/api/v1/search?features_min=1&models_max=20&year=2023")
        assert response.status_code == 200

    def test_pagination_with_filters(self, test_client):
        """Test that pagination works with filters"""
        response = test_client.get("/api/v1/search?page=1&size=10&features_min=1")
        assert response.status_code == 200
        data = response.get_json()
        assert data["page"] == 1
        assert data["size"] == 10

    def test_sorting_with_filters(self, test_client):
        """Test that sorting parameter works with filters"""
        response = test_client.get("/api/v1/search?sorting=newest&features_min=1")
        assert response.status_code == 200

    def test_query_text_with_filters(self, test_client):
        """Test that text search works combined with filters"""
        response = test_client.get("/api/v1/search?q=test&features_min=1&features_max=100")
        assert response.status_code == 200
