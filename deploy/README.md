# Running uvlhub_splent

Everything a host needs is in this directory. It takes Docker with the
Compose plugin, and nothing else.

```bash
cp .env.example .env
# fill in the required values in .env
docker compose up -d
```

`docker compose up` refuses to start until these are set in `.env`,
and names the one that is missing.

- `ELASTICSEARCH_PASSWORD`
- `REDIS_PASSWORD`
- `NGINX_SERVER_NAME`
- `MAIL_HOST`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_FROM`
- `AUTODEPLOY_SECRET`
- `OAUTH_REDIRECT_BASE_URL`
- `ZENODO_ACCESS_TOKEN`
- `BACKUP_DESTINATION`
- `BACKUP_AGE_RECIPIENTS`
- `SECRET_KEY`
- `MARIADB_PASSWORD`
- `MARIADB_ROOT_PASSWORD`
- `SERVER_NAME`
- `BACKUP_HOST_DIR`

A long random string is right for any of them that is a secret, for
example the output of `openssl rand -hex 32`. Choose the database
passwords before the first start, because the database keeps the
ones it starts with.

The web image is built from this repository on the first
`docker compose up`. The framework, the CLI and every feature are
installed from PyPI, at the versions the repository pins.

Every other setting in `.env` has a working default. The optional ones
at the end are commented out, each with what it does.

To upgrade, run these from this directory.

```bash
git pull
docker compose up -d --build
```

The database and the uploaded files live on named volumes, so they
survive it, and the app applies its migrations when it starts.

This directory is generated. Change the product instead and build it
again with `splent product:build`.
