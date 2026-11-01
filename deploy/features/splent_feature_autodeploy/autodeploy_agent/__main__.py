"""``python -m autodeploy_agent``: the agent's process.

Reads its settings from the environment, connects to the Docker Engine
through the mounted socket, starts the check loop and serves the API until
the container is stopped. A deploy cut short by the stop is finished or
undone by the next start (see Deployer._recover).
"""

from __future__ import annotations

import logging
import signal
import sys

from autodeploy_agent import __version__
from autodeploy_agent.api import Api, make_server
from autodeploy_agent.config import AgentConfig
from autodeploy_agent.deployer import Deployer, Scheduler
from autodeploy_agent.state import StateStore

logger = logging.getLogger("autodeploy")

#: Seconds docker-py waits on the Engine. A dump streams for as long as the
#: database takes to read, so this is generous.
DOCKER_TIMEOUT = 600


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )
    config = AgentConfig.from_env()
    logger.info(
        "autodeploy agent %s following %s for %s",
        __version__,
        config.image or "(no image)",
        config.web_container or "(no web container)",
    )
    for problem in config.problems:
        logger.error("Not configured: %s", problem)

    import docker  # only here, so the package imports without the SDK

    client = docker.from_env(timeout=DOCKER_TIMEOUT)
    store = StateStore(config.data_dir)
    deployer = Deployer(client.api, config, store)
    scheduler = Scheduler(deployer, config.interval)
    server = make_server(
        Api(deployer, config.secret, scheduler.trigger), port=config.port
    )

    def stop(_signum, _frame):
        if deployer.busy:
            logger.warning(
                "Stopping in the middle of a deploy; the next start finishes or undoes it"
            )
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    scheduler.start()
    logger.info("API listening on port %s", config.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.stop()
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
