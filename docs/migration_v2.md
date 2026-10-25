# Migrating uvlhub.io 2.12 into uvlhub 3.0

`uvlhub_splent.migration_v2` is the migrator of the cutover (CO-3): strategy
C of the migration plan, `_reference/analisis_uvlhub/06-plan-migracion-uvlhubio.md`
in the workspace. A dump of v2.12 is restored in a schema of its own, an
empty `uvlhub3` is brought to the head of the pinned features by their own
`splent db:upgrade`, and the migrator fills it with SQLAlchemy Core, never
the ORM. Every run starts over: it drops and creates `uvlhub3`,
`uvlhub_v2_src`, `uvlhub_v2_ref` and the outputs in `uvlhub_migration`, and
keeps the inputs of `uvlhub_migration_inputs`.

Every stage of the plan runs. E5 (content) is still a **first pass**: it
loads what the pinned features can hold and lists what it leaves for the
final pass, and the report says `"ready_for_cutover": false` for as long as
that is so (and while DM-1's rotation is not checked, any conflict is open
or any blocking check fails).

## Stages

| Stage | What it does here | State |
|---|---|---|
| E0 preflight | The safeguards of §3.4 (below), the parameters, the versions of the installed features against the contract | done |
| E1 source | The dump restored as root with `sql_log_bin=0` and `event_scheduler=OFF`; its sha256, its Alembic head (P-19) and the AUTO_INCREMENT counters written down; triggers, routines, events and views listed and dropped (P-28) | done |
| E2 profiling | P-00 against `uvlhub_v2_ref`, P-01 to P-28 with the rule of each, the decisions held to their rows | done |
| E3 schema | `CREATE DATABASE uvlhub3` with the contract's collation, `splent db:upgrade` in a process of its own, then V-12, V-14 and the whole contract | done |
| E4 identity | `user`, `user_profile`, `external_identity` (the `orcid` and `github` tables folded in) and `api_token` | done |
| E5 content | Datasets, metadata, authors, feature models, files, metrics, votes and transfers; the tombstones of DM-4 and the names of DM-10 | first pass |
| E6 legacy | `usage_daily` and `usage_note` (DM-5), `doi_mapping` and `legacy_url` (CO-2, C-20), `held_notice` (D13 b, §5.5) | done |
| E7 post-load | Counters with their margin, every foreign key, the tables that must stay empty, V-01 to V-16 | done |
| E8 files | hubfile's `storage-migrate --source <store>/.legacy_mirror --link`, then `file_manifest`, DM-10's names with `file_alias`, unique-paths and V-08 | done |
| E9 derived | FactLabel and metrics, formats, reindex, by the features' commands | done |
| E10 report | The report (JSON), the run's row in `uvlhub_migration.run` | done |

