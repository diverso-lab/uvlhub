# Migrating uvlhub.io 2.12 into uvlhub 3.0

`uvlhub_splent.migration_v2` is the migrator of the cutover (CO-3): strategy
C of the migration plan, `_reference/analisis_uvlhub/06-plan-migracion-uvlhubio.md`
in the workspace. A dump of v2.12 is restored in a schema of its own, an
empty `uvlhub3` is brought to the head of the pinned features by their own
`splent db:upgrade`, and the migrator fills it with SQLAlchemy Core, never
the ORM. Every run starts over: it drops and creates `uvlhub3`,
`uvlhub_v2_src`, `uvlhub_v2_ref` and the outputs in `uvlhub_migration`, and
keeps the inputs of `uvlhub_migration_inputs`.

This is a **first pass**. E5 (content) loads what the pinned features can
hold and lists what it leaves for the final pass; E6 and E9 do not exist
yet. Its report says `"ready_for_cutover": false` for as long as that is so.

## Stages

| Stage | What it does here | State |
|---|---|---|
| E0 preflight | The safeguards of §3.4 (below), the parameters, the versions of the installed features against the contract | done |
| E1 source | The dump restored as root with `sql_log_bin=0` and `event_scheduler=OFF`; its sha256, its Alembic head (P-19) and the AUTO_INCREMENT counters written down; triggers, routines, events and views listed and dropped (P-28) | done |
| E2 profiling | P-00 against `uvlhub_v2_ref`, P-01 to P-28 with the rule of each, the decisions held to their rows | done |
| E3 schema | `CREATE DATABASE uvlhub3` with the contract's collation, `splent db:upgrade` in a process of its own, then V-12, V-14 and the whole contract | done |
| E4 identity | `user`, `user_profile`, `external_identity` (the `orcid` and `github` tables folded in) and `api_token` | done |
| E5 content | Datasets, metadata, authors, feature models, files, metrics, votes and transfers | first pass |
| E6 legacy | Usage aggregates, `legacy_url`, held notices | not yet |
| E7 post-load | Counters with their margin, every foreign key, the tables that must stay empty, V-01 to V-15 | done |
| E8 files | hubfile's `storage-migrate --source <store>/.legacy_mirror --link`, then `file_manifest` and V-08 | done |
| E9 derived | Reindex, FactLabel, formats | not yet |
| E10 report | The report (JSON), the run's row in `uvlhub_migration.run` | done |

E0 refuses to go on when `uvlhub3` shows signs of use (a run that completed,
which stands for the plan's `migration.completed` until 3.0 has an audit
table; a row created after T0; a mail sent; an account that signed in; a
row in a table the migration leaves empty), unless `--force` comes with a
B2 taken in the last 15 minutes; when anyone but the migrator and root is
connected; when `RUN_DB_SEED` is not `false`; and when
`GET_LOCK('uvlhub_migration', 0)` is held.

## Running it

The cutover runs it in an ephemeral container of the 3.0 image, with the
web and the worker of 3.0 not created yet. Root restores the dump; every
other step uses a `migrator` account made for the cutover:

```bash
python -m uvlhub_splent.migration_v2 grants        # the SQL for root to create it (five schemas)
```

```bash
export MIGRATION_DB_PASSWORD=...  MIGRATION_DB_ROOT_PASSWORD=...  RUN_DB_SEED=false
python -m uvlhub_splent.migration_v2 preflight --db-host <db> --t0 2026-11-20T00:00:00 --expected-head e5f6a7b8c9d0
python -m uvlhub_splent.migration_v2 run --db-host <db> \
    --t0 2026-11-20T00:00:00 --expected-head e5f6a7b8c9d0 \
    --admin-email someone@uvlhub.io \
    --dump /b1/uvlhub_v2_12.sql --store-root <HUBFILE_STORAGE_ROOT> \
    --report /b1/report.json --operator "Name"
```

- Passwords come from the environment only, never from the command line.
- `--expected-head` is `f7a8b9c0d1e2` once the hotfix D1 is deployed.
- `--store-root` is hubfile's store, and `<store>/.legacy_mirror` the
  `rsync -a --delete` (never `--inplace`) of v2.12's `uploads/`, on the same
  mount, so each file is hard linked to its key (§6.2, R-27).
