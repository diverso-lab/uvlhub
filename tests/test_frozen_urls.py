"""frozen_urls.toml against the app the product builds (CO-1).

An entry marked served has to be a rule of the url_map, answered by the
endpoint it names. An entry still pending must not be one, so a release
that starts serving it fails here until the manifest says so. Rules are
compared with their variable names dropped: <int:dataset_id> and <int:id>
are one rule.

A served entry with cors_origin or signed_out_keys is also called, through
the test client and with no session: the site it names has to get its
origin back with credentials, and the 401 has to carry those keys. Which
feature answers does not matter here, so a set of pins that drops the
CORS of a frozen route fails even when every feature validates.

The routes in neither the manifest nor its accepted list are reported as an
expected failure until the contract owner decides which ones are accepted.

Run it in the product's web container, which has the features installed:

    docker exec uvlhub_web bash -lc \
        'cd /workspace/uvlhub && python -m pytest tests -q -p no:cacheprovider'

The app loads the features the product pins. To see a working copy instead,
name it in SPLENT_FEATURE_SOURCES, as feature:test does:

    docker exec -e SPLENT_FEATURE_SOURCES=splent_feature_uvl=/workspace/splent_feature_uvl \
        uvlhub_web bash -lc 'cd /workspace/uvlhub && python -m pytest tests -q -p no:cacheprovider'
"""

import re
import tomllib
from pathlib import Path

import pytest

MANIFEST = Path(__file__).resolve().parents[1] / "frozen_urls.toml"
ROWS = range(1, 20)  # the rows of the table in 06 §4.4
STATUSES = {"served", "alias-pending", "gone-pending"}

ENTRIES = tomllib.loads(MANIFEST.read_text())["url"]
ACCEPTED = tomllib.loads(MANIFEST.read_text()).get("accepted", {}).get("rules", [])

ACAO = "Access-Control-Allow-Origin"
ACAC = "Access-Control-Allow-Credentials"
ANOTHER_SITE = "https://evil.example"

# <converter(args):name> or <name>
_VARIABLE = re.compile(r"<(?:(\w+)(?:\([^)]*\))?:)?\w+>")


def _shape(rule: str) -> str:
    """The rule with its variable names dropped, the converters kept."""

    def converter(match):
        name = match.group(1) or "default"
        return f"<{'default' if name == 'string' else name}>"

    return _VARIABLE.sub(converter, rule)


def _label(entry) -> str:
    return entry.get("rule") or entry.get("header")


def _matching_rules(app, entry):
    shape = _shape(entry["rule"])
    methods = set(entry["methods"])
    return [
        rule
        for rule in app.url_map.iter_rules()
        if _shape(rule.rule) == shape and methods & rule.methods
    ]


def _headers_read(app, entry) -> set[str]:
    return {header.lower() for header in app.config.get(entry["config"]) or []}


def _served_with(field):
    return [e for e in ENTRIES if e["status"] == "served" and e.get(field)]


def _call(client, entry, origin=None):
    """The entry's first method on its rule, with no session and no token."""
    headers = {"Origin": origin} if origin else {}
    return client.open(entry["rule"], method=entry["methods"][0], headers=headers)


def _preflight(client, entry, origin):
    return client.open(
        entry["rule"],
        method="OPTIONS",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": entry["methods"][0],
        },
    )


def test_the_manifest_covers_every_row_of_the_table():
    covered = {row for entry in ENTRIES for row in entry["rows"]}

    assert covered == set(ROWS)


