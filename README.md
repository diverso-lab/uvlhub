<div align="center">

  <!-- CI Workflows -->
  <a href="">[![Pytest Testing Suite](https://github.com/diverso-lab/uvlhub/actions/workflows/CI_pytest.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/CI_pytest.yml)</a>
  <a href="">[![Commits Syntax Checker](https://github.com/diverso-lab/uvlhub/actions/workflows/CI_commits.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/CI_commits.yml)</a>
  <a href="">[![Lint](https://github.com/diverso-lab/uvlhub/actions/workflows/CI_lint.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/CI_lint.yml)</a>

</div>

<div style="text-align: center; margin-top: 10px">
  <img src="https://www.uvlhub.io/static/media/logos/default.svg" alt="Logo">
</div>

# uvlhub

**uvlhub** is a repository of feature models in **UVL** (Universal Variability Language) format, integrated with Zenodo and flamapy, and developed following Open Science principles by DiversoLab.

This version of the product is **built on top of [`splent_framework`](https://pypi.org/project/splent-framework/)**, installed as a pip dependency (pinned in `pyproject.toml`; its code does **not** live in this repository). The framework provides the common infrastructure — base blueprints, services, repositories, seeders, configuration and database management — so the product repository focuses on uvlhub's own logic.

The code lives as a Flask application under `app/`, organized into self-contained **features**, and ships with **rosemary**, the project's CLI.

---

## Documentation notice

> **`docs.uvlhub.io` is outdated.** It no longer reflects the current architecture built on `splent_framework`.
>
> The up-to-date documentation lives in this repository's [`docs/`](docs/) folder.

---

## Quickstart

Three steps to spin up the full development environment with Docker:

```bash
# 1. Clone the repository
git clone <repo-url> uvlhub
cd uvlhub

# 2. Create the environment file from the template
cp .env.docker.example .env

# 3. Build and start the services
docker compose -f docker/docker-compose.dev.yml up -d --build
```

Once the containers are up, open:

```
http://localhost
```

(nginx listens on port `:80` and proxies to `web:5000`.)

> The first build takes a while (heavy wheels such as `python-sat`, `dd` and `gevent` are compiled); thanks to the BuildKit pip cache mount, subsequent builds are fast.

---

## Stack

| Layer | Technology |
|------|------------|
| Web | **Flask 3.1** |
| ORM | **SQLAlchemy 2.0** + Flask-Migrate |
| Database | **MariaDB** |
| Queues & sessions | **Redis** + **RQ** |
| Search | **Elasticsearch** |
| Frontend | **Webpack** (per-feature assets) |
| Common infrastructure | **splent_framework** |

Other development-environment services: **MailHog** (UI `:8025`, SMTP `:1025`) and a **Selenium Grid** (hub `:4444` + Chrome + Firefox) for end-to-end tests.

Key requirements: **Python 3.13**. All dependencies are pinned in `pyproject.toml` (`[project.dependencies]`) and installed with `pip install .`. The **rosemary** CLI is a separate package installed with `pip install -e ./rosemary`.

---

## Documentation

All project documentation lives in [`docs/`](docs/):

| Document | Contents |
|-----------|-----------|
| [getting-started.md](docs/getting-started.md) | Setting up the environment and first steps. |
| [architecture.md](docs/architecture.md) | Product architecture on `splent_framework`: `create_app`, configuration and feature loading. |
| [features.md](docs/features.md) | Anatomy of a feature and the catalog of included features. |
| [rosemary.md](docs/rosemary.md) | Reference for the `rosemary` CLI and its commands. |
| [testing.md](docs/testing.md) | The splent testing pyramid and how to run the tests. |
| [deployment.md](docs/deployment.md) | Production deployment with Docker and CD. |
