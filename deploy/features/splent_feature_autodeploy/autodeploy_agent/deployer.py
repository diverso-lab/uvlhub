"""The check, the deploy, and the rollback.

One check:

1. pull the channel image; the same id as the running web container means
   there is nothing to do. The image is then named by its digest, which no
   push can move, and that is what the new container runs;
2. an image that failed before is held until the channel moves on; a paused
   agent or one outside its update window waits;
3. back up: the backup feature's off-host backup, in the web container,
   when the product has it, then the agent's own dump for the rollback
   (never deploy without both);
4. record what the web container runs (``splent version --json``) and a
   fingerprint of the schema;
5. create the new web container with everything the old one was configured
   with, rename the old one ``<name>-previous`` and stop it rather than
   remove it;
6. migrate, once, in a one-off container of the new image;
7. start the new container and wait for ``/readyz`` (and Docker's
   healthcheck not to say unhealthy);
8. ready: remove the previous container and write the history;
9. not ready: keep the new container's last log lines, remove it, put the
   database back if the deploy changed it, start the previous container
   under its name again, and never try that image again.

When the database goes back (:meth:`Deployer._must_restore`): a migration
that failed is always undone, since MariaDB commits DDL as it goes and a
failure can leave half of it behind without recording it. A migration that
finished is undone when the schema fingerprint differs from the one taken
before, because the previous version cannot run on the new schema and a
down-migration is not trusted. An unchanged schema is left alone, so what
was written while the new version tried to start is not lost. A deploy that
stopped before the migration ran never touched the database. Without a
migration step (``AUTODEPLOY_MIGRATE_COMMAND=off``) the new container
migrated as it started, the agent cannot tell a failed migration from
anything else, and the database always goes back.

Every step is written to state.json before it is taken, so an agent that is
restarted halfway (a host reboot, a redeploy of the agent itself) finishes
or undoes the deploy it was in instead of leaving the product half replaced.
"""

from __future__ import annotations

import logging
import shlex
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone

from autodeploy_agent import __version__
from autodeploy_agent import dockerops as ops
from autodeploy_agent.backup import (
    BackupError,
    BackupManager,
    RestoreError,
    run_in_container,
)
from autodeploy_agent.config import AUTO, AgentConfig
from autodeploy_agent.readiness import probe as http_probe
from autodeploy_agent.state import StateStore
from autodeploy_agent.versions import feature_changes, read_versions

logger = logging.getLogger("autodeploy")

# ── What the agent is doing ─────────────────────────────────────────────
NOT_CONFIGURED = "not_configured"
IDLE = "idle"
WAITING_FOR_WINDOW = "waiting_for_window"
DEPLOYING = "deploying"
ROLLING_BACK = "rolling_back"
PAUSED = "paused"
HELD = "held"
ERROR = "error"
STATUSES = (
    NOT_CONFIGURED,
    IDLE,
    WAITING_FOR_WINDOW,
    DEPLOYING,
    ROLLING_BACK,
    PAUSED,
    HELD,
    ERROR,
)

# ── How a deploy ended ──────────────────────────────────────────────────
SUCCESS = "success"
ROLLED_BACK = "rolled_back"
ROLLBACK_FAILED = "rollback_failed"
FAILED = "failed"  # the new container could not even be created

# ── What check() reports ────────────────────────────────────────────────
UP_TO_DATE = "up_to_date"
BUSY = "busy"
RECOVERED = "recovered"

PREVIOUS_SUFFIX = "-previous"
MIGRATE_SUFFIX = "-migrate"
STOP_TIMEOUT = 30
LOG_TAIL_LINES = 80
#: The backup feature, as ``splent version --json`` names it, and what the
#: agent runs in the web container when the product has it.
BACKUP_FEATURE = "splent_feature_backup"
BACKUP_FEATURE_COMMAND = ["splent", "feature:backup", "run", "--tag"]
#: How long a container without a healthcheck must keep running to count
#: as healthy. The product's web container always has one; this is for the
#: case where somebody removed it.
NO_HEALTHCHECK_GRACE = 30


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(moment: datetime | None) -> str | None:
    if moment is None:
        return None
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class RecreateError(RuntimeError):
    """The new container could not be created or started, and the previous
    one is back in place (or ``problems`` says why it is not)."""

    def __init__(self, reason: str, problems: list[str]):
        super().__init__(reason)
        self.reason = reason
        self.problems = problems


