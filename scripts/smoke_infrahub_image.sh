#!/usr/bin/env bash
# Check a candidate Infrahub image against the Infrahub image it extends, without
# Compose, a live Infrahub or network access.
#
#   smoke_infrahub_image.sh IMAGE [BASE_IMAGE] [USER]
#
# BASE_IMAGE defaults to the Community image of the Dockerfile's INFRAHUB_BASE_VERSION.
# USER, when given, is the user the candidate image must run as (root for Community,
# infrahub for Enterprise).
set -euo pipefail

infrahub_image=${1:?Pass the candidate Infrahub image}
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# The reference image is the one the Dockerfile extends, so a version bump that
# edits the Dockerfile ARG moves both sides of the comparison together.
base_version=$(sed -n 's/^ARG INFRAHUB_BASE_VERSION=//p' "$repo_root/Dockerfile")
base_image=${2:-registry.opsmill.io/opsmill/infrahub:${base_version:?No ARG INFRAHUB_BASE_VERSION default in Dockerfile}}
expected_user=${3:-}

if [[ -n "$expected_user" ]]; then
  found_user=$(docker run --rm --network none --entrypoint id "$infrahub_image" -un)
  if [[ "$found_user" != "$expected_user" ]]; then
    echo "The image runs as '$found_user', expected '$expected_user'." >&2
    exit 1
  fi
fi

# Check the Python selected by the image's PATH, as used by its entry points.
base_identity=$(docker run --rm --network none --entrypoint python "$base_image" -c '
import importlib.metadata as metadata
import infrahub_sdk
import json
import platform
print(json.dumps({"python": platform.python_version(), "infrahub-server": metadata.version("infrahub-server"), "infrahub-sdk": infrahub_sdk.__version__}))
')

docker run --rm --network none --entrypoint python \
  -e "EXPECTED_BASE_IDENTITY=$base_identity" "$infrahub_image" -c '
import importlib
import importlib.metadata as metadata
import infrahub_sdk
import json
import os
import platform

# The image extends /.venv from the base image, so both must run the same Python.
expected = json.loads(os.environ["EXPECTED_BASE_IDENTITY"])
found = {"python": platform.python_version(), "infrahub-server": metadata.version("infrahub-server"), "infrahub-sdk": infrahub_sdk.__version__}
assert found == expected, f"image versions {found} differ from base image {expected}"
assert metadata.version("pyavd") == "6.4.0"
for name in ("infrahub", "infrahub.prefect_server.app", "infrahub.server", "infrahub.workers.infrahub_async", "pyavd", "solution_arista_avd"):
    importlib.import_module(name)
print("Infrahub entry points and inherited packages OK:", expected)
'
docker run --rm --network none --entrypoint uv "$infrahub_image" pip check --python /.venv/bin/python
