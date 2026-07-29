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
        patch("app.features.dataset.routes.index_dataset"),
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
    new_dataset.feature_models = []
    with (
        patch.object(dataset_routes.dataset_service, "get_or_404", return_value=owned),
        patch.object(dataset_routes.dataset_service, "create_new_version", return_value=new_dataset),
        patch("app.features.elasticsearch.services.IndexingService"),
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


# --- API-key write API ----------------------------------------------------


def _api_token(test_client, scopes, email="test@example.com"):
    """Create a real API key in the database and return its token.

    Runs on the test module's active app context (no nested context): the
    commit ends the shared session's transaction, so the next request sees
    the new key even under MariaDB's REPEATABLE READ isolation.
    """
    from app import db
    from app.features.apikeys.services import ApiKeyService
    from app.features.auth.models import User

    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(email=email, password="test1234")
        db.session.add(user)
        db.session.commit()
    _, token = ApiKeyService().generate_for_user(user, scopes)
    return token


def test_api_publish_rejects_missing_api_key(test_client):
    test_client.get("/logout", follow_redirects=True)

    response = test_client.post("/api/v1/datasets/1/publish")

    assert response.status_code == 401


def test_api_publish_rejects_key_without_write_scope(test_client):
    token = _api_token(test_client, ["read_dataset"])

    response = test_client.post("/api/v1/datasets/1/publish", headers={"X-API-Key": token})

    assert response.status_code == 403
    assert "scope" in response.get_json()["error"]


def test_api_publish_forbidden_for_another_users_dataset(test_client):
    token = _api_token(test_client, ["write_dataset"], email="rival@example.com")

    with patch.object(dataset_routes.dataset_service, "get_by_id", return_value=MagicMock(user_id=424242)):
        response = test_client.post("/api/v1/datasets/1/publish", headers={"X-API-Key": token})

    assert response.status_code == 403
    assert "own" in response.get_json()["error"]


def test_api_publish_not_found_returns_404(test_client):
    token = _api_token(test_client, ["write_dataset"])

    with patch.object(dataset_routes.dataset_service, "get_by_id", return_value=None):
        response = test_client.post("/api/v1/datasets/999999/publish", headers={"X-API-Key": token})

    assert response.status_code == 404


def test_api_publish_already_published_returns_400(test_client):
    token = _api_token(test_client, ["write_dataset"])
    owned = MagicMock(user_id=_test_user_id(test_client))
    owned.ds_meta_data.dataset_doi = "10.1234/already"

    with patch.object(dataset_routes.dataset_service, "get_by_id", return_value=owned):
        response = test_client.post("/api/v1/datasets/1/publish", headers={"X-API-Key": token})

    assert response.status_code == 400
    assert "already" in response.get_json()["error"].lower()


def test_api_upload_rejects_key_without_write_scope(test_client):
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["read_dataset"])

    response = test_client.post(
        "/api/v1/datasets/upload",
        headers={"X-API-Key": token},
        json={"title": "Model", "uvl_content": "features\n    Root"},
    )

    assert response.status_code == 403


def test_api_upload_with_key_rejects_invalid_uvl(test_client):
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["write_dataset"])

    response = test_client.post(
        "/api/v1/datasets/upload",
        headers={"X-API-Key": token},
        json={"title": "Broken model", "uvl_content": "this is not a uvl model {{{"},
    )

    assert response.status_code == 400
    assert "error" in response.get_json()
    assert response.get_json()["error"]


def test_api_upload_session_path_skips_uvl_validation(test_client):
    # flamapyIDE uploads through the session cookie and must keep its current
    # behaviour: no synchronous flamapy check on that path.
    _login(test_client)
    dataset = MagicMock()
    dataset.id = 88

    with (
        patch.object(
            dataset_routes.dataset_service, "create_draft_from_uvl_import", return_value=(dataset, [MagicMock()])
        ),
        patch.object(dataset_routes.flamapy_service, "check_uvl") as mock_check,
    ):
        response = test_client.post(
            "/api/v1/datasets/upload",
            json={"title": "IDE model", "uvl_content": "this is not a uvl model {{{"},
        )

    assert response.status_code == 201
    mock_check.assert_not_called()
    test_client.get("/logout", follow_redirects=True)


