"""What the agent asks of the Docker Engine.

Everything here takes docker-py's low level client (``docker.APIClient``, or
``docker.DockerClient().api``) as its first argument and nothing else from
docker-py, so the tests hand in a fake and the module imports without the
SDK installed.

The interesting part is :func:`creation_spec`: how a running container is
described again, on a new image, the way Watchtower does it. The container's
own settings are kept (name, environment, labels, mounts, ports, restart
policy, healthcheck, networks and their aliases); whatever it only inherited
from its old image is left out, so the new image's defaults take its place.
"""

from __future__ import annotations

import copy
import json

#: Label Compose writes with the image id it created the container from.
#: Kept in step with the new image, or the next ``docker compose up`` would
#: think the container is stale and recreate it for nothing.
COMPOSE_LABEL_PREFIX = "com.docker.compose."
COMPOSE_IMAGE_LABEL = "com.docker.compose.image"


class PullError(RuntimeError):
    """The registry refused or failed the pull."""


def is_not_found(exc: BaseException) -> bool:
    """Whether a docker-py error means "no such container or image"."""
    return getattr(exc, "status_code", None) == 404 or type(exc).__name__ in {
        "NotFound",
        "ImageNotFound",
    }


def short_id(object_id: str | None) -> str:
    """The 12 characters Docker shows for an id, without ``sha256:``."""
    if not object_id:
        return ""
    return object_id.split(":", 1)[-1][:12]


def inspect_container(api, name_or_id: str) -> dict | None:
    """The container's inspect document, or None when it does not exist."""
    try:
        return api.inspect_container(name_or_id)
    except Exception as exc:  # noqa: BLE001 - only "not found" is expected
        if is_not_found(exc):
            return None
        raise


def inspect_image(api, ref: str) -> dict | None:
    try:
        return api.inspect_image(ref)
    except Exception as exc:  # noqa: BLE001
        if is_not_found(exc):
            return None
        raise


def pull(api, ref: str, auth: dict | None = None) -> str:
    """Pull ``ref`` and return the id of the image it now names.

    The pull is streamed because the Engine reports some failures (a
    manifest it cannot read, a layer it cannot fetch) inside an HTTP 200
    stream rather than as an error status.
    """
    kwargs = {"stream": True, "decode": True}
    if auth:
        kwargs["auth_config"] = auth
    for chunk in api.pull(ref, **kwargs):
        if isinstance(chunk, dict) and chunk.get("error"):
            raise PullError(str(chunk["error"]))
    image = api.inspect_image(ref)
    return image["Id"]


def repository(ref: str) -> str:
    """``ref`` without its tag or digest: ``git.splent.io/org/app``."""
    name = ref.split("@", 1)[0]
    head, sep, tag = name.rpartition(":")
    return head if sep and "/" not in tag else name


def immutable_ref(image: dict, ref: str) -> str:
    """The reference that names exactly ``image``: its digest in the
    repository ``ref`` was pulled from, which no push can move. An image
    the Engine knows by no digest of that repository (built here, never
    pulled) is named by its id, which is just as fixed.
    """
    wanted = repository(ref)
    for digest in image.get("RepoDigests") or []:
        if repository(digest) == wanted:
            return digest
    return image["Id"]


def container_name(attrs: dict) -> str:
    return (attrs.get("Name") or "").lstrip("/")


def health_status(attrs: dict) -> str | None:
    """``healthy``, ``unhealthy``, ``starting``, or None without a healthcheck."""
    health = (attrs.get("State") or {}).get("Health") or {}
    return health.get("Status")


# ── exec ────────────────────────────────────────────────────────────────


def exec_output(
    api, container: str, cmd: list[str], user: str = ""
) -> tuple[int | None, bytes, bytes]:
    """Run ``cmd`` in ``container`` and return (exit code, stdout, stderr)."""
    exec_id = api.exec_create(container, cmd, stdout=True, stderr=True, user=user)["Id"]
    output = api.exec_start(exec_id, demux=True)
    if isinstance(output, tuple):
        stdout, stderr = output
    else:
        stdout, stderr = output, b""
    code = api.exec_inspect(exec_id).get("ExitCode")
    return code, stdout or b"", stderr or b""


def exec_stream(api, container: str, cmd: list[str], user: str = ""):
    """Start ``cmd`` in ``container``. Returns (exec id, iterator of
    (stdout, stderr) chunks); ask ``api.exec_inspect`` for the exit code
    once the iterator is exhausted."""
    exec_id = api.exec_create(container, cmd, stdout=True, stderr=True, user=user)["Id"]
    return exec_id, api.exec_start(exec_id, stream=True, demux=True)


