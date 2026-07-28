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
- `POST /api/v1/datasets/<id>/transfer`, which offers a dataset to
  another account by `user_id` or `email`, restricted to the current
  owner. It returns `202` with a pending offer and moves nothing on its
  own. The receiving account answers through
  `POST /api/v1/datasets/transfers/<id>/accept` or `/decline`, the sender
  can withdraw it with `/cancel`, and both sides can list their offers
  with `GET /api/v1/datasets/transfers`. On acceptance the whole version
  lineage moves as a unit, files included. A dataset carries a permanent
  Zenodo DOI and appears in its owner's public listings, so it is never
  pushed onto an account that did not ask for it.
- `POST /api/v1/datasets/upload` accepts optional `authors` (JSON array,
  or the usual `authors[0][name]` form fields), so a service account can
  publish while crediting the real developer. The authors are stored as
  `Author` rows and become the Zenodo creators. Without them the previous
  behaviour is unchanged. Names and affiliations are stripped of control
  and bidirectional characters, an `orcid` is only accepted when that
  ORCID has signed in to uvlhub at least once, and the publishing account
  is recorded in `ds_meta_data.api_publisher_user_id` (new migration
  `c9d0e1f2a3b4`) and published in the Zenodo record's notes, so credit
  given to somebody else stays traceable.
- `concept_doi` in the publish and new-version API responses.

### Fixed

- Descriptions sent to `POST /api/v1/datasets/upload` are sanitized with
  the same allowlist as the web upload. The dataset page renders the
  description with `safe`, so the API path was an unsanitized HTML sink
  on a public DOI landing page.
- Versioning a dataset that already has a successor is refused, so a
  lineage cannot branch, and the lineage walk covers every branch of rows
  that already did. A partial walk would hide published versions from
  `/versions` and move only part of a lineage on a transfer.
- A version clone whose Zenodo publication fails is removed instead of
  staying in the lineage forever with no DOI, and it no longer inherits
  the concept DOI of its origin before Zenodo has assigned one. The
  removal stops at the point of no return. Publishing a deposition mints
  a permanent public DOI that nobody can withdraw, so the deposition id
  is now committed before that call and the local row is kept afterwards
  whatever else fails. Deleting it would have left a public Zenodo record
  holding the user's files with no local trace of which deposition it is,
  and no way to reconcile the two.
- Persisting the concept DOI can no longer fail a publication that
  already succeeded, and a concept DOI too long for the column is
  dropped rather than breaking the write.
- `user_id` on a transfer is parsed strictly, so a JSON `true` or `1.9`
  is rejected instead of being read as account 1.
- An `orcid` that is not a string in an API author payload is rejected
  with `400` instead of raising and returning `500`.
- API keys stop working when their account is deactivated. The key used
  to keep full `write_dataset` power indefinitely, which includes
  publishing permanent public records to Zenodo.
- `dataset_transfer_request.dataset_id` cascades on delete, and the
  `rosemary db:delete-dataset` cleanup removes transfer offers. Deleting
  a dataset that had ever been offered failed with a foreign key error.
- Migration `c9d0e1f2a3b4` can be downgraded on MySQL and MariaDB. It
  dropped the indexes backing its foreign keys before the table, which
  those engines refuse, leaving the schema pinned at that revision.

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
