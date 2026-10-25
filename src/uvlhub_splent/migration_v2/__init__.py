"""The migrator of uvlhub.io 2.12 into uvlhub 3.0 (CO-3, MIG-04).

Strategy C of the migration plan (``_reference/analisis_uvlhub/06-plan-
migracion-uvlhubio.md``, §3): a dump of v2.12 is restored in a schema of its
own (``uvlhub_v2_src``), an empty ``uvlhub3`` is brought to the head of the
pinned features by their own migrations, and the migrator fills it, never
writing to the source. Every run starts over (principle 3): it drops and
creates ``uvlhub3``, ``uvlhub_v2_src`` and the outputs in
``uvlhub_migration``, and keeps the versioned inputs of
``uvlhub_migration_inputs``.

Stages (§3.4), and what this first pass does of each:

    E0  preflight     the safeguards, the parameters, the pins      done
    E1  source        the dump restored as root, P-19, P-28          done
    E2  profiling     P-00 to P-28 against a clean v2.12, decisions  done
    E3  schema        uvlhub3 at head, V-12, V-14, the contract      done
    E4  identity      accounts, profiles, identities, tokens         done
    E5  content       datasets and everything hanging off them       FIRST PASS
    E6  legacy        usage aggregates, legacy_url, held notices     done
    E7  post-load     counters, foreign keys, counts, V-*           done
    E8  files         hubfile's storage-migrate, file_manifest       done
    E9  derived       FactLabel, formats, reindex, by the features   done
    E10 report        what was loaded, dropped and left open         done

The rules it follows (§3.4): SQLAlchemy Core on connections of its own,
never the ORM or ``db.session``, so no listener of a feature fires during
the load (tests/migration_v2 fails if one does); dates in UTC; a strict
sql_mode; foreign keys off only while a batch loads, then checked one by
one (V-04); batches of 1000 rows by id, a transaction each; the UNIQUE
constraints of the features from E3 on; BINARY when text is compared
across schemas. A feature's rule is called where the feature offers it
as a plain function (apikeys' ``imported_token_fields``, the row
``ApiTokenService.import_token`` stores); where it lives in an ORM service
only (``AuthenticationService.record_legacy_proof``), it is reproduced in
Core here and the tests check that both give the same answer; where it is
a command that needs the app (``splent db:upgrade``, ``splent
feature:hubfile storage-migrate``) it runs in a process of its own, as a
separate step.

Run it with ``python -m uvlhub_splent.migration_v2 --help``, the entry of
the cutover, which builds no app; ``splent product:migrate-v2`` gives the
same commands inside the CLI (uvlhub_splent/commands.py). The data
contract it writes to is ``contract.toml``.
"""

# Recorded in every run and report, with the contract's version.
MIGRATOR_VERSION = "0.1.0"

# Every stage, in order. The ones this pass leaves for later are skipped by
# the pipeline and named in the report.
STAGES = ("E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "E10")
NOT_YET = ()
# What E9 makes again, in the order it runs: the index reads the others.
DERIVED = ("factlabel", "formats", "reindex")