def parse_json_output(raw: bytes) -> dict | None:
    """The first JSON object in a command's output, ignoring anything a
    library printed before it."""
    text = raw.decode("utf-8", errors="replace")
    start = text.find("{")
    if start < 0:
        return None
    try:
        value, _end = json.JSONDecoder().raw_decode(text[start:])
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def log_tail(api, container: str, lines: int = 80) -> str:
    try:
        raw = api.logs(container, stdout=True, stderr=True, tail=lines)
    except Exception as exc:  # noqa: BLE001 - a missing log is not worth failing over
        return f"(the container logs could not be read: {exc})"
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    return str(raw)


# ── Recreating a container on a new image ──────────────────────────────


def _as_list(value):
    if value is None:
        return None
    if isinstance(value, str):
        return [value]
    return list(value) or None


def _same(left, right) -> bool:
    return _as_list(left) == _as_list(right)


def _endpoint(settings: dict, old_ids: set[str]) -> dict:
    """What a network attachment is recreated with.

    Docker adds the container's short id to its aliases on its own; the old
    container's id would be a stale alias on the new one. The address and
    MAC Docker assigned are not copied (the IPAMConfig a compose file asked
    for is), so the new container gets fresh ones.
    """
    # Compose names a service and its container alike, so the same alias can
    # appear twice; once is enough.
    aliases = list(
        dict.fromkeys(a for a in settings.get("Aliases") or [] if a not in old_ids)
    )
    endpoint: dict = {"Aliases": aliases or None}
    for key in ("IPAMConfig", "Links", "DriverOpts"):
        if settings.get(key):
            endpoint[key] = copy.deepcopy(settings[key])
    return endpoint


def creation_spec(
    container: dict,
    old_image: dict | None,
    new_image: dict | None,
    image_ref: str,
    new_image_id: str | None = None,
) -> tuple[dict, list[tuple[str, dict]]]:
    """The body of ``POST /containers/create`` that rebuilds ``container``
    on ``image_ref``, and the extra networks to connect it to afterwards.

    ``old_image`` is the inspect document of the image the container runs,
    ``new_image`` the one of the image it moves to.
    """
    config = copy.deepcopy(container.get("Config") or {})
    host_config = copy.deepcopy(container.get("HostConfig") or {})
    old_cfg = (old_image or {}).get("Config") or {}
    new_cfg = (new_image or {}).get("Config") or {}

    old_ids = {container.get("Id", ""), short_id(container.get("Id"))} - {""}

    # Environment: what the container set itself, on top of the new image's.
    # A variable the old image baked in (PATH, PYTHON_VERSION) is the old
    # image's business and must not shadow what the new one says.
    old_env = set(old_cfg.get("Env") or [])
    own_env = [item for item in config.get("Env") or [] if item not in old_env]
    own_keys = {item.split("=", 1)[0] for item in own_env}
    image_env = [
        item
        for item in new_cfg.get("Env") or []
        if item.split("=", 1)[0] not in own_keys
    ]
    config["Env"] = image_env + own_env

    # Labels: the container's minus those it only inherited from the old
    # image, since the new image brings its own. Compose's are always the
    # container's: an image built by `docker compose build` carries the same
    # project and service labels, and without them Compose no longer owns
    # the container and its next `up` fails on the name.
    old_labels = old_cfg.get("Labels") or {}
    labels = {
        key: value
        for key, value in (config.get("Labels") or {}).items()
        if key.startswith(COMPOSE_LABEL_PREFIX) or old_labels.get(key) != value
    }
    if COMPOSE_IMAGE_LABEL in labels and new_image_id:
        labels[COMPOSE_IMAGE_LABEL] = new_image_id
    config["Labels"] = labels

    # Entrypoint, Cmd and WorkingDir: a value equal to the old image's
    # default was inherited, so it is left to the new image (null means
    # "the image's default"). A value the container chose (Compose's
    # command:) is kept.
    if _same(config.get("Entrypoint"), old_cfg.get("Entrypoint")):
        config["Entrypoint"] = None
        if _same(config.get("Cmd"), old_cfg.get("Cmd")):
            config["Cmd"] = None
    if (config.get("WorkingDir") or "") == (old_cfg.get("WorkingDir") or ""):
        config["WorkingDir"] = ""
    if (config.get("User") or "") == (old_cfg.get("User") or ""):
        config["User"] = ""

    # A healthcheck identical to the old image's was inherited too. One the
    # container declared (the product's compose file) is kept.
    if config.get("Healthcheck") and config.get("Healthcheck") == old_cfg.get(
        "Healthcheck"
    ):
        config.pop("Healthcheck")

    # Anonymous volumes and exposed ports the old image declared.
    old_volumes = old_cfg.get("Volumes") or {}
    volumes = {
        k: v for k, v in (config.get("Volumes") or {}).items() if k not in old_volumes
    }
    config["Volumes"] = volumes or None
    old_ports = old_cfg.get("ExposedPorts") or {}
    exposed = {
        k: v
        for k, v in (config.get("ExposedPorts") or {}).items()
        if k not in old_ports
    }
    for port in host_config.get("PortBindings") or {}:
        exposed[port] = {}
    config["ExposedPorts"] = exposed or None

    # Docker names a container's host after its short id unless told
    # otherwise. Kept, the new container would answer to the old one's id.
    if config.get("Hostname") in old_ids:
        config.pop("Hostname")
    # Deprecated in the container config since API 1.44, where an empty one
    # is still accepted and a set one belongs to the network endpoint.
    if not config.get("MacAddress"):
        config.pop("MacAddress", None)

    config["Image"] = image_ref

    # Legacy links name the old container; rewritten the way Watchtower
    # does so they point at the target by name.
    links = host_config.get("Links") or []
    if links:
        rewritten = []
        for link in links:
            name, _, alias = link.partition(":")
            rewritten.append(f"{name}:{alias.rsplit('/', 1)[-1]}" if alias else link)
        host_config["Links"] = rewritten

    config["HostConfig"] = host_config

    # Networks. The create call carries one endpoint (older Engines accept
    # no more), and the rest are connected before the container starts.
    networks = (container.get("NetworkSettings") or {}).get("Networks") or {}
    mode = host_config.get("NetworkMode") or ""
    extra: list[tuple[str, dict]] = []
    if networks and mode not in ("host", "none") and not mode.startswith("container:"):
        names = list(networks)
        primary = mode if mode in networks else names[0]
        config["NetworkingConfig"] = {
            "EndpointsConfig": {primary: _endpoint(networks[primary], old_ids)}
        }
        extra = [
            (name, _endpoint(networks[name], old_ids))
            for name in names
            if name != primary
        ]
    return config, extra


