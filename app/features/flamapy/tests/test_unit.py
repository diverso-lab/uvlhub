import pytest

from app.features.flamapy.formats import DERIVED_FORMATS, derived_format_path, missing_derived_formats
from app.features.flamapy.services import _UVLErrorListener

pytestmark = pytest.mark.unit


def test_error_listener_starts_empty():
    assert _UVLErrorListener().errors == []


def test_derived_format_path_places_each_format_in_its_sibling_folder():
    uvl = "/data/uploads/user_1/dataset_5/uvl/model.uvl"
    assert derived_format_path(uvl, "glencoe") == "/data/uploads/user_1/dataset_5/glencoe/model.json"
    assert derived_format_path(uvl, "dimacs") == "/data/uploads/user_1/dataset_5/dimacs/model.cnf"
    assert derived_format_path(uvl, "splot") == "/data/uploads/user_1/dataset_5/splot/model.splx"


def test_derived_format_path_mirrors_the_uvl_folder():
    uvl = "/data/uploads/user_1/dataset_5/uvl/subsystems/auth/login.uvl"
    assert derived_format_path(uvl, "dimacs") == "/data/uploads/user_1/dataset_5/dimacs/subsystems/auth/login.cnf"


def test_missing_derived_formats_lists_the_absent_ones(tmp_path):
    uvl_dir = tmp_path / "uvl"
    uvl_dir.mkdir()
    uvl = uvl_dir / "model.uvl"
    uvl.write_text("features")
    (tmp_path / "glencoe").mkdir()
    (tmp_path / "glencoe" / "model.json").write_text("{}")

    missing = missing_derived_formats(str(uvl))

    assert set(missing) == set(DERIVED_FORMATS) - {"glencoe"}


def test_missing_derived_formats_empty_when_all_present(tmp_path):
    uvl_dir = tmp_path / "uvl"
    uvl_dir.mkdir()
    uvl = uvl_dir / "model.uvl"
    uvl.write_text("features")
    for fmt, ext in DERIVED_FORMATS.items():
        (tmp_path / fmt).mkdir()
        (tmp_path / fmt / f"model{ext}").write_text("x")

    assert missing_derived_formats(str(uvl)) == []


def test_error_listener_records_a_formatted_error():
    listener = _UVLErrorListener()

    listener.syntaxError(None, None, 3, 5, "unexpected token", None)

    assert len(listener.errors) == 1
    assert "Line 3:5" in listener.errors[0]
    assert "error" in listener.errors[0]