class Deployer:
    def __init__(
        self,
        api,
        config: AgentConfig,
        store: StateStore,
        *,
        backups: BackupManager | None = None,
        clock: Callable[[], datetime] = utcnow,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        poll_interval: float = 5.0,
        probe: Callable[[str], int | None] = http_probe,
    ):
        self.api = api
        self.config = config
        self.store = store
        self.clock = clock
        self.monotonic = monotonic
        self.sleep = sleep
        self.poll_interval = poll_interval
        self.probe = probe
        self.backups = backups or BackupManager(
            api,
            config.db_container,
            store.backups_dir,
            config.keep_backups,
            clock=clock,
        )
        self._lock = threading.Lock()

    # ── What the API and the scheduler call ────────────────────────────

    @property
    def busy(self) -> bool:
        return self._lock.locked()

    @property
    def previous_name(self) -> str:
        return f"{self.config.web_container}{PREVIOUS_SUFFIX}"

    @property
    def migrate_name(self) -> str:
        return f"{self.config.web_container}{MIGRATE_SUFFIX}"

    def check(self, ignore_window: bool = False) -> str:
        """Run one check, deploying if there is something to deploy.

        Returns what happened. A check already running makes this one a
        no-op that says ``busy``. ``ignore_window`` is for a check a person
        asked for (Check now): asking is the decision the window stands in for.
        """
        if not self._lock.acquire(blocking=False):
            return BUSY
        try:
            return self._check(ignore_window=ignore_window)
        except Exception as exc:  # noqa: BLE001 - the loop must survive anything
            logger.exception("The check failed")
            self.store.update(status=ERROR, detail=f"Unexpected error: {exc}")
            return ERROR
        finally:
            self._lock.release()

    def pause(self) -> dict:
        changes: dict = {"paused": True}
        if not self.busy:
            changes.update(status=PAUSED, detail="")
        self.store.update(**changes)
        logger.info("Paused")
        return self.status()

    def resume(self) -> dict:
        changes: dict = {"paused": False}
        if self.store.get("status") == PAUSED:
            changes.update(status=IDLE, detail="")
        self.store.update(**changes)
        logger.info("Resumed")
        return self.status()

    def status(self) -> dict:
        cfg = self.config
        state = self.store.snapshot()
        now = self.clock()
        status, detail = state["status"], state["detail"]
        if not cfg.configured:
            status, detail = NOT_CONFIGURED, "; ".join(cfg.problems)
        elif state["paused"] and status not in (DEPLOYING, ROLLING_BACK):
            status, detail = PAUSED, ""
        progress = state.get("in_progress")
        if progress:
            progress = {
                key: progress.get(key)
                for key in (
                    "started_at",
                    "step",
                    "from_image",
                    "to_image",
                    "to_ref",
                    "backup",
                    "offsite_backup",
                )
            }
        return {
            "agent_version": __version__,
            "status": status,
            "detail": detail,
            "busy": self.busy,
            "configured": cfg.configured,
            "problems": list(cfg.problems),
            "paused": bool(state["paused"]),
            "image": cfg.image or None,
            "web_container": cfg.web_container or None,
            "db_container": cfg.db_container or None,
            "window": cfg.window_text or None,
            "in_window": cfg.window.contains(now) if cfg.window else True,
            "interval": cfg.interval,
            "health_timeout": cfg.health_timeout,
            "keep_backups": cfg.keep_backups,
            "migrate_command": cfg.migrate_command,
            "ready_url": cfg.ready_url,
            "backup_command": cfg.backup_command,
            "last_check": state["last_check"],
            "running_image": state["running_image"],
            "running_versions": state["running_versions"],
            "pending_image": state["pending_image"],
            "bad_images": list(state["bad_images"] or []),
            "in_progress": progress,
            "last_deploy": state["last_deploy"],
            "backups": [path.name for path in self.backups.list()],
            "now": iso(now),
        }

    # ── The image the web container runs ──────────────────────────────

    def _remember_running_image(self) -> None:
        """Keep the configuration of the image the web container runs."""
        web = ops.inspect_container(self.api, self.config.web_container)
        running = (web or {}).get("Image")
        if not running:
            return
        known = self.store.get("running_image_config") or {}
        if known.get("Id") == running:
            return
        image = ops.inspect_image(self.api, running)
        if image:
            self.store.update(running_image_config=image_config(image))

    def _image_config(self, image_id: str | None) -> dict:
        """The inspect document of ``image_id``, or the copy kept of it."""
        image = ops.inspect_image(self.api, image_id) if image_id else None
        if image:
            return image
        known = self.store.get("running_image_config") or {}
        if image_id and known.get("Id") == image_id:
            return known
        logger.warning(
            "The configuration of %s is gone, so the new container keeps every "
            "env variable and label the old one had",
            ops.short_id(image_id or ""),
        )
        return {}

    # ── The check ───────────────────────────────────────────────────────

    def _check(self, ignore_window: bool = False) -> str:
        cfg = self.config
        if not cfg.configured:
            self.store.update(status=NOT_CONFIGURED, detail="; ".join(cfg.problems))
            return NOT_CONFIGURED

        if self.store.get("in_progress"):
            return self._recover()

        if self.store.get("paused"):
            self.store.update(status=PAUSED, detail="")
            return PAUSED

        if ops.inspect_container(self.api, self.previous_name) is not None:
            # Not one of ours (no deploy is in progress), so not ours to
            # remove: it may be the only copy of something somebody kept.
            self.store.update(
                status=ERROR,
                detail=(
                    f"A container named {self.previous_name} exists although no "
                    f"deploy is in progress. Remove it, or rename it back to "
                    f"{cfg.web_container}, and the agent will carry on."
                ),
            )
            return ERROR

        now = self.clock()
        # Before the pull: with the containerd image store, the pull that
        # moves the channel tag also removes the old image's record, and its
        # configuration is what tells the next deploy which env, labels and
        # command the container only inherited.
        self._remember_running_image()
        try:
            new_id = ops.pull(self.api, cfg.image, cfg.registry_auth)
        except Exception as exc:  # noqa: BLE001 - reported, retried next time
            self.store.update(
                status=ERROR,
                detail=f"Could not pull {cfg.image}: {exc}",
                last_check=iso(now),
            )
            return ERROR

        web = ops.inspect_container(self.api, cfg.web_container)
        if web is None:
            self.store.update(
                status=ERROR,
                detail=f"The web container {cfg.web_container} does not exist",
                last_check=iso(now),
            )
            return ERROR

        running_id = web.get("Image")
        changes: dict = {"last_check": iso(now), "running_image": running_id}
        if self.store.get("running_image") != running_id or not self.store.get(
            "running_versions"
        ):
            changes["running_versions"] = read_versions(self.api, cfg.web_container)

        if new_id == running_id:
            self.store.update(status=IDLE, detail="", pending_image=None, **changes)
            return UP_TO_DATE

        if self.store.is_bad(new_id):
            self.store.update(
                status=HELD,
                detail=(
                    f"The channel points to {ops.short_id(new_id)}, which failed "
                    "before and was rolled back. The agent waits for the next "
                    "release."
                ),
                pending_image=new_id,
                **changes,
            )
            return HELD

        if cfg.window and not ignore_window and not cfg.window.contains(now):
            self.store.update(
                status=WAITING_FOR_WINDOW,
                detail=(
                    f"{ops.short_id(new_id)} is ready and will be deployed between "
                    f"{cfg.window.text.replace('-', ' and ')} UTC."
                ),
                pending_image=new_id,
                **changes,
            )
            return WAITING_FOR_WINDOW

        self.store.update(**changes)
        return self._deploy(web, new_id, self._immutable_ref(new_id))

    def _immutable_ref(self, image_id: str) -> str:
        """The digest the channel image is known by, or its id."""
        image = ops.inspect_image(self.api, image_id) or {"Id": image_id}
        return ops.immutable_ref(image, self.config.image)

    # ── The deploy ──────────────────────────────────────────────────────

    def _deploy(self, web: dict, new_id: str, new_ref: str) -> str:
        cfg = self.config
        started = self.clock()
        old_id = web.get("Image")
        progress = {
            "started_at": iso(started),
            "started_epoch": started.timestamp(),
            "step": "backup",
            "from_image": old_id,
            "to_image": new_id,
            "from_ref": (web.get("Config") or {}).get("Image"),
            "to_ref": new_ref,
            "channel": cfg.image,
            "previous_container": web.get("Id"),
            "new_container": None,
            "backup": None,
            "offsite_backup": None,
            "schema_before": None,
            "migration": None,
            "versions_before": self.store.get("running_versions"),
        }
        self.store.update(
            status=DEPLOYING,
            detail="Backing up",
            pending_image=new_id,
            in_progress=progress,
        )
        logger.info("Deploying %s over %s", new_ref, ops.short_id(old_id))

        try:
            progress["offsite_backup"] = self._offsite_backup(web, old_id)
            backup = self.backups.create(ops.short_id(old_id))
        except BackupError as exc:
            logger.error("Backup failed: %s", exc)
            self.store.update(
                status=ERROR,
                detail=f"The backup failed, so nothing was deployed: {exc}",
                in_progress=None,
            )
            return ERROR
        progress.update(
            step="recreate", backup=backup.name, schema_before=self.backups.schema()
        )
        self.store.update(detail="Replacing the web container", in_progress=progress)

        try:
            self._recreate(web, new_id, new_ref, progress)
        except RecreateError as exc:
            # The new container never ran, so the database is untouched and
            # the previous container is back under its name, running. The
            # image is refused all the same, or the agent would take a
            # backup and fail again every few minutes.
            self.store.mark_bad(new_id)
            entry = self._history_entry(
                progress, FAILED, reason=exc.reason, problems=exc.problems
            )
            self.store.append_history(entry)
            detail = f"The new container could not be started: {exc.reason}"
            if exc.problems:
                detail += ". Needs attention: " + "; ".join(exc.problems)
            self.store.update(
                status=ERROR if exc.problems else HELD,
                detail=detail,
                in_progress=None,
                last_deploy=self._summary(entry),
            )
            return FAILED

        if progress.get("step") == "migrated" or not cfg.migrate_command:
            self._start_new(progress)
        if progress.get("step") != "health":
            # The migration failed, or the new container would not start.
            return self._rollback(progress, progress.get("failure") or "it failed")

        try:
            healthy, reason = self._wait_healthy(progress["new_container"], fresh=True)
        except Exception as exc:  # noqa: BLE001 - whatever it was, undo
            logger.exception("Waiting for health failed")
            healthy, reason = False, f"unexpected error while waiting: {exc}"
        if healthy:
            return self._succeed(progress)
        return self._rollback(progress, reason)

    def _offsite_backup(self, web: dict, old_id: str) -> str | None:
        """The backup feature's off-host backup, taken in the web container
        before anything changes. Returns what was run, or None.

        ``auto`` runs it when the product has the feature, which the
        versions the web container reported say. A command the operator set
        runs whatever the product has. Raises BackupError when it fails: no
        backup, no deploy.
        """
        cfg = self.config
        if not cfg.backup_command:
            return None
        tag = f"pre-deploy-{ops.short_id(old_id) or 'unknown'}"
        if cfg.backup_command == AUTO:
            features = (self.store.get("running_versions") or {}).get("features") or {}
            if BACKUP_FEATURE not in features:
                return None
            command = [*BACKUP_FEATURE_COMMAND, tag]
        else:
            command = shlex.split(cfg.backup_command)
        self.store.update(detail="Taking the off-host backup")
        logger.info("Off-host backup: %s", " ".join(command))
        try:
            code, tail = run_in_container(
                self.api, web["Id"], command, user=cfg.app_user
            )
        except Exception as exc:  # noqa: BLE001
            raise BackupError(f"{command[0]} could not run: {exc}") from exc
        if code != 0:
            raise BackupError(
                f"{' '.join(command)} exited with code {code}: {tail or 'no output'}"
            )
        return " ".join(command)

    def _recreate(self, web: dict, new_id: str, new_ref: str, progress: dict) -> None:
        """Replace the running web container with one on ``new_ref``.

        On return the new container exists and the previous one is stopped;
        with a migration step the migration has run too (step ``migrated``,
        or ``migrate_failed`` with ``failure`` saying why). Raises
        RecreateError, with the previous container restored, when it cannot
        get that far without touching the database.
        """
        cfg = self.config
        old_image = self._image_config(web.get("Image"))
        new_image = ops.inspect_image(self.api, new_id) or {}
        if new_image:
            progress["new_image_config"] = image_config(new_image)
        spec, extra_networks = ops.creation_spec(
            web, old_image, new_image, new_ref, new_image_id=new_id
        )
        if cfg.migrate_command and cfg.web_migrate_on_start:
            # The agent migrates in a step of its own, so the new container's
            # start does not migrate a second time (PL-7).
            spec["Env"] = [
                item
                for item in spec.get("Env") or []
                if not item.startswith("SPLENT_MIGRATE_ON_START=")
            ] + [f"SPLENT_MIGRATE_ON_START={cfg.web_migrate_on_start}"]
        previous_id = web["Id"]

        try:
            self.api.rename(previous_id, self.previous_name)
        except Exception as exc:  # noqa: BLE001
            raise RecreateError(f"could not rename the running container: {exc}", [])

        try:
            created = self.api.create_container_from_config(
                spec, name=cfg.web_container
            )
            progress["new_container"] = created["Id"]
            self.store.update(in_progress=progress)
            for network, endpoint in extra_networks:
                ops.connect_network(self.api, created["Id"], network, endpoint)
            self.api.stop(previous_id, timeout=STOP_TIMEOUT)
        except Exception as exc:  # noqa: BLE001
            raise RecreateError(str(exc), self._undo_recreate(progress)) from exc

        if cfg.migrate_command:
            self._migrate(spec, extra_networks, progress)

    def _migrate(self, spec: dict, extra_networks: list, progress: dict) -> None:
        """Run the migrations once, in a one-off container of the new image
        with the web container's environment, mounts and networks, while
        neither version serves. Sets step ``migrated``, or ``migrate_failed``
        and ``failure``.
        """
        cfg = self.config
        command = ["sh", "-c", cfg.migrate_command]
        job, job_networks = ops.one_off_spec(
            spec, extra_networks, command, cfg.app_user
        )
        try:
            # One an agent killed during a migration left behind.
            stale = ops.inspect_container(self.api, self.migrate_name)
            if stale is not None:
                self.api.remove_container(stale["Id"], force=True)
            created = self.api.create_container_from_config(job, name=self.migrate_name)
            for network, endpoint in job_networks:
                ops.connect_network(self.api, created["Id"], network, endpoint)
        except Exception as exc:  # noqa: BLE001 - nothing ran yet
            raise RecreateError(
                f"the migration container could not be created: {exc}",
                self._undo_recreate(progress),
            ) from exc

        progress.update(step="migrate", migration={"command": cfg.migrate_command})
        self.store.update(detail="Migrating the database", in_progress=progress)
        logger.info("Migrating: %s", cfg.migrate_command)
        code, why = None, ""
        try:
            self.api.start(created["Id"])
            code, why = self._wait_exit(created["Id"])
        except Exception as exc:  # noqa: BLE001
            why = f"the migration container failed: {exc}"
        tail = (
            ops.log_tail(self.api, created["Id"], LOG_TAIL_LINES) if code != 0 else ""
        )
        try:
            self.api.remove_container(created["Id"], force=True)
        except Exception as exc:  # noqa: BLE001
            if not ops.is_not_found(exc):
                logger.warning("Could not remove the migration container: %s", exc)
        progress["migration"].update(exit_code=code)
        if code == 0:
            progress["step"] = "migrated"
        else:
            progress.update(
                step="migrate_failed",
                failure=why or f"the migrations exited with code {code}",
            )
            progress["migration"]["log_tail"] = tail
        self.store.update(in_progress=progress)

    def _wait_exit(self, container_id: str) -> tuple[int | None, str]:
        """Wait for a one-off container to exit. Returns its exit code, or
        None and why it has none."""
        timeout = self.config.health_timeout
        deadline = self.monotonic() + timeout
        while True:
            attrs = ops.inspect_container(self.api, container_id)
            if attrs is None:
                return None, "the migration container disappeared"
            state = attrs.get("State") or {}
            if state.get("Status") in ("exited", "dead"):
                return state.get("ExitCode"), ""
            if self.monotonic() >= deadline:
                return None, f"the migrations did not finish in {timeout} seconds"
            self.sleep(self.poll_interval)

    def _start_new(self, progress: dict) -> None:
        """Start the new container. Sets step ``health``, or ``failure``."""
        progress.update(step="start", started=False)
        self.store.update(in_progress=progress)
        try:
            self.api.start(progress["new_container"])
        except Exception as exc:  # noqa: BLE001
            progress["failure"] = f"the new container did not start: {exc}"
            return
        progress.update(step="health", started=True)
        self.store.update(
            detail="Waiting for the new container to become ready",
            in_progress=progress,
        )

    def _undo_recreate(self, progress: dict) -> list[str]:
        """Put the previous container back under its name, running.

        For a deploy that stopped before the new container ran, so the
        database was never touched and needs no restore. Returns what could
        not be done.
        """
        problems: list[str] = []
        self._remove_new_container(progress)
        problems += self._restore_previous_container(progress, wait=False)
        return problems

    def _wait_healthy(self, container_id: str, fresh: bool = False) -> tuple[bool, str]:
        """Poll until the container is ready, or say why it is not.

        Ready is ``/readyz`` answering 200, by the container's name on the
        product network, while Docker's healthcheck does not say unhealthy.
        An image whose framework has no readiness probe (``/readyz`` is a
        404) or an agent told not to probe falls back to the healthcheck.

        A ``fresh`` container was created for this deploy, so any restart at
        all is a crash. For one that already lived, only restarts during the
        wait count.
        """
        timeout = self.config.health_timeout
        deadline = self.monotonic() + timeout
        running_since = None
        restarts = 0 if fresh else None
        ready_url = self.config.ready_url
        last_answer = None
        while True:
            attrs = ops.inspect_container(self.api, container_id)
            if attrs is None:
                return False, "the container disappeared"
            state = attrs.get("State") or {}
            status = state.get("Status")
            if status in ("exited", "dead"):
                return (
                    False,
                    f"the container stopped with exit code {state.get('ExitCode')}",
                )
            count = attrs.get("RestartCount") or 0
            if restarts is None:
                restarts = count
            elif count > restarts:
                return False, "the container crashed and was restarted"
            health = ops.health_status(attrs)
            if health == "unhealthy":
                return False, "the healthcheck reports it unhealthy"
            if status == "running" and ready_url:
                last_answer = self.probe(ready_url)
                if last_answer == 200:
                    return True, ""
                if last_answer == 404:
                    ready_url = None  # no probe in this version
            if not ready_url:
                if health == "healthy":
                    return True, ""
                if health is None and status == "running":
                    if running_since is None:
                        running_since = self.monotonic()
                    elif self.monotonic() - running_since >= NO_HEALTHCHECK_GRACE:
                        return True, ""
            if self.monotonic() >= deadline:
                if ready_url:
                    answer = (
                        f"answered {last_answer}" if last_answer else "never answered"
                    )
                    return (
                        False,
                        f"it was not ready after {timeout} seconds "
                        f"({self.config.ready_path} {answer})",
                    )
                return False, f"it was not healthy after {timeout} seconds"
            self.sleep(self.poll_interval)

    # ── Endings ─────────────────────────────────────────────────────────

    def _succeed(self, progress: dict) -> str:
        cfg = self.config
        try:
            self.api.remove_container(progress["previous_container"], force=True)
        except Exception as exc:  # noqa: BLE001 - the deploy itself worked
            if not ops.is_not_found(exc):
                logger.warning("Could not remove the previous container: %s", exc)
        after = read_versions(self.api, cfg.web_container)
        entry = self._history_entry(progress, SUCCESS, after=after)
        self.store.append_history(entry)
        self.store.update(
            status=IDLE,
            detail="",
            in_progress=None,
            pending_image=None,
            running_image=progress["to_image"],
            running_versions=after,
            last_deploy=self._summary(entry),
            # The image just deployed is the one the next deploy replaces,
            # and by then the channel may have moved and its record be gone.
            running_image_config=progress.get("new_image_config"),
        )
        logger.info("Deployed %s", ops.short_id(progress["to_image"]))
        return SUCCESS

    def _must_restore(self, progress: dict) -> tuple[bool, str]:
        """Whether a rollback puts the database back, and why (see the
        module's docstring for the rule)."""
        migration = progress.get("migration")
        # A deploy an older agent recorded says nothing about it: at the
        # health wait (or rolling back) the new container had started.
        started = progress.get(
            "started", progress.get("step") in ("health", "rollback")
        )
        if migration is None and not started:
            return False, "the deploy never reached the database"
        if not self.config.migrate_command and migration is None:
            return True, "the new container migrated as it started"
        if migration is not None and migration.get("exit_code") != 0:
            return True, "the migration did not finish"
        before, now = progress.get("schema_before"), self.backups.schema()
        if before is None or now is None:
            return True, "the schema could not be compared"
        if before != now:
            return True, "the migration changed the schema"
        return False, "the schema is the one the previous version ran on"

    def _rollback(self, progress: dict, reason: str) -> str:
        logger.error("Rolling back %s: %s", ops.short_id(progress["to_image"]), reason)
        progress["step"] = "rollback"
        self.store.update(status=ROLLING_BACK, detail=reason, in_progress=progress)

        tail, attempted = self._remove_new_container(progress, keep_record=True)
        if not tail and (progress.get("migration") or {}).get("log_tail"):
            tail = progress["migration"]["log_tail"]
        problems: list[str] = []
        restore, why = self._must_restore(progress)
        backup = progress.get("backup")
        if restore and backup:
            try:
                self.backups.restore(self.store.backups_dir / backup)
            except RestoreError as exc:
                problems.append(f"the database restore failed: {exc}")
        elif restore:
            problems.append("there was no backup to restore")
        logger.info("The database %s: %s", "goes back" if restore else "stays", why)
        problems += self._restore_previous_container(progress, wait=True)

        self.store.mark_bad(progress["to_image"])
        result = ROLLED_BACK if not problems else ROLLBACK_FAILED
        entry = self._history_entry(
            progress,
            result,
            after=attempted,
            reason=reason,
            log_tail=tail,
            problems=problems,
        )
        entry["database_restored"] = bool(restore and backup and not problems)
        entry["database_decision"] = why
        self.store.append_history(entry)
        short = ops.short_id(progress["to_image"])
        if result == ROLLED_BACK:
            status = HELD
            detail = (
                f"{short} failed ({reason}) and was rolled back"
                + (
                    ", database included"
                    if restore
                    else f"; the database stayed: {why}"
                )
                + ". The agent will not deploy it again."
            )
            running = progress["from_image"]
        else:
            status = ERROR
            detail = f"Rolling back {short} needs attention: " + "; ".join(problems)
            running = None
        self.store.update(
            status=status,
            detail=detail,
            in_progress=None,
            pending_image=progress["to_image"],
            running_image=running,
            running_versions=progress.get("versions_before") if running else None,
            last_deploy=self._summary(entry),
        )
        return result

    def _remove_new_container(self, progress: dict, keep_record: bool = False):
        """Remove the container the deploy created, if there is one.

        With ``keep_record`` it first keeps its last log lines and, if it is
        still running, the versions it reports. Returns (log tail, versions).
        """
        cfg = self.config
        job = ops.inspect_container(self.api, self.migrate_name)
        if job is not None:
            try:
                self.api.remove_container(job["Id"], force=True)
            except Exception as exc:  # noqa: BLE001
                logger.error("Could not remove the migration container: %s", exc)
        target = progress.get("new_container")
        if not target:
            current = ops.inspect_container(self.api, cfg.web_container)
            if current and current.get("Id") != progress.get("previous_container"):
                target = current["Id"]
        if not target:
            return "", None
        attrs = ops.inspect_container(self.api, target)
        if attrs is None:
            return "", None
        tail, versions = "", None
        if keep_record:
            if (attrs.get("State") or {}).get("Status") == "running":
                versions = read_versions(self.api, target)
            tail = ops.log_tail(self.api, target, LOG_TAIL_LINES)
        try:
            self.api.remove_container(target, force=True)
        except Exception as exc:  # noqa: BLE001
            if not ops.is_not_found(exc):
                logger.error("Could not remove the new container: %s", exc)
        return tail, versions

    def _restore_previous_container(self, progress: dict, wait: bool) -> list[str]:
        cfg = self.config
        previous_id = progress.get("previous_container")
        previous = ops.inspect_container(self.api, previous_id) if previous_id else None
        if previous is None:
            return [f"the previous container {self.previous_name} is gone"]
        try:
            if ops.container_name(previous) != cfg.web_container:
                self.api.rename(previous_id, cfg.web_container)
            if (previous.get("State") or {}).get("Status") != "running":
                self.api.start(previous_id)
        except Exception as exc:  # noqa: BLE001
            return [f"the previous container could not be started again: {exc}"]
        if wait:
            healthy, why = self._wait_healthy(previous_id)
            if not healthy:
                return [f"the previous container is not healthy either: {why}"]
        return []

    # ── An agent restarted in the middle of a deploy ────────────────────

    def _recover(self) -> str:
        progress = self.store.get("in_progress") or {}
        cfg = self.config
        step = progress.get("step")
        logger.warning("Found an interrupted deploy at step %s", step)

        if step == "backup" or not progress.get("backup"):
            self.store.update(
                status=IDLE,
                detail="A deploy was interrupted before it changed anything.",
                in_progress=None,
            )
            return RECOVERED

        if step == "recreate":
            # The new container never ran, so the database is as it was.
            problems = self._undo_recreate(progress)
            self.store.update(
                status=ERROR if problems else IDLE,
                detail=(
                    "An interrupted deploy was undone before the new container "
                    "ran; it will be tried again."
                    + (" Needs attention: " + "; ".join(problems) if problems else "")
                ),
                in_progress=None,
            )
            return RECOVERED

        if step == "rollback":
            return self._rollback(progress, "the agent restarted during a rollback")

        if step in ("migrate", "migrate_failed"):
            # The migration may have run halfway: no exit code is a failed
            # one, so the database goes back.
            return self._rollback(progress, "the agent restarted during the migration")

        if step == "migrated":
            self._start_new(progress)
            if progress.get("step") != "health":
                return self._rollback(progress, progress.get("failure") or "it failed")

        # start or health: the new container may have run migrations.
        previous = ops.inspect_container(self.api, progress.get("previous_container"))
        current = ops.inspect_container(self.api, cfg.web_container)
        if previous is None:
            if current and current.get("Image") == progress.get("to_image"):
                return self._succeed(progress)
            self.store.update(
                status=ERROR,
                detail=(
                    "An interrupted deploy left no previous container to roll "
                    f"back to. Check {cfg.web_container} by hand."
                ),
                in_progress=None,
            )
            return ERROR
        if current is not None and current.get("Id") != previous.get("Id"):
            progress["new_container"] = current["Id"]
            healthy, reason = self._wait_healthy(current["Id"], fresh=True)
            if healthy:
                return self._succeed(progress)
            return self._rollback(progress, f"after the agent restarted, {reason}")
        return self._rollback(
            progress, "the agent restarted in the middle of the deploy"
        )

    # ── Records ─────────────────────────────────────────────────────────

    def _history_entry(
        self,
        progress: dict,
        result: str,
        *,
        after: dict | None = None,
        reason: str = "",
        log_tail: str = "",
        problems: list[str] | None = None,
    ) -> dict:
        cfg = self.config
        before = progress.get("versions_before") or {}
        after = after or {}
        finished = self.clock()
        started_epoch = progress.get("started_epoch") or finished.timestamp()
        return {
            "started_at": progress.get("started_at"),
            "finished_at": iso(finished),
            "duration_seconds": round(
                max(0.0, finished.timestamp() - started_epoch), 1
            ),
            "result": result,
            "product": cfg.product or before.get("product") or after.get("product"),
            "from_image": progress.get("from_image"),
            "to_image": progress.get("to_image"),
            "from_ref": progress.get("from_ref"),
            "to_ref": progress.get("to_ref"),
            "product_version_from": before.get("product_version"),
            "product_version_to": after.get("product_version"),
            "framework_from": before.get("framework"),
            "framework_to": after.get("framework"),
            "features_changed": feature_changes(before, after) if after else [],
            "channel": progress.get("channel"),
            "backup": progress.get("backup"),
            "offsite_backup": progress.get("offsite_backup"),
            "migration": {
                k: v
                for k, v in (progress.get("migration") or {}).items()
                if k != "log_tail"
            }
            or None,
            "reason": reason,
            "problems": problems or [],
            "log_tail": log_tail,
        }

    @staticmethod
    def _summary(entry: dict) -> dict:
        return {
            key: entry.get(key)
            for key in (
                "finished_at",
                "result",
                "from_image",
                "to_image",
                "product_version_from",
                "product_version_to",
                "reason",
            )
        }


