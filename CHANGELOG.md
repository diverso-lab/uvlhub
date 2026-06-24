# Changelog

All notable changes to this project are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/) and the project follows
[Semantic Versioning](https://semver.org/).

## [2.9] - 2026-06-25

Major release: uvlhub is rebuilt on **splent_framework** and gains **dataset
versioning** — replace a UVL and publish a new, linked Zenodo version.

### Added
- **Dataset UVL versioning.** Replace the UVL of a draft in place, or publish a
  new version of an already-published dataset. A new version creates a fresh
  Zenodo version (its own DOI, linked to the previous one through the shared
  concept DOI) and a new local dataset linked to the previous via
  `dataset_origin_id`.
- **Version history** on the dataset page and a **version badge** in
  "My datasets"; the list now shows only the latest version of each lineage.
- Dataset edit mode now manages UVL files (replace draft files; publish a new
  version for published datasets).

### Changed
- **Rebuilt on splent_framework.** `app/modules/` -> `app/features/`, the bespoke
  `core` is removed, dependencies are pinned in `pyproject.toml`, and the app
  runs from `/workspace`. The rosemary CLI, GitHub Actions and docs were aligned
  to the new layout.
- Every feature refactored to SOLID services/repositories with thin routes and
  the splent testing pyramid (unit / repository / service / integration / e2e /
  load); the hub <-> UVL-domain coupling is inverted via splent signals.
- Editing a synchronized dataset without an explicit type no longer clears its
  Zenodo DOI.

### Fixed
- **Production Docker build/deploy.** The webhook service no longer creates a
  Docker client at import time (which broke `docker build` via
  `rosemary webpack:compile`); rosemary's selenium/locust commands use the
  `/workspace` layout.
- **Generator wizard** now boots its self-hosted Pyodide runtime and the
  **dataset description editor** (TinyMCE) loads its assets — both were 404ing on
  nested asset paths.

### Upgrade notes
- Data-preserving Alembic migrations are included and apply automatically on
  deploy (`flask db upgrade`, run by the production entrypoint).
- Ensure `WORKING_DIR=/workspace` in the production `.env`.
