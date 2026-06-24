import io
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from flask import Response
from werkzeug.exceptions import NotFound

from app import create_app
from app.features.dataset import routes as dataset_routes
from app.features.dataset.services import DatasetMetadataValidationError

pytestmark = pytest.mark.integration


def _mock_dataset_for_qr(dataset_id=1, doi="10.1234/test-doi"):
    dataset = MagicMock()
    dataset.id = dataset_id
    dataset.ds_meta_data = MagicMock()
    dataset.ds_meta_data.dataset_doi = doi
    return dataset


def _login(test_client):
    test_client.post("/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True)


# --- DOI landing page ----------------------------------------------------


@patch("app.features.dataset.services.DSMetaDataService.filter_by_doi")
@patch("app.features.dataset.services.DSViewRecordService.create_cookie")
def test_subdomain_index_success(mock_create_cookie, mock_filter_by_doi, test_client):
    mock_dataset = MagicMock()
    mock_dataset.ds_meta_data.title = "Test dataset"
    mock_dataset.ds_meta_data.description = "Test description"
    mock_dataset.ds_meta_data.dataset_doi = "10.1234/datafset1"
    mock_dataset.ds_meta_data.publication_doi = None
    mock_dataset.ds_meta_data.tags = "tag1,tag2"
    mock_dataset.ds_meta_data.deposition_id = 1
    mock_dataset.ds_meta_data.authors = []
    mock_dataset.feature_models = []
    mock_dataset.created_at = datetime(2024, 1, 1)
    mock_filter_by_doi.return_value = MagicMock(dataset=mock_dataset)
    mock_create_cookie.return_value = "mock_cookie"

    response = test_client.get("/doi/10.1234/datafset1/")

    assert response.status_code == 200
    assert "view_cookie=mock_cookie" in response.headers.get("Set-Cookie")


def test_subdomain_index_not_found(test_client):
    assert test_client.get("/doi/10.1234/non_existent_doi/").status_code == 404


# --- QR codes ------------------------------------------------------------


def test_dataset_qr_by_id_success():
    pytest.importorskip("qrcode")
    app = create_app("testing")
    with (
        patch("app.features.dataset.routes.dataset_service.get_or_404") as mock_get_or_404,
        patch("app.features.dataset.routes._build_dataset_qr_response") as mock_build_qr,
    ):
        mock_get_or_404.return_value = _mock_dataset_for_qr(dataset_id=7, doi="10.1234/dataset7")
        mock_build_qr.return_value = Response(b"qr-image", mimetype="image/png", status=200)
        with app.test_request_context("/datasets/7/qr"):
            response = dataset_routes.dataset_qr_by_id(7)

    assert response.status_code == 200
    assert response.mimetype == "image/png"
    mock_get_or_404.assert_called_once_with(7)


def test_dataset_qr_by_id_without_doi_returns_404():
    pytest.importorskip("qrcode")
    app = create_app("testing")
    with patch("app.features.dataset.routes.dataset_service.get_or_404") as mock_get_or_404:
        mock_get_or_404.return_value = _mock_dataset_for_qr(dataset_id=8, doi=None)
        with app.test_request_context("/datasets/8/qr"):
            with pytest.raises(NotFound):
                dataset_routes.dataset_qr_by_id(8)


def test_dataset_qr_by_doi_success():
    pytest.importorskip("qrcode")
    app = create_app("testing")
    dataset = _mock_dataset_for_qr(dataset_id=9, doi="10.1234/dataset9")
    with (
        patch("app.features.dataset.routes.dsmetadata_service.filter_by_doi") as mock_filter_by_doi,
        patch("app.features.dataset.routes._build_dataset_qr_response") as mock_build_qr,
    ):
        mock_filter_by_doi.return_value = MagicMock(dataset=dataset)
        mock_build_qr.return_value = Response(b"qr-image", mimetype="image/png", status=200)
        with app.test_request_context("/doi/10.1234/dataset9/qr"):
            response = dataset_routes.dataset_qr_by_doi("10.1234/dataset9")

    assert response.status_code == 200
    mock_build_qr.assert_called_once_with(dataset, fmt="png", download=False)


def test_dataset_qr_by_doi_not_found_returns_404():
    pytest.importorskip("qrcode")
    app = create_app("testing")
    with patch("app.features.dataset.routes.dsmetadata_service.filter_by_doi") as mock_filter_by_doi:
        mock_filter_by_doi.return_value = None
        with app.test_request_context("/doi/10.1234/non-existent/qr"):
            with pytest.raises(NotFound):
                dataset_routes.dataset_qr_by_doi("10.1234/non-existent")


# --- downloads with format selection -------------------------------------


def test_download_dataset_route_passes_selected_formats_to_service():
    app = create_app("testing")
    dataset = MagicMock()
    dataset.id = 5

    with app.test_request_context("/datasets/download/5?formats=uvl&formats=dimacs"):
        with (
            patch.object(dataset_routes.dataset_service, "get_or_404", return_value=dataset),
            patch.object(
                dataset_routes.dataset_service, "zip_from_storage", return_value="C:\\tmp\\dataset_5.zip"
            ) as p_zip,
            patch("app.features.dataset.routes.os.path.exists", return_value=True),
            patch.object(dataset_routes.ds_download_record_service, "create_cookie", return_value="cookie-1"),
            patch("app.features.dataset.routes.send_file", return_value=Response("ok", status=200)),
        ):
            response = dataset_routes.download_dataset(5)

    assert response.status_code == 200
    p_zip.assert_called_once_with(dataset, formats=["uvl", "dimacs"])


def test_download_all_dataset_route_passes_selected_formats_to_service():
    app = create_app("testing")

    with app.test_request_context("/datasets/download/all?formats=uvl&formats=splot"):
        with (
            patch.object(dataset_routes.dataset_service, "zip_all_datasets_by_formats") as p_zip_all,
            patch("app.features.dataset.routes.send_file", return_value=Response("ok", status=200)),
            patch("app.features.dataset.routes.os.path.exists", return_value=False),
            patch("app.features.dataset.routes.shutil.rmtree"),
        ):
            response = dataset_routes.download_all_dataset()

    assert response.status_code == 200
    _, kwargs = p_zip_all.call_args
    assert kwargs["formats"] == ["uvl", "splot"]


# --- flamapyIDE import flow ----------------------------------------------


def test_import_dataset_route_renders_create_form_with_preloaded_file(test_client):
    _login(test_client)
    imported_file = {"name": "editor_model.uvl", "serverFilename": "1234_editor_model.uvl", "size": 21, "uuid": "1234"}

    with patch.object(dataset_routes, "_import_remote_uvl_to_temp", return_value=imported_file) as mock_import:
        response = test_client.get(
            "/dataset/import/?import=https://www.uvlhub.io/doi/10.5281/zenodo.1/files/raw/editor_model.uvl"
        )

    assert response.status_code == 200
    assert b"window.initialDropzoneFiles" in response.data
    assert b"editor_model.uvl" in response.data
    mock_import.assert_called_once()
    test_client.get("/logout", follow_redirects=True)


def test_import_dataset_route_returns_400_when_remote_import_fails(test_client):
    _login(test_client)

    with patch.object(
        dataset_routes,
        "_import_remote_uvl_to_temp",
        side_effect=DatasetMetadataValidationError("The imported resource must be a .uvl file."),
    ):
        response = test_client.get(
            "/dataset/import/?import=https://www.uvlhub.io/doi/10.5281/zenodo.1/files/raw/model.txt"
        )

    assert response.status_code == 400
    assert b"The imported resource must be a .uvl file." in response.data
    test_client.get("/logout", follow_redirects=True)


# --- flamapyIDE upload API ----------------------------------------------


def test_api_upload_dataset_requires_authentication(test_client):
    test_client.get("/logout", follow_redirects=True)

    response = test_client.post(
        "/api/v1/datasets/upload", json={"title": "Imported model", "uvl_content": "features\n    Root"}
    )

    assert response.status_code == 401
    payload = response.get_json()
    assert payload["authenticated"] is False
    assert "orcid_url" in payload


def test_api_upload_dataset_creates_draft_when_authenticated(test_client):
    _login(test_client)
    dataset = MagicMock()
    dataset.id = 77

    with patch.object(
        dataset_routes.dataset_service, "create_draft_from_uvl_import", return_value=(dataset, [MagicMock()])
    ) as mock_create:
        response = test_client.post(
            "/api/v1/datasets/upload",
            json={
                "title": "Imported model",
                "filename": "editor_model.uvl",
                "description": "Imported from IDE",
                "uvl_content": "features\n    Root",
            },
        )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["dataset_id"] == 77
    assert payload["feature_models_created"] == 1
    mock_create.assert_called_once()
    test_client.get("/logout", follow_redirects=True)


# --- Edit metadata route -------------------------------------------------


def _test_user_id(test_client):
    with test_client.application.app_context():
        from app.features.auth.models import User

        return User.query.filter_by(email="test@example.com").first().id


def test_edit_metadata_requires_login(test_client):
    test_client.get("/logout", follow_redirects=True)
    response = test_client.get("/dataset/edit/1")
    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")


def test_edit_metadata_forbidden_for_non_owner(test_client):
    _login(test_client)
    with patch.object(dataset_routes.dataset_service, "get_or_404", return_value=MagicMock(user_id=999999)):
        response = test_client.get("/dataset/edit/123")
    assert response.status_code == 403
    test_client.get("/logout", follow_redirects=True)


def test_edit_metadata_not_found_returns_404(test_client):
    _login(test_client)
    response = test_client.get("/dataset/edit/999999")
    assert response.status_code == 404
    test_client.get("/logout", follow_redirects=True)


def test_edit_metadata_post_ajax_returns_success(test_client):
    _login(test_client)
    owned = MagicMock(user_id=_test_user_id(test_client))
    with (
        patch.object(dataset_routes.dataset_service, "get_or_404", return_value=owned),
        patch.object(
            dataset_routes.dataset_service,
            "update_metadata_from_request",
            return_value={"metadata_synced": True, "sync_deferred": False},
        ),
    ):
        response = test_client.post(
            "/dataset/edit/123",
            data={"title": "Edited", "dataset_type": "draft"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
    assert response.status_code == 200
    assert response.get_json()["metadata_synced"] is True
    test_client.get("/logout", follow_redirects=True)


def test_edit_metadata_post_ajax_validation_error_returns_400(test_client):
    _login(test_client)
    owned = MagicMock(user_id=_test_user_id(test_client))
    with (
        patch.object(dataset_routes.dataset_service, "get_or_404", return_value=owned),
        patch.object(
            dataset_routes.dataset_service,
            "update_metadata_from_request",
            side_effect=DatasetMetadataValidationError("Invalid ORCID format"),
        ),
    ):
        response = test_client.post(
            "/dataset/edit/123",
            data={"title": "Edited"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
    assert response.status_code == 400
    assert "Invalid ORCID" in response.get_json()["message"]
    test_client.get("/logout", follow_redirects=True)


# --- Replace UVL route ---------------------------------------------------


def test_replace_hubfile_requires_login(test_client):
    test_client.get("/logout", follow_redirects=True)
    response = test_client.post("/dataset/1/hubfile/1/replace")
    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")


def test_replace_hubfile_forbidden_for_non_owner(test_client):
    _login(test_client)
    with patch.object(dataset_routes.dataset_service, "get_or_404", return_value=MagicMock(user_id=999999)):
        response = test_client.post("/dataset/1/hubfile/1/replace")
    assert response.status_code == 403
    test_client.get("/logout", follow_redirects=True)


def test_replace_hubfile_success(test_client):
    _login(test_client)
    owned = MagicMock(user_id=_test_user_id(test_client))
    with (
        patch.object(dataset_routes.dataset_service, "get_or_404", return_value=owned),
        patch.object(dataset_routes.dataset_service, "replace_hubfile", return_value=MagicMock()) as mock_replace,
    ):
        response = test_client.post(
            "/dataset/1/hubfile/9/replace",
            data={"file": (io.BytesIO(b"features\n    Root"), "new.uvl")},
            content_type="multipart/form-data",
        )
    assert response.status_code == 200
    assert "replaced" in response.get_json()["message"].lower()
    mock_replace.assert_called_once()
    test_client.get("/logout", follow_redirects=True)


def test_replace_hubfile_validation_error_returns_400(test_client):
    _login(test_client)
    owned = MagicMock(user_id=_test_user_id(test_client))
    with (
        patch.object(dataset_routes.dataset_service, "get_or_404", return_value=owned),
        patch.object(
            dataset_routes.dataset_service,
            "replace_hubfile",
            side_effect=DatasetMetadataValidationError("A .uvl file is required."),
        ),
    ):
        response = test_client.post(
            "/dataset/1/hubfile/9/replace",
            data={},
            content_type="multipart/form-data",
        )
    assert response.status_code == 400
    assert ".uvl" in response.get_json()["message"]
    test_client.get("/logout", follow_redirects=True)


# --- New version route ---------------------------------------------------


def test_new_version_requires_login(test_client):
    test_client.get("/logout", follow_redirects=True)
    response = test_client.post("/dataset/1/new-version")
    assert response.status_code == 302


def test_new_version_forbidden_for_non_owner(test_client):
    _login(test_client)
    with patch.object(dataset_routes.dataset_service, "get_or_404", return_value=MagicMock(user_id=999999)):
        response = test_client.post("/dataset/1/new-version")
    assert response.status_code == 403
    test_client.get("/logout", follow_redirects=True)


def test_new_version_success_returns_doi(test_client):
    _login(test_client)
    owned = MagicMock(user_id=_test_user_id(test_client))
    new_dataset = MagicMock(id=42, dataset_version=2)
    new_dataset.ds_meta_data.dataset_doi = "10.5072/zenodo.999"
    with (
        patch.object(dataset_routes.dataset_service, "get_or_404", return_value=owned),
        patch.object(dataset_routes.dataset_service, "create_new_version", return_value=new_dataset),
    ):
        response = test_client.post(
            "/dataset/1/new-version",
            data={"file": (io.BytesIO(b"features\n    Root"), "v2.uvl")},
            content_type="multipart/form-data",
        )
    assert response.status_code == 200
    body = response.get_json()
    assert body["dataset_id"] == 42
    assert body["doi"] == "10.5072/zenodo.999"
    assert body["version"] == 2
    test_client.get("/logout", follow_redirects=True)


def test_new_version_validation_error_returns_400(test_client):
    _login(test_client)
    owned = MagicMock(user_id=_test_user_id(test_client))
    with (
        patch.object(dataset_routes.dataset_service, "get_or_404", return_value=owned),
        patch.object(
            dataset_routes.dataset_service,
            "create_new_version",
            side_effect=DatasetMetadataValidationError("A .uvl file is required."),
        ),
    ):
        response = test_client.post("/dataset/1/new-version", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    test_client.get("/logout", follow_redirects=True)


# --- Compiled asset serving (nested TinyMCE files) -----------------------


def test_dist_asset_serves_nested_tinymce_model(test_client):
    # splent's BaseBlueprint asset route 404s on nested paths; dist_asset must
    # serve them so the TinyMCE description editor can load (base_url /dataset/dist).
    response = test_client.get("/dataset/dist/models/dom/model.js")
    assert response.status_code == 200
    assert "javascript" in response.headers["Content-Type"]


def test_dist_asset_serves_nested_skin_css(test_client):
    response = test_client.get("/dataset/dist/skins/ui/oxide/skin.min.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["Content-Type"]
