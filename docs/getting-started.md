# Getting started: development environment with Docker

This guide explains how to bring up the **uvlhub** development environment (a Flask product built on top of `splent_framework`) using Docker. This is the recommended and verified way to start the project locally.

## Prerequisites

You need to have installed:

- **Docker**
- **Docker Compose v2** (the `docker compose` plugin, not the old `docker-compose`)

The repository is mounted inside the container at `/workspace`, which is both the working directory (`WORKING_DIR=/workspace`) and the root of the `PYTHONPATH`. The application is identified through `SPLENT_APP=app`.

## Step 1: create the environment file

Copy the environment variables template to a `.env` file:

```bash
cp .env.docker.example .env
```

### Key variables in `.env`

| Variable | Description |
|----------|-------------|
| `FLASK_ENV` | Application environment (`development`). Determines which configuration class the `ConfigManager` uses (`DevelopmentConfig`, `TestingConfig`, `ProductionConfig`). |
| `MARIADB_*` | Credentials and connection data for MariaDB (host, port, database, user, password). They make up `SQLALCHEMY_DATABASE_URI`. |
| `WORKING_DIR` | Working directory inside the container. It must be `/workspace`. |
| `REDIS_URL` | Connection URL for Redis, used for the session (Flask-Session) and for the RQ task queue (worker). |
| `MAIL_*` | Mail configuration (Flask-Mail). In development it points to MailHog (SMTP on `:1025`). |

> In development you can usually leave the example values as they are, since they are prepared for the services defined in `docker-compose.dev.yml`.

## Step 2: build and start

```bash
docker compose -f docker/docker-compose.dev.yml up -d --build
```

Once it is up, the application is accessible at:

```
http://localhost
```

`nginx` listens on port `:80` and acts as a proxy toward the `web` container on `:5000`.

> **First build is slow, subsequent builds are fast**
> The first `--build` takes a while because it compiles heavy wheels (`python-sat`, `dd`, `gevent`, etc.). The Dockerfiles use a BuildKit pip *cache mount*, so those wheels are compiled only once and reused: subsequent rebuilds are much faster.

## What the development entrypoint does on startup

The `web` container runs `docker/entrypoints/development_entrypoint.sh`, which performs, in order:

1. `rosemary webpack:compile --watch` — compiles the frontend assets and keeps watching for changes.
2. `scripts/init-testing-db.sh` — initializes the testing database.
3. `scripts/apply_migrations.sh` — applies the database migrations (Flask-Migrate).
4. `rosemary elasticsearch:reset` — resets the Elasticsearch index.
5. `rosemary factlabel:generate` — generates the fact labels.
6. `flask run --host=0.0.0.0 --port=5000 --reload --debug` — starts the Flask development server with automatic reload and debug mode.

## Services and ports

The `docker/docker-compose.dev.yml` file defines the following services:

| Service | Port(s) | Description |
|----------|-----------|-------------|
| `web` | `5000` (internal) | Flask application with webpack in watch mode. Accessed via nginx. |
| `nginx` | `80` | Reverse proxy. Entry point at `http://localhost`. |
| `worker` | — | RQ worker that processes the task queue. |
| `db` | `3306` | MariaDB database. |
| `redis` | — | Redis (sessions and task queue). |
| `elasticsearch` | `9200` | Search engine. |
| `mailhog` | `8025` (UI), `1025` (SMTP) | Test mail server. UI at `http://localhost:8025`. |
| `selenium-hub` | `4444` | Selenium Grid hub for e2e tests. |
| `selenium-chrome` | — | Chrome node of the grid. |
| `selenium-firefox` | — | Firefox node of the grid. |

## Common operations

### View logs

To follow the logs of the `web` container in real time:

```bash
docker compose -f docker/docker-compose.dev.yml logs -f web
```

You can replace `web` with any other service (`worker`, `nginx`, `db`, etc.).

### Stop the environment

```bash
docker compose -f docker/docker-compose.dev.yml down
```

This stops and removes the containers, but keeps the volumes (database data, etc.).

### Reset the database

If you change the MariaDB credentials (`MARIADB_*`) in `.env`, you must also remove the volumes so that the database is reinitialized with the new values:

```bash
docker compose -f docker/docker-compose.dev.yml down -v
```

> The `-v` flag deletes the volumes, including the persisted database data. Start again with `up -d --build` afterward.
