# uvlhub_splent

A web application built with SPLENT, derived from the `sample_splent_spl` product line.

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