- The processes it starts (`splent db:upgrade`, `splent feature:hubfile
  storage-migrate`) build the app, so in the production image they need
  what its ProductionConfig needs, `SECRET_KEY` first. They get the
  server, its port (`MARIADB_PORT`), the migrator account and `uvlhub3`.
- A rehearsal adds `--allow-open-conflicts`: it goes on past the conflicts
  and lists them. The cutover stops at the first stage that leaves one.
- Exit code 3 is a refusal; the report says which stage and why.

Inside the CLI, `splent product:migrate-v2 <command>` gives the same
commands (`src/uvlhub_splent/commands.py`). The CLI builds the product's
app for it, so before anything runs the command closes the connections the
app's engines keep, and refuses while one is still in use: E0 would count
it as somebody else's. The cutover keeps `python -m`, which builds no app.

The parameters of the plan have their environment variables:
`MIGRATION_T0`, `MIGRATION_EXPECTED_HEAD`, `MIGRATION_ADMIN_EMAILS`,
`MIGRATION_ID_MARGIN`, `MIGRATION_DB_HOST`, `MIGRATION_STORE_ROOT`,
`MIGRATION_OPERATOR`. `--help` lists the D12 lives, DM-3's age of a ghost
draft and `--stages`.

## E2: profiling and decisions

E2 makes `uvlhub_v2_ref` from `migration_v2/v2_12_schema.py`, the DDL the
monolith's Alembic chain gives at the release (`tests/migration_v2/v2_schema.py`
makes it, and `test_v2_schema.py` runs the chain again to compare; the
hotfix's revision changes no table), and compares it with the restored
dump both ways (P-00): tables with their engine and collation, columns with
their type, nullability, default and collation, and indexes and foreign
keys by what they hold, since their names are MariaDB's. Each difference is
a `schema_drift` conflict (C-26): no rule of the migrator reads a schema the
chain does not make.

Then P-01 to P-28 of §9.2 run on the source, with P-21, P-23 and P-26 in
Python and P-27 generated from the contract (`profile.PROBES`). Each names
the rule of §8 that handles what it finds and the stage that applies it;
`uvlhub_migration.profile` keeps what each found (a sample of the rows) and
the report its count. Two have no rule, and what they find stops E2,
rehearsal or not: P-17b, a publication type the target's ENUM does not
have, and P-27b, a NULL the target refuses where the contract has no
`on_null` (a production schema can let in what the chain does not).

**Deciding a conflict.** Every conflict in `uvlhub_migration.conflict`
names the source rows it is about (`source_rows`, a JSON list of
`table:id`) and their sha256 (`fingerprint`). Once it is reviewed, whoever
decides copies them into `uvlhub_migration_inputs.decision`:

```sql
INSERT INTO uvlhub_migration_inputs.decision
  (kind, ref, source_rows, fingerprint, resolution, note, author, decided_at)
SELECT kind, ref, source_rows, fingerprint, 'accept', 'Why, in a line', 'Name', UTC_TIMESTAMP()
FROM uvlhub_migration.conflict WHERE id = <id>;
```

