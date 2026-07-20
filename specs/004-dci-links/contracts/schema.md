# Contract: Infrahub Schema for DCI Links

## Files

- `schemas/dcim_extensions.yml`: extend `DcimDevice.role`; keep
  `DcimConnector` as the shared physical endpoint behavior used by both ordinary
  links and DCI links.
- `schemas/dci.yml`: define `NetworkDciLink` and extend `NetworkFabric` with
  the DCI pool source.
- `schemas/ipam_extensions.yml`: add a DCI prefix role only if allocated prefixes
  are stored with role metadata.
- `menus/menu.yml`: expose DCI Links navigation.

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

## Shared Connector Behavior

`NetworkLink` currently gets its physical endpoint shape by inheriting
`DcimConnector`. Because Infrahub node `inherit_from` uses generic kinds,
`NetworkDciLink` must inherit the same generic rather than the concrete
`NetworkLink` node:

```yaml
nodes:
  - name: Link
    namespace: Network
    inherit_from:
      - DcimConnector

  - name: DciLink
    namespace: Network
    label: DCI Link
    include_in_menu: false
    inherit_from:
      - DcimConnector
```

The final implementation must preserve the existing `NetworkLink` kind and
physical endpoint behavior.

## `NetworkDciLink` Attributes

`NetworkDciLink` must directly define only these DCI-specific attributes:

| Name | Kind | Contract |
|------|------|----------|
| `include_in_underlay_protocol` | `Boolean` | Default `true` |
| `endpoint_1_bgp_asn` | `Number` | Required for generation |
| `endpoint_2_bgp_asn` | `Number` | Required for generation |

The final ASN attribute names may vary if implementation chooses clearer local
style, but the values must remain two BGP ASN Numbers and must not introduce
new endpoint device/interface fields.

## Prohibited DCI-Specific Fields

`NetworkDciLink` must not define DCI-specific `enabled`, endpoint device,
endpoint interface, subnet, pool, link ID, endpoint IP, endpoint description,
speed, BFD, MTU, protocol-selection, external-network, or EVPN Gateway
attributes or relationships.

## Fabric DCI Pool

`NetworkFabric` must gain an optional relationship to `CoreIPPrefixPool`:

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
generator requires it only when valid DCI links need `/31` allocation.

## Inherited Relationships

The DCI link must use inherited `DcimConnector.connected_endpoints` behavior.
Generator logic validates exactly two physical interfaces on Border Leaf
devices before emitting PyAVD `l3_edge` intent.

## Schema Validation Expectations

- `uv run infrahubctl schema check schemas/ --branch <branch>` passes.
- Protocol regeneration creates `NetworkDciLink` classes.
- Schema contract tests confirm `NetworkDciLink` reuses the same
  `DcimConnector` physical endpoint behavior as `NetworkLink`.
- Schema contract tests confirm only the allowed DCI-specific attributes are
  defined directly on `NetworkDciLink`.
- Existing data with roles `super_spine`, `spine`, `leaf`, or `l2leaf` remains
  valid.
