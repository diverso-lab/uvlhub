# Changelog

All notable changes to this project are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/) and the project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

Durable links for programmatic publication: a dataset published through
the API can now be followed across its whole life, from the first version
to the newest one, and can be handed over to another account.

### Added

- Zenodo concept DOI stored in `ds_meta_data.dataset_concept_doi` (new
  migration `b8c9d0e1f2a3`, nullable so older records keep working). It
  is read on first publish and on every new version, and every version of
  a lineage shares it. `ZenodoService.get_concept_doi` exposes it, with a
  fallback that derives it from `conceptrecid` when Zenodo omits
  `conceptdoi`.
- `GET /api/v1/datasets/doi/<doi>` now also returns `concept_doi`,
  `version`, `total_versions`, `is_latest`, `latest` and `versions_url`,
  so a client holding an old DOI can discover the newest version. The
  existing keys are untouched.
- `GET /api/v1/datasets/<id>/versions`, returning the whole version
  lineage oldest first, with dataset id, version, DOI and publication
  date for each entry.
- `GET /api/v1/datasets/concept-doi/<concept_doi>`, which resolves a
  lineage (and therefore the latest version) from the stable concept DOI.
- `POST /api/v1/datasets/<id>/transfer`, which hands a dataset over to
  another account by `user_id` or `email`, restricted to the current
  owner. The whole version lineage moves as a unit, files included.
- `POST /api/v1/datasets/upload` accepts optional `authors` (JSON array,
  or the usual `authors[0][name]` form fields), so a service account can
  publish while crediting the real developer. The authors are stored as
  `Author` rows and become the Zenodo creators. Without them the previous
  behaviour is unchanged.
- `concept_doi` in the publish and new-version API responses.

## [2.10] - 2026-07-26

Programmatic publication: datasets can now be created, published and
versioned through the REST API with an API key — no browser involved.
This powers `splent spl:publish`, closing the SPLENT loop (local UVL →
UVLHub → `spl:fetch` anywhere).

### Added

- `write_dataset` API-key scope (selectable in /developer/api-keys) and
  API-key resolution exposing the owning user to write endpoints.
- `POST /api/v1/datasets/upload` now accepts `X-API-Key` (multipart
  `uvl_file` + `title`/`description`), with synchronous UVL validation.
- `POST /api/v1/datasets/<id>/publish` — publish a draft to Zenodo and
  get `{doi, deposition_id, files[]}` back.
- `POST /api/v1/datasets/<id>/new-version` — upload a replacement UVL
  and mint a new linked Zenodo version, with validation and indexing.
- `GET /api/v1/datasets/doi/<doi>` — dataset lookup by DOI.

### Fixed

- `FlamapyService.check_uvl` never invoked the parser, reporting any
  file as a valid model; it now genuinely parses (affects the async
  upload check too, which now reports real errors).
- New dataset versions created via the API are indexed in Elasticsearch
  so they appear in explore/search.

### Security

- Request bodies capped via `MAX_CONTENT_LENGTH` (20 MB) and UVL
  payloads capped at 1 MB before parsing, closing a CPU/memory
  exhaustion vector in the synchronous validator.
- Unknown scopes are rejected when generating API keys.

## [2.9] - 2026-06-25

Major release: uvlhub is rebuilt on **splent_framework** and gains **dataset
versioning** - replace a UVL and publish a new, linked Zenodo version.

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
  **dataset description editor** (TinyMCE) loads its assets - both were 404ing on
  nested asset paths.

### Upgrade notes
- Data-preserving Alembic migrations are included and apply automatically on
  deploy (`flask db upgrade`, run by the production entrypoint).
- Ensure `WORKING_DIR=/workspace` in the production `.env`.
