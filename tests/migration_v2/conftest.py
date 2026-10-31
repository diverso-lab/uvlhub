"""A MariaDB server of its own for the migrator's tests, and a dirty v2.12.

The migrator drops and creates whole databases, so its tests never touch
the development database or the shared test one (uvlhub_splent_db_test,
which other test runs use). They run on a throwaway server, of the same
major version as the product's (mariadb:11.4, docker/docker-compose.*.yml):

- started by run_with_throwaway_db.sh, which names it in
  MIGRATION_V2_TEST_DB_HOST and MIGRATION_V2_TEST_DB_ROOT_PASSWORD and
  removes it when the session ends; or
- started here when this process can reach Docker and a network
  (MIGRATION_V2_TEST_NETWORK), with a name of its own, and removed at the
  end of the session.

Without either, the tests that need it are skipped and say how to run
them. The tests run in the web container, where the features are, so the
server is reached by its name on that container's Docker network.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass, replace
from pathlib import Path

import pytest
import sqlalchemy as sa

from uvlhub_splent.migration_v2.cli import grant_statements
from uvlhub_splent.migration_v2.ledger import ensure_inputs
from uvlhub_splent.migration_v2.params import Params, Server

from . import synthetic

IMAGE = os.getenv("MIGRATION_V2_TEST_DB_IMAGE", "mariadb:11.4")
# The development and test databases' server: never this one.
SHARED_HOSTS = {"uvlhub_splent_db", "uvlhub_splent_db_test"}
SYNTHETIC_SCHEMA = "uvlhub_v2_synth"
# The prefix of the schemas a test that runs a stage on its own uses, so it
# never touches the rehearsal the other tests read.
ISOLATED = "iso"


@dataclass(frozen=True)
class TestServer:
    host: str
    root_password: str
    migrator_password: str


def _engine(host, user, password, database=None):
    url = sa.engine.URL.create(
        "mysql+pymysql",
        username=user,
        password=password,
        host=host,
        port=3306,
        database=database,
        query={"charset": "utf8mb4"},
    )
    return sa.create_engine(url, poolclass=sa.pool.NullPool)


def _wait(host, password, seconds=90):
    engine = _engine(host, "root", password)
    deadline = time.monotonic() + seconds
    try:
        while True:
            try:
                with engine.connect() as connection:
                    connection.exec_driver_sql("SELECT 1")
                return
            except sa.exc.OperationalError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(1)
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def server():
    host = os.getenv("MIGRATION_V2_TEST_DB_HOST")
    root_password = os.getenv("MIGRATION_V2_TEST_DB_ROOT_PASSWORD", "")
    container = None
    if not host:
        network = os.getenv("MIGRATION_V2_TEST_NETWORK")
        if not network or not shutil.which("docker"):
            pytest.skip(
                "the migrator's tests need a throwaway MariaDB: run "
                "tests/migration_v2/run_with_throwaway_db.sh from the CLI container, "
                "or set MIGRATION_V2_TEST_DB_HOST"
            )
        container = f"uvlhub_migv2_test_{uuid.uuid4().hex[:10]}"
        root_password = uuid.uuid4().hex
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "--name",
                container,
                "--network",
                network,
                "--memory",
                "768m",
                "-e",
                f"MARIADB_ROOT_PASSWORD={root_password}",
                IMAGE,
                "--innodb-buffer-pool-size=64M",
                "--performance-schema=OFF",
                "--skip-name-resolve",
                "--max-connections=60",
            ],
            check=True,
            capture_output=True,
        )
        host = container
    if host in SHARED_HOSTS or host == os.getenv("MARIADB_HOSTNAME"):
        pytest.fail(
            f"{host} is the product's database server; the migrator's tests use their own"
        )
    try:
        _wait(host, root_password)
        migrator_password = uuid.uuid4().hex
        engine = _engine(host, "root", root_password)
        with engine.connect() as connection:
            # text(), not exec_driver_sql: pymysql reads the % of '%' as a parameter.
            connection.execute(sa.text("DROP USER IF EXISTS 'migrator'@'%'"))
            for statement in grant_statements(
                _params(host, "", ""), "migrator", "%", migrator_password
            ):
                connection.execute(sa.text(statement))
            # The schemas of the tests that run a stage apart (isolated()).
            connection.execute(
                sa.text(f"GRANT ALL PRIVILEGES ON `{ISOLATED}\\_%`.* TO 'migrator'@'%'")
            )
            connection.commit()
        engine.dispose()
        yield TestServer(host, root_password, migrator_password)
    finally:
        if container:
            subprocess.run(
                ["docker", "rm", "-f", "-v", container],
                capture_output=True,
                check=False,
            )


def _params(host, migrator_password, root_password, **overrides) -> Params:
    server = Server(
        host=host,
        user="migrator",
        password=migrator_password,
        root_user="root",
        root_password=root_password,
    )
    params = Params(
        server=server,
        t0=synthetic.T0,
        expected_head="e5f6a7b8c9d0",
        admin_emails=("Alice@uvlhub.test",),
        operator="tests/migration_v2",
        public_id_key="the key of the public ids of the tests",
        mail_from="hub@uvlhub.test",
    )
    return replace(params, **overrides)


@pytest.fixture(scope="session")
def make_params(server):
    def make(**overrides) -> Params:
        return _params(
            server.host, server.migrator_password, server.root_password, **overrides
        )

    return make


@pytest.fixture
def isolated(make_params, root_engine):
    """Params whose five schemas are the test's own, dropped afterwards."""
    made = []

    def make(tag: str, **overrides) -> Params:
        names = {
            kind: f"{ISOLATED}_{tag}_{kind}"
            for kind in ("src", "ref", "uvlhub3", "work", "inputs")
        }
        made.extend(names.values())
        return make_params(
            source_schema=names["src"],
            reference_schema=names["ref"],
            target_schema=names["uvlhub3"],
            work_schema=names["work"],
            inputs_schema=names["inputs"],
            **overrides,
        )

    yield make
    with root_engine.connect() as connection:
        for schema in made:
            connection.exec_driver_sql(f"DROP DATABASE IF EXISTS `{schema}`")
        connection.commit()