The only resolution is `accept`: the migrator's own handling of the
conflict stands (`ledger.CONFLICTS` says what it is for each kind), and the
conflict is closed. E2 reads the rows of every decision again, and stops,
rehearsal or not, when they changed or went, when the kind is one no stage
raises, when the resolution is not `accept`, or when two decisions name one
conflict. A decision on a drift is held to the drift P-00 finds that run.
The ones that hold close their conflict (`status = 'decided'`, with the
decision's id) when the stage that finds it raises it again; one whose
conflict comes back on other rows stops that stage. The report lists the
decisions that hold and the ones no conflict used. Decisions count only in
a run that has E2.

## The data contract

`src/uvlhub_splent/migration_v2/contract.toml` (MIG-03) holds the heads of
every feature with migrations (V-12) and, for every table the migrator
writes, its columns, types, nullability and collations, each column with
where it comes from (`source`, `rule`, and `on_null` where v2.12 admits a
NULL the target refuses, C-27). The tables it does not fill are listed
too, so a feature that adds one is an unknown that stops E3.

`python -m uvlhub_splent.migration_v2 contract` prints a summary, with what
DM-15 asks for that the pinned features do not give yet, and
`contract --check <host>` compares a live `uvlhub3`.

When a pin changes a feature with migrations, `tests/migration_v2/test_contract.py`
fails until the contract says the new version, its head and whatever its
tables now are, and the migrator writes them (same commit).

## Tests

`tests/migration_v2` builds a dirty v2.12 from the monolith's own Alembic
chain (`v2_12_schema.sql`, which `test_v2_schema.py` checks against the
chain when `_reference/uvlhub_monolith` is in the workspace) plus a row per
anomaly the migrator has a rule for (`synthetic.py` says who is who), dumps
it as B1 is dumped, and runs the stages on it.

They never use the development database or the shared test one. From the
CLI container,

```bash
flock /tmp/splent-test.lock bash uvlhub_splent/tests/migration_v2/run_with_throwaway_db.sh
```

starts a MariaDB 11.4 of their own on the web container's network, names it
in `MIGRATION_V2_TEST_DB_HOST` and `MIGRATION_V2_TEST_DB_ROOT_PASSWORD`,
runs `splent product:test --own-tests`, which hands those to the tests
(`[tool.splent.test] env` in pyproject.toml), and removes the server
however the run ends. The lock is the shared test database's, which the
product's other tests use. With pytest arguments it runs the migrator's
tests alone, without the lock:

```bash
bash uvlhub_splent/tests/migration_v2/run_with_throwaway_db.sh -q -k preflight
```

A plain `splent product:test --own-tests` runs the ones that need no
database and skips the rest, saying how to run them.

## Where this pass departs from the plan

- **DM-15, the identifiers:** `user.email`, `email_canonical`,
  `external_identity.provider` and `provider_id` are `utf8mb4_bin` (auth
  1.26.0, identities 0.5.0). `datasets.pid` (dataset 0.8.0) is at the
  database's collation, where DM-15 asks `utf8mb4_bin`, and `concept_pid`
  and `dataset_tag.name` have no column yet; the report lists them. With
  the address compared exactly, C-13's clashes are the ones auth's
  canonical form finds (two addresses v2.12 told apart, one once NFKC,
  casefold and a stripped space are applied), and a provider is written
  exactly `orcid` or `github` ("GitHub " is github; any other is a
  conflict).
- **Scopes.** dataset registers uvlhub's `read_dataset` and
  `write_dataset`, so a key keeps them (`[scopes]` in the contract); AP-4's
  `datasets:*` vocabulary does not exist.
- **migration.completed** is the completed row of `uvlhub_migration.run`:
  3.0 has no audit table (GV-4). E0 also reads logins, sent mails and rows
  in the tables the migration leaves empty.
- **Every account gets `session_version = 2`**: auth honours v2.12's bare
  remember-me id only at version 1, so no cookie of v2.12 opens a session,
  whatever DM-1 decides.
- **A probable takeover (C-28) must reset**, with auth's
  `must_reset_password`: its hash is copied as it is and opens nothing,
  since signing in with it only mails the owner a reset link, so whoever
  followed the v2.12 link is shut out. `has_usable_password` follows
  §5.2's rule, as for every account.
- **The head is checked in E1**, where the dump is, not in E0.
- **Derived formats** in the mirror are linked by `storage-migrate` with
  their file; 3.0 makes them again (UV-4) all the same.
- **Recovery from Zenodo** (§6.2 step 5) is not done: a file of a published
  dataset that is missing or in mismatch is a conflict.
- **E5 first pass**: `content.DEFERRED` lists what it leaves (descriptions
  copied as they are, lineages loaded as they are with their faults listed,
  `published_at` = `created_at`, no `status = 'legacy'` on metrics, no
  reason on cancelled offers, no column yet for `public_id`,
  `lineage_root_id`, author position or user).
- **Ghost drafts** follow DM-3's recommendation (30 days, `--ghost-draft-days`).
