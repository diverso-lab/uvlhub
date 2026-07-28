import pytest

from app.features.auth.repositories import UserRepository
from app.features.dataset.models import PublicationType
from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository

pytestmark = pytest.mark.repository


def _dataset(doi, email):
    user = UserRepository().create(email=email, password="pw-123456")
    meta = DSMetaDataRepository().create(
        title="t", description="d", publication_type=PublicationType.BOOK, dataset_doi=doi
    )
    return DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)


def test_count_synchronized_only_counts_datasets_with_a_doi(test_app, clean_database):
    _dataset(doi="10.1/sync", email="sync@example.com")
    _dataset(doi=None, email="draft@example.com")

    repo = DataSetRepository()

    assert repo.count_synchronized_datasets() == 1
    assert repo.count_unsynchronized_datasets() == 1


def test_dataset_version_lineage(test_app, clean_database):
    user = UserRepository().create(email="lineage@example.com", password="pw-123456")
    repo = DataSetRepository()

    def make(version, origin_id=None):
        meta = DSMetaDataRepository().create(
            title=f"v{version}", description="d", publication_type=PublicationType.BOOK
        )
        return repo.create(
            user_id=user.id, ds_meta_data_id=meta.id, dataset_version=version, dataset_origin_id=origin_id
        )

    v1 = make(1)
    v2 = make(2, origin_id=v1.id)
    v3 = make(3, origin_id=v2.id)

    # Originals have version 1 and no origin.
    assert v1.dataset_version == 1
    assert v1.dataset_origin_id is None
    # Each version points back at the one it was derived from.
    assert v3.dataset_origin.id == v2.id
    assert v2.dataset_origin.id == v1.id
    # version_root() walks the chain back to the first version.
    assert v3.version_root().id == v1.id
    # The backref exposes the versions derived from a dataset.
    assert [d.id for d in v1.dataset_versions] == [v2.id]
    # all_versions() returns the whole chain oldest-first from any node.
    assert [d.id for d in v3.all_versions()] == [v1.id, v2.id, v3.id]
    assert [d.id for d in v1.all_versions()] == [v1.id, v2.id, v3.id]
    assert v1.has_versions() is True
    assert v3.has_versions() is True


def test_get_synchronized_by_user_returns_only_latest_versions(test_app, clean_database):
    user = UserRepository().create(email="latest@example.com", password="pw-123456")
    repo = DataSetRepository()

    def make(version, doi, origin_id=None):
        meta = DSMetaDataRepository().create(
            title=f"v{version}", description="d", publication_type=PublicationType.BOOK, dataset_doi=doi
        )
        return repo.create(
            user_id=user.id, ds_meta_data_id=meta.id, dataset_version=version, dataset_origin_id=origin_id
        )

    v1 = make(1, "10.1/v1")
    v2 = make(2, "10.1/v2", origin_id=v1.id)
    v3 = make(3, "10.1/v3", origin_id=v2.id)
    standalone = make(1, "10.1/solo")

    ids = {d.id for d in repo.get_synchronized_datasets_by_user(user.id)}

    # Only the tip of the lineage (v3) and the un-versioned dataset show up.
    assert v3.id in ids
    assert standalone.id in ids
    assert v1.id not in ids
    assert v2.id not in ids
    # A dataset with no lineage reports no versions.
    assert standalone.has_versions() is False


def _lineage_with_concept_doi(email, concept_doi, versions=2):
    user = UserRepository().create(email=email, password="pw-123456")
    repo = DataSetRepository()
    created = []
    origin_id = None
    for version in range(1, versions + 1):
        meta = DSMetaDataRepository().create(
            title=f"v{version}",
            description="d",
            publication_type=PublicationType.BOOK,
            dataset_doi=f"10.5072/zenodo.{version}",
            dataset_concept_doi=concept_doi,
        )
        dataset = repo.create(
            user_id=user.id, ds_meta_data_id=meta.id, dataset_version=version, dataset_origin_id=origin_id
        )
        created.append(dataset)
        origin_id = dataset.id
    return created


