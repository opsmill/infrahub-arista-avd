# Phase 0 Research: EVPN Gateway Domains

## Decision: Keep `EvpnGatewayGroup` and do not add `EvpnGateway`

**Rationale**: The active specification prohibits a dedicated per-device `EvpnGateway` object. A Border Leaf becomes an EVPN Gateway only through membership in an `EvpnGatewayGroup`. Any existing schema, query, protocol, menu, test, or documentation draft that defines `EvpnGateway` remains stale and must be removed or replaced.

**Alternatives considered**: Keep the earlier one-gateway-per-device node and adapt it later. Rejected because it violates the node scope and would force generator and menu consumers onto the wrong contract.

## Decision: Model `EvpnDomain` as both Fabric-owned domain and local gateway-group owner

**Rationale**: The Fabric still owns all EVPN Domains through `NetworkFabric.evpn_domains` and `EvpnDomain.fabric`. For local gateway behavior, `EvpnDomain.local_gateway_groups` must be the Component side and `EvpnGatewayGroup.local_domain` must be the required Parent side. This satisfies Infrahub's one-parent rule for gateway groups and lets operators start from an EVPN Domain to discover local gateway groups.

**Alternatives considered**: Keep `NetworkPod.evpn_gateway_groups` as the Component owner and infer local domain from `pod.evpn_domain`. Rejected because the clarified source of truth is `EvpnGatewayGroup.local_domain`, not Pod ownership or inference.

## Decision: Keep `NetworkPod.evpn_domain` optional and make Pod gateway-group linkage non-owning

**Rationale**: Each Pod may belong to zero or one EVPN Domain, preserving existing Pod data and allowing Fabrics with no EVPN Gateway behavior. A gateway group still selects one required Pod as context, but `NetworkPod.evpn_gateway_groups` is an Attribute inverse rather than Component ownership. Generator validation then confirms the selected Pod's `evpn_domain` matches the group's parent `local_domain`.

**Alternatives considered**: Remove the Pod relationship from gateway groups. Rejected because the selected Pod remains required context for member-device eligibility and for validating that gateway members belong to the expected Pod.

## Decision: Use three explicit gateway-group relationships

**Rationale**: `EvpnGatewayGroup.local_domain` is a required `Parent` relationship to `EvpnDomain`, `EvpnGatewayGroup.remote_domain` is a required `Attribute` relationship to another `EvpnDomain`, and `EvpnGatewayGroup.pod` is a required `Attribute` relationship to `NetworkPod`. The schema can express ownership, cardinality, and inverse relationship views; generator validation handles cross-object rules that schema cannot fully constrain.

**Alternatives considered**: Store the local domain as an attribute-like relationship or only infer it from Pod. Rejected because local domain ownership must be structural and discoverable from the EVPN Domain detail view.

## Decision: Key gateway group uniqueness by local domain, Pod, and name

**Rationale**: The spec requires duplicate gateway group names to be prevented within the selected Pod and local EVPN Domain. Use `[local_domain, pod, name__value]`, with bare relationship names for relationships and `__value` for the attribute field.

**Alternatives considered**: Keep `[pod, name__value]`. Rejected because Pod no longer owns the group and the uniqueness rule explicitly includes local EVPN Domain.

## Decision: Keep display schema-valid without denormalized helper fields

**Rationale**: Because `local_domain` is now a direct relationship on `EvpnGatewayGroup`, identity and display can use native relationship paths such as `local_domain__domain_id__value`, `pod__name__value`, `remote_domain__domain_id__value`, and `name__value`. The schema still must not add computed or denormalized helper attributes solely to expose local-domain display data.

**Alternatives considered**: Add helper attributes for local domain ID or local domain Fabric name. Rejected because the clarification says to use schema-valid native fields for identity/display, and the direct `local_domain` relationship provides those fields.

## Decision: Enforce cross-object eligibility in generator-side validation

**Rationale**: Schema can enforce required fields, relationship cardinality, ownership, identity, uniqueness, and one group per device through a cardinality-one inverse. It cannot fully enforce Pod/local-domain equality, remote/local-domain difference, member role, member Pod equality, route-server exclusion, or pyAVD input validity. The hostvar generator must report those as actionable errors before writing EVPN Gateway-specific hostvars.

