"""Production as uvlhub runs it: one host, files on volumes and backed up
off the host, and the deploy agent alone holding the Docker socket (PL-8,
PL-4, PL-2).

The host checks build the production settings from an environment like
deploy/.env and apply them to the test app, then ask it what a request with
a forged Host gets and which host the links it builds name. The rest reads
the compose files the deploy bundle is made of: the product's, and the
production one of every feature it pins.

No database is written, so it needs no test lock of its own, but it runs
with the product's other tests:

    docker exec -u splent splent_cli_container bash -lc \
        'cd /workspace && flock /tmp/splent-test.lock splent product:test --own-tests'
"""

import http.client
import re
import tomllib
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest
import yaml
from flask import url_for

from uvlhub.config import canonical_host

PRODUCT = Path(__file__).resolve().parents[1]
COMPOSE = PRODUCT / "docker" / "docker-compose.prod.yml"
FEATURES = PRODUCT / "features"
WEB = "uvlhub_web_deploy"
HOST = "www.uvlhub.io"
SOCKET = "/var/run/docker.sock"
# The one service that may hold the socket: the deploy agent, in a
# container of its own.
AGENT = ("splent_feature_autodeploy", "splent_feature_autodeploy")
# Services whose healthcheck comes with their feature's next release, as
# (pinned folder, service). Each goes once that release is pinned; any other
# service without one is a failure. None today: nginx 1.5.0 brought its own.
HEALTHCHECK_PENDING: set[tuple[str, str]] = set()


def _services(path: Path) -> dict:
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get(
        "services"
    ) or {}


def _pinned_feature_dirs() -> list[Path]:
    pins = tomllib.loads((PRODUCT / "pyproject.toml").read_text())["tool"]["splent"]
    found = []
    for entry in pins.get("features", []) + pins.get("features_prod", []):
        namespace, _sep, name = entry.partition("/")
        folder = FEATURES / namespace.replace("-", "_") / name
        if folder.exists():
            found.append(folder)
    return found


# ── One host ─────────────────────────────────────────────────────────────


@pytest.fixture
def production_host(app):
    """The test app with the host settings production builds from its .env,
    and the scheme production builds links with outside a request."""
    from uvlhub.config import ProductionConfig

    settings = canonical_host({"SERVER_NAME": HOST})
    settings["PREFERRED_URL_SCHEME"] = ProductionConfig.PREFERRED_URL_SCHEME
    saved = {key: app.config.get(key) for key in settings}
    app.config.update(settings)
    yield app
    app.config.update(saved)


def test_production_answers_by_the_public_host():
    assert canonical_host({"SERVER_NAME": HOST}) == {
        "SERVER_NAME": HOST,
        "TRUSTED_HOSTS": [HOST, "localhost"],
    }
    assert canonical_host(
        {"SERVER_NAME": HOST, "TRUSTED_HOSTS": f"{HOST}, staff.uvlhub.io"}
    )["TRUSTED_HOSTS"] == [HOST, "staff.uvlhub.io"]
    # Unset or still the placeholder: no restriction, and a warning at boot.
    assert canonical_host({}) == {}
    assert canonical_host({"SERVER_NAME": "<SET>"}) == {}


def test_the_production_config_carries_them(monkeypatch):
    from uvlhub.config import ProductionConfig

    monkeypatch.setenv("SECRET_KEY", "a-production-key-long-enough-for-the-check")
    monkeypatch.setenv("SERVER_NAME", HOST)
    monkeypatch.delenv("TRUSTED_HOSTS", raising=False)
    config = ProductionConfig()
    assert config.SERVER_NAME == HOST
    assert config.TRUSTED_HOSTS == [HOST, "localhost"]


@pytest.mark.parametrize("forged", ["attacker.example", "uvlhub.io", "203.0.113.7"])
def test_a_forged_host_gets_no_page(production_host, forged):
    response = production_host.test_client().get("/login", headers={"Host": forged})

    assert response.status_code == 400
    page = response.get_data(as_text=True)
    assert "<aside" not in page and "<form" not in page
    assert f"//{forged}" not in page, "no link names the forged host"


def test_the_public_host_gets_the_page(production_host):
    response = production_host.test_client().get("/login", headers={"Host": HOST})
    assert response.status_code == 200
    assert "<form" in response.get_data(as_text=True)


def test_the_probes_answer_whatever_the_host(production_host):
    """/healthz and /readyz are answered before Flask: Docker's healthcheck
    and the deploy agent ask them by 127.0.0.1 and by the container's name."""
    response = production_host.test_client().get(
        "/healthz", headers={"Host": "127.0.0.1:5000"}
    )
    assert response.status_code == 200


def test_absolute_links_name_the_public_host(production_host):
    # In a request that reached the app by another name it trusts (the
    # deploy's probe uses localhost). The scheme is the request's, https
    # behind nginx.
    with production_host.test_request_context("/", headers={"Host": "localhost"}):
        assert urlsplit(url_for("auth.login", _external=True)).netloc == HOST
    # Outside any request (a command, a background task), with the scheme
    # production prefers.
    with production_host.app_context():
        assert url_for("auth.login", _external=True) == f"https://{HOST}/login"


# ── Files on volumes ─────────────────────────────────────────────────────


# source:target[:mode], where the source may be an interpolation whose
# message holds colons of its own (${VAR:?...}).
MOUNT = re.compile(r"^(\$\{[^}]*\}|[^:]*):(.+?)(?::(?:ro|rw))?$")
# ${VAR:-default}, as the storage roots are written.
DEFAULTED = re.compile(r"^\$\{[A-Z_]+:-([^}]*)\}$")


