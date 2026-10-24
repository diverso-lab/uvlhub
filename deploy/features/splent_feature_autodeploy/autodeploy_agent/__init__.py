"""The autodeploy agent of splent_feature_autodeploy.

It follows a registry image channel (``<registry>/<org>/<product>:stable``,
which only moves when someone runs ``splent product:release``) and, when the
channel points to a new image, replaces the product's web container with one
built from it: database backup first, health check after, and an automatic
rollback (container and database) when the new image does not come up.

The package runs as ``python -m autodeploy_agent`` in its own container. It
talks to the Docker Engine through docker-py's low level client, which it is
handed rather than builds, so every path can be tested against a fake.
"""

__version__ = "0.1.0"
