"""What the agent reads from its environment.

Every setting has a default except the ones nothing can guess: the image to
follow, the web container to replace, the database container to back up and
the secret that guards the API. A value of ``<SET>`` is what an env template
carries before ``splent product:deploy`` fills it in, so it counts as unset.

The image to follow is a channel (``:stable``) or a version tag, never
``:latest`` and never a name without a tag, which Docker reads as
``:latest``: that tag moves on every build, so it can name an image nobody
released. Whatever the channel points to, the web container is created
from the image's digest, which never moves.

A setting that is missing or malformed does not stop the agent. It keeps
serving its API and reports ``not_configured`` with the reason, so the admin
page can say what to fix instead of showing nothing at all.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime

PLACEHOLDER = "<SET>"

DEFAULT_INTERVAL = 300
DEFAULT_HEALTH_TIMEOUT = 600
DEFAULT_KEEP_BACKUPS = 5
DEFAULT_DATA_DIR = "/data"
DEFAULT_PORT = 8080
#: What the one-off migration container runs, from the new image.
DEFAULT_MIGRATE_COMMAND = "splent db:upgrade"
#: What the new web container's own start does about migrations
#: (SPLENT_MIGRATE_ON_START, splent_cli 1.41.0) once the agent has migrated
#: in its one-off step: "off" migrates and checks nothing, which any image
#: accepts; "check" also refuses to serve on a schema behind its code, but
#: needs db:status --check (splent_cli 1.41.0) in the image; "upgrade"
#: migrates again; "keep" leaves the container's own setting.
DEFAULT_WEB_MIGRATE_ON_START = "off"
WEB_MIGRATE_ON_START = frozenset({"off", "check", "upgrade"})
#: The framework's readiness probe (splent_framework 1.22.0 and later).
DEFAULT_READY_PATH = "/readyz"
DEFAULT_WEB_PORT = 5000
#: The user SPLENT's production image runs the app as. The migration and the
#: backup command run as this user, so what they write belongs to the app.
DEFAULT_APP_USER = "splent"
#: Take the backup feature's off-host backup when the product has it.
AUTO = "auto"
OFF_WORDS = frozenset({"off", "none", "false", "no", "0"})

MIN_INTERVAL = 30
MIN_HEALTH_TIMEOUT = 30
MIN_KEEP_BACKUPS = 1

_WINDOW = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$")


def clean(value) -> str:
    """The value as set, or "" when it is empty or still the placeholder."""
    value = (value or "").strip()
    return "" if value == PLACEHOLDER else value


def moving_tag(ref: str) -> str | None:
    """Why ``ref`` names a tag that moves on every build, or None.

    ``repo@sha256:...`` and ``repo:<tag>`` are fine unless the tag is
    ``latest``. A name without a tag or a digest is ``latest`` to Docker.
    """
    if "@" in ref:
        return None
    name, _sep, tag = ref.rpartition(":")
    if not name or "/" in tag:  # no tag, or the colon was a registry's port
        return f"{ref} has no tag, which Docker reads as :latest"
    if tag == "latest":
        return f"{ref} follows :latest"
    return None


@dataclass(frozen=True)
class Window:
    """A daily span of UTC time in which the agent may deploy.

    The start is included and the end is not. A window whose end comes
    before its start wraps past midnight, so ``22:00-04:00`` is the night.
    """

    start: int  # minutes after midnight
    end: int
    text: str

    def contains(self, moment: datetime) -> bool:
        minute = moment.hour * 60 + moment.minute
        if self.start < self.end:
            return self.start <= minute < self.end
        return minute >= self.start or minute < self.end


def parse_window(text: str | None) -> Window | None:
    """``"02:00-05:00"`` as a Window, None for an empty value.

    Raises ValueError with a message meant for the operator.
    """
    text = clean(text)
    if not text:
        return None
    match = _WINDOW.match(text)
    if not match:
        raise ValueError(f"AUTODEPLOY_WINDOW must look like 02:00-05:00, not {text!r}")
    h1, m1, h2, m2 = (int(group) for group in match.groups())
    if h1 > 23 or h2 > 23 or m1 > 59 or m2 > 59:
        raise ValueError(f"AUTODEPLOY_WINDOW has a time that does not exist: {text!r}")
    start, end = h1 * 60 + m1, h2 * 60 + m2
    if start == end:
        raise ValueError(
            "AUTODEPLOY_WINDOW starts and ends at the same minute. Leave it "
            "empty to allow deploys at any time."
        )
    return Window(start, end, f"{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}")


@dataclass(frozen=True)
class AgentConfig:
    image: str = ""
    web_container: str = ""
    db_container: str = ""
    secret: str = field(default="", repr=False)
    interval: int = DEFAULT_INTERVAL
    window: Window | None = None
    health_timeout: int = DEFAULT_HEALTH_TIMEOUT
    keep_backups: int = DEFAULT_KEEP_BACKUPS
    registry_user: str = ""
    registry_token: str = field(default="", repr=False)
    product: str = ""
    data_dir: str = DEFAULT_DATA_DIR
    port: int = DEFAULT_PORT
    # None runs no migration step: the new container migrates as it starts.
    migrate_command: str | None = DEFAULT_MIGRATE_COMMAND
    # SPLENT_MIGRATE_ON_START for the new container after the migration
    # step; None leaves the container's own.
    web_migrate_on_start: str | None = DEFAULT_WEB_MIGRATE_ON_START
    # None waits for Docker's healthcheck alone.
    ready_path: str | None = DEFAULT_READY_PATH
    web_port: int = DEFAULT_WEB_PORT
    app_user: str = DEFAULT_APP_USER
    # AUTO, a command run in the web container before a deploy, or None.
    backup_command: str | None = AUTO
    problems: tuple[str, ...] = ()

    @property
    def configured(self) -> bool:
        return not self.problems

    @property
    def window_text(self) -> str:
        return self.window.text if self.window else ""

    @property
    def ready_url(self) -> str | None:
        """Where the web container answers its readiness probe, by name on
        the product network."""
        if not self.ready_path or not self.web_container:
            return None
        return f"http://{self.web_container}:{self.web_port}{self.ready_path}"

    @property
    def registry_auth(self) -> dict | None:
        """docker-py's auth_config for a private registry, or None."""
        if self.registry_user and self.registry_token:
            return {"username": self.registry_user, "password": self.registry_token}
        return None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> AgentConfig:
        env = os.environ if env is None else env
        problems: list[str] = []

        def number(name: str, default: int, minimum: int) -> int:
            raw = clean(env.get(name))
            if not raw:
                return default
            try:
                value = int(raw)
            except ValueError:
                problems.append(f"{name} must be a whole number, not {raw!r}")
                return default
            if value < minimum:
                problems.append(f"{name} must be at least {minimum}")
                return default
            return value

        def optional(name: str, default: str) -> str | None:
            """A command or a path, or None when it is turned off."""
            raw = clean(env.get(name))
            if not raw:
                return default
            return None if raw.lower() in OFF_WORDS else raw

        image = clean(env.get("AUTODEPLOY_IMAGE")) or clean(env.get("SPLENT_IMAGE"))
        if not image:
            problems.append(
                "No image to follow. Set SPLENT_IMAGE (or AUTODEPLOY_IMAGE) to "
                "the registry channel, for example "
                "git.splent.io/splent-io/<product>:stable"
            )
        elif moving := moving_tag(image):
            problems.append(
                f"{moving}, which moves on every build and can name an image "
                "nobody released. Follow the release channel (:stable) or a "
                "version tag."
            )
        web = clean(env.get("AUTODEPLOY_WEB_CONTAINER"))
        if not web:
            problems.append("AUTODEPLOY_WEB_CONTAINER is not set")
        db = clean(env.get("AUTODEPLOY_DB_CONTAINER"))
        if not db:
            problems.append("AUTODEPLOY_DB_CONTAINER is not set")
        secret = clean(env.get("AUTODEPLOY_SECRET"))
        if not secret:
            problems.append(
                "AUTODEPLOY_SECRET is not set, so nobody could watch or "
                "control the agent"
            )

        try:
            window = parse_window(env.get("AUTODEPLOY_WINDOW"))
        except ValueError as exc:
            problems.append(str(exc))
            window = None

        web_migrate = clean(env.get("AUTODEPLOY_WEB_MIGRATE_ON_START")).lower()
        if not web_migrate:
            web_migrate = DEFAULT_WEB_MIGRATE_ON_START
        elif web_migrate == "keep":
            web_migrate = None
        elif web_migrate not in WEB_MIGRATE_ON_START:
            problems.append(
                "AUTODEPLOY_WEB_MIGRATE_ON_START is off, check, upgrade or keep, "
                f"not {web_migrate!r}"
            )
            web_migrate = DEFAULT_WEB_MIGRATE_ON_START

        ready_path = optional("AUTODEPLOY_READY_PATH", DEFAULT_READY_PATH)
        if ready_path and not ready_path.startswith("/"):
            ready_path = f"/{ready_path}"

        return cls(
            image=image,
            web_container=web,
            db_container=db,
            secret=secret,
            interval=number("AUTODEPLOY_INTERVAL", DEFAULT_INTERVAL, MIN_INTERVAL),
            window=window,
            health_timeout=number(
                "AUTODEPLOY_HEALTH_TIMEOUT", DEFAULT_HEALTH_TIMEOUT, MIN_HEALTH_TIMEOUT
            ),
            keep_backups=number(
                "AUTODEPLOY_KEEP_BACKUPS", DEFAULT_KEEP_BACKUPS, MIN_KEEP_BACKUPS
            ),
            registry_user=clean(env.get("AUTODEPLOY_REGISTRY_USER")),
            registry_token=clean(env.get("AUTODEPLOY_REGISTRY_TOKEN")),
            product=clean(env.get("SPLENT_APP")),
            data_dir=clean(env.get("AUTODEPLOY_DATA_DIR")) or DEFAULT_DATA_DIR,
            port=DEFAULT_PORT,
            migrate_command=optional(
                "AUTODEPLOY_MIGRATE_COMMAND", DEFAULT_MIGRATE_COMMAND
            ),
            web_migrate_on_start=web_migrate,
            ready_path=ready_path,
            web_port=number("AUTODEPLOY_WEB_PORT", DEFAULT_WEB_PORT, 1),
            app_user=clean(env.get("AUTODEPLOY_APP_USER")) or DEFAULT_APP_USER,
            backup_command=optional("AUTODEPLOY_BACKUP_COMMAND", AUTO),
            problems=tuple(problems),
        )
