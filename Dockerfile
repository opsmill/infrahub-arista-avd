ARG INFRAHUB_BASE_VERSION=1.11.6
FROM registry.opsmill.io/opsmill/infrahub:${INFRAHUB_BASE_VERSION}

# Extend the Python environment shipped by the Infrahub image.
ENV UV_PROJECT_ENVIRONMENT="/.venv"

WORKDIR /opt/local

COPY pyproject.toml uv.lock README.md ./
COPY src/ src/

# --no-dev avoids installing the solution's development SDK over Infrahub's SDK.
# --inexact retains extra packages when syncing a compatible existing environment.
# It cannot retain them if a Python mismatch causes uv to recreate /.venv.
RUN uv sync --no-dev --frozen --inexact

WORKDIR /source
