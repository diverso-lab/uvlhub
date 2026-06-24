# Rosemary — Project CLI

`rosemary` is the command-line tool for **uvlhub_diversolab**. It brings together the development, database, testing, frontend, and product operations tasks under a single entry point.

## What rosemary is

- It is a **package owned** by the repository, located in `rosemary/`, with its own `pyproject.toml` and a `src/` layout (the code lives in `rosemary/src/rosemary/`).
- It is installed in editable mode with:

  ```bash
  pip install -e ./rosemary
  ```

  In the Docker containers it **comes pre-installed** (the entrypoint and the Dockerfiles install it alongside the rest of the dependencies), so there is no need to install it manually to use it within the dockerized environment.
- It exposes the `rosemary` entry point.
- Commands are **auto-discovered** from the `rosemary/src/rosemary/commands/` directory: each command is a file in that directory and is registered automatically, without the need to modify a central registry.

## How to run it

`rosemary` needs to be able to import the product's `app` package. This is satisfied in two scenarios:

- **Inside the container** (the usual case during development):

  ```bash
  docker compose -f docker/docker-compose.dev.yml exec web rosemary <command> [options]
  ```

- **In any environment where `app` is importable**, that is, with the repository on the `PYTHONPATH` (`PYTHONPATH=/workspace`, `SPLENT_APP=app`):

  ```bash
  rosemary <command> [options]
  ```

All commands are documented below, grouped by category.

## Testing

| Command | Description |
| --- | --- |
| `rosemary test [feature]` | Runs the pyramid tests. By default it includes unit + repository + service + integration (excludes e2e and load). Flags: `--unit` / `--repository` / `--service` / `--integration` / `--e2e` (combinable, OR logic), `--all` (includes e2e), `--load` (redirects to locust), `-k <keyword>`. |
| `rosemary coverage [feature]` | Runs the tests with coverage. Same set of flags as `test`, plus `--html` (generates the report in `htmlcov/`). |

For details on the test pyramid markers and the structure of each level, see [docs/testing.md](testing.md).

## Database

| Command | Description |
| --- | --- |
| `rosemary db:reset` | Resets the database. Flag: `--clear-migrations`. |
| `rosemary db:seed` | Seeds the database by running the seeders (ordered by `priority`). Flags: `--reset`, `-y`. |
| `rosemary db:console` | Opens an interactive console against the database. |
| `rosemary db:migrate` | Generates/applies the database migrations. |
| `rosemary db:dump` | Dumps the contents of the database. |
| `rosemary db:delete-dataset` | Deletes a dataset from the database. |

## Features

| Command | Description |
| --- | --- |
| `rosemary feature:create <name>` | Creates the scaffolding for a new feature in `app/features/<name>/`. |
| `rosemary feature:list` | Lists the product's features. |

## Search

| Command | Description |
| --- | --- |
| `rosemary elasticsearch:reset` | Resets the Elasticsearch indexes. |
| `rosemary elasticsearch:reindex` | Reindexes the data in Elasticsearch. |

## Frontend

| Command | Description |
| --- | --- |
| `rosemary webpack:compile [<feature>] [--watch]` | Compiles the frontend assets with webpack. Accepts a specific feature and the `--watch` flag to recompile continuously. |

## Cleanup

| Command | Description |
| --- | --- |
| `rosemary clear:all` | Runs all cleanup tasks. |
| `rosemary clear:cache` | Clears the cache. |
| `rosemary clear:log` | Clears the logs. |
| `rosemary clear:uploads` | Clears the uploaded files. |

## Environment

| Command | Description |
| --- | --- |
| `rosemary env` | Displays/manages environment information. |
| `rosemary compose:env` | Manages the docker compose environment. |

## Quality

| Command | Description |
| --- | --- |
| `rosemary linter` | Runs the linter over the code. |
| `rosemary linter:fix` | Runs the linter applying automatic fixes. |
| `rosemary detect_secrets` | Detects secrets in the code. |

## FactLabel

| Command | Description |
| --- | --- |
| `rosemary factlabel:generate` | Generates the fact labels. |
| `rosemary factlabel:pending` | Lists the pending fact labels. |

## Metrics

| Command | Description |
| --- | --- |
| `rosemary metrics:status` | Shows the status of the metrics. |
| `rosemary metrics:backfill` | Backfills the metrics. |
| `rosemary counters:sync` | Synchronizes the counters. |

## Others

| Command | Description |
| --- | --- |
| `rosemary mail:test` | Sends a test email. |
| `rosemary selenium [--driver firefox\|chrome]` | Runs Selenium tasks. Flag: `--driver firefox\|chrome`. |
| `rosemary locust` | Launches the load tests with Locust. |
| `rosemary locust:stop` | Stops the Locust load tests. |
| `rosemary update` | Updates the project. |
| `rosemary update:pip` | Updates the pip dependencies. |
| `rosemary update:npm` | Updates the npm dependencies. |
| `rosemary route:list` | Lists the routes registered in the application. |
| `rosemary info` | Shows project information. |
