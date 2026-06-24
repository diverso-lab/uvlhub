"""Feature discovery and registration for uvlhub.

Replicates the useful contract of splent_framework's FeatureIntegrator without
the SPL machinery (no UVL constraint solving, refinement registry, namespaces).

The set of features that get loaded is declarative: ``[tool.splent.features]``
in the product's pyproject.toml is the base list, and ``[tool.splent.features_<env>]``
adds env-specific entries (``dev`` for development/testing, ``prod`` for
production). If neither list is declared, every package found under
``app/features/`` is loaded — this keeps small playground apps working without
ceremony.

For each selected feature, in order:
  1. ``app.features.<name>.config.inject_config(app)`` — optional. Lets a
     feature mutate ``app.config`` before anything else touches it.
  2. Conventional submodules (routes / models / hooks / signals) are imported
     so that Blueprint definitions inside them become discoverable.
  3. ``app.features.<name>.init_feature(app)`` — optional lifecycle hook for
     setup that needs the app instance.
  4. Every Flask ``Blueprint`` instance found in the feature root or any of
     its submodules is registered. Names are deduplicated.
"""
import importlib
import pkgutil
import sys
import tomllib
from pathlib import Path

from flask import Blueprint, Flask

_SUBMODULES = ("routes", "models", "hooks", "signals")


def register_features(app: Flask, env: str = "dev") -> None:
    declared = _read_declared_features(env)

    import app.features as features_pkg

    for _, name, ispkg in pkgutil.iter_modules(features_pkg.__path__):
        if not ispkg:
            continue
        if declared and name not in declared:
            continue
        _inject_config(name, app)
        feature_module = importlib.import_module(f"app.features.{name}")
        _import_submodules(name)
        _call_init(feature_module, app)
        _register_blueprints(name, feature_module, app)


def _read_declared_features(env: str) -> set[str]:
    """Return the union of [tool.splent.features] and [tool.splent.features_<env>].

    Empty set means "no declarative filter" — load every feature found on disk.
    """
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if not pyproject.exists():
        return set()
    with open(pyproject, "rb") as f:
        cfg = tomllib.load(f)
    splent = cfg.get("tool", {}).get("splent", {})
    base = splent.get("features") or []
    env_list = splent.get(f"features_{env}") or []
    return set(base) | set(env_list)


def _inject_config(name: str, app: Flask) -> None:
    try:
        config_mod = importlib.import_module(f"app.features.{name}.config")
    except ModuleNotFoundError:
        return
    fn = getattr(config_mod, "inject_config", None)
    if callable(fn):
        fn(app)


def _import_submodules(name: str) -> None:
    for sub in _SUBMODULES:
        try:
            importlib.import_module(f"app.features.{name}.{sub}")
        except ModuleNotFoundError:
            pass


def _call_init(feature_module, app: Flask) -> None:
    fn = getattr(feature_module, "init_feature", None)
    if callable(fn):
        fn(app)


def _register_blueprints(name: str, feature_module, app: Flask) -> None:
    candidates = [feature_module]
    for sub in _SUBMODULES:
        mod = sys.modules.get(f"app.features.{name}.{sub}")
        if mod is not None:
            candidates.append(mod)

    seen = set()
    for mod in candidates:
        for attr in dir(mod):
            obj = getattr(mod, attr, None)
            if isinstance(obj, Blueprint) and obj.name not in seen:
                app.register_blueprint(obj)
                seen.add(obj.name)
