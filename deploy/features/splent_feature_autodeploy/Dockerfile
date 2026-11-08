# The autodeploy agent. product:build copies this directory to the product's
# docker/features/splent_feature_autodeploy/ and the deploy compose builds it
# from there.
FROM python:3.13.18-slim-trixie@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# docker-py is the only dependency; the HTTP server is the standard library's.
# Pinned to the release the tests check the agent's calls against.
RUN pip install --no-cache-dir "docker==7.2.0"

WORKDIR /app
COPY autodeploy_agent/ /app/autodeploy_agent/

# Root inside the container, because the Docker socket it is given belongs
# to root on the host. That socket is root on the host whatever user reads
# it, so a non-root user here would buy nothing.
EXPOSE 8080
CMD ["python", "-m", "autodeploy_agent"]
