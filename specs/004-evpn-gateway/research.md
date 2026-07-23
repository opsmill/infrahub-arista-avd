# Phase 0 Research: EVPN Gateway Domains

## Decision: Replace the earlier `EvpnGateway` node draft with `EvpnGatewayGroup`

**Rationale**: The active specification explicitly prohibits a dedicated per-device `EvpnGateway` object. A Border Leaf becomes an EVPN Gateway only through membership in an `EvpnGatewayGroup`. Planning must therefore treat any existing `EvpnGateway` schema, query, generated protocol, menu, test, or documentation draft as stale implementation work to be replaced.

**Alternatives considered**: Keep the earlier one-gateway-per-device node and rename it later. Rejected because it violates FR-002 and would force implementation tasks to unwind the wrong schema contract.

## Decision: Model `EvpnDomain` as a Fabric-owned domain

**Rationale**: The spec requires a Fabric to contain zero or more EVPN Domains and requires `EvpnDomain.domain_id` uniqueness within the related Fabric. Use `EvpnDomain.fabric` as a required `Parent` relationship to `NetworkFabric` and `NetworkFabric.evpn_domains` as the optional inverse `Component` relationship. Use uniqueness constraints `[fabric, domain_id__value]` and `[fabric, name__value]`.

**Alternatives considered**: Scope domains directly to Pods. Rejected because a remote exchange domain such as CORE may exist in a Fabric without Pods, and domain uniqueness is required at Fabric scope.

## Decision: Add one optional local-domain relationship on `NetworkPod`

**Rationale**: Each Pod belongs to zero or one EVPN Domain. `NetworkPod.evpn_domain` provides the Pod's local domain, while `EvpnDomain.pods` lists Pods assigned to the domain. Keeping the relationship optional preserves existing Pod data and supports Fabrics with no gateway-enabled Border Leafs.

**Alternatives considered**: Add a `local_domain` relationship on `EvpnGatewayGroup`. Rejected because the group local domain must be derived from the Pod's EVPN Domain and must not be independently selectable.

## Decision: Model shared gateway behavior on `EvpnGatewayGroup`

**Rationale**: A gateway group is defined for exactly one Pod, has exactly one remote EVPN Domain, and relates to one or more member `DcimDevice` objects. The group carries all shared gateway settings: resiliency model, EVPN L2/L3 enablement, inter-domain flag, D-PATH enablement, and all-active Ethernet Segment identifier/RT import. The inverse `DcimDevice.evpn_gateway_group` relationship is cardinality one so a Border Leaf can belong to at most one group in this phase.

**Alternatives considered**: Put gateway settings directly on `DcimDevice`. Rejected because members of a gateway group must share one common configuration profile, and per-device settings would duplicate intent and permit drift inside the group.

## Decision: Keep gateway group identity/display schema-valid without local-domain helper fields

**Rationale**: The local EVPN Domain is derived from `EvpnGatewayGroup.pod.evpn_domain` for validation, documentation, and hostvar generation. Identity and display must therefore use schema-valid native fields such as Pod, remote EVPN Domain, and group name. If Infrahub accepts direct relationship traversal to `pod.evpn_domain` in `human_friendly_id` or `display_label`, the implementation may use that traversal; otherwise the schema display must omit the local domain and rely on documentation and relationship views. The schema must not add computed or denormalized helper attributes such as a Pod-level local-domain ID solely for gateway group display.

**Alternatives considered**: Add read-only computed helper attributes for Pod local-domain ID or domain fabric name and use those in `EvpnGatewayGroup` identity/display. Rejected because the clarification explicitly prohibits helper fields created solely to display the Pod-derived local EVPN Domain.

## Decision: Enforce complex eligibility in generator-side validation

**Rationale**: Schema can enforce required fields, relationship cardinality, domain/group uniqueness, and one group per device. It cannot fully enforce member role, member Pod equality, Pod/domain Fabric equality, local/remote domain difference, route-server exclusion, or full-mesh peer derivation. The hostvar generator must validate those conditions before emitting EVPN Gateway-specific hostvars.

**Alternatives considered**: Add a dedicated Infrahub proposed-change check. Rejected because FR-080 says this feature must not require a dedicated check when schema constraints and generator-side eligibility rules can enforce or report the behavior.

## Decision: Derive full-mesh peers from groups sharing the same remote EVPN Domain

