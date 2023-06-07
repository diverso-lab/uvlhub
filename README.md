<div align="center">

  <a href="">[![Pytest Testing Suite](https://github.com/diverso-lab/uvlhub/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/tests.yml)</a>
  <a href="">[![Commits Syntax Checker](https://github.com/diverso-lab/uvlhub/actions/workflows/commits.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/commits.yml)</a>
  
</div>

<div style="text-align: center;">
  <img src="https://www.uvlhub.io/static/img/logos/logo-dark.svg" alt="Logo">
</div>

# uvlhub.io

## Set `.env` file in root with:

```
FLASK_APP_NAME=UVLHUB.IO
MYSQL_HOSTNAME=db
MYSQL_DATABASE=uvlhubdb
MYSQL_USER=uvlhubuser
MYSQL_PASSWORD=uvlhubpass
MYSQL_ROOT_PASSWORD=uvlhubrootpass
ZENODO_ACCESS_TOKEN=<GET_ACCESS_TOKEN_IN_ZENODO>
```

## Deploy in develop

```
docker compose -f docker-compose.dev.yml up -d 
```

## Deploy in production

```
docker compose -f docker-compose.prod.yml up -d 
```

## Run migrations

Inside the `web` container, run:

```
flask db migrate
flask db upgrade
```
