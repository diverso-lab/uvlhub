"""
Configuration for uvlhub.

Each class extends the framework's base configuration. Only override
what your product needs — everything else is inherited automatically.

Hierarchy (later layers win):
  1. Framework defaults (Config base class)
  2. This file (product config)
  3. Feature inject_config() calls
"""

import logging
import os
import re

from splent_framework.configuration.default_config import (
    DevelopmentConfig as BaseDev,
    TestingConfig as BaseTest,
    ProductionConfig as BaseProd,
)

logger = logging.getLogger(__name__)


class DevelopmentConfig(BaseDev):
    # Add product-specific dev settings here.
    # Example: EXPLAIN_TEMPLATE_LOADING = True
    pass


class TestingConfig(BaseTest):
    # Add product-specific test settings here.
    # Example: PRESERVE_CONTEXT_ON_EXCEPTION = False
    pass


def canonical_host(environ=os.environ) -> dict:
    """SERVER_NAME and TRUSTED_HOSTS for the public host, from the deployment.

    uvlhub answers by one name, SERVER_NAME (www.uvlhub.io). nginx refuses
    every other Host and redirects the site's other names to it
    (NGINX_REDIRECT_SERVER_NAMES), and the app checks again: a request whose
    Host is not in TRUSTED_HOSTS gets a 400 and no page, whatever stands in
    front. Flask builds every absolute link with SERVER_NAME, inside a
    request too, so a mail or a callback never names another host. Since
    Flask 3.1 SERVER_NAME no longer limits which hosts are routed; that is
    TRUSTED_HOSTS' job.

    TRUSTED_HOSTS, separated by spaces or commas, defaults to SERVER_NAME and
    localhost, the name the deploy's own probe uses inside the container
    (nginx never lets it through from outside). The probes, /healthz and
    /readyz, are answered before Flask and take any Host.
    """
    server_name = (environ.get("SERVER_NAME") or "").strip()
    if not server_name or server_name == "<SET>":
        return {}
    trusted = [
        host for host in re.split(r"[\s,]+", environ.get("TRUSTED_HOSTS") or "") if host
    ]
    return {
        "SERVER_NAME": server_name,
        "TRUSTED_HOSTS": trusted or [server_name, "localhost"],
    }


class ProductionConfig(BaseProd):
    def __init__(self):
        super().__init__()
        host = canonical_host()
        if not host:
            logger.warning(
                "SERVER_NAME is not set: the app answers to any Host nginx lets "
                "through and builds links from it. Set it to the public host."
            )
        for key, value in host.items():
            setattr(self, key, value)
