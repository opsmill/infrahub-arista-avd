# Specification Quality Checklist: EVPN Gateway Domains

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-07-22
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details beyond the schema-design contract and required downstream gateway intent scope
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders where possible while preserving required Infrahub and EVPN terminology
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic for outcomes, except schema-validation and hostvar-output wording required by this Infrahub/AVD feature
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation mechanics leak into the specification beyond the required artifact scope and existing role dependency

## Notes

- Validation iteration 1 passed after updating the active spec for the new EVPN Domain and EVPN Gateway Group model.
- The spec now explicitly rejects a dedicated per-device `EvpnGateway` object. A Border Leaf becomes an EVPN Gateway only through EVPN Gateway Group membership.
- The spec captures Fabric zero-or-more EVPN Domains, Pod zero-or-one EVPN Domain membership, local and remote EVPN Domains per gateway group, shared group configuration, full-mesh peering for gateways sharing a remote domain, and route server or route reflector exclusion.
- Conditional visibility for all-active settings is captured as required where available, with a clear fallback when UI-level conditional visibility is not available.
- Validation iteration 2 passed after tightening Pod membership: each EVPN Gateway Group is defined for exactly one Pod, all member devices must belong to that Pod, and the group's local EVPN Domain is derived from that Pod's EVPN Domain.
- Validation iteration 3 passed after clarifying EVPN Services menu navigation: the menu exposes EVPN Domains through a Domains tab, does not expose EVPN Gateway Groups directly, and relies on Domain detail relationships for gateway group discovery.