def one_off_spec(
    spec: dict, extra_networks: list[tuple[str, dict]], cmd: list[str], user: str
) -> tuple[dict, list[tuple[str, dict]]]:
    """The web container's creation body turned into a one-off job: the same
    image, environment, mounts and networks, running ``cmd`` as ``user``.

    It answers to no alias (nginx resolves the web container by name and
    must never find the job), publishes no port, restarts never, has no
    healthcheck, and carries none of Compose's labels, which would make
    Compose take it for the service's container.
    """
    job = copy.deepcopy(spec)
    host_config = job.get("HostConfig") or {}
    job["Cmd"] = list(cmd)
    job["User"] = user
    job["Healthcheck"] = {"Test": ["NONE"]}
    job["ExposedPorts"] = None
    job["Labels"] = {
        k: v
        for k, v in (job.get("Labels") or {}).items()
        if not k.startswith(COMPOSE_LABEL_PREFIX)
    }
    job.pop("Hostname", None)
    host_config["PortBindings"] = {}
    host_config["RestartPolicy"] = {"Name": "no"}
    job["HostConfig"] = host_config
    # Nor the address a compose file fixed for the web container, which the
    # job would hold while the web container waits to start.
    endpoints = (job.get("NetworkingConfig") or {}).get("EndpointsConfig") or {}
    for endpoint in endpoints.values():
        endpoint["Aliases"] = None
        endpoint.pop("IPAMConfig", None)
    extra = [
        (
            name,
            {k: v for k, v in endpoint.items() if k != "IPAMConfig"}
            | {"Aliases": None},
        )
        for name, endpoint in extra_networks
    ]
    return job, extra


def connect_network(api, container_id: str, network: str, endpoint: dict) -> None:
    ipam = endpoint.get("IPAMConfig") or {}
    # docker-py takes links as {container: alias}; the Engine reports them
    # as "container:alias" strings.
    links = {
        name: alias or None
        for name, _sep, alias in (
            link.partition(":") for link in endpoint.get("Links") or []
        )
    }
    api.connect_container_to_network(
        container_id,
        network,
        aliases=endpoint.get("Aliases"),
        links=links or None,
        ipv4_address=ipam.get("IPv4Address") or None,
        ipv6_address=ipam.get("IPv6Address") or None,
    )
