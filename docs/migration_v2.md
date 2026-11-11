# Migrating uvlhub.io 2.12 into uvlhub 3.0

`uvlhub_splent.migration_v2` is the migrator of the cutover (CO-3): strategy
C of the migration plan, `_reference/analisis_uvlhub/06-plan-migracion-uvlhubio.md`
in the workspace. A dump of v2.12 is restored in a schema of its own, an
empty `uvlhub3` is brought to the head of the pinned features by their own
`splent db:upgrade`, and the migrator fills it with SQLAlchemy Core, never
the ORM. Every run starts over: it drops and creates `uvlhub3`,
`uvlhub_v2_src`, `uvlhub_v2_ref` and the outputs in `uvlhub_migration`, and
keeps the inputs of `uvlhub_migration_inputs`.

Every stage of the plan runs, E5 (content) included as its final pass:
the report says `"e5_first_pass": {"first_pass": false, "deferred": []}`,
and `"ready_for_cutover": true` once nothing else is pending: no stage
stopped, no conflict open, no blocking check failed, and DM-1's rotation
checked. E9's checks do not count, since what they make is made again once
3.0 is up.

## Stages

| Stage | What it does here | State |
|---|---|---|
| E0 preflight | The safeguards of §3.4 (below), the parameters, the versions of the installed features against the contract | done |
| E1 source | The dump restored as root with `sql_log_bin=0` and `event_scheduler=OFF`; its sha256, its Alembic head (P-19) and the AUTO_INCREMENT counters written down; triggers, routines, events and views listed and dropped (P-28) | done |
| E2 profiling | P-00 against `uvlhub_v2_ref` (a rule reads a server's default collation), P-01 to P-28 with the rule of each, the decisions held to their rows | done |
| E3 schema | `CREATE DATABASE uvlhub3` with the contract's collation, `splent db:upgrade` in a process of its own, then V-12, V-14 and the whole contract | done |
| E4 identity | `user`, `user_profile`, `external_identity` (the `orcid` and `github` tables folded in) and `api_token` | done |
| E5 content | Datasets with their public id, lineage root and concept (CO-5, the concept DOIs v2.12 left empty from Zenodo's records), Zenodo's dates and the DOIs it minted that v2.12 lost (§4.3), metadata with their descriptions cleaned again and quarantined (C-01, C-29), authors, feature models, files, metrics marked legacy (§7.3), votes and transfers; the tombstones of DM-4, the names of DM-10, the curation of RU-06 and the lineages their concept DOIs repair (C-05) | done |
| E6 legacy | `usage_daily` and `usage_note` (DM-5), `doi_mapping` and legacy_urls' `legacy_url` by its import (CO-2, C-20), the held notices in mail's outbox (D13 b, §5.5) | done |
| E7 post-load | Counters with their margin, every foreign key, the tables that must stay empty, V-01 to V-16, every one blocking | done |
| E8 files | hubfile's `storage-migrate --source <store>/.legacy_mirror --link`, the published files recovered from Zenodo (§6.2 step 5), then `file_manifest`, DM-10's names with hubfile's `hubfile_alias`, unique-paths and V-08 | done |
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
export MIGRATION_PUBLIC_ID_KEY=<a key kept for every rehearsal and the cutover>  MAIL_FROM=<3.0's sender>
python -m uvlhub_splent.migration_v2 preflight --db-host <db> --t0 2026-11-20T00:00:00 --expected-head e5f6a7b8c9d0
python -m uvlhub_splent.migration_v2 run --db-host <db> \
    --t0 2026-11-20T00:00:00 --expected-head e5f6a7b8c9d0 \
    --admin-email someone@uvlhub.io \
    --dump /b1/uvlhub_v2_12.sql --store-root <HUBFILE_STORAGE_ROOT> \
    --report /b1/report.json --operator "Name"
```

- Passwords come from the environment only, never from the command line,
  and so does `MIGRATION_PUBLIC_ID_KEY`, the key of the datasets' public
  ids (§4.2; `SECRET_KEY` when it is not set, E0 refuses without either).
  It is a secret of the cutover: the same key for every rehearsal and the
  cutover gives every dataset the same public id each time, and whoever
  has it can work a dataset's public id out of its sequential id. Keep it
  with B1, never in the repository.
- `MAIL_FROM` is 3.0's sender, as its `.env.prod` says: the notices E6
  holds in mail's outbox go from it (E0 refuses without an address there).
  Once RB-2 is over, `splent feature:mail release --tag rb2` in the web
  container of 3.0 sends them; `--hold-tag` names another batch.
- `--expected-head` is `f7a8b9c0d1e2` once the hotfix D1 is deployed, and
  then `--b0` (or `MIGRATION_B0`) names B0, the dump of `ds_meta_data` its
  upgrade notes take before its revision cleans the descriptions in place
  (C-29). E1 reads the originals from it and drops what it restored; a run
  without it says, as an alert, that what the hotfix took out is lost.
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
- Exit code 3 is a refusal; the report says which stage and why, and
  lists every conflict with its kind, its rows and what the stage said of
  it (`conflict_detail`), so it can be read once the server is gone. Of the
  conflicts about accounts it gives the rows alone, never an address or an
  iD.

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

## Zenodo, before the run

Two commands fetch what the run reads from Zenodo, from the host of
operation only (never from staging, R-07), once the source is restored
(a run with `--stages E0,E1` restores it). They ask Zenodo one request at
a time, wait when it answers 429 or 5xx (its `Retry-After` when it gives
one), only GET, with no token, and keep what they fetch in
`uvlhub_migration_inputs`, which every run reads and none drops.

```bash
python -m uvlhub_splent.migration_v2 zenodo-snapshot --db-host <db>
python -m uvlhub_splent.migration_v2 zenodo-files --db-host <db> \
    --store-root <HUBFILE_STORAGE_ROOT> --cache <a folder of the operator's>
```

- `zenodo-snapshot` (MIG-06, §4.3) keeps the public record of every
  deposition in `zenodo_snapshot`. E5 takes from it the day each dataset
  was published (`published_at`), the concept DOIs v2.12 left empty, the
  DOIs Zenodo minted that v2.12 never saved (A15-04), and the dates of the
  tombstones, and orders the curated lineages by it. A record is taken
  only when its DOI is the dataset's, or, for a deposition without a DOI,
  when its id is the deposition's and its title the metadata's. A
  published dataset whose DOI no record validates is a conflict
  (`doi_record_missing`), and so is a deposition without a DOI whose
  record is another's (`deposition_record_mismatch`); a deposition with no
  record at all (the public API's 404: Zenodo never published it) is
  `failed`.
- `zenodo-files` (§6.2 step 5) finds every file of a published dataset that
  the mirror lacks, or holds with other bytes than its row says (the same
  check `storage-migrate` makes), and fetches it from the record its DOI
  cites, and nothing else. It looks for a loose file named as the hubfile
  (or by its relative path), then for the entry `uvl/<relative_path>` of
  `dataset_<id>.zip`, or of the record's only archive when it has no such
  one, where the entry may also be the relative path itself or the one
  entry under a folder that ends so. A download is kept only when it is
  the md5 Zenodo publishes, in the cache by deposition and md5, so a second
  run downloads nothing it has. Each file goes to `zenodo_files` with its
  bytes, size, md5 and sha256, or with why it could not be had
  (`not_in_record`, `ambiguous_name`, `md5_mismatch`, `not_in_zip`,
  `record_invalid`, `too_large`, `fetch_failed`). A table of an older
  migrator is refused; drop it and run the command again.

## E2: profiling and decisions

E2 makes `uvlhub_v2_ref` from `migration_v2/v2_12_schema.py`, the DDL the
monolith's Alembic chain gives at the release (`tests/migration_v2/v2_schema.py`
makes it, and `test_v2_schema.py` runs the chain again to compare; the
hotfix's revision changes no table), and compares it with the restored
dump both ways (P-00): tables with their engine and collation, columns with
their type, nullability, default and collation, and indexes and foreign
keys by what they hold, since their names are MariaDB's. Each difference is
a `schema_drift` conflict (C-26), unless a rule of the migrator reads it.
One does (`profile.drift_rule`). A table or a column that differs in its
collation alone, between `utf8mb4_general_ci` and `utf8mb4_uca1400_ai_ci`,
the defaults of uvlhub.io's server and of MariaDB 11.4, holds the same
bytes, which the migrator reads in BINARY and loads into columns with the
contract's collation, so nothing it loads depends on it. The report lists
those drifts with their rule (`schema_drift_ruled`); any other difference
stays a conflict.

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

## E5: the curation (RU-06)

`src/uvlhub_splent/migration_v2/curation.toml` says what R1 decided on the
datasets uvlhub.io published more than once, and E5 applies it as it loads,
never by hand on the database. `--curation` (or `MIGRATION_CURATION`)
names another file, and `none` applies none.

- `[[lineage]]` makes published datasets the versions of one lineage, in
  the order Zenodo published them (the time of their record in
  `zenodo_snapshot`, else their `created_at`, then their id). The first is
  the root, each stands on the one before (`dataset_origin_id`) and they
  are numbered from 1 (`dataset_version`). Each keeps its own DOI and its
  own concept DOI, so every DOI lands on its record, `/doi/<concept>/`
  answers with the versions that carry that concept, and explore shows the
  lineage once. Votes follow to the root, as for any lineage.
- `[[draft]]` lists drafts that duplicate other datasets. A draft is its
  owner's, so nothing is hidden or dropped, and the report lists them for
  their owners.
- `[[review]]` lists datasets that look alike and stay as they are, for
  someone to decide.

A member of a lineage is named by its id and its DOI. The run stops at E5,
rehearsal or not, when a rule does not hold for the source (a dataset that
does not load, another DOI, a member that is not published, a version of a
member the lineage does not name, a member that stands on a dataset outside
it, or members of more than one account). `uvlhub_migration.curated` keeps
the place each dataset had in v2.12 and the one it was given, and the
report the lineages before and after (`curation`).

Then the concept DOIs repair the rest (C-05): the datasets of one concept
DOI, the one v2.12 kept or the one their record gives, are one lineage in
the order of their `created_at`, each on the one before, with their
`dataset_version` as it is. Where the versions do not rise with the dates,
nothing changes and the faults stay conflicts (`lineage_*`), for a
`[[lineage]]` in the curation: V-09 blocks, so a branch is never accepted
as it is. The lineages the curation made stay as it made them.
`curated` has a row for each dataset repaired (`C-05 <concept>`), and the
report the chains (`lineages_by_concept`).

## E6: the use, the old addresses and the notices of the move

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
- **`doi_mapping` and `legacy_url`** (CO-2, C-20): dataset 0.10.0 still
  redirects `/doi/<old>` by its own `doi_mapping` (302), so E6 loads v2.12's
  there, each chain followed to its end, a DOI a dataset of 3.0 has, in one
  hop. A cycle (`doi_mapping_cycle`), or a chain that ends at a DOI no
  dataset has or runs into a cycle (`doi_mapping_dangling`), is a conflict
  and loads nowhere; a second mapping of one DOI, which v2.12's lookup never
  reached, is dropped as `shadowed`. The same mappings go to legacy_urls
  0.1.0, `/doi/<old>/` with a 308 to `/doi/<new>/` and the mapping as its
  ref, through its own import (`splent feature:legacy_urls import`, a JSON
  file the migrator writes and removes, in a process of its own as E8 runs
  `storage-migrate`), every row or none; their dates are set to T0
  afterwards. legacy_urls answers them only where the hub would answer 404,
  so dataset's own 302 comes first while it keeps its `doi_mapping`. The
  `/hubfiles/raw/<id>/<old name>` of a file DM-10 renamed is hubfile's
  alias (E8), not a row there: hubfile's own 308 answers it first.
- **The notices of the move** (D13 b, §5.5): the mails that wait for the
  end of RB-2, since a rollback would make them false: one to each party of
  every offer E5 cancelled, and one to every account with keys carried
  over, saying until when each works or why it was carried over revoked.
  English and Spanish (MIG-09), no link with a token. E6 writes them into
  mail 1.6.0's outbox with Core, `state = 'held'` under the tag
  `--hold-tag` (`rb2`), from `MAIL_FROM` (E0 refuses without it), dated T0,
  kept whole and retryable; nothing sends them, the sweep included, until
  `splent feature:mail release --tag rb2` once RB-2 is over (§9.3).
  `uvlhub_migration.held_notice` says what each outbox row is about (its
  kind, the offer or the account). A rollback drops uvlhub3 with them.

## E9: derived data

Nothing derived is migrated (§7). Once the files are in the store, E9 runs
the features' own commands, each in a process of its own as E3 and E8 do,
with the store as `HUBFILE_STORAGE_ROOT`:

- `factlabel`: `splent feature:factlabel generate`, every FactLabel, then
  `metrics-backfill --force`, each file's metrics made from it in the place
  of v2.12's that E5 copied (a file whose FactLabel fails keeps those,
  `extractor_version = 'legacy:<v2.12's>'`, the plan's `status = 'legacy'`
  in factlabel's terms: `metrics-status` counts them as stale and
  `metrics-backfill` extracts them again once their FactLabel is there);
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
confirmation links and sessions were never stored), auth's `auth_token`
(which confirmemail's links use since its 2.0) and reset's `reset_token`
are empty, and no text value of a table
the migrator loads is something itsdangerous signed, with any key
(`rules.is_signed`). Links of v2.12 mailed before the cutover open nothing:
they lead to the page of an expired link (ID-15).

Deriving a key per purpose from `SECRET_KEY` (PL-9) is the framework's:
from splent_framework 1.26.0, `SPLENT_DERIVED_KEYS = true` makes each
purpose (sessions, CSRF, one-time tokens, signed URLs) sign with a key of
its own derived from `SECRET_KEY` with HKDF-SHA256, and `SECRET_KEY` itself
signs nothing. uvlhub turns it on from its first start
(`SPLENT_DERIVED_KEYS = true` in the product's `[tool.splent.config]`):
there is nothing signed before the cutover to keep, since the key rotates
anyway. The migrator signs nothing either way.

## After the run: the product's own content

The migrator leaves `role`, `team_member`, `citation_reference`, `setting` and
`media_item` empty, and `splent db:seed` refuses production because it brings
the demo data. So once 3.0 is up, load uvlhub's own content by itself: in the
web container, as the app's user, `UvlhubTeamSeeder().run()` and
`UvlhubAppearanceSeeder().run()` from `uvlhub_splent.seeders` in an app context,
then `splent feature:citation references-load` and `splent feature:dataset dump`.

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
is who), dumps it as B1 is dumped, puts Zenodo's records in
`zenodo_snapshot` and a file in `zenodo_files`, and runs the stages on it.

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

## Where the migrator departs from the plan

- **DM-15, the identifiers:** `user.email`, `email_canonical`,
  `external_identity.provider` and `provider_id` are `utf8mb4_bin` (auth
  1.27.0, identities 0.5.0), and so is `datasets.concept_pid` (dataset
  0.10.0). `datasets.pid` is at the database's collation, where DM-15 asks
  `utf8mb4_bin`, and `dataset_tag.name` has no column yet; the report lists
  them. With
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
- **Recovery from Zenodo** (§6.2 step 5). For a published dataset the
  bytes Zenodo published are the ones its DOI cites, so they win. E8 takes
  each file of a published dataset that `storage-migrate` left missing or
  in mismatch from `zenodo_files` and writes the bytes to its key as a new
  file renamed into place, never through the hard link, so the mirror
  keeps its own; what uvl derived from the old bytes goes, and E9 makes it
  again. The row says `recovered` and takes their size, their checksum in
  the row's algorithm (md5 for a row before uvlhub 2.0) and their sha256.
  When the mirror's bytes are Zenodo's already, the row was the wrong
  part, and only the row changes. `uvlhub_migration.file_repair` keeps the
  row's old values and the mirror's size and sha256 (`restored`,
  `replaced` or `row_fixed`). A file Zenodo cannot give stays a
  `file_missing` or `file_mismatch` conflict, with its dataset, DOI, path
  and why, and stops the cutover. V-08 takes `ok` and `recovered`.
- **Descriptions** (C-01, C-29, D21): each is loaded as `html_legacy`,
  cleaned again by dataset's own sanitiser (`descriptions.clean_html`),
  from the text v2.12 has now, as §2.1 says, so what uvlhub.io shows stays;
  V-13 cleans each once more and finds nothing to change. The original of
  every one that changes goes to `uvlhub_migration.quarantine_description`
  with what was loaded: B0's after the hotfix D1, the source's before it.
  The report's `descriptions` gives the two classes of §8 (formatting, and
  active content, whose metadata ids a curator reads) and how many
  descriptions use each element (P-22), which says whether uvlhub should
  let images in (D21).