@pytest.mark.parametrize("entry", ENTRIES, ids=_label)
def test_each_entry_says_who_serves_it_or_what_closes_it(entry):
    assert entry["status"] in STATUSES
    assert entry["v212"] and entry["clients"] and entry["target"]
    if entry.get("kind") == "header":
        assert entry["header"] and entry["config"]
    else:
        assert entry["rule"].startswith("/") and entry["methods"]
    if entry["status"] == "served":
        assert entry["served_by"]
        if entry.get("kind") != "header":
            assert entry["endpoint"]
    else:
        assert entry["plan"]
    if entry.get("cors_origin") or entry.get("signed_out_keys"):
        # Called as they are written, so with no variable to fill in.
        assert entry.get("kind") != "header"
        assert _shape(entry["rule"]) == entry["rule"]


@pytest.mark.parametrize(
    "entry", [e for e in ENTRIES if e["status"] == "served"], ids=_label
)
def test_a_served_entry_is_served(app, entry):
    if entry.get("kind") == "header":
        assert entry["header"].lower() in _headers_read(app, entry)
        return

    rules = _matching_rules(app, entry)

    assert rules, f"no rule of the url_map serves {entry['rule']}"
    assert entry["endpoint"] in {rule.endpoint for rule in rules}
    allowed = set().union(*(rule.methods for rule in rules))
    assert set(entry["methods"]) <= allowed
    # The rule that answers, not only one that exists: of two features that
    # claim an address, the one registered first takes every request.
    if "<" not in entry["rule"]:
        answering = app.url_map.bind("localhost").match(
            entry["rule"], method=entry["methods"][0]
        )
        assert answering[0] == entry["endpoint"]


@pytest.mark.parametrize(
    "entry", [e for e in ENTRIES if e["status"] != "served"], ids=_label
)
def test_a_pending_entry_is_not_served_yet(app, entry):
    if entry.get("kind") == "header":
        assert entry["header"].lower() not in _headers_read(app, entry)
        return

    rules = _matching_rules(app, entry)

    assert not rules, (
        f"{entry['rule']} is served by {rules[0].endpoint}: "
        "mark it served in frozen_urls.toml"
    )


@pytest.mark.parametrize("entry", _served_with("cors_origin"), ids=_label)
def test_a_served_entry_answers_its_client_site_with_credentials(app, entry):
    origin = entry["cors_origin"]
    client = app.test_client()

    for response in (_preflight(client, entry, origin), _call(client, entry, origin)):
        assert response.headers.getlist(ACAO) == [origin]
        assert response.headers.get(ACAC) == "true"


@pytest.mark.parametrize("entry", _served_with("cors_origin"), ids=_label)
def test_a_served_entry_gives_another_site_no_cors(app, entry):
    client = app.test_client()

    for response in (
        _preflight(client, entry, ANOTHER_SITE),
        _call(client, entry, ANOTHER_SITE),
    ):
        assert ACAO not in response.headers
        assert ACAC not in response.headers


@pytest.mark.parametrize("entry", _served_with("signed_out_keys"), ids=_label)
def test_a_served_entry_tells_a_signed_out_caller_how_to_sign_in(app, entry):
    response = _call(app.test_client(), entry)

    assert response.status_code == 401
    assert set(entry["signed_out_keys"]) <= set(response.get_json())


def test_every_accepted_new_route_is_served(app):
    served = {_shape(rule.rule) for rule in app.url_map.iter_rules()}

    assert [rule for rule in ACCEPTED if _shape(rule) not in served] == []


def test_every_route_is_frozen_or_accepted(app):
    """The other half of CO-1, not enforced yet: the accepted list is the
    contract owner's to fill. Until it holds every new route, the ones in
    neither list are reported here as an expected failure. Once it does,
    this passes, and the xfail turns into an assert."""
    listed = {_shape(entry["rule"]) for entry in ENTRIES if "rule" in entry}
    listed |= {_shape(rule) for rule in ACCEPTED}

    unlisted = sorted(
        {
            rule.rule
            for rule in app.url_map.iter_rules()
            if _shape(rule.rule) not in listed
        }
    )

    if unlisted:
        pytest.xfail(
            f"{len(unlisted)} rules are neither frozen nor accepted: "
            + ", ".join(unlisted)
        )
