# Schema Contract: EVPN Gateway Domains

## Scope

This contract defines the Infrahub schema interface for EVPN Domain and EVPN Gateway Group intent. It is consumed by object data, the per-device hostvar generator query, custom menu configuration, protocol generation, and documentation.

## File Contract

Add or replace the schema file under `schemas/evpn/`:

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

The implementation must reuse the `border_leaf` device role from PR #74 / branch `feat/dci-links`:

- `DcimDevice.role` includes `border_leaf` with label `Border Leaf`.
- `ROLE_TO_AVD_TYPE["border_leaf"] == "l3leaf"`.
- Hostvar code treats `border_leaf` as part of the L3 leaf family for uplinks, tenants, and gateway generation.

If those changes are not present on `feat/evpn-gateway`, they must be merged/rebased or imported before gateway-group implementation proceeds. Do not model gateway behavior on regular `leaf` as a substitute.

## Kind Contract

The implementation must expose these concrete kinds:

| Kind | Namespace | Include In Menu | Purpose |
|------|-----------|-----------------|---------|
| `EvpnDomain` | `Evpn` | `false` | EVPN Domain owned by one Fabric. |
| `EvpnGatewayGroup` | `Evpn` | `false` | Shared EVPN Gateway configuration and member Border Leaf group for one Pod. |

No new generic is required for this cycle. The schema must not define `EvpnGateway`.

## Relationship Contract

| Source | Relationship | Peer | Cardinality | Required | Kind | Identifier |
|--------|--------------|------|-------------|----------|------|------------|
| `NetworkFabric` | `evpn_domains` | `EvpnDomain` | many | No | Component | `fabric__evpn_domains` |
| `EvpnDomain` | `fabric` | `NetworkFabric` | one | Yes | Parent | `fabric__evpn_domains` |
| `NetworkPod` | `evpn_domain` | `EvpnDomain` | one | No | Attribute | `evpn_domain__pods` |
| `EvpnDomain` | `pods` | `NetworkPod` | many | No | Attribute | `evpn_domain__pods` |
| `NetworkPod` | `evpn_gateway_groups` | `EvpnGatewayGroup` | many | No | Component | `pod__evpn_gateway_groups` |
| `EvpnGatewayGroup` | `pod` | `NetworkPod` | one | Yes | Parent | `pod__evpn_gateway_groups` |
| `EvpnGatewayGroup` | `remote_domain` | `EvpnDomain` | one | Yes | Attribute | `evpn_gateway_group__remote_domain` |
| `EvpnDomain` | `remote_gateway_groups` | `EvpnGatewayGroup` | many | No | Attribute | `evpn_gateway_group__remote_domain` |
| `EvpnGatewayGroup` | `members` | `DcimDevice` | many | Yes | Attribute | `evpn_gateway_group__members` |
| `DcimDevice` | `evpn_gateway_group` | `EvpnGatewayGroup` | one | No | Attribute | `evpn_gateway_group__members` |

`EvpnGatewayGroup` must not define a `local_domain` relationship. The local domain is derived from `EvpnGatewayGroup.pod.evpn_domain`.

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
- `EvpnGatewayGroup`: `[pod, name__value]`

Attribute references in uniqueness constraints must use `__value`; relationship references must be bare relationship names.

## Display Contract

Both new nodes must define:

- `label`
- `icon`
- `include_in_menu: false`
- `human_friendly_id`
- `display_label`
- `order_by`

`EvpnDomain` identity must include Fabric and domain ID. `EvpnGatewayGroup` identity and display must use schema-valid native fields such as Pod, remote EVPN Domain, and group name. It may include the Pod-derived local EVPN Domain only through a direct `pod.evpn_domain` relationship traversal if Infrahub accepts that path in `human_friendly_id` or `display_label`.

The implementation must not add computed or denormalized helper attributes solely to show the Pod-derived local EVPN Domain in `EvpnGatewayGroup` identity/display. Examples to avoid for this purpose include a Pod-level local-domain ID helper or a domain fabric-name helper used only to make display traversal work.

## Migration Contract

- Schema additions must be additive for existing Fabric, Pod, and Device data.
- Relationships added to `NetworkFabric`, `NetworkPod`, and `DcimDevice` must be optional on existing objects.
- Required attributes belong only to new `EvpnDomain` and `EvpnGatewayGroup` objects.
- If an earlier draft introduced `EvpnGateway`, remove or replace it with `EvpnGatewayGroup` before implementation proceeds.
- After schema changes, regenerate `src/solution_arista_avd/protocols.py`; do not hand-edit generated protocol code.

## Non-Goals

- No `EvpnGateway` node.
- No new device role beyond the PR #74 `border_leaf` dependency.
- No MLAG, Anycast IP, route-server, or route-reflector gateway model.
- No dedicated Infrahub check or proposed-change validation implementation.
- No direct `CoreArtifactTarget` or new generator target on `EvpnDomain` or `EvpnGatewayGroup`.
- No manually modeled gateway peer objects.
- No duplicated remote peer hostname, local domain ID, or remote domain ID text fields.