def test_api_upload_multipart_happy_path(test_client):
    # The CLI sends multipart/form-data (title/description fields plus a
    # uvl_file part); this pins that contract end to end: a real draft is
    # created and its stored content matches the uploaded bytes.
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["write_dataset"])
    uvl_bytes = b"features\n    Root"

    response = test_client.post(
        "/api/v1/datasets/upload",
        headers={"X-API-Key": token},
        data={
            "title": "CLI multipart model",
            "description": "Uploaded through the multipart contract.",
            "uvl_file": (io.BytesIO(uvl_bytes), "cli_model.uvl"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    dataset_id = response.get_json()["dataset_id"]
    dataset = dataset_routes.dataset_service.get_by_id(dataset_id)
    assert dataset.ds_meta_data.title == "CLI multipart model"
    assert dataset.ds_meta_data.description == "Uploaded through the multipart contract."
    hubfiles = dataset.files()
    assert [hubfile.name for hubfile in hubfiles] == ["cli_model.uvl"]
    with open(hubfiles[0].get_full_path(), "rb") as stored:
        assert stored.read() == uvl_bytes


def test_api_upload_multipart_rejects_invalid_uvl(test_client):
    # Same multipart contract, invalid model: proves the synchronous flamapy
    # check also runs on the file-upload path, not only on json uvl_content.
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["write_dataset"])

    response = test_client.post(
        "/api/v1/datasets/upload",
        headers={"X-API-Key": token},
        data={
            "title": "Broken multipart model",
            "description": "Should be rejected by flamapy.",
            "uvl_file": (io.BytesIO(b"this is not a uvl model {{{"), "broken.uvl"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["error"]


def test_api_upload_rejects_a_key_whose_account_was_deactivated(test_client):
    # An administrator deactivating an account has to stop its API keys too.
    # write_dataset mints permanent public DOIs, so a key that outlives its
    # account keeps that power with nobody accountable for it.
    from app import db
    from app.features.auth.models import User

    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["write_dataset"], email="deactivated@example.com")

    user = User.query.filter_by(email="deactivated@example.com").first()
    user.active = False
    db.session.commit()

    response = test_client.post(
        "/api/v1/datasets/upload",
        headers={"X-API-Key": token},
        json={"title": "Model from a dead account", "uvl_content": "features\n    Root"},
    )

    assert response.status_code == 403

    user.active = True
    db.session.commit()


@pytest.mark.parametrize("orcid", [12345, 1.5, ["0000-0002-1825-0097"], {"id": "x"}])
def test_api_upload_rejects_a_non_string_orcid_with_400(test_client, orcid):
    # JSON allows any type here. The normalizer assumed a string and raised
    # AttributeError, which the route does not catch, so a malformed author
    # payload surfaced as a 500 instead of the documented 400.
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["write_dataset"])

    response = test_client.post(
        "/api/v1/datasets/upload",
        headers={"X-API-Key": token},
        json={
            "title": "Model with a bad author",
            "uvl_content": "features\n    Root",
            "authors": [{"name": "A", "orcid": orcid}],
        },
    )

    assert response.status_code == 400
    assert "ORCID" in response.get_json()["error"]


def test_api_upload_rejects_oversized_uvl(test_client):
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["write_dataset"])
    oversized = b"a" * (1024 * 1024 + 1)

    with patch.object(dataset_routes.flamapy_service, "check_uvl") as mock_check:
        response = test_client.post(
            "/api/v1/datasets/upload",
            headers={"X-API-Key": token},
            data={"title": "Huge model", "uvl_file": (io.BytesIO(oversized), "huge.uvl")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 413
    assert "too large" in response.get_json()["error"]
    mock_check.assert_not_called()


def test_api_new_version_rejects_key_without_write_scope(test_client):
    token = _api_token(test_client, ["read_dataset"])

    response = test_client.post("/api/v1/datasets/1/new-version", headers={"X-API-Key": token})

    assert response.status_code == 403


def test_api_new_version_forbidden_for_another_users_dataset(test_client):
    token = _api_token(test_client, ["write_dataset"], email="rival@example.com")

    with patch.object(dataset_routes.dataset_service, "get_by_id", return_value=MagicMock(user_id=424242)):
        response = test_client.post("/api/v1/datasets/1/new-version", headers={"X-API-Key": token})

    assert response.status_code == 403


def test_api_new_version_without_file_returns_400(test_client):
    token = _api_token(test_client, ["write_dataset"])
    owned = MagicMock(user_id=_test_user_id(test_client))

    with patch.object(dataset_routes.dataset_service, "get_by_id", return_value=owned):
        response = test_client.post(
            "/api/v1/datasets/1/new-version",
            headers={"X-API-Key": token},
            data={},
            content_type="multipart/form-data",
        )

    assert response.status_code == 400
    assert ".uvl" in response.get_json()["error"]


def test_api_new_version_success_returns_doi_and_files(test_client):
    token = _api_token(test_client, ["write_dataset"])
    owned = MagicMock(user_id=_test_user_id(test_client))
    new_dataset = MagicMock(id=43, dataset_version=2)
    new_dataset.ds_meta_data.dataset_doi = "10.5072/zenodo.1000"
    new_dataset.ds_meta_data.dataset_concept_doi = "10.5072/zenodo.999"
    hubfile = MagicMock()
    hubfile.name = "v2.uvl"
    new_dataset.files.return_value = [hubfile]

    with (
        patch.object(dataset_routes.dataset_service, "get_by_id", return_value=owned),
        patch.object(dataset_routes.dataset_service, "create_new_version", return_value=new_dataset),
        patch("app.features.dataset.routes.IndexingService"),
    ):
        response = test_client.post(
            "/api/v1/datasets/1/new-version",
            headers={"X-API-Key": token},
            data={"file": (io.BytesIO(b"features\n    Root"), "v2.uvl")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    body = response.get_json()
    assert body["doi"] == "10.5072/zenodo.1000"
    assert body["version"] == 2
    assert body["files"][0]["name"] == "v2.uvl"
    assert body["files"][0]["raw_url"].endswith("/doi/10.5072/zenodo.1000/files/raw/v2.uvl/")


def test_api_new_version_with_key_rejects_invalid_uvl(test_client):
    # Mirror of test_api_upload_with_key_rejects_invalid_uvl: the replacement
    # UVL must go through the synchronous flamapy check before any Zenodo call.
    token = _api_token(test_client, ["write_dataset"])
    owned = MagicMock(user_id=_test_user_id(test_client))

    with (
        patch.object(dataset_routes.dataset_service, "get_by_id", return_value=owned),
        patch.object(dataset_routes.dataset_service, "create_new_version") as mock_create,
    ):
        response = test_client.post(
            "/api/v1/datasets/1/new-version",
            headers={"X-API-Key": token},
            data={"file": (io.BytesIO(b"this is not a uvl model {{{"), "broken.uvl")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 400
    assert response.get_json()["error"]
    mock_create.assert_not_called()


def test_api_new_version_rejects_non_utf8_file(test_client):
    token = _api_token(test_client, ["write_dataset"])
    owned = MagicMock(user_id=_test_user_id(test_client))

    with (
        patch.object(dataset_routes.dataset_service, "get_by_id", return_value=owned),
        patch.object(dataset_routes.dataset_service, "create_new_version") as mock_create,
    ):
        response = test_client.post(
            "/api/v1/datasets/1/new-version",
            headers={"X-API-Key": token},
            data={"file": (io.BytesIO(b"\xff\xfe\x00garbage"), "binary.uvl")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 400
    assert "UTF-8" in response.get_json()["error"]
    mock_create.assert_not_called()


def test_api_new_version_rejects_oversized_uvl(test_client):
    token = _api_token(test_client, ["write_dataset"])
    owned = MagicMock(user_id=_test_user_id(test_client))
    oversized = b"a" * (1024 * 1024 + 1)

    with (
        patch.object(dataset_routes.dataset_service, "get_by_id", return_value=owned),
        patch.object(dataset_routes.dataset_service, "create_new_version") as mock_create,
        patch.object(dataset_routes.flamapy_service, "check_uvl") as mock_check,
    ):
        response = test_client.post(
            "/api/v1/datasets/1/new-version",
            headers={"X-API-Key": token},
            data={"file": (io.BytesIO(oversized), "huge.uvl")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 413
    assert "too large" in response.get_json()["error"]
    mock_check.assert_not_called()
    mock_create.assert_not_called()


def test_api_new_version_indexes_new_dataset(test_client):
    # The new DOI must reach Elasticsearch so the version shows up in explore.
    token = _api_token(test_client, ["write_dataset"])
    owned = MagicMock(user_id=_test_user_id(test_client))
    new_dataset = MagicMock(id=44, dataset_version=3)
    new_dataset.ds_meta_data.dataset_doi = "10.5072/zenodo.1001"
    new_dataset.ds_meta_data.dataset_concept_doi = "10.5072/zenodo.999"
    new_dataset.files.return_value = []

    with (
        patch.object(dataset_routes.dataset_service, "get_by_id", return_value=owned),
        patch.object(dataset_routes.dataset_service, "create_new_version", return_value=new_dataset),
        patch("app.features.dataset.routes.IndexingService") as mock_indexing,
    ):
        response = test_client.post(
            "/api/v1/datasets/1/new-version",
            headers={"X-API-Key": token},
            data={"file": (io.BytesIO(b"features\n    Root"), "v3.uvl")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    mock_indexing.return_value.index_dataset_and_hubfiles.assert_called_once_with(
        new_dataset, new_dataset.feature_models
    )


def test_api_dataset_by_doi_requires_read_scope(test_client):
    token = _api_token(test_client, ["write_dataset"])

    response = test_client.get("/api/v1/datasets/doi/10.1234/whatever", headers={"X-API-Key": token})

    assert response.status_code == 403


def test_api_dataset_by_doi_not_found_returns_404(test_client):
    token = _api_token(test_client, ["read_dataset"])

    response = test_client.get("/api/v1/datasets/doi/10.9999/does-not-exist", headers={"X-API-Key": token})

    assert response.status_code == 404


def test_api_upload_publish_lookup_happy_path(test_client):
    # Full API-key flow with the Zenodo primitives mocked: a real draft is
    # created on disk and in the DB, published through the real
    # ZenodoDatasetService orchestration, then looked up by DOI.
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["read_dataset", "write_dataset"])

    upload = test_client.post(
        "/api/v1/datasets/upload",
        headers={"X-API-Key": token},
        json={"title": "API model", "filename": "api_model.uvl", "uvl_content": "features\n    Root"},
    )
    assert upload.status_code == 201
    dataset_id = upload.get_json()["dataset_id"]

    with (
        patch.object(dataset_routes.zenodo_service, "create_new_deposition", return_value={"id": 4321}),
        patch.object(dataset_routes.zenodo_service, "upload_zip"),
        patch.object(dataset_routes.zenodo_service, "publish_deposition"),
        patch.object(dataset_routes.zenodo_service, "get_doi", return_value="10.5072/zenodo.4321"),
        patch.object(dataset_routes.zenodo_service, "get_concept_doi", return_value="10.5072/zenodo.4320"),
        patch("app.features.dataset.routes.IndexingService"),
    ):
        publish = test_client.post(f"/api/v1/datasets/{dataset_id}/publish", headers={"X-API-Key": token})

    assert publish.status_code == 200
    body = publish.get_json()
    assert body["doi"] == "10.5072/zenodo.4321"
    assert body["concept_doi"] == "10.5072/zenodo.4320"
    assert body["deposition_id"] == 4321
    assert body["files"][0]["name"] == "api_model.uvl"
    assert body["files"][0]["raw_url"].endswith("/doi/10.5072/zenodo.4321/files/raw/api_model.uvl/")

    lookup = test_client.get("/api/v1/datasets/doi/10.5072/zenodo.4321", headers={"X-API-Key": token})
    assert lookup.status_code == 200
    found = lookup.get_json()
    assert found["dataset_id"] == dataset_id
    assert found["title"] == "API model"
    assert found["files"][0]["name"] == "api_model.uvl"
    assert found["files"][0]["raw_url"].endswith("/doi/10.5072/zenodo.4321/files/raw/api_model.uvl/")
    # Lineage discovery: a single published dataset is its own latest version.
    assert found["concept_doi"] == "10.5072/zenodo.4320"
    assert found["version"] == 1
    assert found["is_latest"] is True
    assert found["latest"] == {"dataset_id": dataset_id, "version": 1, "doi": "10.5072/zenodo.4321"}


# --- Compiled asset serving (nested paths) -------------------------------
# dist/ holds webpack build artifacts (git-ignored, not built in CI), so these
# probe the route with a temporary nested tree instead of the real TinyMCE files.


def test_dist_asset_serves_nested_js(test_client, tmp_path, monkeypatch):
    # BaseBlueprint's single-segment asset route 404s on nested paths; dist_asset
    # must serve them so the TinyMCE editor loads from base_url /dataset/dist.
    nested = tmp_path / "dist" / "models" / "dom"
    nested.mkdir(parents=True)
    (nested / "model.js").write_text("// probe")
    monkeypatch.setattr(dataset_routes, "_DATASET_ASSETS_DIR", str(tmp_path))

    response = test_client.get("/dataset/dist/models/dom/model.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["Content-Type"]


def test_dist_asset_pins_css_mimetype(test_client, tmp_path, monkeypatch):
    nested = tmp_path / "dist" / "skins" / "ui" / "oxide"
    nested.mkdir(parents=True)
    (nested / "skin.min.css").write_text("body{}")
    monkeypatch.setattr(dataset_routes, "_DATASET_ASSETS_DIR", str(tmp_path))

    response = test_client.get("/dataset/dist/skins/ui/oxide/skin.min.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["Content-Type"]


# --- Version lineage API --------------------------------------------------


def _seed_lineage(email, concept_doi, doi_prefix, versions=2, user_id=None):
    """Create a real published lineage in the database, oldest first."""
    from app.features.auth.models import User
    from app.features.auth.repositories import UserRepository
    from app.features.dataset.models import PublicationType
    from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository

    if user_id is None:
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = UserRepository().create(email=email, password="pw-123456")
        user_id = user.id

    created = []
    origin_id = None
    for version in range(1, versions + 1):
        meta = DSMetaDataRepository().create(
            title=f"Lineage v{version}",
            description="d",
            publication_type=PublicationType.BOOK,
            dataset_doi=f"{doi_prefix}.{version}",
            dataset_concept_doi=concept_doi,
            deposition_id=version,
            tags="",
        )
        dataset = DataSetRepository().create(
            user_id=user_id, ds_meta_data_id=meta.id, dataset_version=version, dataset_origin_id=origin_id
        )
        created.append(dataset)
        origin_id = dataset.id
    return created


def test_api_dataset_versions_returns_the_whole_lineage(test_client):
    token = _api_token(test_client, ["read_dataset"])
    v1, v2 = _seed_lineage("versions@example.com", "10.5072/zenodo.7000", "10.5072/zenodo.700")

    response = test_client.get(f"/api/v1/datasets/{v1.id}/versions", headers={"X-API-Key": token})

    assert response.status_code == 200
    body = response.get_json()
    assert body["dataset_id"] == v1.id
    assert body["concept_doi"] == "10.5072/zenodo.7000"
    assert body["total_versions"] == 2
    assert body["latest"] == {"dataset_id": v2.id, "version": 2, "doi": "10.5072/zenodo.700.2"}
    assert [entry["dataset_id"] for entry in body["versions"]] == [v1.id, v2.id]
    assert [entry["version"] for entry in body["versions"]] == [1, 2]
    assert [entry["is_latest"] for entry in body["versions"]] == [False, True]
    assert all(entry["publication_date"] for entry in body["versions"])


def test_api_dataset_versions_requires_read_scope(test_client):
    token = _api_token(test_client, ["write_dataset"])

    response = test_client.get("/api/v1/datasets/1/versions", headers={"X-API-Key": token})

    assert response.status_code == 403


def test_api_dataset_versions_requires_an_api_key(test_client):
    test_client.get("/logout", follow_redirects=True)

    assert test_client.get("/api/v1/datasets/1/versions").status_code == 401


def test_api_dataset_versions_not_found_returns_404(test_client):
    token = _api_token(test_client, ["read_dataset"])

    response = test_client.get("/api/v1/datasets/999999/versions", headers={"X-API-Key": token})

    assert response.status_code == 404
    assert response.get_json()["error"] == "Dataset not found"


def test_api_lineage_by_concept_doi_resolves_the_latest_version(test_client):
    token = _api_token(test_client, ["read_dataset"])
    v1, v2 = _seed_lineage("concept-api@example.com", "10.5072/zenodo.7100", "10.5072/zenodo.710")

    response = test_client.get("/api/v1/datasets/concept-doi/10.5072/zenodo.7100", headers={"X-API-Key": token})

    assert response.status_code == 200
    body = response.get_json()
    assert body["concept_doi"] == "10.5072/zenodo.7100"
    assert body["latest"]["dataset_id"] == v2.id
    assert [entry["dataset_id"] for entry in body["versions"]] == [v1.id, v2.id]


def test_api_lineage_by_concept_doi_not_found_returns_404(test_client):
    token = _api_token(test_client, ["read_dataset"])

    response = test_client.get("/api/v1/datasets/concept-doi/10.5072/zenodo.404", headers={"X-API-Key": token})

    assert response.status_code == 404


def test_api_lineage_by_concept_doi_requires_read_scope(test_client):
    token = _api_token(test_client, ["write_dataset"])

    response = test_client.get("/api/v1/datasets/concept-doi/10.5072/zenodo.1", headers={"X-API-Key": token})

    assert response.status_code == 403


def test_api_dataset_by_doi_exposes_the_newer_version(test_client):
    # A client holding an old DOI must be able to discover the newest version.
    token = _api_token(test_client, ["read_dataset"])
    v1, v2 = _seed_lineage("old-doi@example.com", "10.5072/zenodo.7200", "10.5072/zenodo.720")

    response = test_client.get("/api/v1/datasets/doi/10.5072/zenodo.720.1", headers={"X-API-Key": token})

    assert response.status_code == 200
    body = response.get_json()
    # Existing keys keep working.
    assert body["dataset_id"] == v1.id
    assert body["doi"] == "10.5072/zenodo.720.1"
    assert body["title"] == "Lineage v1"
    assert "files" in body
    # Lineage discovery.
    assert body["concept_doi"] == "10.5072/zenodo.7200"
    assert body["version"] == 1
    assert body["total_versions"] == 2
    assert body["is_latest"] is False
    assert body["latest"] == {"dataset_id": v2.id, "version": 2, "doi": "10.5072/zenodo.720.2"}
    assert body["versions_url"].endswith(f"/api/v1/datasets/{v1.id}/versions")


# --- Ownership transfer ---------------------------------------------------


def test_api_transfer_requires_an_api_key(test_client):
    test_client.get("/logout", follow_redirects=True)

    assert test_client.post("/api/v1/datasets/1/transfer").status_code == 401


def test_api_transfer_requires_write_scope(test_client):
    token = _api_token(test_client, ["read_dataset"])

    response = test_client.post("/api/v1/datasets/1/transfer", headers={"X-API-Key": token})

    assert response.status_code == 403


def test_api_transfer_not_found_returns_404(test_client):
    token = _api_token(test_client, ["write_dataset"])

    with patch.object(dataset_routes.dataset_service, "get_by_id", return_value=None):
        response = test_client.post("/api/v1/datasets/999999/transfer", headers={"X-API-Key": token})

    assert response.status_code == 404


def test_api_transfer_forbidden_for_another_users_dataset(test_client):
    token = _api_token(test_client, ["write_dataset"], email="rival@example.com")

    with patch.object(dataset_routes.dataset_service, "get_by_id", return_value=MagicMock(user_id=424242)):
        response = test_client.post("/api/v1/datasets/1/transfer", headers={"X-API-Key": token}, json={"user_id": 1})

    assert response.status_code == 403
    assert "own" in response.get_json()["error"]


def test_api_transfer_without_target_returns_400(test_client):
    token = _api_token(test_client, ["write_dataset"])
    owned = MagicMock(user_id=_test_user_id(test_client))

    with patch.object(dataset_routes.dataset_service, "get_by_id", return_value=owned):
        response = test_client.post("/api/v1/datasets/1/transfer", headers={"X-API-Key": token}, json={})

    assert response.status_code == 400
    assert "target account is required" in response.get_json()["error"]


def test_api_transfer_unknown_target_returns_404(test_client):
    token = _api_token(test_client, ["write_dataset"])
    owned = MagicMock(user_id=_test_user_id(test_client))

    with patch.object(dataset_routes.dataset_service, "get_by_id", return_value=owned):
        response = test_client.post(
            "/api/v1/datasets/1/transfer",
            headers={"X-API-Key": token},
            json={"email": "nobody@example.com"},
        )

    assert response.status_code == 404
    assert response.get_json()["error"] == "Target account not found"


def test_api_transfer_to_the_current_owner_returns_400(test_client):
    token = _api_token(test_client, ["write_dataset"])
    owner_id = _test_user_id(test_client)
    (dataset,) = _seed_lineage(
        "transfer-noop@example.com", "10.5072/zenodo.7300", "10.5072/zenodo.730", versions=1, user_id=owner_id
    )

    response = test_client.post(
        f"/api/v1/datasets/{dataset.id}/transfer",
        headers={"X-API-Key": token},
        json={"user_id": owner_id},
    )

    assert response.status_code == 400
    assert "already belongs" in response.get_json()["error"]


def test_api_transfer_offers_the_lineage_and_moves_it_only_once_accepted(test_client, tmp_path, monkeypatch):
    # Nothing moves on the sender's word alone: a published dataset carries a
    # permanent DOI and shows up in its owner's public listings, so the
    # receiving account has to say yes. Once it does, the whole lineage travels
    # together; a half-moved lineage would be unversionable by both accounts.
    from app.features.auth.repositories import UserRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    token = _api_token(test_client, ["write_dataset"])
    owner_id = _test_user_id(test_client)
    v1, v2 = _seed_lineage("transfer-api@example.com", "10.5072/zenodo.7400", "10.5072/zenodo.740", user_id=owner_id)
    service_account = UserRepository().create(email="service-account@example.com", password="pw-123456")

    with patch("app.features.mail.services.MailService"):
        response = test_client.post(
            f"/api/v1/datasets/{v1.id}/transfer",
            headers={"X-API-Key": token},
            json={"email": "service-account@example.com"},
        )

    assert response.status_code == 202
    body = response.get_json()
    assert body["status"] == "pending"
    assert body["to_user_id"] == service_account.id
    assert body["lineage_dataset_ids"] == [v1.id, v2.id]
    # Still the sender's until the offer is answered.
    assert v1.user_id == owner_id
    assert v2.user_id == owner_id

    # The sender cannot accept on the recipient's behalf.
    refused = test_client.post(f"/api/v1/datasets/transfers/{body['transfer_id']}/accept", headers={"X-API-Key": token})
    assert refused.status_code == 403
    assert v1.user_id == owner_id

    recipient_token = _api_token(test_client, ["write_dataset"], email="service-account@example.com")
    with patch("app.features.mail.services.MailService"):
        accepted = test_client.post(
            f"/api/v1/datasets/transfers/{body['transfer_id']}/accept",
            headers={"X-API-Key": recipient_token},
        )

    assert accepted.status_code == 200
    accepted_body = accepted.get_json()
    assert accepted_body["status"] == "accepted"
    assert accepted_body["previous_owner_id"] == owner_id
    assert accepted_body["new_owner_id"] == service_account.id
    assert accepted_body["transferred_dataset_ids"] == [v1.id, v2.id]
    assert v1.user_id == service_account.id
    assert v2.user_id == service_account.id

    # The previous owner can no longer version it; the new owner is in charge.
    denied = test_client.post(
        f"/api/v1/datasets/{v2.id}/new-version",
        headers={"X-API-Key": token},
        data={"file": (io.BytesIO(b"features\n    Root"), "v3.uvl")},
        content_type="multipart/form-data",
    )
    assert denied.status_code == 403


def test_api_transfer_can_be_declined_and_the_dataset_stays_put(test_client, tmp_path, monkeypatch):
    from app.features.auth.repositories import UserRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    token = _api_token(test_client, ["write_dataset"])
    owner_id = _test_user_id(test_client)
    (dataset,) = _seed_lineage(
        "transfer-declined@example.com", "10.5072/zenodo.7600", "10.5072/zenodo.760", versions=1, user_id=owner_id
    )
    UserRepository().create(email="declining-account@example.com", password="pw-123456")

    with patch("app.features.mail.services.MailService"):
        offer = test_client.post(
            f"/api/v1/datasets/{dataset.id}/transfer",
            headers={"X-API-Key": token},
            json={"email": "declining-account@example.com"},
        )
        transfer_id = offer.get_json()["transfer_id"]
        recipient_token = _api_token(test_client, ["write_dataset"], email="declining-account@example.com")
        declined = test_client.post(
            f"/api/v1/datasets/transfers/{transfer_id}/decline", headers={"X-API-Key": recipient_token}
        )

    assert declined.status_code == 200
    assert declined.get_json()["status"] == "declined"
    assert dataset.user_id == owner_id

    read_token = _api_token(test_client, ["read_dataset"])
    listed = test_client.get("/api/v1/datasets/transfers", headers={"X-API-Key": read_token})
    assert listed.status_code == 200
    outgoing = {entry["transfer_id"]: entry["status"] for entry in listed.get_json()["outgoing"]}
    assert outgoing[transfer_id] == "declined"


@pytest.mark.parametrize("bad_user_id", [True, 1.9])
def test_api_transfer_rejects_a_user_id_that_is_not_a_whole_number(test_client, bad_user_id):
    # int(True) is 1 and int(1.9) is 1, so a permissive cast would offer the
    # dataset to whichever account holds id 1.
    token = _api_token(test_client, ["write_dataset"])
    owner_id = _test_user_id(test_client)
    (dataset,) = _seed_lineage(
        f"transfer-coerce-{str(bad_user_id).lower()}@example.com",
        "10.5072/zenodo.7700",
        f"10.5072/zenodo.77{int(bad_user_id)}",
        versions=1,
        user_id=owner_id,
    )

    response = test_client.post(
        f"/api/v1/datasets/{dataset.id}/transfer",
        headers={"X-API-Key": token},
        json={"user_id": bad_user_id},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "user_id must be an integer."
    assert dataset.user_id == owner_id


def test_api_versions_reports_every_branch_of_a_split_lineage(test_client):
    # Legacy rows can hold two children of the same node. A client asking for
    # the newest version must not be handed a sibling while a published
    # version is missing from the listing entirely.
    from app.features.dataset.models import PublicationType
    from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository

    token = _api_token(test_client, ["read_dataset"])
    owner_id = _test_user_id(test_client)
    (v1,) = _seed_lineage(
        "branched-api@example.com", "10.5072/zenodo.7800", "10.5072/zenodo.780", versions=1, user_id=owner_id
    )

    def branch(doi):
        meta = DSMetaDataRepository().create(
            title="branch",
            description="d",
            publication_type=PublicationType.BOOK,
            dataset_doi=doi,
            dataset_concept_doi="10.5072/zenodo.7800",
            deposition_id=2,
            tags="",
        )
        return DataSetRepository().create(
            user_id=owner_id, ds_meta_data_id=meta.id, dataset_version=2, dataset_origin_id=v1.id
        )

    branch_a = branch("10.5072/zenodo.780.2a")
    branch_b = branch("10.5072/zenodo.780.2b")

    response = test_client.get(f"/api/v1/datasets/{branch_b.id}/versions", headers={"X-API-Key": token})

    assert response.status_code == 200
    body = response.get_json()
    assert body["total_versions"] == 3
    assert [entry["dataset_id"] for entry in body["versions"]] == [v1.id, branch_a.id, branch_b.id]
    assert body["latest"]["dataset_id"] == branch_b.id

    # And the DOI of the newest branch resolves to itself, not to a sibling.
    by_doi = test_client.get("/api/v1/datasets/doi/10.5072/zenodo.780.2b", headers={"X-API-Key": token})
    assert by_doi.status_code == 200
    assert by_doi.get_json()["is_latest"] is True


# --- Optional authors on the upload API -----------------------------------


def _link_orcid(orcid_id, email):
    """Register an ORCID as belonging to a uvlhub account.

    Mirrors what the ORCID OAuth flow leaves behind once a researcher has
    signed in here at least once.
    """
    from app import db
    from app.features.auth.models import User
    from app.features.orcid.models import Orcid
    from app.features.profile.models import UserProfile

    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(email=email, password="test1234")
        db.session.add(user)
        db.session.commit()
    profile = UserProfile.query.filter_by(user_id=user.id).first()
    if profile is None:
        profile = UserProfile(user_id=user.id, name="Ada", surname="Lovelace")
        db.session.add(profile)
        db.session.commit()
    if Orcid.query.filter_by(orcid_id=orcid_id).first() is None:
        db.session.add(Orcid(orcid_id=orcid_id, profile_id=profile.id))
        db.session.commit()
    return user


def test_api_upload_credits_the_authors_it_is_given(test_client):
    # The marketplace publishes with its own key while crediting the developer.
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["write_dataset"])
    _link_orcid("0000-0002-1825-0097", "ada@example.com")

    response = test_client.post(
        "/api/v1/datasets/upload",
        headers={"X-API-Key": token},
        json={
            "title": "Credited model",
            "filename": "credited.uvl",
            "uvl_content": "features\n    Root",
            "authors": [
                {"name": "Lovelace, Ada", "affiliation": "Analytical Engine", "orcid": "0000-0002-1825-0097"},
                {"name": "Hopper, Grace"},
            ],
        },
    )

    assert response.status_code == 201
    body = response.get_json()
    assert [author["name"] for author in body["authors"]] == ["Lovelace, Ada", "Hopper, Grace"]

    dataset = dataset_routes.dataset_service.get_by_id(body["dataset_id"])
    stored = [(author.name, author.affiliation, author.orcid) for author in dataset.ds_meta_data.authors]
    assert stored == [
        ("Lovelace, Ada", "Analytical Engine", "0000-0002-1825-0097"),
        ("Hopper, Grace", "", ""),
    ]

    # And they reach Zenodo, not only the local database.
    metadata = dataset_routes.zenodo_service.build_metadata(dataset)
    assert metadata["creators"] == [
        {"name": "Lovelace, Ada", "affiliation": "Analytical Engine", "orcid": "0000-0002-1825-0097"},
        {"name": "Hopper, Grace"},
    ]
    # Credit given to someone else stays traceable to the account that claimed
    # it, on the permanent record itself.
    assert dataset.ds_meta_data.api_publisher_user_id == _test_user_id(test_client)
    assert f"uvlhub account {_test_user_id(test_client)}" in metadata["notes"]


def test_api_upload_refuses_an_orcid_that_belongs_to_nobody_here(test_client):
    # An ORCID is machine resolvable: Zenodo turns it into a permanent link to
    # that researcher's profile. Accepting one on the word of whoever holds an
    # API key is enough to pin an arbitrary record on a real named person.
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["write_dataset"])

    with patch.object(dataset_routes.dataset_service, "create_draft_from_uvl_import") as mock_create:
        response = test_client.post(
            "/api/v1/datasets/upload",
            headers={"X-API-Key": token},
            json={
                "title": "Planted credit",
                "uvl_content": "features\n    Root",
                "authors": [{"name": "Carberry, Josiah", "orcid": "0000-0003-1419-2405"}],
            },
        )

    assert response.status_code == 400
    assert "not linked to any uvlhub account" in response.get_json()["error"]
    mock_create.assert_not_called()


def test_api_upload_sanitizes_the_description_it_stores(test_client):
    # The dataset page renders the description with |safe, so an API key must
    # not be able to run script on a public DOI landing page.
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["write_dataset"])

    response = test_client.post(
        "/api/v1/datasets/upload",
        headers={"X-API-Key": token},
        json={
            "title": "Scripted description",
            "filename": "scripted.uvl",
            "uvl_content": "features\n    Root",
            "description": '<img src=x onerror="alert(1)"><b>bold</b><script>alert(2)</script>',
        },
    )

    assert response.status_code == 201
    dataset = dataset_routes.dataset_service.get_by_id(response.get_json()["dataset_id"])
    description = dataset.ds_meta_data.description
    assert "onerror" not in description
    assert "<script>" not in description
    assert "<img" not in description
    # The formatting the web upload has always allowed survives.
    assert "<b>bold</b>" in description


def test_api_upload_strips_control_characters_from_the_author_name(test_client):
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["write_dataset"])

    response = test_client.post(
        "/api/v1/datasets/upload",
        headers={"X-API-Key": token},
        json={
            "title": "Spoofed author",
            "filename": "spoofed.uvl",
            "uvl_content": "features\n    Root",
            "authors": [{"name": "Bad‮Name\nwith newline\tand tab"}],
        },
    )

    assert response.status_code == 201
    dataset = dataset_routes.dataset_service.get_by_id(response.get_json()["dataset_id"])
    assert [author.name for author in dataset.ds_meta_data.authors] == ["BadName with newline and tab"]


def test_api_upload_accepts_authors_as_a_multipart_json_field(test_client):
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["write_dataset"])

    response = test_client.post(
        "/api/v1/datasets/upload",
        headers={"X-API-Key": token},
        data={
            "title": "Multipart credited model",
            "authors": '[{"name": "Hopper, Grace", "affiliation": "US Navy"}]',
            "uvl_file": (io.BytesIO(b"features\n    Root"), "credited_multipart.uvl"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    dataset = dataset_routes.dataset_service.get_by_id(response.get_json()["dataset_id"])
    assert [author.name for author in dataset.ds_meta_data.authors] == ["Hopper, Grace"]
    assert dataset.ds_meta_data.authors[0].affiliation == "US Navy"


def test_api_upload_without_authors_keeps_crediting_the_key_owner(test_client):
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["write_dataset"])

    response = test_client.post(
        "/api/v1/datasets/upload",
        headers={"X-API-Key": token},
        json={"title": "Uncredited model", "filename": "uncredited.uvl", "uvl_content": "features\n    Root"},
    )

    assert response.status_code == 201
    dataset = dataset_routes.dataset_service.get_by_id(response.get_json()["dataset_id"])
    assert [author.name for author in dataset.ds_meta_data.authors] == ["User, Test"]


def test_api_upload_rejects_invalid_author_data(test_client):
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["write_dataset"])

    with patch.object(dataset_routes.dataset_service, "create_draft_from_uvl_import") as mock_create:
        response = test_client.post(
            "/api/v1/datasets/upload",
            headers={"X-API-Key": token},
            json={
                "title": "Bad author model",
                "uvl_content": "features\n    Root",
                "authors": [{"name": "Ada", "orcid": "0000-0002-1825-0096"}],
            },
        )

    assert response.status_code == 400
    assert "ORCID" in response.get_json()["error"]
    mock_create.assert_not_called()


def test_api_upload_rejects_an_author_without_a_name(test_client):
    test_client.get("/logout", follow_redirects=True)
    token = _api_token(test_client, ["write_dataset"])

    response = test_client.post(
        "/api/v1/datasets/upload",
        headers={"X-API-Key": token},
        json={
            "title": "Nameless author model",
            "uvl_content": "features\n    Root",
            "authors": [{"affiliation": "Uni"}],
        },
    )

    assert response.status_code == 400
    assert "name" in response.get_json()["error"]


def test_api_transfer_to_an_inactive_account_returns_400(test_client):
    from app.features.auth.repositories import UserRepository

    token = _api_token(test_client, ["write_dataset"])
    owner_id = _test_user_id(test_client)
    (dataset,) = _seed_lineage(
        "transfer-inactive@example.com", "10.5072/zenodo.7500", "10.5072/zenodo.750", versions=1, user_id=owner_id
    )
    inactive = UserRepository().create(email="inactive-account@example.com", password="pw-123456")
    inactive.active = False
    UserRepository().session.commit()

    response = test_client.post(
        f"/api/v1/datasets/{dataset.id}/transfer",
        headers={"X-API-Key": token},
        json={"email": "inactive-account@example.com"},
    )

    assert response.status_code == 400
    assert "not active" in response.get_json()["error"]
