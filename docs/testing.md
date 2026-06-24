# Testing

Testing in `uvlhub` follows the **splent testing pyramid**: a six-level
structure in which each level tests a different layer of the product, from the
most isolated logic to end-to-end and load scenarios.

All tests live inside each feature, under `app/features/<name>/tests/`, with
**one file per level**. The [`rosemary`](#rosemary-test) CLI is responsible for
selecting which levels to run based on the pytest *markers*.

## The pyramid: the 6 levels

Each level has a fixed file and a fixed marker. Test selection is done by
marker, not by file name.

| File | Marker | What it tests |
| --- | --- | --- |
| `test_unit.py` | `unit` | Pure logic, without the Flask app or a database. |
| `test_repository.py` | `repository` | Repositories against the database. |
| `test_service.py` | `service` | Services (business logic) against the database. |
| `test_integration.py` | `integration` | HTTP routes through the Flask *test client*. |
| `test_selenium.py` | `e2e` | End-to-end in the browser, via Selenium Grid. |
| `locustfile.py` | `load` | Load tests, launched with `rosemary locust`. |

The base of the pyramid (`unit`) is the fastest and the one that should have
the most tests; the top (`e2e` and `load`) is the slowest and most expensive,
reserved for validating complete flows.

### Module-level marker

> **Important:** each test file carries a module-level `pytestmark` that marks
> **all** the tests in that file with its corresponding level.

```python
# app/features/<name>/tests/test_unit.py
import pytest

pytestmark = pytest.mark.unit

def test_algo():
    ...
```

```python
# app/features/<name>/tests/test_repository.py
import pytest

pytestmark = pytest.mark.repository
```

```python
# app/features/<name>/tests/test_service.py
import pytest

pytestmark = pytest.mark.service
```

```python
# app/features/<name>/tests/test_integration.py
import pytest

pytestmark = pytest.mark.integration
```

```python
# app/features/<name>/tests/test_selenium.py
import pytest

pytestmark = pytest.mark.e2e
```

This way, it is enough to declare the `pytestmark` once per file, and there is
no need to decorate each individual test function. The markers are defined in
`[tool.pytest.ini_options]` of `pyproject.toml`.

## `rosemary test [feature]`

Runs the tests relying on the pyramid markers. If a feature is given, it is
limited to `app/features/<feature>`; otherwise, it traverses all features.

By default it runs the **four lower levels**: `unit`, `repository`,
`service`, and `integration` (it excludes `e2e` and `load`).

```bash
# All tests by default (unit + repository + service + integration)
rosemary test

# Only the dataset feature, default levels
rosemary test dataset
```

### Per-level selection flags

The flags `--unit`, `--repository`, `--service`, `--integration`, and `--e2e` are
**combinable** (they are added with OR: the indicated levels are run).

```bash
# Only unit tests
rosemary test --unit

# Only unit + repository of the auth feature
rosemary test auth --unit --repository

# Only integration
rosemary test --integration
```

### `--all`, `--load`, and `-k`

```bash
# Also includes the e2e (Selenium)
rosemary test --all

# Only the e2e
rosemary test --e2e

# Redirects to the load tests -> equivalent to launching locust
rosemary test --load

# Filters by keyword (same as pytest -k)
rosemary test dataset -k upload
```

- `--all`: adds the `e2e` level to the default run.
- `--e2e`: selects the end-to-end level (requires Selenium Grid).
- `--load`: redirects to the load tests, managed by `rosemary locust`.
- `-k <keyword>`: filters the tests by keyword.

## `rosemary coverage [feature]`

Measures coverage using the same set of flags as `rosemary test`
(`--unit`, `--repository`, `--service`, `--integration`, `--e2e`, `--all`,
`--load`, `-k`), adding `--html` to generate a browsable report.

```bash
# Coverage with the default selection
rosemary coverage

# Coverage of a specific feature
rosemary coverage dataset

# Coverage of only the unit + service levels
rosemary coverage --unit --service

# Generates the HTML report in htmlcov/
rosemary coverage --html
```

With `--html`, the report is generated in the `htmlcov/` directory.

## The shared conftest

The common fixtures live in `app/features/conftest.py` and are available to
all features:

- **`test_app`**: instance of the Flask application configured for tests.
- **`test_client`**: Flask *test client* for making HTTP requests (used mainly
  in `test_integration.py`).
- **`clean_database`**: leaves the database in a clean state for the test.

It also includes the **`login()`** and **`logout()`** helpers to authenticate the
user in the tests that need it.

```python
# app/features/<name>/tests/test_integration.py
import pytest

pytestmark = pytest.mark.integration

def test_pagina_protegida(test_client):
    login(test_client, "user@example.com", "password")
    response = test_client.get("/ruta/protegida")
    assert response.status_code == 200
    logout(test_client)
```

## e2e tests: Selenium Grid

The `e2e` level (`test_selenium.py`) requires the **Selenium Grid** to be up. In
the Docker development environment it is provided by the services:

- `selenium-hub` (`:4444`)
- `selenium-chrome`
- `selenium-firefox`

These services are part of `docker/docker-compose.dev.yml`. With the Grid
available, the e2e tests can be run:

```bash
# Only e2e
rosemary test --e2e

# Default + e2e
rosemary test --all
```

There is also the `rosemary selenium [--driver firefox|chrome]` command to launch
Selenium sessions against the Grid.

## Load tests: load / locust

The `load` level (`locustfile.py`) is **not** run with `pytest`, but with Locust
through `rosemary`:

```bash
# Launch the load tests
rosemary locust

# Stop the load tests
rosemary locust:stop
```

`rosemary test --load` redirects to this same load flow.

## Continuous Integration (CI)

The Pytest workflow is in `.github/workflows/CI_pytest.yml`. On each run:

- Brings up a **MariaDB** database as a service.
- Configures the environment with `PYTHONPATH=workspace` and `SPLENT_APP=app`.
- Installs the product with `pip install --pre .`.
- Runs:

```bash
pytest app/features -m "(unit or repository or service or integration) and not slow"
```

That is, in CI the **four lower levels** of the pyramid are run (`unit`,
`repository`, `service`, `integration`), **excluding** the tests marked as
`slow`. The `e2e` (Selenium Grid) and `load` (Locust) levels are left out of the
Pytest workflow.
