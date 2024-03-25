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
DOMAIN=localhost
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

## Using Rosemary CLI

`Rosemary` is a CLI tool developed to facilitate project management and development tasks.

To use the Rosemary CLI, you need to be inside the `web_app_container` Docker container. This ensures that Rosemary operates in the correct environment and has access to all necessary files and settings.

First, make sure your Docker environment is running. Then, access the `web_app_container` using the following command:

```
docker exec -it web_app_container /bin/sh
```

In the terminal, you should see the prefix `/app #`. You are now ready to use Rosemary's commands.

### Update Project Dependencies

To update all project dependencies, run:

```
rosemary update
```

Note: it is the responsibility of the developer to check that the update of the dependencies has not broken any 
functionality and each dependency maintains backwards compatibility. Use the script with care!

### Extending the Project with New Modules

To quickly generate a new module within the project, including necessary boilerplate files 
like `__init__.py`, `routes.py`, `models.py`, `repositories.py`, `services.py`, `forms.py`,
and a basic `index.html` template, you can use the `rosemary` CLI tool's `make:module` 
command. This command will create a new blueprint structure ready for development.

To create a new module, run the following command from the root of the project:

```
rosemary make:module <module_name>
```

Replace `<module_name>` with the desired name of your module. For example, to create a 
module named "zenodo", you would run:

```
rosemary make:module zenodo
```


This command creates a new directory under `app/blueprints/` with the name of your module and sets up the initial files and directories needed to get started, including a dedicated `templates` directory for your module's templates.

**Note:** If the module already exists, `rosemary` will simply notify you and not overwrite any existing files.

This feature is designed to streamline the development process, making it easy to add new features to the project.

### Testing All Modules

To run tests across all modules in the project, you can use the following command:

```
rosemary test
```

This command will execute all tests found within the app/blueprints directory, covering all the modules of the project.

### Testing a Specific Module

If you're focusing on a particular module and want to run tests only for that module, you can specify the module
name as an argument to the rosemary test command. For example, to run tests only for the zenodo module, you would 
use:

```
rosemary test zenodo
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
