# Data Model: EVPN Gateway Domains

## Entity: EvpnDomain

**Kind**: `EvpnDomain`

**Purpose**: Represents one named EVPN Domain inside a Fabric. A domain may be assigned to Pods, own local EVPN Gateway Group children, and be referenced by gateway groups as a remote exchange domain.

**Fields**:

| Field | Kind | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | Text | Yes | None | Human-readable domain name, unique within the Fabric. |
| `domain_id` | Text | Yes | None | EVPN D-PATH domain ID in ASN(asplain):local_admin or ASN(asdot):local_admin notation, for example `65100:1`. Use `parameters.regex`, not deprecated top-level regex, if schema validation is added. |
| `description` | Text | No | None | Optional operator note. |

**Relationships**:

| Name | Peer | Cardinality | Kind | Required | Identifier | Notes |
|------|------|-------------|------|----------|------------|-------|
| `fabric` | `NetworkFabric` | one | Parent | Yes | `fabric__evpn_domains` | Fabric that owns the domain. |
| `pods` | `NetworkPod` | many | Attribute | No | `evpn_domain__pods` | Pods assigned to this EVPN Domain. |
| `local_gateway_groups` | `EvpnGatewayGroup` | many | Component | No | `evpn_domain__local_gateway_groups` | Gateway groups owned by this local domain. |
| `remote_gateway_groups` | `EvpnGatewayGroup` | many | Attribute | No | `evpn_gateway_group__remote_domain` | Gateway groups that use this domain as their remote exchange domain. |

**Display and identity**:

- `label`: `EVPN Domain`
- `include_in_menu: false`
- `human_friendly_id`: `fabric__name__value`, `domain_id__value`
- `display_label`: include Fabric name, domain name, and domain ID.
- `order_by`: `fabric__name__value`, `domain_id__value`, `name__value`

**Uniqueness**:

- `[fabric, domain_id__value]`
- `[fabric, name__value]`

## Entity: EvpnGatewayGroup

**Kind**: `EvpnGatewayGroup`

**Purpose**: Represents one group of Border Leaf devices acting as EVPN Gateways. The group local domain is its parent `EvpnDomain` through `local_domain`; the group also selects one Pod as non-owning context and one distinct remote EVPN Domain for inter-domain exchange.

**Fields**:

| Field | Kind | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | Text | Yes | None | Gateway group name, unique within the selected Pod and local EVPN Domain. |
| `resiliency_model` | Dropdown | Yes | `all_active_multihoming` | Only actionable value in this phase. |
| `evpn_l2_enabled` | Boolean | Yes | `true` | Maps to pyAVD `evpn_gateway.evpn_l2.enabled`. |
| `evpn_l3_enabled` | Boolean | Yes | `true` | Maps to pyAVD `evpn_gateway.evpn_l3.enabled`. |
| `evpn_l3_inter_domain` | Boolean | Yes | `true` | Maps to pyAVD `evpn_gateway.evpn_l3.inter_domain`. |
| `d_path_enabled` | Boolean | Yes | `true` | Maps to pyAVD `evpn_gateway.d_path.enabled`. |
| `all_active_multihoming_enabled` | Boolean | Yes | `true` | Maps to pyAVD `evpn_gateway.all_active_multihoming.enabled`. |
| `ethernet_segment_identifier` | Text | Yes | None | EVPN Ethernet Segment Identifier, Type 1 format. |
| `ethernet_segment_rt_import` | Text | Yes | None | Low-order 6 bytes of the ES-Import route target. |
| `description` | Text | No | None | Optional operator note. |

**Dropdown choices**:

```yaml
choices:
  - name: all_active_multihoming
    label: All-Active Multihoming
```

No `mlag`, `anycast_ip`, route-server, or route-reflector choice is allowed in this phase.

**Relationships**:

| Name | Peer | Cardinality | Kind | Required | Identifier | Notes |
|------|------|-------------|------|----------|------------|-------|
| `local_domain` | `EvpnDomain` | one | Parent | Yes | `evpn_domain__local_gateway_groups` | Parent EVPN Domain that owns the group. |
| `pod` | `NetworkPod` | one | Attribute | Yes | `pod__evpn_gateway_groups` | Selected Pod context. Its `evpn_domain` must match `local_domain`. |
| `remote_domain` | `EvpnDomain` | one | Attribute | Yes | `evpn_gateway_group__remote_domain` | Remote EVPN Domain for inter-domain exchange. Must differ from `local_domain`. |
| `members` | `DcimDevice` | many | Attribute | Yes | `evpn_gateway_group__members` | Border Leaf member devices. Schema should require the relationship; generator validation reports empty groups if non-empty many relationships cannot be fully enforced. |

