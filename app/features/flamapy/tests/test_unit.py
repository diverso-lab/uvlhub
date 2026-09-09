import pytest

from app.features.flamapy.services import _UVLErrorListener, derived_format_path

pytestmark = pytest.mark.unit


def test_error_listener_starts_empty():
    assert _UVLErrorListener().errors == []


def test_derived_format_path_for_a_root_file():
    uvl = "/data/uploads/user_1/dataset_5/uvl/model.uvl"
    assert derived_format_path(uvl, "glencoe", ".json") == "/data/uploads/user_1/dataset_5/glencoe/model.json"


def test_derived_format_path_mirrors_the_folder():
    uvl = "/data/uploads/user_1/dataset_5/uvl/subsystems/auth/login.uvl"
    assert (
        derived_format_path(uvl, "dimacs", ".cnf") == "/data/uploads/user_1/dataset_5/dimacs/subsystems/auth/login.cnf"
    )


def test_error_listener_records_a_formatted_error():
    listener = _UVLErrorListener()

    listener.syntaxError(None, None, 3, 5, "unexpected token", None)

    assert len(listener.errors) == 1
    assert "Line 3:5" in listener.errors[0]
    assert "error" in listener.errors[0]
