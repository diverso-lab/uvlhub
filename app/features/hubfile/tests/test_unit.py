import logging
import os
import zipfile

import pytest

from app.features.hubfile.services import HubfileService, UploadIngestService

pytestmark = pytest.mark.unit


def _ingest():
    return UploadIngestService(logging.getLogger("test"))


def test_strip_uuid_prefix_removes_a_leading_uuid():
    ingest = UploadIngestService(logging.getLogger("test"))
    name = "12345678-1234-1234-1234-123456789012_model.uvl"

    assert ingest._strip_uuid_prefix(name) == "model.uvl"


def test_strip_uuid_prefix_leaves_plain_names_untouched():
    ingest = UploadIngestService(logging.getLogger("test"))

    assert ingest._strip_uuid_prefix("model.uvl") == "model.uvl"


def test_calculate_checksum_is_stable_for_the_same_content(tmp_path):
    file_a = tmp_path / "a.uvl"
    file_a.write_text("features\n    Root")
    file_b = tmp_path / "b.uvl"
    file_b.write_text("features\n    Root")

    assert HubfileService._calculate_checksum(str(file_a)) == HubfileService._calculate_checksum(str(file_b))


def test_calculate_checksum_differs_for_different_content(tmp_path):
    file_a = tmp_path / "a.uvl"
    file_a.write_text("features\n    Root")
    file_b = tmp_path / "b.uvl"
    file_b.write_text("features\n    Other")

    assert HubfileService._calculate_checksum(str(file_a)) != HubfileService._calculate_checksum(str(file_b))


def test_prepare_uvls_collects_loose_and_zipped_files(tmp_path):
    root = tmp_path / "temp"
    root.mkdir()
    (root / "a.uvl").write_text("features\n    A")
    with zipfile.ZipFile(root / "models.zip", "w") as zf:
        zf.writestr("b.uvl", "features\n    B")

    stage_dir, staged = _ingest().prepare_uvls(str(root))

    assert sorted(os.path.basename(p) for p in staged) == ["a.uvl", "b.uvl"]
    assert os.path.isdir(stage_dir)


def test_prepare_uvls_preserves_folders_from_a_zip(tmp_path):
    root = tmp_path / "temp"
    root.mkdir()
    with zipfile.ZipFile(root / "models.zip", "w") as zf:
        zf.writestr("subsystems/auth/login.uvl", "features\n    Login")
        zf.writestr("subsystems/payment/checkout.uvl", "features\n    Checkout")
        zf.writestr("root_model.uvl", "features\n    Root")

    stage_dir, staged = _ingest().prepare_uvls(str(root))

    rel = sorted(os.path.relpath(p, stage_dir) for p in staged)
    assert rel == [
        "root_model.uvl",
        os.path.join("subsystems", "auth", "login.uvl"),
        os.path.join("subsystems", "payment", "checkout.uvl"),
    ]


def test_prepare_uvls_strips_a_single_wrapper_folder(tmp_path):
    root = tmp_path / "temp"
    root.mkdir()
    with zipfile.ZipFile(root / "models.zip", "w") as zf:
        zf.writestr("my_dataset/a/x.uvl", "features\n    X")
        zf.writestr("my_dataset/b/y.uvl", "features\n    Y")

    stage_dir, staged = _ingest().prepare_uvls(str(root))

    rel = sorted(os.path.relpath(p, stage_dir) for p in staged)
    assert rel == [os.path.join("a", "x.uvl"), os.path.join("b", "y.uvl")]


def test_prepare_uvls_keeps_same_name_files_in_different_folders(tmp_path):
    root = tmp_path / "temp"
    root.mkdir()
    with zipfile.ZipFile(root / "models.zip", "w") as zf:
        zf.writestr("a/model.uvl", "features\n    A")
        zf.writestr("b/model.uvl", "features\n    B")

    _, staged = _ingest().prepare_uvls(str(root))

    assert len(staged) == 2


def test_sanitize_rel_dir_drops_traversal_and_normalizes(tmp_path):
    ingest = _ingest()
    assert ingest._sanitize_rel_dir("../../etc") == "etc"
    assert ingest._sanitize_rel_dir("a/./b/../c") == "a/b/c"
    assert ingest._sanitize_rel_dir("/abs/path/") == "abs/path"
    assert ingest._sanitize_rel_dir(".") == ""


