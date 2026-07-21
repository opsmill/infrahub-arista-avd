# Contract: Infrahub Schema for DCI Links

## Files

- `schemas/dcim_extensions.yml`: extend `DcimDevice.role`; keep the existing
  `NetworkLink` physical endpoint model; add the Network Link DCI role and safe
  DCI-specific fields.
- `schemas/dci.yml`: extend `NetworkFabric` with the DCI pool source and remove
  the stale standalone DCI link schema surface.
- `menus/menu.yml`: remove stale standalone DCI link navigation and keep DCI
  discovery aligned with existing Network Link navigation.

Every new schema file must start with:

```yaml
---
# yaml-language-server: $schema=https://schema.infrahub.app/infrahub/schema/latest.json
version: "1.0"
```

## Device Role Extension

The existing `DcimDevice.role` dropdown must retain all current choices and add:

```yaml
- name: border_leaf
  label: Border Leaf
```

Automation uses the machine value `border_leaf`, not the display label.

## Network Link Role Extension

The existing `NetworkLink` kind must remain the single physical link model. Add
or extend an optional `role` dropdown on `NetworkLink` with:

```yaml
- name: dci
  label: DCI
```

Existing links with no role or non-DCI role values must remain valid and must not
trigger DCI generator behavior.

## Network Link DCI Attributes

`NetworkLink` may directly define only these DCI-specific fields:

| Name | Kind | Contract |
|------|------|----------|
| `role` | `Dropdown` | Optional; `dci` selects DCI generator behavior |
| `include_in_underlay_protocol` | `Boolean` | Safe default `true`; emitted only for DCI-role output |
| `endpoint_1_bgp_asn` | `Number` | Optional in schema, required for eligible DCI generation |
| `endpoint_2_bgp_asn` | `Number` | Optional in schema, required for eligible DCI generation |

The final ASN attribute names may vary if implementation chooses clearer local
style, but the values must remain two typed BGP ASN numbers and must not
introduce new endpoint device/interface fields.

## Prohibited DCI-Specific Fields

`NetworkLink` must not define DCI-specific `enabled`, endpoint device, endpoint
interface, subnet, pool, link ID, endpoint IP, endpoint description, speed, BFD,
MTU, name, description, protocol-selection, external-network, or EVPN Gateway
attributes or relationships.

## Existing Connected Endpoint Behavior

The DCI model must use the existing `NetworkLink.connected_endpoints` behavior.
Generator logic validates exactly two physical interfaces on Border Leaf devices
before emitting PyAVD `l3_edge` intent.

## Fabric DCI Pool

`NetworkFabric` must have an optional relationship to `CoreIPPrefixPool`:

```yaml
extensions:
  nodes:
    - kind: NetworkFabric
      relationships:
        - name: dci_pool
          label: DCI IP Pool
          peer: CoreIPPrefixPool
          kind: Attribute
          cardinality: one
          optional: true
          identifier: fabric__dci_pool
```

Existing fabric objects remain valid because the relationship is optional. The
generator requires it only when valid DCI-role links need `/31` allocation.

## Removal Contract

The previous standalone DCI link kind must be absent from:

- Schema definitions.
- Generated protocol classes.
- Exported GraphQL schema.
- Generated query models.
- Hostvars query and generator logic.
- Menus.
- Documentation.
- Tests.

No committed object-data migration is required unless implementation discovers
repository seed data for the stale kind. Local branch trial data should be
recreated or manually converted to `NetworkLink` objects with `role = dci`.

## Schema Validation Expectations

- `uv run infrahubctl schema check schemas/ --branch <branch>` passes.
- Protocol regeneration no longer produces classes for the stale standalone DCI
  link kind.
- Schema contract tests confirm `NetworkLink.role` supports `dci`.
- Schema contract tests confirm existing Network Link behavior is preserved.
- Schema contract tests confirm only the allowed DCI-specific fields are defined
  directly on `NetworkLink`.
- Existing data with device roles `super_spine`, `spine`, `leaf`, or `l2leaf`
  remains valid.