**Rationale**: The remote EVPN Domain is the source of truth for inter-domain BGP peer selection. For a target Border Leaf in a gateway group, the generator traverses the group's `remote_domain.remote_gateway_groups` inverse relationship, collects member Border Leafs from all other valid groups sharing that remote domain, excludes the target device, and sorts peer hostnames deterministically. pyAVD EVPN multi-domain gateway remote peers represent remote EVPN gateway peers, so same-local-domain candidates must be rejected or excluded during validation.

**Alternatives considered**: Store peer hostnames or peer objects manually. Rejected because FR-036 prohibits manually modeled remote peer relationships and because duplicated peer data would drift from domain membership.

## Decision: Keep only `all_active_multihoming` as an actionable resiliency model

**Rationale**: The feature supports only all-active multihoming in this phase. The `resiliency_model` dropdown should define object-form choices with one value, `all_active_multihoming`, and default to that value. All-active fields are required for group objects in this phase. If Infrahub UI conditional visibility is unavailable, labels/descriptions and generator-side validation must make the applicability clear.

**Alternatives considered**: Add future choices now and block them in validation. Rejected because it exposes invalid operator selections before they are supported.

## Decision: Emit non-deprecated pyAVD 6.3.0 EVPN Gateway keys

**Rationale**: AVD `v6.3.0` defines `evpn_gateway.remote_peers[].hostname`, `evpn_gateway.evpn_l2.enabled`, `evpn_gateway.evpn_l3.enabled`, `evpn_gateway.evpn_l3.inter_domain`, `evpn_gateway.d_path.enabled`, `evpn_gateway.d_path.local_domain_id`, `evpn_gateway.d_path.remote_domain_id`, `evpn_gateway.all_active_multihoming.enabled`, and `evpn_gateway.all_active_multihoming.evpn_ethernet_segment.identifier` / `rt_import`. Deprecated keys under `all_active_multihoming` are marked for removal in AVD 7.0.0 and must not be emitted by new code.

**Alternatives considered**: Emit both old and new keys for compatibility. Rejected because the repository pins pyAVD 6.3.0 and should avoid adding deprecated data in new hostvars.

## Decision: Keep EVPN Gateway peer objects hostname-only in this phase

**Rationale**: AVD `v6.3.0` permits `evpn_gateway.remote_peers[].hostname` by itself when the named remote peer exists in the aggregated AVD inventory, because `get_avd_facts()` can resolve the peer's BGP ASN and overlay peering address from that peer's hostvars. This repository stores per-device hostvars but the structured-config generator fetches all fabric device hostvar files before calling `get_avd_facts()`, so the contract is valid when every gateway member has generated hostvars before structured-config generation. The implementation must treat missing peer facts during structured-config generation as a validation failure rather than adding independent peer IP or ASN fields to the schema.

**Alternatives considered**: Add `remote_peer_ip_address` and `remote_peer_bgp_as` fields to `EvpnGatewayGroup` or `DcimDevice`. Rejected because the current feature derives peer intent from domain membership, and manually duplicated peer transport data would widen the schema beyond the domain/group model. Add those fields later only if peer hostvars cannot be present in the same fabric run.

## Decision: Emit gateway hostvars per device under `l3leaf.nodes[].evpn_gateway`

**Rationale**: The current generator builds a per-device hostvars payload and includes only the target device under `l3leaf.nodes`. Emitting the derived `evpn_gateway` payload on that node ensures only group-member Border Leafs receive gateway configuration. Using `l3leaf.defaults` or a shared node-group field could apply gateway behavior to ungrouped Border Leafs.

**Alternatives considered**: Emit `l3leaf.defaults.evpn_gateway` for every Pod. Rejected because FR-075 requires ungrouped Border Leafs to keep existing Border Leaf hostvars without EVPN Gateway-specific fields.

## Decision: Add a custom Domains menu item for `EvpnDomain`

**Rationale**: The existing custom menu has an EVPN Services group, and EVPN Domains are the primary service boundary for this feature. Add one `EvpnDomain` item labelled `Domains` there and keep `EvpnDomain.include_in_menu: false` to prevent duplicate automatic menu entries. Do not add an `EvpnGatewayGroup` item to EVPN Services; gateway groups remain reachable by opening an EVPN Domain and following its local or remote gateway group relationships.

**Alternatives considered**: Point the menu at `EvpnGateway`. Rejected because the dedicated gateway object is out of scope. Point the menu directly at `EvpnGatewayGroup`. Rejected because the operator workflow should start from an EVPN Domain and then explore its gateway groups. Relying on auto-generated menu entries was rejected because the repository owns a custom sidebar.
