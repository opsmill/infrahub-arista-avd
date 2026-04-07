# Research: Migrate AvdArtifact to CoreFileObject

## Decision 1: CoreFileObject SDK API Pattern

**Decision**: Use `upload_from_bytes()` and `download_file()` methods on CoreFileObject-based nodes, available in infrahub-sdk >= 1.19.0.

**Rationale**: SDK 1.19.0 (released 2026-03-16) introduced first-class CoreFileObject support. The current 1.18.1 lacks `upload_from_bytes()`, `upload_from_path()`, and `download_file()` methods entirely.

**API Pattern for upload**:
```python
node = await client.create(kind="AvdHostvarFile", ...)
node.upload_from_bytes(content=json.dumps(data).encode(), name="filename.json")
await node.save(allow_upsert=True)
```

**API Pattern for download**:
```python
node = await client.get(kind="AvdStructuredConfigFile", ...)
content: bytes = await node.download_file()
data = json.loads(content)
```

**Alternatives considered**:
- Keep using `client.object_store.upload/get` — rejected because it's a lower-level API that doesn't provide version control, branch isolation, or automatic metadata
- Use `upload_from_path` with temp files — rejected because `upload_from_bytes` avoids filesystem I/O

## Decision 2: Trigger Strategy for Backfill Generator

**Decision**: Retarget the backfill generator to a new group (`avd_structured_configs`) containing `AvdStructuredConfigFile` nodes. The trigger watches `AvdStructuredConfigFile.checksum` changes.

**Rationale**: CoreFileObject automatically manages the `checksum` attribute when file content changes. Using this directly avoids manually copying checksums to the parent AvdArtifact. The trigger `node_kind` aligns with the generator's target group, ensuring only the specific affected file triggers a generator run (not all artifacts).

**Alternatives considered**:
- Option A: Keep a manual checksum attribute on AvdArtifact, copy from child on update — rejected because it defeats the purpose of using CoreFileObject's automatic checksum management and adds unnecessary code
- Option C: Trigger on child, generator targets parent group — rejected because Infrahub can't resolve which specific parent to run for, causing generator to run for all targets

## Decision 3: Object Store vs CoreFileObject Storage

**Decision**: CoreFileObject and `client.object_store` use the same underlying storage backend, but CoreFileObject adds graph-database-managed metadata, versioning, and permissions.

**Key differences**:

| Aspect | `client.object_store` (current) | CoreFileObject (new) |
|--------|-------------------------------|---------------------|
| API endpoint | `/api/storage/object/{id}` | `/api/storage/files/{node_id}` |
| Content type | String only | Binary (bytes, Path) |
| Metadata | Manual (identifier, checksum) | Automatic (file_name, file_size, file_type, checksum, storage_id) |
| Version control | None | Full branch isolation and time-travel |
| Node association | Manual attribute tracking | Part of the node itself |

## Decision 4: AvdArtifact Preservation Strategy

**Decision**: Keep AvdArtifact as the parent node with Component relationships to two CoreFileObject children. Remove the 6 manual object store attributes via `state: absent`.

**Rationale**: Preserves the existing device-to-artifact relationship, the `avd_artifacts` group membership for the hostvar generator, and the single-artifact-per-device model. File objects become owned components of the artifact.

**Alternatives considered**:
- Replace AvdArtifact entirely with two separate file object nodes — rejected per user preference to keep AvdArtifact
- Have AvdArtifact itself inherit from CoreFileObject — rejected because it can only store one file, and we need two (hostvars + structured config)

## Decision 5: Backfill Generator Query Restructure

**Decision**: The backfill generator's GQL query must be rerooted on `AvdStructuredConfigFile` instead of `AvdArtifact`, traversing up to the parent artifact and device.

**Rationale**: Since the generator now targets `AvdStructuredConfigFile` nodes (for trigger alignment), the query must start from the file object. The parameter changes from `device_hostname: device__name__value` to `device_hostname: artifact__device__name__value` (traversing through the parent).

## Decision 6: SDK Version Upgrade

**Decision**: Upgrade infrahub-sdk from `==1.18.1` to `>=1.19.0` in pyproject.toml.

**Rationale**: CoreFileObject support requires 1.19.0+. This is a minor version bump with no known breaking changes for the APIs used in this project.

**Risk**: The `ariadne-codegen` override in `[tool.uv]` must be preserved as it's required by infrahub-sdk's pinning constraints.