def test_get_by_concept_doi_returns_the_oldest_version(test_app, clean_database):
    v1, v2 = _lineage_with_concept_doi("concept@example.com", "10.5072/zenodo.0")

    found = DataSetRepository().get_by_concept_doi("10.5072/zenodo.0")

    assert found.id == v1.id
    assert [dataset.id for dataset in found.all_versions()] == [v1.id, v2.id]


def test_get_by_concept_doi_is_none_for_unknown_or_empty_values(test_app, clean_database):
    _lineage_with_concept_doi("concept2@example.com", "10.5072/zenodo.0")

    repo = DataSetRepository()

    assert repo.get_by_concept_doi("10.5072/zenodo.404") is None
    assert repo.get_by_concept_doi("") is None
    assert repo.get_by_concept_doi(None) is None


def test_all_versions_covers_every_branch_of_a_split_lineage(test_app, clean_database):
    # The service refuses to version an already superseded dataset, so new
    # lineages stay linear. Rows written before that guard (or by hand) can
    # still have two children of the same node, and following a single branch
    # would hide a published version from /versions and from a transfer.
    user = UserRepository().create(email="branched@example.com", password="pw-123456")
    repo = DataSetRepository()

    def make(version, doi, origin_id=None):
        meta = DSMetaDataRepository().create(
            title=f"v{version}", description="d", publication_type=PublicationType.BOOK, dataset_doi=doi
        )
        return repo.create(
            user_id=user.id, ds_meta_data_id=meta.id, dataset_version=version, dataset_origin_id=origin_id
        )

    v1 = make(1, "10.5072/zenodo.1")
    branch_a = make(2, "10.5072/zenodo.2", origin_id=v1.id)
    branch_b = make(2, "10.5072/zenodo.3", origin_id=v1.id)

    expected = [v1.id, branch_a.id, branch_b.id]
    for node in (v1, branch_a, branch_b):
        assert [dataset.id for dataset in node.all_versions()] == expected
        assert node.version_root().id == v1.id

    # The dataset asking the question is always part of the answer.
    assert branch_b.id in {dataset.id for dataset in branch_b.all_versions()}
    assert v1.is_superseded() is True
    assert branch_b.is_superseded() is False


def test_latest_version_prefers_a_published_version_over_an_orphan_clone(test_app, clean_database):
    # A clone whose Zenodo publication failed has no DOI: it must never shadow
    # the version that does exist on Zenodo.
    user = UserRepository().create(email="orphan@example.com", password="pw-123456")
    repo = DataSetRepository()
    published_meta = DSMetaDataRepository().create(
        title="v1", description="d", publication_type=PublicationType.BOOK, dataset_doi="10.5072/zenodo.11"
    )
    published = repo.create(user_id=user.id, ds_meta_data_id=published_meta.id, dataset_version=1)
    orphan_meta = DSMetaDataRepository().create(title="v2", description="d", publication_type=PublicationType.BOOK)
    orphan = repo.create(
        user_id=user.id, ds_meta_data_id=orphan_meta.id, dataset_version=2, dataset_origin_id=published.id
    )

    assert published.latest_version().id == published.id
    assert orphan.latest_version().id == published.id
    assert published.is_latest_version() is True
    assert orphan.is_latest_version() is False


def test_concept_doi_column_tolerates_older_records(test_app, clean_database):
    # Datasets published before the column existed keep it null and stay usable.
    user = UserRepository().create(email="legacy@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(
        title="legacy", description="d", publication_type=PublicationType.BOOK, dataset_doi="10.5072/zenodo.9"
    )
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)

    assert dataset.ds_meta_data.dataset_concept_doi is None
    assert dataset.get_concept_doi() is None
    assert dataset.is_latest_version() is True
    assert dataset.latest_version().id == dataset.id


# --- Migration round trip on the real engine -------------------------------


def _load_migration(module_name):
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[4] / "migrations" / "versions" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fk_name(connection, table, column):
    from sqlalchemy import text

    row = connection.execute(
        text(
            "SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table "
            "AND COLUMN_NAME = :column AND REFERENCED_TABLE_NAME IS NOT NULL"
        ),
        {"table": table, "column": column},
    ).first()
    return row[0] if row else None


