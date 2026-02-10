# Implementation Plan: Server Cabling Service

**Branch**: `004-server-cabling-service` | **Date**: 2026-02-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-server-cabling-service/spec.md`

## Summary

Implement a generator that automatically cables servers to leaf switches in the same rack and assigns VLANs from interface profiles. When a `ComputePhysicalServer` is created or updated, the generator finds leaf switches in the same rack, identifies available server-role interfaces, creates `NetworkLink` connections, and copies VLAN assignments from server interface profiles to the leaf-side ports. The feature also includes server object templates and server-specific interface profiles with VLAN definitions.

## Technical Context

**Language/Version**: Python >=3.11, <3.14
**Primary Dependencies**: infrahub-sdk==1.18.1
**Storage**: Infrahub (Neo4j-backed)
**Testing**: pytest (unit tests with AsyncMock)
**Target Platform**: Infrahub generator runtime
**Project Type**: Single project (existing codebase extension)
**Constraints**: Generator must be idempotent; server must already exist in a rack with provisioned leaf switches

## Project Structure

### Documentation (this feature)

```text
specs/004-server-cabling-service/
├── plan.md              # This file
├── spec.md              # Feature specification
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Task list (generated next)
```

### Source Code (files to create/modify)

```text
# Schema changes
schemas/compute/compute.yml              # Add generate_template: true, inherit GeneratorTarget

# Seed data
objects/05_profiles.yml                  # Add server interface profiles with VLANs
objects/08_server_templates.yml          # NEW: Server object templates (compute-1nic, compute-2nic, gpu-1nic)
objects/01_groups.yml                    # Add "servers" group for generator targets

# Generator
generators/generate_server_cabling.py   # NEW: ServerCablingGenerator class
generators/generate_server_cabling.gql  # NEW: GraphQL query for ComputePhysicalServer

# Configuration
.infrahub.yml                           # Register new generator + query

# Tests
tests/unit/test_server_cabling.py       # NEW: Unit tests for the generator
```

**Structure Decision**: Follow existing generator patterns (RackGenerator, BackfillStructuredConfigGenerator). New generator file + GQL query + seed data. Schema extensions for template support and VLAN profiles.

## Implementation Approach

### 1. Schema Changes

**`ComputePhysicalServer` modifications** (`schemas/compute/compute.yml`):
- Add `generate_template: true` to enable object template support (creates `TemplateComputePhysicalServer`)
- Add `GeneratorTarget` to `inherit_from` list for checksum-based change detection
- The `interfaces` relationship is already inherited from `NetworkGenericDevice`

**Profile VLAN relationships**: Already exist via `vlan/vlan.yml` extensions on `NetworkInterface`. The `ProfileNetworkInterface` and `TemplateNetworkInterface` both automatically get `tagged_vlan` and `untagged_vlan` relationships from the extension. Profiles in seed data just need to reference VLANs.

### 2. Seed Data

**Server Interface Profiles** (extend `objects/05_profiles.yml`):
- `profile-server-compute`: role=server, mtu=9000, tagged_vlan=[Servers, Storage]
- `profile-server-gpu`: role=server, mtu=9000, tagged_vlan=[Servers, Storage, Backup]

**Server Object Templates** (new `objects/08_server_templates.yml`):
- `compute-server-single`: role=compute, 1x Ethernet interface with `profile-server-compute`
- `compute-server-dual`: role=compute, 2x Ethernet interfaces with `profile-server-compute`
- `gpu-server-single`: role=gpu, 1x Ethernet interface with `profile-server-gpu`

**Groups** (extend `objects/01_groups.yml`):
- Add `servers` CoreStandardGroup for generator targeting

### 3. Generator Design

**Query** (`generators/generate_server_cabling.gql`):
- Root: `ComputePhysicalServer` filtered by `server_name` parameter
- Fetch: server hostname, role, status, rack (with devices and their interfaces), server interfaces with profiles

**Generator class** (`generators/generate_server_cabling.py`):

```
class ServerCablingGenerator(InfrahubGenerator):

    generate(data):
        1. Parse query response for the target server
        2. Get server interfaces (skip already-linked ones for idempotency)
        3. Find leaf switches in the same rack
        4. Get available (unlinked) server/storage-role interfaces on leaves
        5. Validate sufficient interfaces are available
        6. Distribute server interfaces across leaves (round-robin)
        7. Create NetworkLinks between paired interfaces
        8. Copy VLANs from server interface profiles to leaf-side interfaces
        9. Set all connected interfaces to "active" status
```

**Key design decisions**:
- **Idempotency**: Skip server interfaces that already have a link (check `link` relationship). Use `allow_upsert=True` for link creation with HFID-based deduplication.
- **Round-robin distribution**: For dual-homed servers with 2+ leaves, alternate interfaces across leaves. For single-leaf racks, connect all to the single leaf.
- **VLAN copy**: Read `tagged_vlan` and `untagged_vlan` from the server interface's profile, then assign those same VLANs to the corresponding leaf interface.
- **Interface availability**: Filter leaf interfaces by role (server/storage) and exclude those with existing links.
- **Link naming**: Follow existing pattern: `{server_hostname}-{server_iface}__{leaf_hostname}-{leaf_iface}`
- **Medium**: Default to `copper` for server-to-leaf connections.

### 4. Registration

Add to `.infrahub.yml`:
- New query: `generate_server_cabling` pointing to GQL file
- New generator definition: `generate-server-cabling` with target group `servers`, parameter `server_name: hostname__value`

### 5. Protocol Regeneration

After schema changes, `ComputePhysicalServer` will gain `GeneratorTarget` inheritance (adding `checksum` attribute) and `generate_template: true` will create `TemplateComputePhysicalServer`. Protocols need regeneration but this requires a running Infrahub instance. For unit testing purposes, use mock objects.

### 6. Testing Strategy

Unit tests following existing patterns from `test_backfill_structured_config.py`:
- Mock `InfrahubClient` with `AsyncMock`
- Test single-homed cabling (1 server interface → 1 leaf interface)
- Test dual-homed cabling (2 server interfaces → 2 different leaf interfaces)
- Test VLAN assignment from profiles to leaf interfaces
- Test idempotency (already-linked interfaces skipped)
- Test edge cases: no leaves in rack, no available interfaces, single leaf with dual-homed server
- Test round-robin distribution across leaves
