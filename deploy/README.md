# Running uvlhub

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
- `AUTODEPLOY_SECRET`
- `OAUTH_REDIRECT_BASE_URL`
- `ZENODO_ACCESS_TOKEN`
- `BACKUP_DESTINATION`
- `BACKUP_AGE_RECIPIENTS`
- `OBSERVABILITY_DSN`
- `OBSERVABILITY_EMAIL_TO`
- `OBSERVABILITY_MATRIX_HOMESERVER`
- `OBSERVABILITY_MATRIX_ROOM_ID`
- `OBSERVABILITY_MATRIX_TOKEN`
- `MAIL_HOST`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_FROM`
- `SECRET_KEY`
- `MARIADB_PASSWORD`
- `MARIADB_ROOT_PASSWORD`
- `SERVER_NAME`
- `BACKUP_HOST_DIR`

A long random string is right for any of them that is a secret, for
example the output of `openssl rand -hex 32`. Choose the database
passwords before the first start, because the database keeps the
ones it starts with.

The web service runs `git.splent.io/splent-io/uvlhub:stable`, the image the product's releases
publish. `SPLENT_IMAGE` in `.env` names another one. To build the
image from this repository instead, run

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build
```

Every other setting in `.env` has a working default. The optional ones
at the end are commented out, each with what it does.

To upgrade, run these from this directory.

```bash
git pull
docker compose pull
docker compose up -d
```

The database and the uploaded files live on named volumes, so they
survive it, and the app applies its migrations when it starts.

This directory is generated. Change the product instead and build it
again with `splent product:build`.
