"""frozen_urls.toml against the app the product builds (CO-1).

An entry marked served has to be a rule of the url_map, answered by the
endpoint it names. An entry still pending must not be one, so a release
that starts serving it fails here until the manifest says so. Rules are
compared with their variable names dropped: <int:dataset_id> and <int:id>
are one rule.

Run it in the product's web container, which has the features installed:

    docker exec uvlhub_splent_web bash -lc \
        'cd /workspace/uvlhub_splent && python -m pytest tests -q -p no:cacheprovider'

The app loads the features the product pins. To see a working copy instead,
name it in SPLENT_FEATURE_SOURCES, as feature:test does:

    docker exec -e SPLENT_FEATURE_SOURCES=splent_feature_featuremodel=/workspace/splent_feature_featuremodel \
        uvlhub_splent_web bash -lc 'cd /workspace/uvlhub_splent && python -m pytest tests -q -p no:cacheprovider'
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


def test_every_accepted_new_route_is_served(app):
    served = {_shape(rule.rule) for rule in app.url_map.iter_rules()}

    assert [rule for rule in ACCEPTED if _shape(rule) not in served] == []
