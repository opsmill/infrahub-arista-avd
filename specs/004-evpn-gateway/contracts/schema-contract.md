# Schema Contract: EVPN Gateway Domains

## Scope

This contract defines the Infrahub schema interface for EVPN Domain and EVPN Gateway Group intent. It is consumed by object data, the per-device hostvar generator query, custom menu configuration, protocol generation, and documentation.

## File Contract

Update the schema file under `schemas/evpn/`:

```text
schemas/evpn/evpn_gateway.yml
```

The file must start with:

```yaml
---
# yaml-language-server: $schema=https://schema.infrahub.app/infrahub/schema/latest.json
version: "1.0"
```

Relationships added to existing nodes must use `extensions.nodes` with matching relationship identifiers.

## Dependency Contract

The implementation must reuse the `border_leaf` device role:

- `DcimDevice.role` includes `border_leaf` with label `Border Leaf`.
- `ROLE_TO_AVD_TYPE["border_leaf"] == "l3leaf"`.
- Hostvar code treats `border_leaf` as part of the L3 leaf family for uplinks, tenants, and gateway generation.

Do not model gateway behavior on regular `leaf` as a substitute.

## Kind Contract

The implementation must expose these concrete kinds:

| Kind | Namespace | Include In Menu | Purpose |
|------|-----------|-----------------|---------|
| `EvpnDomain` | `Evpn` | `false` | EVPN Domain owned by one Fabric. |
| `EvpnGatewayGroup` | `Evpn` | `false` | Shared EVPN Gateway configuration and member Border Leaf group owned by one local domain. |

No new generic is required for this cycle. The schema must not define `EvpnGateway`.

## Relationship Contract

| Source | Relationship | Peer | Cardinality | Required | Kind | Identifier |
|--------|--------------|------|-------------|----------|------|------------|
| `NetworkFabric` | `evpn_domains` | `EvpnDomain` | many | No | Component | `fabric__evpn_domains` |
| `EvpnDomain` | `fabric` | `NetworkFabric` | one | Yes | Parent | `fabric__evpn_domains` |
| `NetworkPod` | `evpn_domain` | `EvpnDomain` | one | No | Attribute | `evpn_domain__pods` |
| `EvpnDomain` | `pods` | `NetworkPod` | many | No | Attribute | `evpn_domain__pods` |
| `EvpnDomain` | `local_gateway_groups` | `EvpnGatewayGroup` | many | No | Component | `evpn_domain__local_gateway_groups` |
| `EvpnGatewayGroup` | `local_domain` | `EvpnDomain` | one | Yes | Parent | `evpn_domain__local_gateway_groups` |
| `NetworkPod` | `evpn_gateway_groups` | `EvpnGatewayGroup` | many | No | Attribute | `pod__evpn_gateway_groups` |
| `EvpnGatewayGroup` | `pod` | `NetworkPod` | one | Yes | Attribute | `pod__evpn_gateway_groups` |
| `EvpnGatewayGroup` | `remote_domain` | `EvpnDomain` | one | Yes | Attribute | `evpn_gateway_group__remote_domain` |
| `EvpnDomain` | `remote_gateway_groups` | `EvpnGatewayGroup` | many | No | Attribute | `evpn_gateway_group__remote_domain` |
| `EvpnGatewayGroup` | `members` | `DcimDevice` | many | Yes | Attribute | `evpn_gateway_group__members` |
| `DcimDevice` | `evpn_gateway_group` | `EvpnGatewayGroup` | one | No | Attribute | `evpn_gateway_group__members` |

`EvpnGatewayGroup.local_domain` is the only `Parent` relationship on the group. `EvpnGatewayGroup.pod` must not be a `Parent` relationship, and `NetworkPod.evpn_gateway_groups` must not be a `Component` relationship.

## Attribute Contract

`EvpnDomain` must provide:

| Name | Kind | Required | Default |
|------|------|----------|---------|
| `name` | Text | Yes | None |
| `domain_id` | Text | Yes | None |
| `description` | Text | No | None |

If `domain_id` uses format validation, use `parameters.regex` and accept colon-delimited ASN(asplain):local_admin and ASN(asdot):local_admin values.

`EvpnGatewayGroup` must provide:

| Name | Kind | Required | Default |
|------|------|----------|---------|
| `name` | Text | Yes | None |
| `resiliency_model` | Dropdown | Yes | `all_active_multihoming` |
| `evpn_l2_enabled` | Boolean | Yes | `true` |
| `evpn_l3_enabled` | Boolean | Yes | `true` |
| `evpn_l3_inter_domain` | Boolean | Yes | `true` |
| `d_path_enabled` | Boolean | Yes | `true` |
| `all_active_multihoming_enabled` | Boolean | Yes | `true` |
| `ethernet_segment_identifier` | Text | Yes | None |
| `ethernet_segment_rt_import` | Text | Yes | None |
| `description` | Text | No | None |

`resiliency_model` must define choices in object form:

```yaml
choices:
  - name: all_active_multihoming
    label: All-Active Multihoming
```

No `mlag`, `anycast_ip`, route-server, or route-reflector choice is allowed.

## Uniqueness Contract

- `EvpnDomain`: `[fabric, domain_id__value]`
- `EvpnDomain`: `[fabric, name__value]`
- `EvpnGatewayGroup`: `[local_domain, pod, name__value]`

Attribute references in uniqueness constraints must use `__value`; relationship references must be bare relationship names.

## Display Contract

Both new nodes must define:

- `label`
- `icon`
- `include_in_menu: false`
- `human_friendly_id`
- `display_label`
- `order_by`

`EvpnDomain` identity must include Fabric and domain ID. `EvpnGatewayGroup` display and ordering must use schema-valid native fields such as parent `local_domain`, selected `pod`, selected `remote_domain`, and group `name`. `EvpnGatewayGroup.human_friendly_id` uses `pod__name__value` and `name__value` because Infrahub rejects local-domain peer attributes that are only unique per Fabric.

The implementation must not add computed or denormalized helper attributes solely to show local EVPN Domain data in `EvpnGatewayGroup` identity/display.

## Migration Contract

- Schema additions to `NetworkFabric`, `NetworkPod`, and `DcimDevice` must remain optional for existing Fabric, Pod, and Device objects.
- Required attributes belong only to `EvpnDomain` and `EvpnGatewayGroup` objects.
- Changing an existing draft `EvpnGatewayGroup.pod` Parent relationship to `EvpnGatewayGroup.local_domain` Parent is a relationship ownership migration. Validate it on an explicit Infrahub branch.
- Existing draft gateway groups can be migrated only when the selected Pod has an `evpn_domain` and that domain can become the group's parent `local_domain`.
- Existing draft gateway groups whose selected Pod lacks an EVPN Domain, whose selected Pod does not match the intended local domain, or whose remote domain equals the local domain must be reported as invalid before gateway hostvars are accepted.
- If an earlier draft introduced `EvpnGateway`, remove or replace it with `EvpnGatewayGroup` before implementation proceeds.
- After schema changes, regenerate `src/solution_arista_avd/protocols.py`; do not hand-edit generated protocol code.

## Non-Goals

- No `EvpnGateway` node.
- No new device role beyond `border_leaf`.
- No MLAG, Anycast IP, route-server, or route-reflector gateway model.
- No dedicated Infrahub check or proposed-change validation implementation.
- No direct `CoreArtifactTarget` or new generator target on `EvpnDomain` or `EvpnGatewayGroup`.
- No manually modeled gateway peer objects.
- No duplicated remote peer hostname, local domain ID, or remote domain ID text fields.
