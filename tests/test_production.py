"""uvlhub boots in production with the features it pins (PL-9, NEW-4).

The app is built as the production image starts it, with
ProductionConfig and every feature's production settings, and asked what
the deploy agent and a browser ask: the probes, by the container's address,
and the login page, by the public host over the TLS proxy. A feature whose
next release no longer starts in production, or a setting that only
production reads, fails here and not on the first deploy.

It is built in a process of its own: an app registers template hooks,
menus and signals for the whole process, and the other tests count them.
Its database is the test database, which it only reads, and its files go
to a temporary folder. It runs with the product's other tests:

    docker exec -u splent splent_cli_container bash -lc \
        'cd /workspace && flock /tmp/splent-test.lock splent product:test --own-tests'
"""

import json
import os
import secrets
import subprocess
import sys

import pytest
from splent_framework.fixtures.fixtures import _reset_db

HOST = "www.uvlhub.io"
MARK = "uvlhub-production-boot "

# Run in the child: build the app and report what it answers.
BOOT = f"""
import json

from uvlhub_splent import create_app

app = create_app("production")
client = app.test_client()


def answer(path, host, **headers):
    response = client.get(path, headers={{"Host": host, **headers}})
    return {{
        "status": response.status_code,
        "headers": dict(response.headers),
        "cookies": response.headers.getlist("Set-Cookie"),
    }}


print({MARK!r} + json.dumps({{
    "config": {{
        key: app.config.get(key)
        for key in ("DEBUG", "TESTING", "SERVER_NAME", "TRUSTED_HOSTS",
                    "PREFERRED_URL_SCHEME")
    }},
    "healthz": answer("/healthz", "127.0.0.1:5000"),
    "readyz": answer("/readyz", "uvlhub_splent_web_deploy:5000"),
    "login": answer("/login", {HOST!r}, **{{"X-Forwarded-Proto": "https"}}),
    "forged": answer("/login", "attacker.example", **{{"X-Forwarded-Proto": "https"}}),
}}))
"""


@pytest.fixture(scope="module")
def production(app, tmp_path_factory):
    """What the production app answered, once its tables are there."""
    with app.app_context():
        _reset_db()
    store = tmp_path_factory.mktemp("production")
    env = {
        **os.environ,
        "SPLENT_ENV": "prod",
        "SECRET_KEY": secrets.token_urlsafe(48),
        "SERVER_NAME": HOST,
        "SPLENT_TRUSTED_PROXIES": "1",
        # The test database, never the one the environment names.
        "MARIADB_DATABASE": os.environ["MARIADB_TEST_DATABASE"],
        "PROTECTED_UPLOADS_DIR": str(store / "protected_uploads"),
        "UPLOADS_DIR": str(store / "uploads"),
        "ARCHIVE_DIR": str(store / "archive"),
    }
    env.pop("TRUSTED_HOSTS", None)
    env.pop("SPLENT_COOKIE_SECURE", None)
    run = subprocess.run(
        [sys.executable, "-c", BOOT],
        env=env,
        cwd=store,
        capture_output=True,
        text=True,
        timeout=300,
    )
    reports = [line for line in run.stdout.splitlines() if line.startswith(MARK)]
    assert run.returncode == 0 and reports, run.stderr[-4000:]
    return json.loads(reports[-1].removeprefix(MARK))


def test_production_is_not_debug_and_names_the_public_host(production):
    assert production["config"] == {
        "DEBUG": False,
        "TESTING": False,
        "SERVER_NAME": HOST,
        "TRUSTED_HOSTS": [HOST, "localhost"],
        "PREFERRED_URL_SCHEME": "https",
    }


def test_the_probes_answer_by_the_containers_address(production):
    assert production["healthz"]["status"] == 200
    # The database and the session store answer.
    assert production["readyz"]["status"] == 200


def test_the_login_page_answers_by_the_public_host_over_https(production):
    login = production["login"]

    assert login["status"] == 200
    assert login["headers"]["Strict-Transport-Security"].startswith("max-age=")
    assert login["headers"]["X-Content-Type-Options"] == "nosniff"
    assert login["cookies"], "the login page opens a session"
    assert all("Secure" in cookie for cookie in login["cookies"])


def test_a_forged_host_gets_no_page_in_production(production):
    assert production["forged"]["status"] == 400
