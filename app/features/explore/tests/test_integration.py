import pytest

pytestmark = pytest.mark.integration


def test_explore_page_renders(test_client):
    assert test_client.get("/explore").status_code == 200


def test_api_search_with_features_filter(test_client):
    """Test /api/v1/search with features_min and features_max parameters"""
    response = test_client.get("/api/v1/search?features_min=5&features_max=50")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data
    assert "total" in data
    assert "page" in data


def test_api_search_with_models_filter(test_client):
    """Test /api/v1/search with models_min and models_max parameters"""
    response = test_client.get("/api/v1/search?models_min=1&models_max=10")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data


def test_api_search_with_size_filter(test_client):
    """Test /api/v1/search with size_min and size_max parameters (in bytes)"""
    response = test_client.get("/api/v1/search?size_min=1048576&size_max=104857600")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data


def test_api_search_with_files_filter(test_client):
    """Test /api/v1/search with files_min and files_max parameters"""
    response = test_client.get("/api/v1/search?files_min=1&files_max=10")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data


def test_api_search_with_year_filter(test_client):
    """Test /api/v1/search with year parameter"""
    response = test_client.get("/api/v1/search?year=2023")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data


def test_api_search_with_only_authors_filter(test_client):
    """Test /api/v1/search with only_with_authors parameter"""
    response = test_client.get("/api/v1/search?only_with_authors=true")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data


def test_api_search_with_multiple_filters(test_client):
    """Test /api/v1/search with multiple filters combined"""
    response = test_client.get(
        "/api/v1/search?features_min=5&features_max=50&models_min=1&models_max=5&year=2023&only_with_authors=true"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data
    assert "total" in data


def test_api_search_with_large_ranges(test_client):
    """Test that search works with large range values"""
    response = test_client.get("/api/v1/search?features_min=1&features_max=10000")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data
    assert isinstance(data["results"], list)


def test_api_search_response_structure(test_client):
    """Test that response has required structure"""
    response = test_client.get("/api/v1/search")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data


def test_api_search_with_query_and_filters(test_client):
    """Test /api/v1/search combining text query with filters"""
    response = test_client.get("/api/v1/search?q=dataset&features_min=1&features_max=100")
    assert response.status_code == 200
    data = response.get_json()
    assert "results" in data