def _mounts(service: dict) -> dict[str, str]:
    """Each mount target of ``service`` and its source."""
    found = {}
    for volume in service.get("volumes") or []:
        source, target = MOUNT.match(volume).groups()
        found[target] = source
    return found


def _config() -> dict:
    pyproject = tomllib.loads((PRODUCT / "pyproject.toml").read_text())
    return pyproject["tool"]["splent"]["config"]


@pytest.mark.parametrize(
    "variable, default",
    [
        ("PROTECTED_UPLOADS_DIR", "/workspace/uvlhub/protected_uploads"),
        ("ARCHIVE_DIR", "/workspace/uvlhub/archive"),
    ],
)
def test_each_storage_root_is_the_target_of_a_named_volume(variable, default):
    compose = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    web = compose["services"][WEB]
    expression = f"${{{variable}:-{default}}}"

    # The app reads the root from the very expression the mount uses, so
    # the two cannot disagree whatever deploy/.env says.
    assert web["environment"][variable] == expression
    source = _mounts(web)[expression]
    assert source in (compose.get("volumes") or {}), "a named volume"


def test_the_public_uploads_are_on_a_named_volume():
    compose = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    mounts = _mounts(compose["services"][WEB])
    source = mounts["/workspace/uvlhub/src/uvlhub/static/uploads"]
    assert source in compose["volumes"]


def test_the_database_is_on_a_named_volume():
    compose = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    mounts = _mounts(compose["services"]["uvlhub_db_deploy"])
    assert mounts["/var/lib/mysql"] in compose["volumes"]


# ── Backups ──────────────────────────────────────────────────────────────


def test_every_setting_of_the_product_reaches_the_deploy_bundle():
    """A value in [tool.splent.config] that no feature declares stayed out of
    deploy/.env.example, so it held in development and not in production: that
    is how SEARCH_PAGE=false left search's page in front of explore's /search."""
    root = Path(__file__).resolve().parents[1]
    config = tomllib.loads((root / "pyproject.toml").read_text())["tool"]["splent"]
    example = (root / "deploy" / ".env.example").read_text()
    missing = [key for key in config["config"] if f"\n{key}=" not in f"\n{example}"]
    assert not missing


def test_every_storage_root_is_backed_up():
    """BACKUP_PATHS are the targets of the web service's named volumes, as
    they are by default: a root left out would come back empty from a
    restore, and a path that is no volume is the container's own layer."""
    compose = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    roots = set()
    for target, source in _mounts(compose["services"][WEB]).items():
        if source in (compose.get("volumes") or {}):
            defaulted = DEFAULTED.match(target)
            roots.add(defaulted.group(1) if defaulted else target)
    assert sorted(_config()["BACKUP_PATHS"]) == sorted(roots)


def test_the_backups_go_to_a_disk_mounted_from_elsewhere():
    """A directory destination is another machine's disk, which the host
    mounts and compose binds at /backups (splent_feature_backup's README).
    Never a named volume: it would be on the disk it backs up. compose
    refuses to start until the operator names it."""
    compose = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    source = _mounts(compose["services"][WEB])["/backups"]
    assert source.startswith("${BACKUP_HOST_DIR:?")
    assert source not in (compose.get("volumes") or {})
    example = (PRODUCT / "docker" / ".env.prod.example").read_text(encoding="utf-8")
    for key in ("BACKUP_HOST_DIR", "BACKUP_DESTINATION", "BACKUP_AGE_RECIPIENTS"):
        assert re.search(rf"^{key}=<SET>$", example, re.M), key


# ── Deploys ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("readyz, healthy", [(200, True), (503, False)])
def test_the_web_service_is_ready_when_readyz_says_so(monkeypatch, readyz, healthy):
    """The probe runs in the container's Python, as product:build writes it:
    healthy when /readyz answers 200, not when it answers 503 because the
    database or the session store does not."""
    test = _services(COMPOSE)[WEB]["healthcheck"]["test"]
    assert test[:3] == ["CMD", "python3", "-c"]
    asked = []

    class Connection:
        def __init__(self, host, port, timeout):
            self.address = (host, port)

        def request(self, method, path):
            asked.append((*self.address, path))

        def getresponse(self):
            return SimpleNamespace(status=readyz)

    monkeypatch.setattr(http.client, "HTTPConnection", Connection)
    with pytest.raises(SystemExit) as probe:
        exec(test[3], {})
    assert asked == [("127.0.0.1", 5000, "/readyz")]
    assert (not probe.value.code) is healthy


def test_every_long_lived_service_has_a_healthcheck():
    for folder in [PRODUCT, *_pinned_feature_dirs()]:
        compose = folder / "docker" / "docker-compose.prod.yml"
        if not compose.exists():
            continue
        for name, service in _services(compose).items():
            if (folder.name, name) in HEALTHCHECK_PENDING:
                continue
            assert "healthcheck" in service, f"{name} in {compose}"


def test_only_the_deploy_agent_holds_the_docker_socket():
    holders = []
    files = [COMPOSE] + [
        folder / "docker" / "docker-compose.prod.yml"
        for folder in _pinned_feature_dirs()
    ]
    for compose in files:
        if not compose.exists():
            continue
        for name, service in _services(compose).items():
            if any(SOCKET in str(volume) for volume in service.get("volumes") or []):
                holders.append((re.sub(r"@.*", "", compose.parents[1].name), name))
    assert holders and set(holders) <= {AGENT}, holders


def test_webhook_is_not_selected():
    """The monolith's webhook redeployed from the web container through the
    Docker socket. autodeploy replaces it."""
    pins = tomllib.loads((PRODUCT / "pyproject.toml").read_text())["tool"]["splent"]
    selected = " ".join(pins.get("features", []) + pins.get("features_prod", []))
    assert "splent_feature_webhook" not in selected
    assert "splent_feature_autodeploy" in selected
