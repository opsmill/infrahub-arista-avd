# Schema Design Specification: Migrate AvdArtifact to CoreFileObject

> **This is a schema design spec.** The implementing agent MUST use the `infrahub:schema-creator` skill to build and validate all schema definitions.

**Feature Branch**: `011-avdartifact-file-object`
**Created**: 2026-04-01
**Status**: Draft
**Input**: User description: "I want to migrate the avdartifact to use object files that is new in 1.8."

## Context

The current `AvdArtifact` node manually manages object store references using pairs of Text attributes (`hostvar_identifier` / `hostvar_checksum` and `structured_config_identifier` / `structured_config_checksum`) plus computed URL attributes. Infrahub 1.8 introduced `CoreFileObject`, a built-in generic that provides system-managed file storage with automatic `file_name`, `file_size`, `file_type`, `checksum`, and `storage_id` attributes, plus full version control and branch isolation.

This migration keeps `AvdArtifact` as the central node but replaces its manual object store attributes with two CoreFileObject-based child nodes (`AvdHostvarFile` and `AvdStructuredConfigFile`) owned by the artifact via Component relationships. This preserves the single artifact-per-device model while leveraging Infrahub's native file storage.

## Schema Files

All schema definitions live in `schemas/*.yml`. Each file must start with:

```yaml
---
# yaml-language-server: $schema=https://schema.infrahub.app/infrahub/schema/latest.json
version: "1.0"
```

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add CoreFileObject child nodes to AvdArtifact (Priority: P1)

The AvdArtifact node currently stores hostvars and structured config JSON via manual `*_identifier` and `*_checksum` attributes with explicit `client.object_store` calls. Two new CoreFileObject-based nodes (`AvdHostvarFile` and `AvdStructuredConfigFile`) should be added as Component children of AvdArtifact, using Infrahub's native file management which automatically handles checksums, file metadata, and storage identifiers.

**Why this priority**: This is the foundational schema change. Both file types must exist as children of AvdArtifact before generators and transforms can be updated to use them.

**Independent Test**: After loading the updated schema, an AvdArtifact node can own child file objects that are uploaded via the CoreFileObject API, with Infrahub automatically populating `file_name`, `file_size`, `checksum`, and `storage_id`.

**Acceptance Scenarios**:

1. **Given** the updated schema is loaded, **When** a hostvar JSON file is uploaded as an AvdHostvarFile child of an AvdArtifact, **Then** Infrahub automatically tracks file_name, file_size, file_type, checksum, and storage_id
2. **Given** a structured config file object exists as a child of AvdArtifact, **When** the file content is updated, **Then** Infrahub creates a new version with an updated checksum while preserving the previous version
3. **Given** an AvdArtifact node, **When** viewing it in the UI, **Then** both child file objects are visible and navigable via Component relationships

---

### User Story 2 - Maintain pipeline triggers via file object checksum (Priority: P2)

The backfill generator is currently triggered by changes to `structured_config_checksum` on AvdArtifact. With structured config now stored as a CoreFileObject child node, the trigger mechanism must work via the `checksum` attribute inherited from CoreFileObject on the `AvdStructuredConfigFile` node.

**Why this priority**: Without working triggers, the backfill generator won't fire when structured config is updated, breaking the AVD pipeline automation.

**Independent Test**: Updating the structured config file object's content causes a checksum change that triggers the backfill generator.

**Acceptance Scenarios**:

1. **Given** a structured config file object is updated with new content, **When** the checksum changes, **Then** the backfill generator is triggered
2. **Given** the backfill generator runs, **When** it queries the structured config, **Then** it retrieves file content from the AvdStructuredConfigFile node via the CoreFileObject API

---

### User Story 3 - Clean up deprecated manual attributes (Priority: P3)

The six manual attributes (`hostvar_identifier`, `hostvar_checksum`, `hostvar_url`, `structured_config_identifier`, `structured_config_checksum`, `structured_config_url`) should be removed from AvdArtifact since the CoreFileObject child nodes provide equivalent functionality natively.

**Why this priority**: Cleanup follows the functional migration. Removing dead attributes keeps the schema clean and avoids confusion.

**Independent Test**: After loading the updated schema, AvdArtifact no longer shows the six removed attributes in the UI.

**Acceptance Scenarios**:

1. **Given** the new schema is loaded, **When** viewing AvdArtifact in the UI, **Then** only `name` and `device` remain alongside the new Component relationships to file objects
2. **Given** generators and transforms are updated, **When** the AVD pipeline runs end-to-end, **Then** no code references the removed attributes

---

### Edge Cases

- What happens to existing AvdArtifact nodes that have data in the old `hostvar_identifier` and `structured_config_identifier` attributes during migration?
- How does the schema handle the case where a device has a hostvar file object but no structured config file object yet (pipeline partially complete)?
- What happens if a file upload fails mid-way -- does the file object node exist without a valid storage_id?
- How should the schema behave when the same device needs its file objects regenerated (idempotent upsert)?
- What if the CoreFileObject `checksum` attribute behaves differently from the current manually-computed checksum for trigger purposes?

## Requirements *(mandatory)*

### Functional Requirements

#### Nodes & Generics