def image_config(image: dict) -> dict:
    """The part of an image's inspect document a recreation reads."""
    config = image.get("Config") or {}
    return {
        "Id": image.get("Id"),
        "Config": {
            key: config.get(key)
            for key in ("Env", "Labels", "Cmd", "Entrypoint", "WorkingDir", "User")
        },
    }


class Scheduler:
    """Runs a check every ``interval`` seconds, or sooner when asked."""

    def __init__(self, deployer: Deployer, interval: int):
        self.deployer = deployer
        self.interval = interval
        self._wake = threading.Event()
        self._forced = threading.Event()
        self._stopping = threading.Event()
        self._thread = threading.Thread(
            target=self._run, name="autodeploy-scheduler", daemon=True
        )

    def start(self) -> None:
        self._thread.start()

    def trigger(self, ignore_window: bool = False) -> None:
        if ignore_window:
            self._forced.set()
        self._wake.set()

    def stop(self) -> None:
        self._stopping.set()
        self._wake.set()

    def _run(self) -> None:
        while not self._stopping.is_set():
            forced = self._forced.is_set()
            self._forced.clear()
            outcome = self.deployer.check(ignore_window=forced)
            logger.info("Check finished: %s", outcome)
            self._wake.wait(self.interval)
            self._wake.clear()
