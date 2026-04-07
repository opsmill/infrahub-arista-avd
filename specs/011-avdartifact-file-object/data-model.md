# Data Model: Migrate AvdArtifact to CoreFileObject

## Entity Relationship Overview

```
DcimDevice (existing, unchanged)
  └── avd_artifact (Attribute, one) ──→ AvdArtifact (existing, modified)
                                          ├── hostvar_file (Component, one) ──→ AvdHostvarFile (new, CoreFileObject)
                                          └── structured_config_file (Component, one) ──→ AvdStructuredConfigFile (new, CoreFileObject)
```

## Entities

### AvdArtifact (modified)

**Kind**: `AvdArtifact`
**Status**: Modified — 6 attributes removed, 2 Component relationships added

| Field | Type | Change | Notes |
|-------|------|--------|-------|
| name | Text | Retained | Device hostname, required |
| device | Relationship → DcimDevice | Retained | Attribute, cardinality one |
| hostvar_file | Relationship → AvdHostvarFile | **Added** | Component, cardinality one, optional |
| structured_config_file | Relationship → AvdStructuredConfigFile | **Added** | Component, cardinality one, optional |
| hostvar_identifier | Text | **Removed** | `state: absent` |
| hostvar_checksum | Text | **Removed** | `state: absent` |
| hostvar_url | URL | **Removed** | `state: absent` |
| structured_config_identifier | Text | **Removed** | `state: absent` |
| structured_config_checksum | Text | **Removed** | `state: absent` |
| structured_config_url | URL | **Removed** | `state: absent` |

### AvdHostvarFile (new)

**Kind**: `AvdHostvarFile`
**Inherits from**: `CoreFileObject`
**Purpose**: Stores per-device pyAVD hostvars as a JSON file

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| file_name | Text | CoreFileObject | Auto-managed, read-only |
| file_size | Number | CoreFileObject | Auto-managed, read-only (bytes) |
| file_type | Text | CoreFileObject | Auto-managed, read-only (MIME) |
| checksum | Text | CoreFileObject | Auto-managed, read-only (SHA-1) |
| storage_id | Text | CoreFileObject | Auto-managed, read-only (UUID) |
| artifact | Relationship → AvdArtifact | Defined | Parent, cardinality one, required |

**Display**: `human_friendly_id: ["artifact__name__value"]`, `display_label: artifact__name__value`
**Uniqueness**: `[["artifact"]]` — one hostvar file per artifact
**Menu**: `include_in_menu: false` — accessed via parent AvdArtifact

### AvdStructuredConfigFile (new)

**Kind**: `AvdStructuredConfigFile`
**Inherits from**: `CoreFileObject`
**Purpose**: Stores per-device AVD structured configuration as a JSON file

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| file_name | Text | CoreFileObject | Auto-managed, read-only |
| file_size | Number | CoreFileObject | Auto-managed, read-only (bytes) |
| file_type | Text | CoreFileObject | Auto-managed, read-only (MIME) |
| checksum | Text | CoreFileObject | Auto-managed, read-only (SHA-1). Trigger source for backfill generator |
| storage_id | Text | CoreFileObject | Auto-managed, read-only (UUID) |
| artifact | Relationship → AvdArtifact | Defined | Parent, cardinality one, required |

**Display**: `human_friendly_id: ["artifact__name__value"]`, `display_label: artifact__name__value`
**Uniqueness**: `[["artifact"]]` — one structured config file per artifact
**Menu**: `include_in_menu: false` — accessed via parent AvdArtifact

## Relationship Identifiers

| Relationship | Identifier | Side A | Side B |
|-------------|-----------|--------|--------|
| Artifact → Hostvar File | `avdartifact__hostvar_file` | Component (AvdArtifact) | Parent (AvdHostvarFile) |
| Artifact → Structured Config File | `avdartifact__structured_config_file` | Component (AvdArtifact) | Parent (AvdStructuredConfigFile) |
| Device → Artifact | `device__avd_artifact` | Existing, unchanged | Existing, unchanged |

## Groups

| Group | Members | Purpose |
|-------|---------|---------|
| `avd_artifacts` | AvdArtifact nodes | Existing — target for hostvar generator |
| `avd_structured_configs` | AvdStructuredConfigFile nodes | **New** — target for backfill generator |

## Trigger Changes

| Trigger | Before | After |
|---------|--------|-------|
| backfill-structured-config | `node_kind: AvdArtifact`, watches `structured_config_checksum` | `node_kind: AvdStructuredConfigFile`, watches `checksum` |

## Generator Target Changes

| Generator | Before | After |
|-----------|--------|-------|
| backfill-structured-config | `targets: avd_artifacts` | `targets: avd_structured_configs` |
| backfill-structured-config query | Rooted on `AvdArtifact(device__name__value)` | Rooted on `AvdStructuredConfigFile(artifact__device__name__value)` |

## Migration Notes

- All 6 removed attributes use `state: absent` in the schema YAML
- No manual data migration — re-running generators repopulates file objects
- The `infrahub-sdk` upgrade from `==1.18.1` to `>=1.19.0` is required
- Protocol classes must be regenerated after schema changes