E0 refuses to go on when `uvlhub3` shows signs of use (a run that completed,
which stands for the plan's `migration.completed`, as the migrator writes
no audit event; a row created after T0; a mail sent; an account that signed in; a
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
export SECRET_KEY=<3.0's new key>  MIGRATION_V2_SECRET_KEY_SHA256=<sha256 of v2.12's>
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
  storage-migrate` and E9's commands) build the app, so in the production
  image they need what its ProductionConfig needs, `SECRET_KEY` first
  (DM-1, below). They get the server, its port (`MARIADB_PORT`), the
  migrator account and `uvlhub3`.
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

## E6: what no feature has a place for yet

The pinned features have no table for these, so E6 writes them to
`uvlhub_migration`, for the features that will import them:

- **`usage_daily`** (DM-5, §7.2): v2.12's four record tables by dataset or
  file, kind and day, with `visitors` (an account, else the browser's
  cookie, else each record) and `records`. A record of its owner, of a
  dataset that is not published, of a dataset not loaded, without its
  target or without its date is not counted, and `counts` says how many of
  each; the raw records do not pass. E6 aggregates them in
  `uvlhub_migration.usage_daily` and loads them into statistics 0.5.0's
  `usage_daily` with `source = 'legacy_v2'`, which its dashboard shows next
  to 3.0's own (`live`), and the public note that says why the figures went
  down into `usage_note` (`legacy_v2`, `until` the day before T0).
  `usage_event` and `usage_salt`, 3.0's own visits, stay empty. The
  report's `dm5` gives v2.12's counters, the aggregates and the note.
- **`doi_mapping` and `legacy_url`** (CO-2, C-20): dataset 0.9.0 still
  redirects `/doi/<old>` by its own `doi_mapping` (302), so E6 loads v2.12's
  there, each chain followed to its end, a DOI a dataset of 3.0 has, in one
  hop. A cycle (`doi_mapping_cycle`), or a chain that ends at a DOI no
  dataset has or runs into a cycle (`doi_mapping_dangling`), is a conflict
  and loads nowhere; a second mapping of one DOI, which v2.12's lookup never
  reached, is dropped as `shadowed`. `legacy_url` keeps every path that
  answers somewhere else now, decoded as a route reads it, with a 308: those
  mappings, and `/hubfiles/raw/<id>/<old name>` of every file DM-10
  renamed. It is what the future legacy_urls feature imports.
- **`held_notice`** (D13 b, §5.5): the mails of the move that wait for the
  end of RB-2, since a rollback would make them false: one to each party of
  every offer E5 cancelled, and one to every account with keys carried
  over, saying until when each works or why it was carried over revoked.
  English and Spanish (MIG-09), no link with a token. mail 1.5.0's outbox
  knows `queued`, `sending`, `sent` and `failed`, and its sweep sends every
  queued row, so nothing can wait there: mail needs a held state (or a
  `not_before`) and a command that releases a tag of them, and then E6
  queues them there.

## E9: derived data

Nothing derived is migrated (§7). Once the files are in the store, E9 runs
the features' own commands, each in a process of its own as E3 and E8 do,
with the store as `HUBFILE_STORAGE_ROOT`:

- `factlabel`: `splent feature:factlabel generate`, every FactLabel, then
  `metrics-backfill --force`, each file's metrics made from it in the place
  of v2.12's that E5 copied (a file whose FactLabel fails keeps those);
- `formats`: `splent feature:uvl generate`, Glencoe, DIMACS and SPLOT;
- `reindex`: `splent feature:explore reset`, the index made again.

E9 never stops the run: a command that fails is a check that does not
block (`E9-<name>`) and an alert in the report, and is run again once 3.0
is up (explore answers with its SQL fallback meanwhile). `--derived`
chooses what runs, so the cutover can leave FactLabel and formats for
after the opening, as the plan's day does (§9.3, 4:05). The rehearsal of
the tests runs factlabel's and uvl's commands, and the reindex with
`ELASTICSEARCH_ENABLED=false`, since the development's node is shared.
`hubfile_factlabel` has the role `derived` in the contract: E7 checks it is
empty, before E9; `hubfile_metrics` is loaded and then made again, so a
second run gives other `extracted_at` there.

## DM-1: SECRET_KEY is rotated

3.0 starts with a key of its own. The migrator reads none: P-26 reads
v2.12's reset links without one (their payload is not encrypted), and it
writes nothing signed. What the operator sets, in the container that runs
it and then in the web and the worker of 3.0:

- `SECRET_KEY`: a new one, at least 32 characters
  (`python -c "import secrets; print(secrets.token_urlsafe(64))"`), never
  v2.12's nor the framework's development key, which ProductionConfig
  refuses. Everything 3.0 signs comes from it: sessions, CSRF, its
  remember-me cookie. `CONFIRM_EMAIL_SALT` stops mattering.
- `MIGRATION_V2_SECRET_KEY_SHA256`: the sha256 of v2.12's key, taken from
  its `.env` (`printf %s "$OLD_SECRET_KEY" | sha256sum | cut -d' ' -f1`),
  so v2.12's key is never in the cutover's environment. E0 refuses when
  `SECRET_KEY` is that key, or when the hash is set and `SECRET_KEY` is
  not; without the hash the report says `"dm1": {"rotation_checked":
  false}`, and the run is not ready for the cutover.

V-16 (E7) checks that nothing carried over is signed: no column loaded
comes from one v2.12 signed with its key (`reset_token.token`; its
confirmation links and sessions were never stored), auth's `auth_token`,
confirmemail's and reset's tables are empty, and no text value of a table
the migrator loads is something itsdangerous signed, with any key
(`rules.is_signed`). Links of v2.12 mailed before the cutover open nothing:
they lead to the page of an expired link (ID-15).

Deriving a key per purpose from `SECRET_KEY` (PL-9) is the framework's:
1.25.0 signs everything with `SECRET_KEY` itself.

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
chain (`migration_v2/v2_12_schema.py`, which `test_v2_schema.py` checks
against the chain when `_reference/uvlhub_monolith` is in the workspace)
plus a row per anomaly the migrator has a rule for (`synthetic.py` says who
is who), dumps it as B1 is dumped, puts a Zenodo record in
`zenodo_snapshot`, and runs the stages on it.

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
  1.26.0, identities 0.5.0). `datasets.pid` (dataset 0.9.0) is at the
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
  audit 0.1.0 brings `audit_event`, which the migrator leaves empty and
  does not write the event to yet (GV-4). E0 also reads logins, sent mails
  and rows in the tables the migration leaves empty.
- **Every account gets `session_version = 2`**: auth honours v2.12's bare
  remember-me id only at version 1, so no cookie of v2.12 opens a session,
  with the old key or the new one.
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
  `concept_pid` or `lineage_root_id`).
- **Authors** (DL-5, dataset 0.9.0): each credit at its place, from 0 in
  the order of the ids of its metadata, as dataset0007 numbers them; its
  given and family names only from a name written "Family, Given" with
  exactly one comma (dataset's `names_of`), NULL for any other, so a name
  is never split on a guess; and its account, the one whose ORCID identity
  (an `orcid` row of `external_identity`, E4) has the author's iD, NULL
  without one. The authors of an anonymous dataset are kept the same way
  in `private_authors`. The declaration of the co-authors (D18,
  `authors_declared_at` and `_by_id`) is NULL for everything carried over,
  and no mail asks for it; `dataset_orcid_check`, orcid.org's answers, is
  left empty, for 3.0 to fill as iDs are credited.
- **Ghost drafts** (DM-3): a draft with no file, no DOI and no deposition,
  older than 30 days (`--ghost-draft-days`), is dropped as `ghost_draft`.
- **Self-votes** (DM-8) are dropped as `self_vote`, after a vote moves to
  the root of its lineage, so a vote on a version of one's own goes too.
- **DOIs without a dataset** (DM-4, C-03): v2.12 deleted the dataset and
  left its metadata, DOI included. Each becomes a withdrawn dataset, with
  its metadata and authors, so dataset's landing answers its DOI with the
  tombstone, 410 with the citation (`landing_response`, DL-2), where it
  answered 404; `test_a_tombstones_doi_answers_410_with_its_citation` asks
  the product's app. The reason is `other`, the note says it was deleted
  before uvlhub 3.0, `withdrawn_at` is NULL (v2.12 kept no date) and the
  dates come from Zenodo's record in `zenodo_snapshot` (validated by its
  sha256 and its DOI). Without one it is dated T0 and raises
  `tombstone_undated`, since its citation would give T0's year. The owner
  went with the dataset: the first account of `MIGRATION_ADMIN_EMAILS`
  holds it (DM-13), and without one loaded no tombstone is made
  (`tombstone_without_owner`). Its id is new, above the source's counter;
  `uvlhub_migration.tombstone` and `id_map` say which.
- **Two files on one path** (DM-10, C-11): the first by id keeps its name,
  the one v2.12 served at `/doi/<doi>/files/raw/<path>`, and every other
  gets `~<id>` before its extension. E8 writes the names after
  `storage-migrate`, which finds a file by its v2.12 name, and
  `uvlhub_migration.file_alias` keeps the old one: `/hubfiles/raw/<id>/<old
  name>` answers 400 ("Filename mismatch") in hubfile 0.8.0 until hubfile
  reads it (an alias table, and a 308 to the new name).
- **C-30** also covers a DOI that is not the one Zenodo mints for its
  deposition (`10.5281/zenodo.<deposition_id>`), which P-25b finds.
