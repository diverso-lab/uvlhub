# uvlhub_splent

A web application built with SPLENT, derived from the `openhubs_spl` product line (OpenHubs).

This repository is a thin shell. It declares which features the product installs
(see `pyproject.toml`) and SPLENT composes, validates and runs them.

## Run it locally

Your machine only needs **Docker**, **Git** and **GNU Make**. Python, Node and
the database all live inside containers, so nothing else has to be installed.

### 1. Create a workspace

A SPLENT product is not standalone. It lives in a workspace folder next to the
SPLENT tooling repositories.

```bash
mkdir splent_workspace && cd splent_workspace
git clone https://github.com/diverso-lab/splent_framework.git
git clone https://github.com/diverso-lab/splent_cli.git
git clone <url-of-this-repository>
```

Those three are all you need to run the product. The variability model this
product derives from is not one of them: `pyproject.toml` records its DOI under
`[tool.splent.spl_model]`, so the CLI downloads it once from UVLHub and caches
it under `.splent_cache/spls/`.

### 2. Check your Git config file

The CLI container mounts your `~/.gitconfig`. If that file does not exist,
Docker creates it as an empty directory and installing features fails later.
Create it once as a real file.

```bash
rm -rf ~/.gitconfig && touch ~/.gitconfig
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 3. Start the SPLENT CLI

```bash
cd splent_cli
make setup
```

That prepares the workspace `.env`, starts the CLI container and drops you
inside it. Every `splent` command below runs in there. From the host you can
also use `docker exec splent_cli_container splent <command>`.

### 4. Bring the product up

```bash
splent product:select uvlhub_splent
splent product:resolve        # install the features declared in pyproject.toml
splent product:derive --dev   # build images, run migrations, start the stack
splent db:seed -y             # load demo data, optional
```

The first derive downloads images and compiles assets, so give it a few minutes.
When it finishes the app is served at <http://localhost:5012>, and
`splent product:port` prints that URL again whenever you need it.

## Everyday commands

| Command | What it does |
|---------|--------------|
| `splent product:up --dev` | Start the stack |
| `splent product:down --dev` | Stop the stack |
| `splent product:restart` | Restart the Flask app |
| `splent product:logs` | Tail the container logs |
| `splent product:console` | Python shell with the app loaded |
| `splent feature:status` | Features installed in this product |
| `splent db:migrate` | Generate and apply a migration |
| `splent product:port` | Print the local URL |

## Frozen URLs

`frozen_urls.toml` lists every public address uvlhub.io 2.12 hands out that
this product keeps answering, and `tests/test_frozen_urls.py` checks it
against the app the product builds: the rules it serves, and the CORS and
the sign-in answer flamapyIDE relies on. No `splent` command runs it yet
(`product:test` runs the features' tests only) and neither does the CI, so
run it in the web container whenever the pins change and before a release:

```bash
docker exec uvlhub_splent_web bash -lc 'cd /workspace/uvlhub_splent && python -m pytest tests -q -p no:cacheprovider'
```

Its docstring says how to run it against working copies of the features.

## Deploy to production

`splent product:build` (the CI runs it) merges `docker/.env.prod.example` with
what every pinned feature declares into `deploy/.env.example`, and
`splent product:deploy` turns it into `deploy/.env` on the server, generating
the database and service passwords and asking for what only the operator
knows. `docker/.env.prod.example` explains each value; this is the picture.

```
browser --443--> TLS terminator on the host --127.0.0.1:92--> nginx (splent_feature_nginx) --> uvlhub_splent_web_deploy:5000
```

The nginx feature listens on HTTP only, so HTTPS comes from a terminator on
the host (nginx, Caddy, Traefik). Point it at nginx, `NGINX_HTTP_HOST_PORT`
(92 with this product's port offset), not at the web port 5012: the Host
check, the rate limit on the account forms, the long timeouts of the Zenodo
routes and the redacted access log are nginx's. The terminator has to

- keep the Host it received (Caddy does by default; nginx needs
  `proxy_set_header Host $host`);
- set `X-Forwarded-For` and `X-Forwarded-Proto`;
- wait as long as nginx does on the publishing routes, 600 s, or simply on
  everything (nginx's own default is 60 s).

`product:deploy` asks for:

| Variable | What to give |
|---|---|
| `SERVER_NAME` | The public host, `www.uvlhub.io`. Every absolute link names it, and the app refuses any other Host (400, no page). |
| `OAUTH_REDIRECT_BASE_URL` | `https://www.uvlhub.io`, the base of the ORCID and GitHub callbacks. |
| `NGINX_SERVER_NAME` | The name nginx serves the site by, `www.uvlhub.io`. Any other Host is refused. |
| `MAIL_HOST`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM` | The SMTP account (STARTTLS on 587). The deploy offers a random `MAIL_PASSWORD`: type the real one. |
| `ZENODO_ACCESS_TOKEN` | A Zenodo token with `deposit:write` and `deposit:actions`. |

and generates `SECRET_KEY`, the MariaDB passwords, `REDIS_PASSWORD` (redis
runs with a password in production) and `ELASTICSEARCH_PASSWORD` (the node
runs with security on, and the app signs in as `elastic`).

and, optionally, `NGINX_REDIRECT_SERVER_NAMES=uvlhub.io`: the bare domain
gets a 301 to `https://www.uvlhub.io` with its path, so old links keep
working and the app never sees another name.

