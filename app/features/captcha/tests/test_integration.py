import pytest

pytestmark = pytest.mark.integration


def test_generate_captcha_endpoint_returns_a_png_data_uri(test_client):
    response = test_client.get("/captcha/generate")

    assert response.status_code == 200
    assert response.get_data(as_text=True).startswith("data:image/png;base64,")