def test_transfer_migration_downgrades_on_a_real_database_with_rows(test_app, clean_database):
    """Run the migration's own upgrade and downgrade against live MariaDB.

    The unit-level guard next to this one only patches ``op`` and asserts the
    call order, so it never emits a single statement and cannot see an engine
    refusing one. This does emit them. It reproduces the exact reported
    failure, error 1553 "Cannot drop index ...: needed in a foreign key
    constraint", which is only observable against a real engine holding real
    rows.
    """
    from datetime import datetime

    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import inspect, text
    from unittest.mock import patch

    from app import db

    migration = _load_migration("c9d0e1f2a3b4_add_api_publisher_and_transfers")

    with db.engine.begin() as connection:
        operations = Operations(MigrationContext.configure(connection))

        # create_all() built these with auto-generated constraint names, which
        # are not the names the migration uses. Drop them so the migration can
        # build the objects itself, exactly as it does on a real deployment.
        operations.drop_table("dataset_transfer_request")
        operations.drop_constraint(
            _fk_name(connection, "ds_meta_data", "api_publisher_user_id"), "ds_meta_data", type_="foreignkey"
        )
        operations.drop_column("ds_meta_data", "api_publisher_user_id")

        with patch.object(migration, "op", operations):
            migration.upgrade()

            assert "dataset_transfer_request" in inspect(connection).get_table_names()

            # Rows matter: an empty table can hide constraint problems that a
            # populated one cannot.
            connection.execute(
                text("INSERT INTO user (id, email, password, created_at, active) VALUES (:i, :e, 'x', :c, 1)"),
                [
                    {"i": 9001, "e": "mig-from@example.com", "c": datetime(2026, 1, 1)},
                    {"i": 9002, "e": "mig-to@example.com", "c": datetime(2026, 1, 1)},
                ],
            )
            connection.execute(
                text(
                    "INSERT INTO ds_meta_data (id, title, description, publication_type, metadata_synced) "
                    "VALUES (9001, 't', 'd', 'BOOK', 1)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO datasets "
                    "(id, user_id, ds_meta_data_id, created_at, feature_model_count, dataset_version) "
                    "VALUES (9001, 9001, 9001, :c, 0, 1)"
                ),
                {"c": datetime(2026, 1, 1)},
            )
            connection.execute(
                text(
                    "INSERT INTO dataset_transfer_request "
                    "(id, dataset_id, from_user_id, to_user_id, status, created_at) "
                    "VALUES (9001, 9001, 9001, 9002, 'PENDING', :c)"
                ),
                {"c": datetime(2026, 1, 1)},
            )

            # The assertion. Before the fix this raised OperationalError 1553
            # on the first drop_index and left the schema stuck halfway.
            migration.downgrade()

            assert "dataset_transfer_request" not in inspect(connection).get_table_names()
            assert "api_publisher_user_id" not in [
                column["name"] for column in inspect(connection).get_columns("ds_meta_data")
            ]

            # Back up to head, so the schema this test borrowed is returned in
            # the state the rest of the suite expects.
            migration.upgrade()

        assert "dataset_transfer_request" in inspect(connection).get_table_names()


def test_transfer_request_is_removed_with_its_dataset(test_app, clean_database):
    # The foreign key carries ON DELETE CASCADE. Without it the constraint
    # refused every deletion of a dataset that had ever been offered, and the
    # admin cleanup command aborted with error 1451.
    from datetime import datetime

    from app import db
    from app.features.dataset.models import DatasetTransferRequest, DatasetTransferStatus

    sender = UserRepository().create(email="cascade-from@example.com", password="pw-123456")
    recipient = UserRepository().create(email="cascade-to@example.com", password="pw-123456")
    dataset = _dataset(doi="10.5072/zenodo.cascade", email="cascade-owner@example.com")

    transfer = DatasetTransferRequest(
        dataset_id=dataset.id,
        from_user_id=sender.id,
        to_user_id=recipient.id,
        status=DatasetTransferStatus.DECLINED,
        created_at=datetime(2026, 1, 1),
    )
    db.session.add(transfer)
    db.session.commit()

    db.session.delete(dataset)
    db.session.commit()

    assert DatasetTransferRequest.query.filter_by(dataset_id=dataset.id).count() == 0