@pytest.fixture(scope="session")
def root_engine(server):
    engine = _engine(server.host, "root", server.root_password)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def synthetic_dump(server, root_engine, tmp_path_factory) -> Path:
    """The dirty v2.12 dumped as B1's logical copy is (§9.6), then dropped,
    so only the restored copy remains, as on the day."""
    with root_engine.connect() as connection:
        synthetic.build(connection, SYNTHETIC_SCHEMA)
    dump = tmp_path_factory.mktemp("b1") / "uvlhub_v2_12.sql"
    folder = tmp_path_factory.mktemp("client")
    defaults = folder / "client.cnf"
    defaults.write_text(f"[client]\npassword={server.root_password}\n")
    defaults.chmod(0o600)
    with dump.open("wb") as out:
        subprocess.run(
            [
                shutil.which("mariadb-dump") or "mysqldump",
                f"--defaults-extra-file={defaults}",
                f"--host={server.host}",
                "--user=root",
                "--single-transaction",
                "--quick",
                "--routines",
                "--triggers",
                "--events",
                "--hex-blob",
                "--default-character-set=utf8mb4",
                SYNTHETIC_SCHEMA,
            ],
            stdout=out,
            check=True,
        )
    with root_engine.connect() as connection:
        connection.exec_driver_sql(f"DROP DATABASE `{SYNTHETIC_SCHEMA}`")
        connection.commit()
    return dump


@pytest.fixture(scope="session")
def store(tmp_path_factory) -> Path:
    """hubfile's store with v2.12's uploads/ mirrored inside it (§6.2)."""
    root = tmp_path_factory.mktemp("hubfile_store")
    synthetic.write_mirror(root / ".legacy_mirror")
    return root


@pytest.fixture(scope="session")
def seedless():
    """RUN_DB_SEED=false for the session, whatever the product's .env says."""
    before = os.environ.get("RUN_DB_SEED")
    os.environ["RUN_DB_SEED"] = "false"
    yield
    if before is None:
        os.environ.pop("RUN_DB_SEED", None)
    else:
        os.environ["RUN_DB_SEED"] = before


class ListenerSpy:
    """Every session and mapper event of the ORM, recorded while on.

    The migrator writes with Core, so a run must record none: not the
    dataset's DSMetrics after_insert, not hubfile's Session.after_commit,
    not anything a feature adds later (§3.4).
    """

    SESSION_EVENTS = (
        "after_begin",
        "after_transaction_create",
        "before_flush",
        "after_flush",
        "before_commit",
        "after_commit",
        "after_rollback",
        "after_soft_rollback",
        "before_attach",
        "after_attach",
        "do_orm_execute",
    )
    MAPPER_EVENTS = (
        "before_insert",
        "after_insert",
        "before_update",
        "after_update",
        "before_delete",
        "after_delete",
    )

    def __init__(self):
        self.fired = []
        self._listening = []

    def _recorder(self, kind, name):
        def record(*_args, **_kwargs):
            self.fired.append(f"{kind}.{name}")

        return record

    def __enter__(self):
        from sqlalchemy.orm import Mapper, Session

        for name in self.SESSION_EVENTS:
            listener = self._recorder("Session", name)
            sa.event.listen(Session, name, listener)
            self._listening.append((Session, name, listener))
        for name in self.MAPPER_EVENTS:
            listener = self._recorder("Mapper", name)
            sa.event.listen(Mapper, name, listener)
            self._listening.append((Mapper, name, listener))
        return self

    def __exit__(self, *_exc):
        for target, name, listener in self._listening:
            sa.event.remove(target, name, listener)


@dataclass
class Migrated:
    report: dict
    params: Params
    fired: list
    engine: sa.Engine


@pytest.fixture(scope="session")
def migrated(make_params, synthetic_dump, store, seedless, root_engine):
    """One rehearsal of the whole pipeline on the dirty v2.12, as R0 runs it."""
    from uvlhub_splent.migration_v2.pipeline import run

    report_path = store.parent / "report.json"
    params = make_params(
        dump=synthetic_dump,
        store_root=store,
        report=report_path,
        allow_open_conflicts=True,
        # The development's search node is shared: E9's reset is no test's
        # to make there, so it runs without one, and fails as it would.
        reindex_command=(
            "env",
            "ELASTICSEARCH_ENABLED=false",
            *Params.reindex_command,
        ),
    )
    with root_engine.connect() as connection:
        inputs = ensure_inputs(connection, params.inputs_schema)
        connection.execute(
            inputs["zenodo_snapshot"].insert(), synthetic.zenodo_snapshot()
        )
        connection.execute(inputs["zenodo_files"].insert(), synthetic.zenodo_files())
        connection.commit()
    with ListenerSpy() as spy:
        report = run(params)
    return Migrated(report=report, params=params, fired=spy.fired, engine=root_engine)
