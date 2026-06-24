# Production deployment

This guide describes how **uvlhub** is deployed in production: the Compose files, the production image, the environment variable template, and the CD (continuous delivery) flow toward Docker Hub and the automatic redeploy via webhook.

> The container mounts the repository at `/workspace` (`PYTHONPATH=/workspace`, `WORKING_DIR=/workspace`, `SPLENT_APP=app`). All of the application's internal paths are resolved relative to that mount point.

## Production Compose

Deployment is orchestrated with `docker/docker-compose.prod.yml`, which defines the services needed to serve the application. On top of that base file there are several **variants** that are combined according to the needs of the environment:

| File | Purpose |
|---|---|
| `docker/docker-compose.prod.yml` | Base production Compose. |
| `docker/docker-compose.prod.ssl.*` | Variant with SSL/TLS termination. |
| `docker/docker-compose.prod.webhook.*` | Variant that enables the webhook redeploy service. |
| `docker/docker-compose.prod.watchtower.*` | Variant with Watchtower for automatic image updates. |

The variants are applied by chaining files with `-f`. For example, base + SSL + webhook:

```bash
docker compose \
  -f docker/docker-compose.prod.yml \
  -f docker/docker-compose.prod.ssl.yml \
  -f docker/docker-compose.prod.webhook.yml \
  up -d
```

Combine only the variants that apply to your environment (SSL if you terminate TLS on the host itself, webhook if you want automatic redeploy, watchtower if you delegate image updates to Watchtower).

## Production image: `Dockerfile.prod`

The production image is built with `docker/images/Dockerfile.prod`. Its build process essentially carries out the following steps:

1. **`pip install .`** — installs the `uvlhub` Flask product and all of its dependencies pinned in `pyproject.toml` (`[project.dependencies]`).
2. **`npm install`** — installs the frontend dependencies.
3. **`rosemary webpack:compile`** — compiles the features' frontend assets.
4. **`NODE_ENV=production`** — the compilation is performed in production mode.
5. **`.version` from `VERSION_TAG`** — writes the `/workspace/.version` file from the `VERSION_TAG` argument/variable, recording the deployed version.
6. **`gunicorn`** — the application is served with Gunicorn as the WSGI server (instead of the development environment's `flask run`).

Unlike the development environment, in production the assets are compiled once during the build (without `--watch`) and the application runs under Gunicorn.

## Environment variables: `.env.docker.production.example`

The `.env.docker.production.example` file acts as a **template** for the environment variables required in production. Copy it and fill it in with the real values for your deployment:

```bash
cp .env.docker.production.example .env
```

Relevant variables to configure:

- **`SECRET_KEY`** — **mandatory in production**. It must be set to a strong, secret value; it is the key Flask uses to sign sessions and other sensitive material.
- **`MARIADB_*`** — credentials and configuration for the MariaDB database (used by `SQLALCHEMY_DATABASE_URI` in `app/config.py`).
- **`DOMAIN`** — the public domain under which the application is served.

> Do not reuse the example values in a real environment. In particular, `SECRET_KEY` must be unique and must not be committed to the repository.

## CD flow (continuous delivery)

Continuous deployment relies on two GitHub Actions workflows.

### `CD_dockerhub.yml` — image build and push

It is triggered on **every GitHub release**. It builds the production image and **publishes (pushes) it to Docker Hub**. The build uses BuildKit (`DOCKER_BUILDKIT=1`), so that heavy dependencies are compiled by taking advantage of layer caching.

In broad terms:

```text
GitHub release
   └─> CD_dockerhub.yml
         ├─ DOCKER_BUILDKIT=1
         ├─ build of docker/images/Dockerfile.prod
         └─ push of the image to Docker Hub
```

### `CD_webhook.yml` — triggering the redeploy

After passing **Pytest on `main`**, this workflow **triggers a deploy webhook** against the production server. It is the mechanism that initiates the automatic redeploy once the test suite has turned green on the main branch.

```text
push/merge on main
   └─> Pytest (CI) OK
         └─> CD_webhook.yml
               └─ triggers the deploy webhook on the server
```

## `webhook` feature: redeploy on the server

The **`webhook`** feature is the server-side piece that receives the deploy signal and runs the **redeploy** inside the containers. Its flow is:

1. **`git_update.sh`** — updates the repository mounted at `/workspace` to the latest state of the branch.
2. **`pip install --pre .`** — reinstalls the `uvlhub` product with its dependencies inside the `web` and `worker` containers.
3. **`pip install -e ./rosemary`** — reinstalls the `rosemary` CLI (a separate package, `src/` layout) in editable mode.
4. **Restart** of the `web` and `worker` containers to pick up the new code.

```text
webhook received
   ├─ git_update.sh                  # updates /workspace
   ├─ pip install --pre .            # reinstalls uvlhub (web + worker)
   ├─ pip install -e ./rosemary      # reinstalls the rosemary CLI
   └─ restart of the web and worker containers
```

In this way, the full cycle chains together the image `push` on every release (`CD_dockerhub.yml`), the webhook trigger after Pytest on `main` (`CD_webhook.yml`), and the actual redeploy on the server managed by the `webhook` feature.
