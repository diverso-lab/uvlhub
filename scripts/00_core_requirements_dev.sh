#!/bin/bash

set -e

# An editable install points at the source, so a git pull changes the code
# without touching the environment. Its metadata, though, is frozen at
# install time: a dependency the package declared later is absent from
# "pip show Requires", pip check has nothing to compare against, and the
# new code fails at import while the install still looks healthy. Comparing
# the declared dependencies against the recorded ones catches exactly that.
# So does comparing the versions: after a release pip still records the old
# one, and installing a feature that asks for the new one would fetch the
# package from PyPI in place of the checkout.
needs_install () {
    local package=$1 location=$2
    pip show "$package" 2>/dev/null \
        | grep -q "Editable project location.*$location" || return 0
    python - "$package" "$location" <<'PY' || return 0
import subprocess
import sys
import tomllib
from pathlib import Path


def canonical(name):
    return name.strip().lower().replace("_", "-")


package, location = sys.argv[1], sys.argv[2]
pyproject = Path(location) / "pyproject.toml"
if not pyproject.is_file():
    sys.exit(0)

project = tomllib.loads(pyproject.read_text())["project"]
declared = set()
for spec in project.get("dependencies", []):
    for sep in ("[", ";", ">", "<", "=", "!", "~", " "):
        spec = spec.split(sep)[0]
    if spec:
        declared.add(canonical(spec))

recorded = set()
recorded_version = None
shown = subprocess.run(
    [sys.executable, "-m", "pip", "show", package],
    capture_output=True,
    text=True,
).stdout
for line in shown.splitlines():
    if line.startswith("Requires:"):
        recorded = {canonical(r) for r in line.split(":", 1)[1].split(",") if r.strip()}
    elif line.startswith("Version:"):
        recorded_version = line.split(":", 1)[1].strip()

stale = project.get("version") and project.get("version") != recorded_version
sys.exit(1 if declared - recorded or stale else 0)
PY
    return 1
}

if [ -d /workspace/splent_framework ]; then
    if needs_install splent_framework /workspace/splent_framework; then
        echo "    installing splent_framework..."
        pip install --no-cache-dir --root-user-action=ignore -e /workspace/splent_framework
    else
        echo "    splent_framework already installed."
    fi
else
    echo "    installing splent_framework from pyproject.toml [core]..."
    pip install --no-cache-dir "uvlhub_splent[core]"
fi

if [ -d /workspace/splent_cli ]; then
    if needs_install splent_cli /workspace/splent_cli; then
        echo "    installing splent_cli..."
        pip install --no-cache-dir --root-user-action=ignore -e /workspace/splent_cli
    else
        echo "    splent_cli already installed."
    fi
else
    echo "    splent_cli not found, skipping."
fi

# pip wrote the egg-info into the checkouts as root; it goes back to the
# workspace's owner, as 00_install_features does for the features.
owner="$(stat -c %u:%g /workspace)"
if [ "$(id -u)" = 0 ] && [ "${owner%%:*}" != 0 ]; then
    for path in /workspace/splent_framework /workspace/splent_cli; do
        [ -d "$path" ] || continue
        find -H "$path" -path "$path/.git" -prune -o -user 0 \
            -exec chown -h "$owner" {} + 2>/dev/null || true
    done
fi
