<div align="center">

  <a href="">[![Pytest Testing Suite](https://github.com/diverso-lab/fmlib/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/diverso-lab/fmlib/actions/workflows/tests.yml)</a>
  <a href="">[![Commits Syntax Checker](https://github.com/diverso-lab/fmlib/actions/workflows/commits.yml/badge.svg?branch=main)](https://github.com/diverso-lab/fmlib/actions/workflows/commits.yml)</a>
  
</div>

# fmlib

## Set `.env` file in root with:

```
MYSQL_HOSTNAME=db
MYSQL_DATABASE=fmlibdb
MYSQL_USER=fmlibuser
MYSQL_PASSWORD=fmlibpass
MYSQL_ROOT_PASSWORD=fmlibrootpass
ZENODO_ACCESS_TOKEN=<GET_ACCESS_TOKEN_IN_ZENODO>
SECRET_KEY=<GET_SECRET_KEY_RUNNING_SECRET.PY>
```

## Run containers

```
docker compose up -d 
```

## Run migrations

Inside the `fmlib-web` container, run:

```
flask db init
flask db migrate
flask db upgrade
```
