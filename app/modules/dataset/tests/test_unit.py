from unittest.mock import MagicMock, patch

import pytest

from app.modules.dataset.services import DataSetService


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        pass

    yield test_client


# Test unitario que devuelve el DOI
@patch("os.getenv")  # Mockear la llamada a os.getenv
def test_get_uvlhub_doi(mock_getenv):

    # Configurar el valor de retorno del mock para DOMAIN
    mock_getenv.return_value = "uvlhub.io"

    # Crear un mock del dataset y ds_meta_data
    mock_dataset = MagicMock()
    mock_dataset.ds_meta_data.dataset_doi = "10.1234/test_doi"

    # Crear una instancia del servicio
    service = DataSetService()

    # Ejecutar la función
    result = service.get_uvlhub_doi(mock_dataset)

    # Verificar que devuelve la URL esperada
    assert result == "http://uvlhub.io/doi/10.1234/test_doi"

    # Verificar que getenv fue llamado correctamente
    mock_getenv.assert_called_once_with("DOMAIN", "localhost")


# Test de integración para un DOI válido que devuelve un dataset
@patch("app.modules.dataset.services.DSMetaDataService.filter_by_doi")
@patch("app.modules.dataset.services.DSViewRecordService.create_cookie")
def test_subdomain_index_success(mock_create_cookie, mock_filter_by_doi, test_client):
    mock_dataset = MagicMock()
    mock_filter_by_doi.return_value = MagicMock(dataset=mock_dataset)
    mock_create_cookie.return_value = "mock_cookie"

    response = test_client.get("/doi/10.1234/datafset1/")
    # Verificamos que el dataset existe con ese DOI
    assert response.status_code == 200

    # Acceder a las cookies desde los encabezados de la respuesta
    cookies = response.headers.get("Set-Cookie")

    # Verificar que la cookie 'view_cookie' se ha establecido correctamente
    assert "view_cookie=mock_cookie" in cookies


# Test para cuando el DOI no se encuentra
def test_subdomain_index_not_found(test_client):
    response = test_client.get("/doi/10.1234/non_existent_doi/")

    # Verificar que devuelve 404 cuando no se encuentra el dataset
    assert response.status_code == 404
