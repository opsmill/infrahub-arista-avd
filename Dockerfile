# The base image is Infrahub Community by default. The public sandbox runs Infrahub Enterprise, so
# .github/workflows/publish-images.yml also builds this file with
# INFRAHUB_BASE_IMAGE=registry.opsmill.io/opsmill/infrahub-enterprise and INFRAHUB_IMAGE_USER=infrahub.
ARG INFRAHUB_BASE_IMAGE=registry.opsmill.io/opsmill/infrahub
ARG INFRAHUB_BASE_VERSION=1.12.2
FROM ${INFRAHUB_BASE_IMAGE}:${INFRAHUB_BASE_VERSION}

# The user the image runs as: root for Community, infrahub for Enterprise, as in each base image.
ARG INFRAHUB_IMAGE_USER=root

# Extend the Python environment shipped by the Infrahub image.
ENV UV_PROJECT_ENVIRONMENT="/.venv"

# Installing into /.venv needs root; the image switches back to its own user below.
USER root

WORKDIR /opt/local

COPY pyproject.toml uv.lock README.md ./
COPY src/ src/

# --no-dev avoids installing the solution's development SDK over Infrahub's SDK.
# --inexact retains extra packages when syncing a compatible existing environment.
# It cannot retain them if a Python mismatch causes uv to recreate /.venv.
RUN uv sync --no-dev --frozen --inexact

USER ${INFRAHUB_IMAGE_USER}

WORKDIR /source