**Display and identity**:

- `label`: `EVPN Gateway Group`
- `include_in_menu: false`
- `human_friendly_id`: `pod__name__value`, `name__value`. Infrahub rejects local-domain peer attributes here because `EvpnDomain` identifiers are unique per Fabric rather than globally unique.
- `display_label`: include local EVPN Domain, selected Pod, remote EVPN Domain, and group name.
- `order_by`: `local_domain__domain_id__value`, `pod__name__value`, `remote_domain__domain_id__value`, `name__value`
- Do not add computed or denormalized helper attributes solely to show local-domain data.

**Uniqueness**:

- `[local_domain, pod, name__value]`

## Extension: NetworkFabric

**Kind**: `NetworkFabric`

**Added relationship**:

| Name | Peer | Cardinality | Kind | Required | Identifier | Notes |
|------|------|-------------|------|----------|------------|-------|
| `evpn_domains` | `EvpnDomain` | many | Component | No | `fabric__evpn_domains` | Domains owned by the Fabric. |

The extension is additive and optional for existing Fabric objects.

## Extension: NetworkPod

**Kind**: `NetworkPod`

**Added relationships**:

| Name | Peer | Cardinality | Kind | Required | Identifier | Notes |
|------|------|-------------|------|----------|------------|-------|
| `evpn_domain` | `EvpnDomain` | one | Attribute | No | `evpn_domain__pods` | EVPN Domain assigned to the Pod. |
| `evpn_gateway_groups` | `EvpnGatewayGroup` | many | Attribute | No | `pod__evpn_gateway_groups` | Non-owning inverse for gateway groups that select this Pod as context. |

Both extensions are additive and optional for existing Pod objects. `NetworkPod.evpn_gateway_groups` must not be `Component` in this model.

## Extension: DcimDevice

**Kind**: `DcimDevice`

**Added relationship**:

| Name | Peer | Cardinality | Kind | Required | Identifier | Notes |
|------|------|-------------|------|----------|------------|-------|
| `evpn_gateway_group` | `EvpnGatewayGroup` | one | Attribute | No | `evpn_gateway_group__members` | Inverse group membership. A device can belong to at most one gateway group in this phase. |

The extension is additive and optional for existing device objects.

## Derived pyAVD Hostvar Values

Only target devices with role `border_leaf` and membership in one valid `EvpnGatewayGroup` emit the gateway payload.

| pyAVD value | Source |
|-------------|--------|
| `l3leaf.nodes[].evpn_gateway.evpn_l2.enabled` | `EvpnGatewayGroup.evpn_l2_enabled` |
| `l3leaf.nodes[].evpn_gateway.evpn_l3.enabled` | `EvpnGatewayGroup.evpn_l3_enabled` |
| `l3leaf.nodes[].evpn_gateway.evpn_l3.inter_domain` | `EvpnGatewayGroup.evpn_l3_inter_domain` |
| `l3leaf.nodes[].evpn_gateway.d_path.enabled` | `EvpnGatewayGroup.d_path_enabled` |
| `l3leaf.nodes[].evpn_gateway.d_path.local_domain_id` | `EvpnGatewayGroup.local_domain.domain_id` |
| `l3leaf.nodes[].evpn_gateway.d_path.remote_domain_id` | `EvpnGatewayGroup.remote_domain.domain_id` |
| `l3leaf.nodes[].evpn_gateway.all_active_multihoming.enabled` | `EvpnGatewayGroup.all_active_multihoming_enabled` |
| `l3leaf.nodes[].evpn_gateway.all_active_multihoming.evpn_ethernet_segment.identifier` | `EvpnGatewayGroup.ethernet_segment_identifier` |
| `l3leaf.nodes[].evpn_gateway.all_active_multihoming.evpn_ethernet_segment.rt_import` | `EvpnGatewayGroup.ethernet_segment_rt_import` |
| `l3leaf.nodes[].evpn_gateway.remote_peers[].hostname` | Hostnames of other valid `border_leaf` members in gateway groups that share the same `remote_domain`, sorted deterministically and excluding the target device. |