**Alternatives considered**: Add a dedicated Infrahub proposed-change check. Rejected because this feature must not require a dedicated check when schema constraints and generator-side validation can enforce or report the behavior.

## Decision: Derive full-mesh peers from groups sharing the same remote EVPN Domain

**Rationale**: The remote EVPN Domain is the source of truth for inter-domain gateway peer selection. For a target Border Leaf in a gateway group, the generator traverses `local_group.remote_domain.remote_gateway_groups`, validates each candidate group's own `local_domain`, selected Pod, and members, excludes the target device, and sorts peer hostnames deterministically.

**Alternatives considered**: Store peer hostnames or peer objects manually. Rejected because peer intent is derivable from domain/group membership, and duplicated peer data would drift from the model.

## Decision: Keep only `all_active_multihoming` as an actionable resiliency model

**Rationale**: The feature supports only all-active multihoming in this phase. The `resiliency_model` dropdown should define object-form choices with one value, `all_active_multihoming`, and default to that value. All-active Ethernet Segment values are required for gateway groups in this phase.

**Alternatives considered**: Add future choices now and block them in validation. Rejected because it exposes invalid operator selections before they are supported.

## Decision: Emit non-deprecated pyAVD 6.3.0 EVPN Gateway keys

**Rationale**: AVD `v6.3.0` defines `evpn_gateway.remote_peers[].hostname`, `evpn_gateway.evpn_l2.enabled`, `evpn_gateway.evpn_l3.enabled`, `evpn_gateway.evpn_l3.inter_domain`, `evpn_gateway.d_path.enabled`, `evpn_gateway.d_path.local_domain_id`, `evpn_gateway.d_path.remote_domain_id`, `evpn_gateway.all_active_multihoming.enabled`, and `evpn_gateway.all_active_multihoming.evpn_ethernet_segment.identifier` / `rt_import`. Deprecated keys under `all_active_multihoming` are marked for removal in AVD 7.0.0 and must not be emitted by new code.

**Alternatives considered**: Emit both old and new keys for compatibility. Rejected because the repository pins pyAVD 6.3.0 and should avoid adding deprecated data in new hostvars.

## Decision: Keep EVPN Gateway peer objects hostname-only in this phase

**Rationale**: AVD `v6.3.0` permits `evpn_gateway.remote_peers[].hostname` by itself when the named remote peer exists in the aggregated AVD inventory, because `get_avd_facts()` can resolve the peer's BGP ASN and overlay peering address from that peer's hostvars. The structured-config generator already aggregates Fabric hostvar files before calling pyAVD, so the plan should preserve hostname-only peer entries and treat missing peer facts as validation failures.

**Alternatives considered**: Add peer IP address or BGP ASN fields to `EvpnGatewayGroup` or `DcimDevice`. Rejected because this feature derives peer intent from domain membership and should not widen the schema with manually duplicated transport data.

## Decision: Emit gateway hostvars per grouped Border Leaf under `l3leaf.nodes[].evpn_gateway`

**Rationale**: The hostvar generator builds per-device hostvars and should emit gateway data only for target devices with role `border_leaf` that are members of one valid gateway group. Using per-node output prevents ungrouped Border Leafs in the same Pod or Fabric from receiving EVPN Gateway behavior.

**Alternatives considered**: Emit `l3leaf.defaults.evpn_gateway` for every Pod or local domain. Rejected because ungrouped Border Leafs must continue generating normal Border Leaf hostvars without EVPN Gateway-specific fields.

## Decision: Keep the EVPN Services menu domain-first

**Rationale**: The existing custom menu has an EVPN Services group, and EVPN Domains are the primary navigation boundary. Add or keep one `EvpnDomain` item labelled `Domains`, keep `EvpnDomain.include_in_menu: false`, and do not add an `EvpnGatewayGroup` menu item. Gateway groups are discovered through `EvpnDomain.local_gateway_groups` and `EvpnDomain.remote_gateway_groups`.

**Alternatives considered**: Point the menu directly at `EvpnGatewayGroup`. Rejected because the operator workflow should start from an EVPN Domain and then inspect local or remote gateway group relationships.
