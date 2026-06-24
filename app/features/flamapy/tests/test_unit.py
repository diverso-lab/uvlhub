import pytest

from app.features.flamapy.services import _UVLErrorListener

pytestmark = pytest.mark.unit


def test_error_listener_starts_empty():
    assert _UVLErrorListener().errors == []


def test_error_listener_records_a_formatted_error():
    listener = _UVLErrorListener()

    listener.syntaxError(None, None, 3, 5, "unexpected token", None)

    assert len(listener.errors) == 1
    assert "Line 3:5" in listener.errors[0]
    assert "error" in listener.errors[0]