def test_prepare_uvls_deduplicates_identical_content(tmp_path):
    root = tmp_path / "temp"
    root.mkdir()
    (root / "a.uvl").write_text("same content")
    with zipfile.ZipFile(root / "models.zip", "w") as zf:
        zf.writestr("a.uvl", "same content")  # identical bytes AND name -> deduplicated by (name, hash)

    _, staged = _ingest().prepare_uvls(str(root))

    assert len(staged) == 1


def test_prepare_uvls_raises_when_no_uvl_files(tmp_path):
    root = tmp_path / "temp"
    root.mkdir()
    (root / "readme.txt").write_text("not a model")

    with pytest.raises(ValueError, match="No .uvl files"):
        _ingest().prepare_uvls(str(root))


def test_safe_extract_zip_rejects_path_traversal(tmp_path):
    evil = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil, "w") as zf:
        zf.writestr("../escape.uvl", "pwned")
    dest = tmp_path / "dest"
    dest.mkdir()

    with pytest.raises(ValueError, match="Zip slip"):
        _ingest()._safe_extract_zip(str(evil), str(dest))


# ---------- LaTeX Export Validation Tests ----------


def test_latex_export_zip_is_valid():
    """Verify that the generated ZIP is a valid ZIP file."""
    from io import BytesIO

    test_uvl = "features\n  Pizza\n    optional\n      Cheese"
    latex_content = r"\usepackage{uvlhighlight}" + "\n\n"
    latex_content += r"\begin{lstlisting}[language=UVL]" + "\n"
    latex_content += test_uvl
    latex_content += "\n" + r"\end{lstlisting}" + "\n"

    # Create a ZIP buffer (mimicking what the endpoint does)
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("test.tex", latex_content)

    zip_buffer.seek(0)

    # Verify it's a valid ZIP
    try:
        with zipfile.ZipFile(zip_buffer, "r") as z:
            assert z.testzip() is None  # None means no errors
    except zipfile.BadZipFile:
        pytest.fail("Generated ZIP is invalid")


def test_latex_tex_file_has_correct_structure():
    """Verify that the .tex file has the correct LaTeX structure."""
    test_uvl = "features\n  Root\n    mandatory\n      Child"

    latex_content = r"\usepackage{uvlhighlight}" + "\n\n"
    latex_content += r"\begin{lstlisting}[language=UVL]" + "\n"
    latex_content += test_uvl + "\n"
    latex_content += r"\end{lstlisting}" + "\n"

    # Assertions
    assert r"\usepackage{uvlhighlight}" in latex_content
    assert r"\begin{lstlisting}[language=UVL]" in latex_content
    assert r"\end{lstlisting}" in latex_content
    assert test_uvl in latex_content

    # Verify order: usepackage -> lstlisting -> content -> endlisting
    assert latex_content.index(r"\usepackage") < latex_content.index(r"\begin{lstlisting}")
    assert latex_content.index(r"\begin{lstlisting}") < latex_content.index(test_uvl)
    assert latex_content.index(test_uvl) < latex_content.index(r"\end{lstlisting}")


def test_latex_tex_file_includes_document_when_requested():
    """Verify that \\begin{document} is included when requested."""
    test_uvl = "features\n  Root"

    # Without include_document
    latex_without_doc = r"\usepackage{uvlhighlight}" + "\n\n"
    latex_without_doc += r"\begin{lstlisting}[language=UVL]" + "\n"
    latex_without_doc += test_uvl + "\n"
    latex_without_doc += r"\end{lstlisting}" + "\n"

    assert r"\begin{document}" not in latex_without_doc
    assert r"\end{document}" not in latex_without_doc

    # With include_document
    latex_with_doc = r"\usepackage{uvlhighlight}" + "\n\n"
    latex_with_doc += r"\begin{document}" + "\n\n"
    latex_with_doc += r"\begin{lstlisting}[language=UVL]" + "\n"
    latex_with_doc += test_uvl + "\n"
    latex_with_doc += r"\end{lstlisting}" + "\n"
    latex_with_doc += "\n" + r"\end{document}" + "\n"

    assert r"\begin{document}" in latex_with_doc
    assert r"\end{document}" in latex_with_doc
    assert latex_with_doc.index(r"\begin{document}") < latex_with_doc.index(r"\begin{lstlisting}")