Do not emit deprecated pyAVD 6.3.0 keys `all_active_multihoming.enable_d_path`, `all_active_multihoming.evpn_domain_id_local`, or `all_active_multihoming.evpn_domain_id_remote` in new hostvars.

Peer entries remain hostname-only in this phase. The structured-config generator must aggregate every fabric device's stored hostvars before calling pyAVD so `get_avd_facts()` can resolve remote peer facts from the named gateway devices. If a remote peer hostname cannot be resolved from generated hostvars, structured-config generation must fail with an actionable error instead of relying on manually modeled peer IP or BGP ASN fields.

## Validation Rules

Schema-level validation:

- `EvpnDomain.name` and `EvpnDomain.domain_id` are required `Text` attributes.
- `EvpnDomain.domain_id` is unique per `fabric`.
- `EvpnDomain.name` is unique per `fabric`.
- `NetworkPod.evpn_domain` is cardinality one and optional.
- `EvpnDomain.local_gateway_groups` is the Component side of `EvpnGatewayGroup.local_domain`.
- `EvpnGatewayGroup.local_domain` is the only Parent relationship on the group and has `cardinality: one` plus `optional: false`.
- `EvpnGatewayGroup.pod` and `EvpnGatewayGroup.remote_domain` are required cardinality-one Attribute relationships.
- `EvpnGatewayGroup.name` is unique per `local_domain` and `pod`.
- `EvpnGatewayGroup.resiliency_model` has only `all_active_multihoming`.
- `EvpnGatewayGroup.members` is cardinality many and should be required.
- `DcimDevice.evpn_gateway_group` relates to at most one `EvpnGatewayGroup`.
- All bidirectional relationships use matching `identifier` values.
- All relationship peers use full schema kinds.
- `EvpnDomain` and `EvpnGatewayGroup` set `include_in_menu: false`.
- No `EvpnGateway` node is defined.

Generator-time validation:

- The target device role is `border_leaf` before gateway hostvars are emitted.
- The target device belongs to exactly one gateway group if gateway hostvars are emitted.
- The target device is present in the gateway group's `members`.
- The gateway group has a parent `local_domain`.
- The gateway group has one selected Pod.
- The selected Pod has one `evpn_domain`.
- `EvpnGatewayGroup.pod.evpn_domain` matches `EvpnGatewayGroup.local_domain`.
- `EvpnGatewayGroup.remote_domain` is present and differs from `EvpnGatewayGroup.local_domain`.
- The local and remote domains belong to the expected Fabric context.
- The group has one or more member devices.
- Every member device has role `border_leaf`.
- Every member device belongs to the group's selected Pod.
- No member device belongs to more than one gateway group.
- Route-server and route-reflector remote-domain behavior is not modeled or accepted.
- Peer derivation is deterministic and does not include the target device.
- Hostname-only remote peers resolve during the fabric-wide structured-config run after all gateway member hostvars exist.
- Non-`border_leaf` target devices never receive `evpn_gateway` hostvars.
- Border Leafs not in a gateway group continue to generate existing Border Leaf hostvars without EVPN Gateway-specific fields.
- Invalid gateway data raises an actionable generator error before the target device's `AvdHostvarFile` is written.
- The final hostvars pass `pyavd.validate_inputs()` before storage.

## State Transitions

| State | Condition | Allowed Next State |
|-------|-----------|--------------------|
| Non-gateway Border Leaf | Device role is `border_leaf` and `evpn_gateway_group` is empty | Gateway member after the device is added to one valid group. |
| Gateway group member | Device role is `border_leaf`, belongs to one valid group, group has matching `local_domain` and selected Pod `evpn_domain` | Non-gateway after removal from the group; invalid if role, Pod, or group data changes. |
| Invalid for generation | Generator sees missing parent local domain, missing Pod domain, Pod/local mismatch, same local/remote domain, non-Border Leaf member, cross-Pod member, or pyAVD-invalid data | Correct schema/object data before hostvar generation. |
| Remote-domain singleton | Group remote domain is not shared by any other valid group | Valid model state; generated peer list is empty unless later groups share that remote domain. |
