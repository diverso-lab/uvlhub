# Features

In uvlhub, functionality is organized into **features**. Each feature is a
self-contained module under `app/features/<name>/` that groups together its
routes, models, services, repositories, forms, seeders, templates, frontend
assets, and its entire testing pyramid. The product is composed by declaring
which features are loaded in the `pyproject.toml`, and the `feature_loader` is
responsible for discovering them and registering them in the Flask application.

## Anatomy of a feature

A feature lives in `app/features/<name>/` and is made up of the following
files:

```
app/features/<name>/
├── __init__.py          # defines the feature's Blueprint
├── routes.py            # routes (endpoints) of the feature
├── models.py            # SQLAlchemy models
├── repositories.py      # data access (repositories)
├── services.py          # business logic (services)
├── forms.py             # WTForms forms
├── seeders.py           # sample data / seeding
├── templates/<name>/    # the feature's Jinja templates
│   └── index.html
├── assets/js/           # the feature's frontend
│   ├── scripts.js
│   └── webpack.config.js
└── tests/               # testing pyramid (see testing doc)
    ├── test_unit.py
    ├── test_repository.py
    ├── test_service.py
    ├── test_integration.py
    ├── test_selenium.py
    └── locustfile.py
```

### Purpose of each file

- **`__init__.py`**: defines the feature's Blueprint. It is the entry point
  that imports and exposes `<name>_bp`.
- **`routes.py`**: declares the routes (HTTP endpoints) registered in the
  feature's Blueprint.
- **`models.py`**: the feature's SQLAlchemy models.
- **`repositories.py`**: data access repositories. They inherit from
  `BaseRepository`.
- **`services.py`**: services with the business logic. They inherit from
  `BaseService`.
- **`forms.py`**: WTForms forms used by the routes/templates.
- **`seeders.py`**: seeders to populate the database with sample data.
  They inherit from `BaseSeeder`.
- **`templates/<name>/`**: the feature's Jinja templates (includes at least
  `index.html`). The `template_folder` is declared in the Blueprint.
- **`assets/js/`**: the feature's frontend, built with webpack
  (`scripts.js` + `webpack.config.js`). It is compiled with `rosemary webpack:compile`.
- **`tests/`**: the feature's testing pyramid (unit, repository, service,
  integration, e2e/selenium, and load/locust). See the testing documentation.

### The Blueprint (`__init__.py`)

Each feature's `__init__.py` defines its Blueprint using `BaseBlueprint`:

```python
from splent_framework.blueprints.base_blueprint import BaseBlueprint

<name>_bp = BaseBlueprint("<name>", __name__, template_folder="templates")
```

### Base classes imported from splent_framework

The base building blocks of each feature are imported from the
`splent_framework` framework (it is a pip dependency; its code is **not** in the
repo):

```python
from splent_framework.blueprints.base_blueprint import BaseBlueprint
from splent_framework.services.BaseService import BaseService
from splent_framework.repositories.BaseRepository import BaseRepository
from splent_framework.seeders.BaseSeeder import BaseSeeder
```

- **`BaseBlueprint`** (`splent_framework.blueprints.base_blueprint`): the base
  for the feature's Blueprint (`__init__.py`).
- **`BaseService`** (`splent_framework.services.BaseService`): the base for the
  services (`services.py`).
- **`BaseRepository`** (`splent_framework.repositories.BaseRepository`): the base
  for the repositories (`repositories.py`).
- **`BaseSeeder`** (`splent_framework.seeders.BaseSeeder`): the base for the
  seeders (`seeders.py`).

## How a feature is discovered and registered

Discovery and registration are performed by `app/feature_loader.py` through the
`register_features(app, env)` function. Its behavior is as follows:

1. It reads the list of features from the `pyproject.toml`, specifically
   `[tool.splent].features` unioned (∪) with `features_<env>` (the
   environment-specific list, e.g. `features_dev` or `features_prod`).
2. For each feature in that list:
   - It imports its `__init__.py` and its submodules (`routes`, `models`, `hooks`,
     `signals`) if they exist.
   - It calls `init_feature(app)` if the feature defines that function.
   - It registers all the Blueprints found in the application (with
     deduplication by name).

It is a **declarative whitelist**: a feature is only loaded if it is declared
in the `pyproject.toml`. (The old `.moduleignore` is no longer used.)

### Declaring the feature in the pyproject.toml

For a feature to be loaded, it **must** be declared in the
`[tool.splent]` section of the root `pyproject.toml`:

```toml
[tool.splent]
features = [
    "apikeys",
    "auth",
    "captcha",
    # ...
    "<name>",
]
features_dev = []
features_prod = []
```

- **`features`**: features that are always loaded.
- **`features_dev`** / **`features_prod`**: additional features that are loaded
  only in the corresponding environment (they are merged with `features`).

If a feature exists in `app/features/<name>/` but does not appear in these lists,
the `feature_loader` will not load it.

## Creating a feature

To create a new feature, use the rosemary command:

```bash
rosemary feature:create <name>
```

This command generates the complete scaffolding of the feature in
`app/features/<name>/`:

- `__init__.py` with the Blueprint
  (`<name>_bp = BaseBlueprint("<name>", __name__, template_folder="templates")`).
- `routes.py`
- `models.py`
- `repositories.py`
- `services.py`
- `forms.py`
- `seeders.py`
- `templates/<name>/index.html`
- `assets/js/scripts.js` and `assets/js/webpack.config.js` (frontend with webpack)
- The testing pyramid in `tests/`: `test_unit.py`, `test_repository.py`,
  `test_service.py`, `test_integration.py`, `test_selenium.py` and
  `locustfile.py`.

### Activating the feature

Creating the scaffolding does **not** activate the feature on its own. It must be
declared in `[tool.splent].features` of the `pyproject.toml` so that the
`feature_loader` discovers and registers it:

```toml
[tool.splent]
features = [
    # ... existing features ...
    "<name>",
]
```

## Seeders and priority

A feature's seeders inherit from `BaseSeeder` and can define an optional
`priority` attribute. The `rosemary db:seed` command orders the execution of the
seeders by `priority` (default value **10**), which makes it possible to control
the order when some data depends on other data.

```python
from splent_framework.seeders.BaseSeeder import BaseSeeder


class <Name>Seeder(BaseSeeder):
    priority = 10  # lower priority runs first; default 10
```
