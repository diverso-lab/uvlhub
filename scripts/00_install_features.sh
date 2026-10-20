#!/bin/bash

# This script installs the features listed in the product's pyproject.toml.
#
# It is the DEVELOPMENT install path, and it never contacts PyPI. Every install
# below is `pip install -e` against a directory under
# /workspace/uvlhub_splent/features/, which `splent product:resolve` fills
# in: pinned features are cloned from GitHub at their tag into
# .splent_cache/features/ and symlinked here, editable ones are symlinked
# straight to the checkout at the workspace root.
#
# The production image does not run this script. entrypoints/entrypoint.dev.sh
# is its only caller; the prod image installs features with pip from PyPI in
# the builder stage of docker/Dockerfile.uvlhub_splent.prod.
#
# Pinned features: skip if already pip-installed at the correct version.
# Editable features: skip if already installed from the same path.
# ---------------------------------------------------------------------------

set -e

echo ""

features=$(python3 -c '
import os, tomllib
with open("/workspace/uvlhub_splent/pyproject.toml", "rb") as f:
    data = tomllib.load(f)
splent = data.get("tool", {}).get("splent", {})
feats = list(splent.get("features", []))
# SPLENT_ENV as the framework reads it: stripped, lowercased, and the long
# spellings mapped to the short ones, so both install the same features_<env>.
env = (os.getenv("SPLENT_ENV") or "").strip().lower()
env = {"development": "dev", "production": "prod", "testing": "test"}.get(env, env)
if env:
    feats += [f for f in splent.get(f"features_{env}", []) if f not in feats]
if not feats:
    feats = data.get("project", {}).get("optional-dependencies", {}).get("features", [])
print("\n".join(feats))
')

if [ -z "$features" ]; then
    echo "    no features declared."
    exit 0
fi

installed=0
skipped=0
to_install=()
install_paths=()
# Counted by hand: bash's array length syntax opens a Jinja comment here.
pending=0

for feature in $features; do
    # Parse "splent-io/splent_feature_auth@v1.2.9" → pkg_name, version
    if echo "$feature" | grep -q '/'; then
        name_ver="${feature#*/}"
    else
        name_ver="$feature"
    fi

    pkg_name="${name_ver%%@*}"
    declared_version="${name_ver#*@}"
    [ "$declared_version" = "$name_ver" ] && declared_version=""

    # Check if already installed
    current_version=$(pip show "$pkg_name" 2>/dev/null | grep "^Version:" | awk '{print $2}')

    if [ -n "$declared_version" ]; then
        # Pinned feature: check version match
        clean_version="${declared_version#v}"  # strip leading 'v'
        if [ "$current_version" = "$clean_version" ]; then
            skipped=$((skipped + 1))
            continue
        fi
    else
        # Editable feature: check if installed from the right path
        found_path=""
        for org_dir in /workspace/uvlhub_splent/features/*; do
            [ -d "$org_dir" ] || continue
            candidate="$org_dir/$pkg_name"
            if [ -d "$candidate" ]; then
                found_path="$candidate"
                break
            fi
        done

        if [ -z "$found_path" ]; then
            echo "    $feature not found locally, skipping."
            continue
        fi

        editable_loc=$(pip show "$pkg_name" 2>/dev/null | grep "Editable project location" | cut -d' ' -f4-)
        if [ -n "$editable_loc" ]; then
            real_path=$(cd "$found_path" 2>/dev/null && pwd -P) || real_path=""
            current_real=$(cd "$editable_loc" 2>/dev/null && pwd -P) || current_real=""
            if [ "$current_real" = "$real_path" ]; then
                skipped=$((skipped + 1))
                continue
            fi
        fi
    fi

    # Install
    found_path=""
    for org_dir in /workspace/uvlhub_splent/features/*; do
        [ -d "$org_dir" ] || continue
        for candidate in "$org_dir/$name_ver" "$org_dir/$pkg_name"; do
            if [ -d "$candidate" ]; then
                found_path="$candidate"
                break 2
            fi
        done
    done

    if [ -n "$found_path" ]; then
        echo "    installing $pkg_name..."
        to_install+=("$feature")
        pending=$((pending + 1))
        install_paths+=("$found_path")
    else
        echo "    $feature not found, skipping."
    fi
done

mark_installed() {
    # Record the features in the product manifest, all in one interpreter:
    # starting Python and importing the CLI per feature cost about a second each.
    python3 - "$@" <<'PY' 2>/dev/null || true
import os, sys
from splent_cli.utils.lifecycle import advance_state, resolve_feature_key_from_entry
app = os.getenv("SPLENT_APP", "")
product_path = os.path.join(os.getenv("WORKING_DIR", "/workspace"), app)
for entry in sys.argv[1:]:
    key, ns, name, ver = resolve_feature_key_from_entry(entry)
    advance_state(product_path, app, key, to="installed", namespace=ns, name=name, version=ver)
PY
}

# The dev image ships setuptools, so building without isolation needs no
# network. A feature with another build backend falls back to an isolated
# build. All features go to pip at once, which resolves their dependencies
# once instead of once per feature; if that fails, they are installed one by
# one so the failing feature is named.
pip_install() {
    pip install --root-user-action=ignore --no-build-isolation "$@" >/dev/null 2>&1 \
        || pip install --root-user-action=ignore "$@" >/dev/null 2>&1
}

if [ "$pending" -gt 0 ]; then
    editable_args=()
    for path in "${install_paths[@]}"; do
        editable_args+=(-e "$path")
    done
    if pip_install "${editable_args[@]}"; then
        installed=$pending
        mark_installed "${to_install[@]}"
    else
        ok=()
        for i in "${!to_install[@]}"; do
            if pip_install -e "${install_paths[$i]}"; then
                ok+=("${to_install[$i]}")
                installed=$((installed + 1))
            else
                echo "    FAIL: error installing ${to_install[$i]}"
            fi
        done
        if [ "$installed" -gt 0 ]; then
            mark_installed "${ok[@]}"
        fi
    fi
fi

echo "    $installed installed, $skipped already up to date."
