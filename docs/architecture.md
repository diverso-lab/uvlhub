# Product architecture

`uvlhub_diversolab` is a **Flask product** named `uvlhub` built on top of
`splent_framework`. The framework is consumed as a **pip dependency**
(`splent_framework==1.6.1`); its code **does not live in this repository**. The
repository contains only the product: the app composition, the configuration,
the _features_, and the product-specific pieces that the framework does not cover.

- **Python 3.13.**
- The container mounts the repository at `/workspace`, with
  `PYTHONPATH=/workspace`, `WORKING_DIR=/workspace`, and `SPLENT_APP=app`.
- **All dependencies are pinned** in `pyproject.toml`
  (`[project.dependencies]`). Installation is `pip install .` — `requirements.txt`
  and `constraints.txt` **no longer** exist.
- `packages = []`: the `app` package **is not packaged**, it is imported via
  `PYTHONPATH` (thanks to the repo being mounted at `/workspace`).

---

## The `create_app` _factory_

`app/__init__.py` defines `create_app(config_name)`, the _factory_ that composes
the application. It assembles, in order, the following pieces:

1. **`ConfigManager`** — reads `app/config.py` (see below).
2. **`db`** — re-exported from `splent_framework.db` (same _singleton_).
3. **Flask-Migrate** — database migrations.
4. **Flask-Session** — sessions (backed by Redis).
5. **`register_features`** — from `app/feature_loader.py`, loads the _features_.
6. **Flask-Login** — authentication, including the `user_loader`.
7. **`LoggingManager`** — log management.
8. **CORS**.
9. **Swagger** (`flasgger`) — API documentation.
10. **Flask-Mail** — email sending.
11. Jinja **context processors** and the `format_thousands` filter.

In addition, **`ErrorHandlerManager`** reads `app/errors.py` to register the
error handlers.

### Re-export of `db`

`db` is **re-exported** from `splent_framework.db`. That is, the product and the
framework share **the same SQLAlchemy _singleton_**: the models defined in the
_features_ (`models.py`) and those provided by the framework operate on the same
`db` instance. This avoids duplicating the _engine_ and the session, and
guarantees that migrations, _seeders_, and repositories work against a single
source of truth.

---

## Configuration: `app/config.py`

`app/config.py` defines the configuration hierarchy:

- `Config` (base)
- `DevelopmentConfig`
- `TestingConfig`
- `ProductionConfig`

Among the values it manages: `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`
(built from the `MARIADB_*` variables), the `SESSION_*` variables
(Redis), `FLAMAPY_IDE_ORIGINS`, etc.

The **`ConfigManager`** of `splent_framework` locates this configuration through
the environment variable **`SPLENT_APP`**: it imports the
`{SPLENT_APP}.config` module (with `SPLENT_APP=app`, that is `app.config`) and
looks for the `{Env}Config` class corresponding to the active environment. This
way, the framework does not need to know in advance the path of the product's
configuration: it discovers it by convention from `SPLENT_APP`.

---

## Error handling: `app/errors.py`

`app/errors.py` provides the product's error handlers. For example,
`handle_404(app, e)` discriminates by the request path:

- If the path **starts with `/api/`**, it responds with **JSON**.
- Otherwise, it renders the `404.html` template.

The **`ErrorHandlerManager`** of `splent_framework` discovers this module the
same way `ConfigManager` discovers the configuration: through `SPLENT_APP`,
reading `app/errors.py` and registering the handlers in the app.

---

## Loading _features_: `feature_loader` and `[tool.splent]`

### The local _feature loader_

`app/feature_loader.py` is **local to the product** (copied from `egc`). It
exposes `register_features(app, env)`, which:

1. Reads from `pyproject.toml` the **union** of `features` ∪ `features_<env>` from
   the `[tool.splent]` block.
2. For each _feature_, imports its `__init__` and its `routes` / `models` /
   `hooks` / `signals` submodules.
3. Calls `init_feature(app)` if the _feature_ defines it.
4. Registers **all the `Blueprint`s** found (with **deduplication by name**).

It is a **declarative whitelist**: the active _features_ are declared explicitly
in `pyproject.toml`. The `.moduleignore` mechanism **no longer** exists.

### The `[tool.splent]` block of `pyproject.toml`

In the root `pyproject.toml`:

