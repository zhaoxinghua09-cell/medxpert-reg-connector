# MedXpert reg-connector · container image
# Lets MCP hosts (and catalog scanners such as Glama) start the stdio server
# without any Python setup on the host.
#
# Build:  docker build -t medxpert-reg-connector .
# Run:    docker run -i --rm medxpert-reg-connector

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first (best layer caching)
RUN pip install --no-cache-dir "fastmcp>=3.4,<5"

# Server + bundled knowledge base (27 hubs ship inside the package)
COPY medxpert_reg_connector ./medxpert_reg_connector
COPY LICENSE README.md server.json ./

# Read-only by design: no credentials, no network egress at runtime.
# Optional: mount an external knowledge base and point REG_HUB_REFS at it.
ENV REG_HUB_REFS=""

# stdio transport -> must run interactive (-i)
ENTRYPOINT ["python", "-m", "medxpert_reg_connector"]