- **FR-001**: Schema MUST define two file object node types that inherit from `CoreFileObject`: `AvdHostvarFile` and `AvdStructuredConfigFile`, under the `Avd` namespace
- **FR-002**: The existing `AvdArtifact` node MUST be preserved (not removed) and serve as the parent for the two file object nodes
- **FR-003**: All node names MUST be PascalCase and namespace MUST follow `^[A-Z][a-z0-9]+$` pattern

#### Attributes

- **FR-010**: The `hostvar_identifier`, `hostvar_checksum`, `hostvar_url`, `structured_config_identifier`, `structured_config_checksum`, and `structured_config_url` attributes on AvdArtifact MUST be removed via `state: absent`
- **FR-011**: File object nodes inherit `file_name`, `file_size`, `file_type`, `checksum`, and `storage_id` from CoreFileObject -- these MUST NOT be redefined
- **FR-012**: AvdArtifact MUST retain its `name` attribute (device hostname) and `device` relationship

#### Relationships

- **FR-020**: AvdArtifact MUST have a Component relationship to `AvdHostvarFile` (cardinality one) with identifier `avdartifact__hostvar_file`
- **FR-021**: AvdArtifact MUST have a Component relationship to `AvdStructuredConfigFile` (cardinality one) with identifier `avdartifact__structured_config_file`
- **FR-022**: Each file object node MUST have a Parent relationship back to `AvdArtifact` (cardinality one) with matching identifier
- **FR-023**: The existing `avd_artifact` relationship on DcimDevice and the `device` relationship on AvdArtifact MUST be preserved unchanged

#### Display & Identification

- **FR-040**: Each file object node MUST define `human_friendly_id` using the parent artifact's name (e.g., `["artifact__name__value"]`)
- **FR-041**: Each file object node MUST define `display_label` showing the parent artifact name
- **FR-042**: File object nodes SHOULD use `include_in_menu: false` since they are accessed via the parent AvdArtifact

#### Uniqueness Constraints

- **FR-050**: Each file object node MUST define `uniqueness_constraints` ensuring one file object per artifact (e.g., `[["artifact"]]`)

#### Migration

- **FR-060**: Removed attributes MUST use `state: absent` rather than being deleted from the YAML
- **FR-061**: The migration path MUST ensure existing data can be re-generated by running the AVD generators after schema load (no manual data migration required)
- **FR-062**: The `infrahub-sdk` version MUST be upgraded to `>=1.19.0` to support CoreFileObject API operations (file upload/download via SDK)

### Key Entities

- **AvdArtifact (preserved)**: The existing node, retained as the parent. Keeps `name`, `device` relationship. Gains two Component relationships to file object children. Loses 6 manual object store attributes.
- **AvdHostvarFile**: A CoreFileObject-based node owned by AvdArtifact via Component/Parent relationship. Stores per-device pyAVD hostvars as a JSON file. Replaces the hostvar_identifier/checksum/url attributes.
- **AvdStructuredConfigFile**: A CoreFileObject-based node owned by AvdArtifact via Component/Parent relationship. Stores per-device AVD structured configuration as a JSON file. Replaces the structured_config_identifier/checksum/url attributes. The `checksum` attribute (inherited from CoreFileObject) serves as the trigger for the backfill generator.

## Assumptions

- **CoreFileObject SDK support**: The infrahub-sdk `>=1.19.0` provides methods for file upload/download on CoreFileObject-based nodes, replacing the current `client.object_store.upload()` / `client.object_store.get()` pattern.
- **Checksum trigger compatibility**: The `checksum` attribute inherited from CoreFileObject on `AvdStructuredConfigFile` can be used with `CoreNodeTriggerAttributeMatch` to trigger the backfill generator, similar to how `structured_config_checksum` works today.
- **No manual data migration**: Since all AvdArtifact data is generated by generators, re-running the generators after schema migration will repopulate the file object child nodes. No manual migration of existing object store data is needed.
- **Generator group membership**: AvdArtifact remains in the `avd_artifacts` group for generator targeting. The backfill generator trigger may need to be updated to watch `AvdStructuredConfigFile.checksum` instead of `AvdArtifact.structured_config_checksum`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `infrahubctl schema check schemas/` passes with zero validation errors after loading the updated schema
- **SC-002**: AvdArtifact retains its `name` and `device` relationship and gains navigable Component relationships to child file objects
- **SC-003**: The new file object nodes appear in the Infrahub UI as children of AvdArtifact with CoreFileObject-inherited attributes (file_name, file_size, checksum, etc.)
- **SC-004**: Running the AVD hostvar generator creates AvdHostvarFile child nodes with automatically-managed file metadata
- **SC-005**: Running the AVD structured config generator creates AvdStructuredConfigFile child nodes and the backfill generator is triggered by checksum changes
- **SC-006**: All three AVD transforms (EOS config, fabric doc, device doc) successfully retrieve structured config from the AvdStructuredConfigFile nodes
- **SC-007**: The end-to-end AVD pipeline (hostvar generation -> structured config generation -> backfill -> transforms) completes successfully using the new file object pattern
- **SC-008**: No references to `hostvar_identifier`, `hostvar_checksum`, `structured_config_identifier`, or `structured_config_checksum` remain in generator or transform code