- **Publication DOI and tags** (C-16, C-23): `publication_doi` is the DOI
  bare, as dataset's `publication_doi_of` reads it (`https://doi.org/<doi>`
  and `doi:<doi>` too), an address trimmed, and anything else as it was;
  the tags stay a string, as decided, split on commas, each trimmed, the
  empty and repeated ones gone, joined by `,` as dataset writes them.
- **Public ids** (CO-5, D6, §4.2): every dataset, tombstones included,
  gets `public_id`, a ULID of its `created_at` whose 80 random bits are
  the first of HMAC-SHA256(`MIGRATION_PUBLIC_ID_KEY`, `"dataset:<id>"`),
  falling back to `SECRET_KEY` (E0 refuses without either): every run with
  the same key gives each dataset the same id, which nobody can work out
  from its sequential one. Keep the key for the rehearsals and the
  cutover. `lineage_root_id` is the first version of its lineage as it
  loads (its own id for an original or a tombstone), and `concept_pid` the
  metadata's concept DOI, as
  dataset0009 fills them. Where v2.12 kept none, the concept DOI of the
  dataset's record in `zenodo_snapshot` fills both `concept_pid` and the
  metadata's `dataset_concept_doi`, which `/doi/<concept>/` reads; one
  v2.12 kept is never changed.
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
  left its metadata, DOI included, or the DOI Zenodo minted for its
  deposition, which v2.12 never saved (A15-04). Each becomes a withdrawn
  dataset, with its metadata and authors, so dataset's landing answers its
  DOI with the
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
  hubfile 0.9.0's `hubfile_alias` keeps the old one, so
  `/hubfiles/raw/<id>/<old name>`, which answered 400 ("Filename
  mismatch"), answers a 308 to the new name.
- **C-30** also covers a DOI that is not the one Zenodo mints for its
  deposition (`10.5281/zenodo.<deposition_id>`), which P-25b finds, and one
  whose record in `zenodo_snapshot` does not validate
  (`doi_record_missing`). C-30 and C-10 (a DOI of two metadata) stay
  conflicts by design: the plan resolves them by hand, and the only
  resolution, `accept`, loads the rows as `ledger.CONFLICTS` says.
