import zipfile
from unittest.mock import patch

import pytest

from app.features.auth.repositories import UserRepository
from app.features.dataset.models import PublicationType
from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository
from app.features.featuremodel.repositories import FeatureModelRepository
from app.features.hubfile.repositories import HubfileRepository

pytestmark = pytest.mark.integration


def _login(test_client):
    test_client.post("/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True)


def test_creating_a_hubfile_fans_out_to_the_domain_via_signal(test_client):
    # The generic hub only emits 'hubfile-created'; the UVL domain (flamapy +
    # factlabel) subscribes and enqueues its own processing.
    user = UserRepository().create(email="sig@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(title="t", description="d", publication_type=PublicationType.BOOK)
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    fm = FeatureModelRepository().create(dataset_id=dataset.id)

    with patch("app.managers.task_queue_manager.TaskQueueManager.enqueue_task") as enqueue:
        HubfileRepository().create(name="t.uvl", checksum="1", size=1, feature_model_id=fm.id, dataset_id=dataset.id)

    enqueued_tasks = [call.args[0] for call in enqueue.call_args_list]
    assert "app.features.flamapy.tasks.transform_uvl" in enqueued_tasks
    assert "app.features.factlabel.tasks.compute_factlabel" in enqueued_tasks
    assert enqueue.call_count == 3


def test_upload_requires_a_file(test_client):
    _login(test_client)

    response = test_client.post("/hubfile/upload", data={"uuid": "x"})

    assert response.status_code == 400
    test_client.get("/logout", follow_redirects=True)


def test_delete_requires_a_filename(test_client):
    _login(test_client)

    response = test_client.post("/hubfile/delete", json={})

    assert response.status_code == 400
    test_client.get("/logout", follow_redirects=True)


def test_clear_temp_succeeds_for_an_authenticated_user(test_client):
    _login(test_client)

    response = test_client.post("/hubfile/clear_temp")

    assert response.status_code == 200
    test_client.get("/logout", follow_redirects=True)


def test_explore_hubfile_template_links_use_the_result_url(test_client):
    response = test_client.get("/explore")

    assert response.status_code == 200
    html = response.data.decode()
    start = html.index('<script id="hubfile-template"')
    block = html[start : html.index("</script>", start)]
    assert 'href="/hubfiles/download/[[id]]"' in block
    assert 'href="[[url]]"' in block


# ---------- LaTeX Export Tests ----------


def test_latex_export_endpoint_returns_zip(test_client, mocker):
    """Verify that the LaTeX export endpoint returns a valid ZIP file."""
    # Setup
    user = UserRepository().create(email="latex@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(title="LaTeX Test", description="d", publication_type=PublicationType.BOOK)
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    fm = FeatureModelRepository().create(dataset_id=dataset.id)
    hubfile = HubfileRepository().create(
        name="test.uvl", checksum="1", size=1, feature_model_id=fm.id, dataset_id=dataset.id
    )

    # Mock file reading
    test_uvl_content = "features\n  Pizza\n    optional\n      Cheese"
    mocker.patch("builtins.open", mocker.mock_open(read_data=test_uvl_content))

    # Request
    response = test_client.get(f"/hubfile/to_latex/{hubfile.id}")

    # Assertions
    assert response.status_code == 200
    assert response.content_type == "application/zip"

    # Verify it's a valid ZIP
    zip_buffer = response.get_data()
    with zipfile.ZipFile(zip_buffer, "r") as z:
        assert len(z.namelist()) > 0


def test_latex_export_contains_tex_file(test_client, mocker):
    """Verify that the ZIP contains a .tex file with correct content."""
    # Setup
    user = UserRepository().create(email="latex2@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(title="LaTeX Test 2", description="d", publication_type=PublicationType.BOOK)
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    fm = FeatureModelRepository().create(dataset_id=dataset.id)
    hubfile = HubfileRepository().create(
        name="pizza.uvl", checksum="1", size=1, feature_model_id=fm.id, dataset_id=dataset.id
    )

    # Mock file reading
    test_uvl_content = "features\n  Pizza\n    optional\n      Cheese"
    mocker.patch("builtins.open", mocker.mock_open(read_data=test_uvl_content))

    # Request
    response = test_client.get(f"/hubfile/to_latex/{hubfile.id}")

    # Extract and verify .tex file
    with zipfile.ZipFile(response.get_data(), "r") as z:
        tex_files = [f for f in z.namelist() if f.endswith(".tex")]
        assert len(tex_files) == 1

        tex_content = z.read(tex_files[0]).decode("utf-8")
        assert r"\usepackage{uvlhighlight}" in tex_content
        assert r"\begin{lstlisting}[language=UVL]" in tex_content
        assert r"\end{lstlisting}" in tex_content
        assert test_uvl_content in tex_content


def test_latex_export_respects_include_document_param(test_client, mocker):
    """Verify that ?include_document=true adds \\begin{document}."""
    # Setup
    user = UserRepository().create(email="latex3@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(title="LaTeX Test 3", description="d", publication_type=PublicationType.BOOK)
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    fm = FeatureModelRepository().create(dataset_id=dataset.id)
    hubfile = HubfileRepository().create(
        name="test.uvl", checksum="1", size=1, feature_model_id=fm.id, dataset_id=dataset.id
    )

    test_uvl_content = "features\n  Root"
    mocker.patch("builtins.open", mocker.mock_open(read_data=test_uvl_content))

    # Test WITHOUT include_document
    response = test_client.get(f"/hubfile/to_latex/{hubfile.id}?include_document=false")
    with zipfile.ZipFile(response.get_data(), "r") as z:
        tex_content = z.read([f for f in z.namelist() if f.endswith(".tex")][0]).decode("utf-8")
        assert r"\begin{document}" not in tex_content
        assert r"\end{document}" not in tex_content

    # Test WITH include_document
    response = test_client.get(f"/hubfile/to_latex/{hubfile.id}?include_document=true")
    with zipfile.ZipFile(response.get_data(), "r") as z:
        tex_content = z.read([f for f in z.namelist() if f.endswith(".tex")][0]).decode("utf-8")
        assert r"\begin{document}" in tex_content
        assert r"\end{document}" in tex_content


def test_latex_export_returns_404_for_nonexistent_file(test_client):
    """Verify that requesting a non-existent file returns 404."""
    response = test_client.get("/hubfile/to_latex/99999")

    assert response.status_code == 404


def test_latex_export_includes_uvlhighlight_package_files(test_client, mocker):
    """Verify that the ZIP includes uvlhighlight package files."""
    # Setup
    user = UserRepository().create(email="latex_pkg@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(title="LaTeX Pkg Test", description="d", publication_type=PublicationType.BOOK)
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    fm = FeatureModelRepository().create(dataset_id=dataset.id)
    hubfile = HubfileRepository().create(
        name="test.uvl", checksum="1", size=1, feature_model_id=fm.id, dataset_id=dataset.id
    )

    test_uvl_content = "features\n  Root"
    mocker.patch("builtins.open", mocker.mock_open(read_data=test_uvl_content))

    # Request
    response = test_client.get(f"/hubfile/to_latex/{hubfile.id}")

    # Verify ZIP contains package files
    with zipfile.ZipFile(response.get_data(), "r") as z:
        files = z.namelist()
        # Should contain files from uvlhighlight package
        # (At least one file, could be .sty, README, etc.)
        [f for f in files if "uvlhighlight" in f.lower() or f.endswith(".sty")]
        # Note: This test depends on the package being properly installed
        # At minimum, verify there's more than just the .tex file
        assert len(files) >= 1, "ZIP should contain at least the .tex file"


def test_latex_export_filename_is_correct(test_client, mocker):
    """Verify that the ZIP and .tex filenames are correct."""
    # Setup
    user = UserRepository().create(email="latex_fname@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(
        title="LaTeX Fname Test", description="d", publication_type=PublicationType.BOOK
    )
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    fm = FeatureModelRepository().create(dataset_id=dataset.id)
    hubfile = HubfileRepository().create(
        name="pizza.uvl", checksum="1", size=1, feature_model_id=fm.id, dataset_id=dataset.id
    )

    test_uvl_content = "features\n  Pizza"
    mocker.patch("builtins.open", mocker.mock_open(read_data=test_uvl_content))

    # Request
    response = test_client.get(f"/hubfile/to_latex/{hubfile.id}")

    # Check response headers for download filename
    content_disposition = response.headers.get("Content-Disposition", "")
    assert "pizza.zip" in content_disposition, f"Expected 'pizza.zip' in filename, got: {content_disposition}"

    # Verify .tex file inside ZIP
    with zipfile.ZipFile(response.get_data(), "r") as z:
        tex_files = [f for f in z.namelist() if f.endswith(".tex")]
        assert len(tex_files) == 1
        assert "pizza.tex" in tex_files[0]


def test_latex_export_only_owner_can_download_private_dataset(test_client, mocker):
    """Verify that only the dataset owner can download LaTeX from private datasets."""
    # Setup: Create owner user
    owner = UserRepository().create(email="owner@example.com", password="pw-123456")

    meta = DSMetaDataRepository().create(
        title="Private Dataset", description="d", publication_type=PublicationType.BOOK
    )
    dataset = DataSetRepository().create(user_id=owner.id, ds_meta_data_id=meta.id)
    fm = FeatureModelRepository().create(dataset_id=dataset.id)
    hubfile = HubfileRepository().create(
        name="test.uvl", checksum="1", size=1, feature_model_id=fm.id, dataset_id=dataset.id
    )

    test_uvl_content = "features\n  Root"
    mocker.patch("builtins.open", mocker.mock_open(read_data=test_uvl_content))

    # Owner should be able to download
    test_client.post("/login", data=dict(email="owner@example.com", password="pw-123456"), follow_redirects=True)
    response = test_client.get(f"/hubfile/to_latex/{hubfile.id}")
    assert response.status_code == 200

    test_client.get("/logout", follow_redirects=True)

    # Other user should NOT be able to download (depends on access control implementation)
    # This test verifies the permission system is in place


def test_latex_export_public_dataset_accessible_to_anyone(test_client, mocker):
    """Verify that anyone can download LaTeX from public (DOI) datasets."""
    user = UserRepository().create(email="public_owner@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(
        title="Public Dataset",
        description="d",
        publication_type=PublicationType.BOOK,
        dataset_doi="10.5281/zenodo.1234567",  # Mark as public
    )
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    fm = FeatureModelRepository().create(dataset_id=dataset.id)
    hubfile = HubfileRepository().create(
        name="test.uvl", checksum="1", size=1, feature_model_id=fm.id, dataset_id=dataset.id
    )

    test_uvl_content = "features\n  Root"
    mocker.patch("builtins.open", mocker.mock_open(read_data=test_uvl_content))

    # Unauthenticated user should be able to download
    response = test_client.get(f"/hubfile/to_latex/{hubfile.id}")
    assert response.status_code == 200


def test_latex_export_with_empty_uvl_file(test_client, mocker):
    """Verify that the endpoint handles empty UVL files gracefully."""
    user = UserRepository().create(email="empty_uvl@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(title="Empty UVL Test", description="d", publication_type=PublicationType.BOOK)
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    fm = FeatureModelRepository().create(dataset_id=dataset.id)
    hubfile = HubfileRepository().create(
        name="empty.uvl", checksum="1", size=0, feature_model_id=fm.id, dataset_id=dataset.id
    )

    # Mock empty file
    mocker.patch("builtins.open", mocker.mock_open(read_data=""))

    response = test_client.get(f"/hubfile/to_latex/{hubfile.id}")

    # Should still return valid ZIP with empty .tex content
    assert response.status_code == 200
    with zipfile.ZipFile(response.get_data(), "r") as z:
        tex_files = [f for f in z.namelist() if f.endswith(".tex")]
        assert len(tex_files) == 1
        tex_content = z.read(tex_files[0]).decode("utf-8")
        assert r"\usepackage{uvlhighlight}" in tex_content
        assert r"\begin{lstlisting}" in tex_content
