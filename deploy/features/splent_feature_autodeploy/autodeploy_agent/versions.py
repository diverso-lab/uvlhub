"""What the web container runs, as ``splent version --json`` reports it.

Read before and after a deploy, so the history can say which features moved
and from which version to which. A container that cannot answer (an image
without the CLI, a command that fails) gives None, and the deploy goes on:
the versions are a record, not a gate.
"""

from __future__ import annotations

from autodeploy_agent.dockerops import exec_output, parse_json_output

VERSION_COMMAND = ["splent", "version", "--json"]


def read_versions(api, container: str) -> dict | None:
    try:
        code, stdout, _stderr = exec_output(api, container, VERSION_COMMAND)
    except Exception:  # noqa: BLE001 - a record, never a reason to fail
        return None
    if code != 0:
        return None
    data = parse_json_output(stdout)
    if not data:
        return None
    product = data.get("product") or {}
    features = {}
    for feature in data.get("features") or []:
        if isinstance(feature, dict) and feature.get("name"):
            features[feature["name"]] = feature.get("version")
    return {
        "product": product.get("name"),
        "product_version": product.get("version"),
        "framework": data.get("framework"),
        "cli": data.get("cli"),
        "features": features,
    }


def feature_changes(before: dict | None, after: dict | None) -> list[dict]:
    """Every feature whose version differs, as ``{"name", "from", "to"}``.

    A feature that appears has ``from`` None, one that goes has ``to`` None.
    """
    old = (before or {}).get("features") or {}
    new = (after or {}).get("features") or {}
    changes = []
    for name in sorted(set(old) | set(new)):
        if old.get(name) != new.get(name):
            changes.append({"name": name, "from": old.get(name), "to": new.get(name)})
    return changes