```toml
[tool.splent]
features = [ ... 22 features ... ]
features_dev = []
features_prod = []
```

- `features` — _features_ active in **all** environments.
- `features_dev` — additional _features_ only in **development**.
- `features_prod` — additional _features_ only in **production**.

In the current state, `features_dev` and `features_prod` are empty, and the
**22 _features_** of the product are declared in `features`:

```
apikeys        auth          captcha       confirmemail
dataset        downloadqueue elasticsearch explore
factlabel      featuremodel  flamapy       generator
hubfile        mail          orcid         profile
public         reset         statistics    team
webhook        zenodo
```

---

## Product-specific pieces in `app/`

`splent_framework` covers the **common infrastructure** (composition, `db`,
config/error/logging managers, blueprint _base classes_, services, repositories,
and _seeders_). But there are specific needs of `uvlhub` that the framework does
**not** solve. These pieces live in `app/` and are kept **outside the framework**
because they are particular to this product:

### `app/managers/task_queue_manager.py`

Management of asynchronous jobs with **RQ**. When enqueuing, it **returns the
`job`** (so its status/result can be queried). In **testing** it uses
**`fakeredis`**, so the tests do not depend on a real Redis. This policy of
returning the `job` and the _fallback_ to `fakeredis` are product decisions, not
the framework's.

### `app/selenium/common.py`

Support for _end-to-end_ tests with **Selenium**, capable of handling **Chrome and
Firefox** through **Selenium Grid**. It exposes `get`/`set_service_driver`. It is
specific to this product's E2E testing _setup_.

### `app/environment/host.py`

**Host mapping** for the tests. It translates the host seen from the code (which
runs in `/workspace` inside the container) to the real network host: for example
`/workspace` → `web:5000` / `nginx_web_server_container`. This resolves the
difference between the process's perspective and that of the container network,
something particular to the `uvlhub` deployment.

### `app/bootstraps/locustfile_bootstrap.py`

**Discovers the `locustfile`s** distributed across `app/features`, so that the
load tests (Locust) can find them without manual configuration.

---

## Directory tree of `app/`

```
app/
├── __init__.py              # create_app(config_name): la factory
├── config.py                # Config / Development / Testing / Production
├── errors.py                # handle_404, etc. (lo lee ErrorHandlerManager)
├── feature_loader.py        # register_features(app, env) — lista blanca
├── managers/
│   └── task_queue_manager.py    # RQ: devuelve job; fakeredis en testing
├── selenium/
│   └── common.py                # Chrome+Firefox vía Selenium Grid
├── environment/
│   └── host.py                  # mapeo de host /workspace -> web:5000
├── bootstraps/
│   └── locustfile_bootstrap.py  # descubre locustfiles en app/features
└── features/
    ├── conftest.py          # fixtures test_app, test_client, clean_database
    ├── apikeys/
    ├── auth/
    ├── captcha/
    ├── confirmemail/
    ├── dataset/
    ├── downloadqueue/
    ├── elasticsearch/
    ├── explore/
    ├── factlabel/
    ├── featuremodel/
    ├── flamapy/
    ├── generator/
    ├── hubfile/
    ├── mail/
    ├── orcid/
    ├── profile/
    ├── public/
    ├── reset/
    ├── statistics/
    ├── team/
    ├── webhook/
    └── zenodo/
```

Each `app/features/<name>/` follows the same anatomy: `__init__.py` (with the
`BaseBlueprint`), `routes.py`, `models.py`, `services.py`, `repositories.py`,
`forms.py`, `seeders.py`, `templates/<name>/`, `assets/js/` (frontend with
webpack), and `tests/`.

---

## Deployment model summary

- The **repository is mounted at `/workspace`** inside the container, with
  `PYTHONPATH=/workspace`, `WORKING_DIR=/workspace`, and `SPLENT_APP=app`.
- The **dependencies live in `pyproject.toml`** and are installed with
  `pip install .` (without `requirements.txt` or `constraints.txt`).
- The `app` package **is not packaged** (`packages = []`); it is imported via
  `PYTHONPATH` since the repo is mounted at `/workspace`.
- The framework (`splent_framework`) and the CLI (`rosemary`, a separate package)
  are installed separately; the product is limited to **composing** the app and
  providing configuration, _features_, and the product-specific pieces described
  above.