Two values follow from the topology:

- `NGINX_TRUSTED_PROXY_CIDRS=172.16.0.0/12` with `NGINX_BIND_HOST=127.0.0.1`.
  nginx believes the terminator, which arrives from the docker network's
  gateway (the `peer=` field of nginx's access log shows it), and nobody else
  can reach the port.
- `SPLENT_TRUSTED_PROXIES=1`. nginx is the only hop the app talks to, and it
  forwards one `X-Forwarded-For` (the client), one `X-Forwarded-Proto` and
  one `X-Forwarded-Host`. The 2 that the CLI suggests for "the nginx feature
  behind a TLS front" makes the app look for two values in each and ignore
  the one it finds: `http://` links, which GitHub refuses as a callback,
  cookies without `Secure` and no HSTS.

Publishing to Zenodo still runs inside the request, so nginx gives the
publishing routes and the ZIP downloads `NGINX_LONG_REQUEST_TIMEOUT=600s` and
gunicorn gets `GUNICORN_TIMEOUT=630`, a little more, so nginx gives up first
and the worker still records the DOI.

Left to the operator on purpose:

- `ZENODO_ALLOW_PRODUCTION=true` goes into `deploy/.env` of the one
  deployment that publishes the hub's real records, never into a file every
  build reads, since its DOIs are permanent.
- `ORCID_CLIENT_*` and `GITHUB_CLIENT_*`: empty turns that sign-in off.

`NGINX_REDIRECT_SERVER_NAMES`, the pinned `X-Forwarded-Host` and nginx's
healthcheck take effect with the release of `splent_feature_nginx` after
1.4.0, the version pinned today, and autodeploy's digest, migration step
and `/readyz` wait with its release after 0.2.0.

### One host

uvlhub answers by `SERVER_NAME` alone. nginx closes the connection of any
Host that is not `NGINX_SERVER_NAME`, redirects `NGINX_REDIRECT_SERVER_NAMES`
to it, and forwards the Host it matched, never one a client sent in
`X-Forwarded-Host`. The app checks again (`TRUSTED_HOSTS`, which defaults to
`SERVER_NAME` and `localhost`, the name the deploy's probe uses inside the
container) and builds every absolute link, mails and callbacks included,
with `SERVER_NAME`. `tests/test_deploy.py` sends a forged Host and checks
the links.

### Files, deploys and backups

- Dataset files live under `PROTECTED_UPLOADS_DIR`, on the named volume
  `uvlhub_splent_web_deploy_protected_uploads`. The compose file gives the
  app the very path the volume is mounted at, so the two cannot disagree.
  The public uploads and the database are on named volumes too.
- The web service is healthy when `/readyz` answers 200: the database and
  the session store answer.
- `splent_feature_autodeploy` deploys every release in its own container,
  the only one with the Docker socket. It runs the release by its digest,
  backs up, migrates once in a one-off container, waits for `/readyz`, and
  rolls back when the release is not ready, restoring the database when the
  migration failed or changed the schema. Its README has the details.
- Elasticsearch is derived from the database and the files and is not
  backed up: after a restore, `splent feature:explore reindex` rebuilds it.
- Off-host, encrypted backups come with `splent_feature_backup`, once the
  product selects it.

## Migrating uvlhub.io 2.12

`python -m uvlhub_splent.migration_v2` is the migrator of the cutover: it
restores a dump of v2.12, builds an empty `uvlhub3` with the pinned
features' migrations and fills it, held to a versioned data contract
(`src/uvlhub_splent/migration_v2/contract.toml`). It is a first pass, and
its tests run on a MariaDB of their own:

```bash
bash uvlhub_splent/tests/migration_v2/run_with_throwaway_db.sh -q
```

[docs/migration_v2.md](docs/migration_v2.md) has the stages, how to run
it, the contract and where it departs from the plan.

## When something looks wrong

```bash
splent product:logs       # what the app actually says
splent doctor             # full workspace diagnosis
```

`splent product:validate` goes further and checks that the feature selection
satisfies the variability model, downloading the model first if this machine
has never seen it.

## Documentation

Everything else, from the feature catalog and the UVL variability model to the
full command reference and deployment, lives at
[docs.splent.io](https://docs.splent.io).
