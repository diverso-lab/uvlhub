"""E3, the schema: an empty uvlhub3 at the head of the pinned features (§3.3).

The database is created with the contract's character set and collation
(DM-15), then ``splent db:upgrade`` brings every feature to its head, in a
process of its own: the features' migrations need the app, and the app has
no place in the migrator's process, which writes with Core only. That
process gets the server and its port, the migrator account and uvlhub3 as
its only database, and RUN_DB_SEED=false; it runs db:upgrade and nothing else, so the seed never
does (auth0002_role finds no account to give a role to).

Then the schema is held to the contract: V-12, the heads splent_migrations
records, and V-14, the collation of every text column, as the plan's SQL
does against uvlhub_migration_inputs.contract_collation, and the rest of
the contract (tables, columns, types, nullability). Any difference stops
the run.
"""

from __future__ import annotations

import os
import subprocess

import sqlalchemy as sa

from uvlhub.migration_v2 import contract as contract_module
from uvlhub.migration_v2.db import qualified, quote
from uvlhub.migration_v2.params import Refused

# V-14, as the plan writes it.
V14 = """
SELECT c.table_name, c.column_name, c.collation_name, k.expected
FROM information_schema.columns c
JOIN {inputs}.contract_collation k
  ON k.table_name = c.table_name AND k.column_name = c.column_name
WHERE c.table_schema = :target AND NOT (c.collation_name <=> k.expected)
"""


def child_env(params, **extra) -> dict:
    """The environment of a process that runs a feature's command on
    uvlhub3: this one's, with the database, the account and the seed
    switched to the migration's. The CLI keeps what its caller exports over
    the product's .env, so these win there too."""
    env = dict(os.environ)
    env.update(
        MARIADB_HOSTNAME=params.server.host,
        # splent_framework 1.24.0 builds the address with it; 3306 before.
        MARIADB_PORT=str(params.server.port),
        MARIADB_DATABASE=params.target_schema,
        # A test app the command might build points at uvlhub3 as well,
        # never at the shared test database.
        MARIADB_TEST_DATABASE=params.target_schema,
        MARIADB_USER=params.server.user,
        MARIADB_PASSWORD=params.server.password,
        RUN_DB_SEED="false",
    )
    env.update(extra)
    return env


def run_child(stage: str, command, env) -> str:
    """Run a feature's command; its output, or Refused with its tail."""
    result = subprocess.run(
        list(command),
        env=env,
        cwd=env.get("WORKING_DIR") or None,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        tail = output.strip().splitlines()[-15:]
        raise Refused(
            stage, [f"{' '.join(command)} failed ({result.returncode})"] + tail
        )
    return output


def create_database(engine, params, contract) -> None:
    target = quote(params.target_schema)
    with engine.connect() as connection:
        connection.exec_driver_sql(f"DROP DATABASE IF EXISTS {target}")
        connection.exec_driver_sql(
            f"CREATE DATABASE {target} CHARACTER SET {contract.charset} "
            f"COLLATE {contract.collation}"
        )
        connection.commit()


def write_contract_collation(connection, inputs, contract) -> None:
    """The contract's collations into the inputs schema, for V-14's SQL. The
    copy follows contract.toml, the versioned original."""
    table = inputs["contract_collation"]
    with connection.begin():
        connection.execute(table.delete())
        connection.execute(
            table.insert(),
            [
                {"table_name": t, "column_name": c, "expected": collation}
                for t, c, collation in contract.collations()
            ],
        )


def check_schema(connection, params, contract) -> list[str]:
    """V-12, V-14 and the contract, on uvlhub3. [] when it all holds."""
    found = []
    applied = dict(
        connection.execute(
            sa.text(
                f"SELECT feature, last_migration FROM "
                f"{qualified(params.target_schema, 'splent_migrations')}"
            )
        ).all()
    )
    found += [
        f"V-12 {line}" for line in contract_module.head_differences(contract, applied)
    ]
    for table, column, collation, expected in connection.execute(
        sa.text(V14.format(inputs=quote(params.inputs_schema))),
        {"target": params.target_schema},
    ).all():
        found.append(
            f"V-14 {table}.{column}: {collation}, the contract says {expected}"
        )
    default = connection.execute(
        sa.text(
            "SELECT default_character_set_name, default_collation_name "
            "FROM information_schema.schemata WHERE schema_name = :s"
        ),
        {"s": params.target_schema},
    ).one()
    if tuple(default) != (contract.charset, contract.collation):
        found.append(f"{params.target_schema} defaults to {default[0]} {default[1]}")
    columns = contract_module.schema_columns(connection, params.target_schema)
    found += contract_module.differences(contract, columns)
    return found


def build_schema(ctx) -> None:
    params, contract = ctx.params, ctx.contract
    create_database(ctx.engine, params, contract)
    output = run_child("E3", params.upgrade_command, child_env(params))
    ctx.facts["upgrade_output"] = output.strip().splitlines()[-40:]
    with ctx.engine.connect() as connection:
        write_contract_collation(connection, ctx.inputs, contract)
        found = check_schema(connection, params, contract)
    if found:
        raise Refused("E3", found)
    ctx.facts["dm15_pending"] = contract.dm15_pending()
