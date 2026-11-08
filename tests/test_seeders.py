"""The seed of a development database, as splent db:seed makes it (NEW-4).

Every seeder of the features the product pins, in the order db:seed runs
them, then the product's own, on an empty test database: a seeder that no
longer fits the pins, or that runs before the data it builds on, fails here
and not in the first db:seed of a new workspace. Then what uvlhub's own
seeders write: its organisations in page order, each with its logo from
the media library, its member, and uvlhub.io's words on theme's 404.

It empties the test database before and after, so run it under the test
lock, with the product's other tests:

    docker exec -u splent splent_cli_container bash -lc \
        'cd /workspace && flock /tmp/splent-test.lock splent product:test --own-tests'
"""

import contextlib

import pytest
from splent_framework.fixtures.fixtures import _reset_db

from uvlhub_splent.seeders import APPEARANCE, MEMBERS, ORGANISATIONS

PRODUCT_SEEDERS = "uvlhub_splent.seeders"
TEAM_SEEDERS = "splent_io.splent_feature_team.seeders"
# The seed indexes its datasets for /explore. Under a prefix of its own, so
# the test database's datasets never reach the search index of the
# development app on the same node; the index goes afterwards.
SEARCH_PREFIX = "uvlhub_splent_test_seed"


@pytest.fixture(scope="module")
def seeders(app):
    """The seeders db:seed runs, once they ran on an empty database."""
    from splent_cli.commands.database.db_seed import get_installed_seeders
    from splent_io.splent_feature_elasticsearch.services import (
        ElasticsearchError,
        ElasticsearchService,
    )
    from splent_framework.search.search_registry import get_search_sources

    found, errors = get_installed_seeders()
    assert errors == [], errors
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(app.config, "ELASTICSEARCH_INDEX_PREFIX", SEARCH_PREFIX)
        with app.app_context():
            _reset_db()
            for seeder in found:
                seeder.run()
        yield found
        with app.app_context():
            _reset_db()
            for source in get_search_sources():
                with contextlib.suppress(ElasticsearchError):
                    ElasticsearchService().delete_index(source["key"])


def test_every_seeder_runs_and_the_products_come_last(seeders):
    modules = [type(seeder).__module__ for seeder in seeders]

    assert TEAM_SEEDERS not in modules, "the product's replaces team's"
    assert [m for m in modules if m == PRODUCT_SEEDERS] == modules[-2:]


def test_uvlhubs_organisations_in_page_order_with_their_member(app, seeders):
    from splent_io.splent_feature_team.models import Role, TeamMember

    with app.app_context():
        roles = Role.query.order_by(Role.order).all()
        assert [role.name for role in roles] == [o["name"] for o in ORGANISATIONS]
        logos = [role.logo for role in roles]
        member = TeamMember.query.filter_by(email=MEMBERS[0]["email"]).one()
        assert [role.name for role in member.roles] == [MEMBERS[0]["organisation"]]

    browser = app.test_client()
    page = browser.get("/team").get_data(as_text=True)
    for organisation in ORGANISATIONS:
        assert organisation["name"] in page
    assert [browser.get(logo).status_code for logo in logos] == [200] * len(logos)


def test_theme_404_says_what_uvlhub_io_says(app, seeders):
    from splent_framework.services.service_locator import service_proxy

    with app.app_context():
        settings = service_proxy("SettingsService")
        assert {key: settings.get(key) for key in APPEARANCE} == APPEARANCE
