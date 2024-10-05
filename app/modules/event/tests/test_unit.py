import tempfile
import os

from app import event_service


def test_consume_new_hubfile():
    with tempfile.NamedTemporaryFile(suffix='.uvl', delete=False) as temp_file:
        temp_file.write(b"""features
    Chat
        mandatory
            Connection
                alternative
                    "Peer 2 Peer"
                    Server
            Messages
                or
                    Text
                    Video
                    Audio
        optional
            "Data Storage"
            "Media Player"

constraints
    Server => "Data Storage"
    Video | Audio => "Media Player"
""")
        path = temp_file.name
        event = {"event_type": "hubfile_created", "event_data": {"path": path}}

    event_service._new_hubfile(event)

    json_path = path.replace(".uvl", ".json")
    cnf_path = path.replace(".uvl", ".cnf")
    splx_path = path.replace(".uvl", ".splx")
    assert os.path.exists(json_path)
    assert os.path.exists(cnf_path)
    assert os.path.exists(splx_path)
