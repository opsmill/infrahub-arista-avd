# Quickstart: Migrate AvdArtifact to CoreFileObject

## Prerequisites

- Infrahub instance running (`inv start`)
- Python >= 3.11
- `uv sync --all-packages` after SDK upgrade

## Migration Steps

1. **Upgrade SDK**: Update `pyproject.toml` to `infrahub-sdk>=1.19.0`, run `uv sync`
2. **Update schema**: Add `AvdHostvarFile` and `AvdStructuredConfigFile` nodes to `schemas/objects/objects.yml`, mark old attributes `state: absent`
3. **Load schema**: `inv load-schema`
4. **Regenerate protocols**: `infrahubctl protocols --output src/solution_arista_avd/protocols.py`
5. **Update generators**: Replace `client.object_store.upload()` with `upload_from_bytes()` on file object nodes
6. **Update transforms**: Replace `client.object_store.get()` with `download_file()` on file object nodes
7. **Update backfill generator**: Retarget to `avd_structured_configs` group, update GQL query
8. **Update trigger**: Watch `AvdStructuredConfigFile.checksum` instead of `AvdArtifact.structured_config_checksum`
9. **Create group**: Add `avd_structured_configs` group in object data files
10. **Run tests**: `pytest tests/unit && inv lint`

## Verification

```bash
# Schema validation
infrahubctl schema check schemas/

# Run generators end-to-end
# (via Infrahub UI or API — trigger fabric generator, verify file objects created)

# Run all tests
pytest tests/
```
