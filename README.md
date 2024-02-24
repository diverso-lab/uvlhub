<div align="center">

  <a href="">[![Pytest Testing Suite](https://github.com/diverso-lab/uvlhub/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/tests.yml)</a>
  <a href="">[![Commits Syntax Checker](https://github.com/diverso-lab/uvlhub/actions/workflows/commits.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/commits.yml)</a>
  
</div>

<div style="text-align: center;">
  <img src="https://www.uvlhub.io/static/img/logos/logo-light.svg" alt="Logo">
</div>

# uvlhub.io

Repository of feature models in UVL format integrated with Zenodo and FlamaPy - Developed by DiversoLab

## Clone repo

```
git clone https://github.com/diverso-lab/uvlhub.git
```

## Set `.env` file in root with:

Create an `.env` file in the root of the project with this information. It is important to obtain a token in Zenodo first. **We recommend creating the token in the Sandbox version of Zenodo, in order to generate fictitious DOIs and not make intensive use of the real Zenodo SLA.**

```
FLASK_APP_NAME=UVLHUB.IO
MARIADB_HOSTNAME=db
MARIADB_PORT=3306
MARIADB_DATABASE=uvlhubdb
MARIADB_USER=uvlhubuser
MARIADB_PASSWORD=uvlhubpass
MARIADB_ROOT_PASSWORD=uvlhubrootpass
ZENODO_ACCESS_TOKEN=<GET_ACCESS_TOKEN_IN_ZENODO>
```

## Deploy in develop

To deploy the software under development environment, run:

```
docker compose -f docker-compose.dev.yml up -d 
```

This will apply the migrations to the database and run the Flask application. 

**If everything worked correctly, you should see the deployed version of UVLHub in development at `http://localhost`.**

### Migrations

However, if during development there are new changes in the model, run inside the `web` container:

```
flask db migrate
flask db upgrade
```

### Tests

To run unit test, please enter inside `web` container:

```
pytest app/tests/units.py
```

## Deploy in production (Docker Compose)

```
docker compose -f docker-compose.prod.yml up -d 
```

## Deploy in production (Docker Swarm)

To have an elastic growth of services, the use of Docker Swarm is recommended.

First, we start a new cluster

```
docker swarm init --advertise-addr <IP_SERVER>
```

Now, we start the services

```
docker stack deploy -c docker-compose.swarm.yml uvlhub
```

To stop the deployment:

```
docker stack rm uvlhub
```

## SSL certificates

To generate a new certificate, run: 

```
cd scripts
chmod +x ssl_setup.sh && ./ssl_setup.sh
```

To renew a certificate that is less than 60 days from expiry, execute:

```
cd scripts
chmod +x ssl_renew.sh && ./ssl_renew.sh
```

## Update dependencies

To update all project dependencies automatically, run:

```
cd scripts
chmod +x update_dependencies.sh && ./update_dependencies.sh
```

Note: it is the responsibility of the developer to check that the update of the dependencies has not broken any functionality and each dependency maintains backwards compatibility. Use the script with care!

