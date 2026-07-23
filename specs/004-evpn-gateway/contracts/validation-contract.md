# Validation Contract: EVPN Gateway Domains

## Scope

This feature does not implement a dedicated Infrahub check or proposed-change validation check for EVPN Gateway intent. Invalid gateway intent is handled by schema constraints where possible and by generator-side validation before EVPN Gateway hostvars are written.

## Non-Goals

Do not add any of the following in this feature:

- `queries/evpn_gateway_validation.gql`
- `checks/evpn_gateway_validation.py`
- `.infrahub.yml` query or check definition entries for EVPN Gateway validation
- Unit tests that target an `EvpnGatewayValidation` Infrahub check class

## Generator-Side Validation Rules

For every target device considered for EVPN Gateway hostvars, the hostvar generator must raise actionable errors when:

- The target device is in an `EvpnGatewayGroup` but its role is not `border_leaf`.
- The target device's inverse `evpn_gateway_group` relationship does not match the group's `members` relationship.
- A gateway group has no member devices.
- Any group member role is not `border_leaf`.
- Any group member belongs to a Pod different from the gateway group's selected Pod.
- A member device is present in more than one gateway group.
- The gateway group parent `local_domain` is missing.
- The gateway group selected Pod is missing.
- The selected Pod has no `evpn_domain`.
- The selected Pod's `evpn_domain` differs from the gateway group's parent `local_domain`.
- The gateway group remote domain is missing.
- The parent `local_domain` and selected `remote_domain` are the same object.
- The parent `local_domain` and selected `remote_domain` use the same `domain_id` in the same Fabric.
- The local domain, remote domain, and selected Pod are inconsistent with the expected Fabric context.
- `resiliency_model` is not `all_active_multihoming`.
- Required all-active Ethernet Segment values are missing.
- Route-server or route-reflector remote-domain behavior is modeled or requested.
- A peer candidate from another group sharing the remote domain is malformed, non-Border Leaf, or lacks a resolvable hostname.

Ungrouped Border Leafs and non-Border Leaf devices that are not in a gateway group must continue to generate hostvars without EVPN Gateway-specific fields.

## Error Message Contract

Errors must include actionable context:

- Gateway group display label or name.
- Target device name when detected during per-device generation.
- Failing relationship or field.
- Expected value.
- Actual value when available.
- Suggested correction at the model level, such as moving the gateway group under the correct EVPN Domain, assigning the selected Pod to that same EVPN Domain, or removing a non-Border Leaf member.

## Peer Set Contract

Peer derivation must expose remote-domain singleton cases without inventing data:

- If no other valid gateway group shares the remote domain, the peer list is empty.
- If multiple groups share the remote domain, every valid Border Leaf member in peer candidate groups appears once, excluding the target device.
- Each candidate group's selected Pod must match that candidate group's parent local domain.
- The target device never appears in its own peer list.
- Peer hostnames are sorted deterministically.

## Tests Contract

Unit tests must cover generator-side failures for:

- Non-`border_leaf` target in a gateway group.
- Non-`border_leaf` member in a gateway group.
- Member device in another Pod.
- Missing parent `local_domain`.
- Pod without an EVPN Domain.
- Pod EVPN Domain that differs from parent `local_domain`.
- Missing remote domain.
- Same local and remote domain.
- Same local and remote domain ID in the same Fabric.
- Empty member list.
- Duplicate device group membership, when representable in test data.
- Unsupported `resiliency_model`.
- Missing Ethernet Segment identifier or RT import.

Unit tests must cover successful generation for:

- One local EVPN Domain owning one or more gateway groups.
- Two or more gateway groups in different local domains sharing one remote domain.
- Multiple Border Leaf members per group.
- Empty remote peer list when no other group shares the remote domain.
