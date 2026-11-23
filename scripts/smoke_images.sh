#!/usr/bin/env bash
# Validate images without Compose, live Infrahub, or network device access.
set -euo pipefail

infrahub_image=${1:?Pass the candidate Infrahub image}
catalog_image=${2:?Pass the candidate service-portal image}
semaphore_image=${3:?Pass the candidate Semaphore image}
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# The reference image is the one the Dockerfile extends, so a version bump that
# edits the Dockerfile ARG moves both sides of the comparison together.
base_version=$(sed -n 's/^ARG INFRAHUB_BASE_VERSION=//p' "$repo_root/Dockerfile")
base_image=${4:-registry.opsmill.io/opsmill/infrahub:${base_version:?No ARG INFRAHUB_BASE_VERSION default in Dockerfile}}
catalog_container=
trap 'if [[ -n "$catalog_container" ]]; then docker rm -f "$catalog_container" >/dev/null; fi' EXIT

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
assert {"python": platform.python_version(), "infrahub-server": metadata.version("infrahub-server"), "infrahub-sdk": infrahub_sdk.__version__} == expected
assert metadata.version("pyavd") == "6.4.0"
for name in ("infrahub", "infrahub.prefect_server.app", "infrahub.server", "infrahub.workers.infrahub_async", "pyavd", "solution_arista_avd"):
    importlib.import_module(name)
print("Infrahub entry points and inherited packages OK:", expected)
'
docker run --rm --network none --entrypoint uv "$infrahub_image" pip check --python /.venv/bin/python

catalog_container=$(docker run -d --network none "$catalog_image")
catalog_ready=false
for ((attempt=0; attempt<45; attempt++)); do
  if docker exec "$catalog_container" /app/.venv/bin/python -c \
    'import urllib.request; urllib.request.urlopen("http://localhost:8501/_stcore/health", timeout=2)' >/dev/null 2>&1; then
    catalog_ready=true
    break
  fi
  sleep 1
done
if [[ "$catalog_ready" != true ]]; then
  docker logs "$catalog_container"
  exit 1
fi
docker exec "$catalog_container" /app/.venv/bin/python -c \
  'import sys, streamlit, infrahub_sdk; assert sys.version_info[:3] == (3, 14, 7); print("Service portal health and imports OK")'
docker exec "$catalog_container" uv pip check --python /app/.venv/bin/python

docker run --rm --network none --entrypoint /bin/sh \
  -e PYTHONDONTWRITEBYTECODE=1 -v "$repo_root:/workspace:ro" -w /workspace "$semaphore_image" -c '
set -eu
python3 -c '\''import importlib.metadata as m; assert m.version("pyavd") == "6.4.0"; assert m.version("ansible-core") == "2.19.13"'\''
pip3 check
ansible-galaxy collection list --format json | python3 -c '\''
import json, sys
collections = json.load(sys.stdin)
assert any(items.get("arista.avd", {}).get("version") == "6.4.0" for items in collections.values())
print("Semaphore AVD package and collection alignment OK")
'\''
ansible-playbook --syntax-check -i localhost, -e fabric_name=smoke ansible/deploy.yml ansible/test.yml
'
