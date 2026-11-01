"""The web container's readiness probe, asked over the product network.

The framework answers ``/readyz`` (splent_framework 1.22.0 and later) with
200 when the database and the services the product declares answer, and
503 otherwise, before any of the app's own code runs. The agent asks it by
the container's name, so it is the new container that answers, through the
same network nginx reaches it by.

No proxy is ever used: an ``HTTP_PROXY`` in the agent's environment must
not see, or answer, a probe meant for the container next door.
"""

from __future__ import annotations

import urllib.error
import urllib.request

TIMEOUT = 5

_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def probe(url: str, timeout: float = TIMEOUT) -> int | None:
    """The HTTP status ``url`` answers, or None when nothing answers."""
    try:
        with _OPENER.open(url, timeout=timeout) as answer:
            return answer.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except (OSError, ValueError):
        return None