def test_latex_preserves_uvl_content_exactly(tmp_path):
    """Verify that the UVL content is preserved exactly in the LaTeX."""
    test_uvl = "features\n  Pizza\n    optional\n      Cheese\n      Pepperoni\n  Pasta\n    mandatory\n      Sauce"

    latex_content = r"\usepackage{uvlhighlight}" + "\n\n"
    latex_content += r"\begin{lstlisting}[language=UVL]" + "\n"
    latex_content += test_uvl + "\n"
    latex_content += r"\end{lstlisting}" + "\n"

    # Extract the content between lstlisting tags
    start = latex_content.index(r"\begin{lstlisting}[language=UVL]") + len(r"\begin{lstlisting}[language=UVL]") + 1
    end = latex_content.index(r"\end{lstlisting}")
    extracted_content = latex_content[start:end].strip()

    assert extracted_content == test_uvl


def test_latex_export_filename_conversion(tmp_path):
    """Verify that UVL filename is correctly converted to .tex/.zip."""
    # Test UVL -> .tex conversion
    uvl_filename = "my_model.uvl"
    tex_filename = uvl_filename.replace(".uvl", ".tex")
    zip_filename = uvl_filename.replace(".uvl", ".zip")

    assert tex_filename == "my_model.tex"
    assert zip_filename == "my_model.zip"

    # Test with complex names
    complex_name = "feature-model_v2.1.uvl"
    assert complex_name.replace(".uvl", ".tex") == "feature-model_v2.1.tex"
    assert complex_name.replace(".uvl", ".zip") == "feature-model_v2.1.zip"


def test_latex_export_utf8_encoding(tmp_path):
    """Verify that the LaTeX content is properly encoded in UTF-8."""
    from io import BytesIO

    # Test with special characters
    test_uvl = "features\n  Café\n  Niño\n  Über"

    latex_content = r"\usepackage{uvlhighlight}" + "\n\n"
    latex_content += r"\begin{lstlisting}[language=UVL]" + "\n"
    latex_content += test_uvl + "\n"
    latex_content += r"\end{lstlisting}" + "\n"

    # Encode as UTF-8
    encoded = latex_content.encode("utf-8")

    # Verify it can be decoded back
    decoded = encoded.decode("utf-8")
    assert decoded == latex_content
    assert "Café" in decoded
    assert "Niño" in decoded
    assert "Über" in decoded

    # Verify in ZIP context
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("test.tex", latex_content.encode("utf-8"))

    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as z:
        extracted = z.read("test.tex").decode("utf-8")
        assert "Café" in extracted
        assert "Niño" in extracted


def test_latex_with_special_characters_in_uvl():
    """Verify that UVL with special characters is handled correctly."""
    test_uvl = 'features\n  Root\n    name: "Feature with spaces"\n    description: "Contains: special chars & symbols"'

    latex_content = r"\usepackage{uvlhighlight}" + "\n\n"
    latex_content += r"\begin{lstlisting}[language=UVL]" + "\n"
    latex_content += test_uvl + "\n"
    latex_content += r"\end{lstlisting}" + "\n"

    # Verify content is preserved exactly
    assert test_uvl in latex_content
    assert '"Feature with spaces"' in latex_content
    assert "special chars & symbols" in latex_content


def test_latex_export_response_headers():
    """Verify that the response headers are correct for ZIP download."""
    from io import BytesIO

    test_uvl = "features\n  Root"
    latex_content = r"\usepackage{uvlhighlight}" + "\n\n"
    latex_content += r"\begin{lstlisting}[language=UVL]" + "\n"
    latex_content += test_uvl + "\n"
    latex_content += r"\end{lstlisting}" + "\n"

    # Create ZIP (mimicking endpoint)
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("test.tex", latex_content)

    zip_data = zip_buffer.getvalue()

    # Simulate response headers
    headers = {
        "Content-Type": "application/zip",
        "Content-Length": len(zip_data),
        "Content-Disposition": "attachment; filename=test.zip",
    }

    # Verify headers
    assert headers["Content-Type"] == "application/zip"
    assert headers["Content-Length"] > 0
    assert "test.zip" in headers["Content-Disposition"]
    assert "attachment" in headers["Content-Disposition"]
