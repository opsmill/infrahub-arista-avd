# Phase 0 Research: DCI Links

All planning clarifications are resolved below.

## R1. Border Leaf role placement and AVD classification

**Decision**: Add `border_leaf` to the existing `DcimDevice.role` dropdown in
`schemas/dcim_extensions.yml`, with label `Border Leaf`. Map it to PyAVD
`l3leaf` in `src/solution_arista_avd/avd.py` and treat it as leaf-family in the
hostvars generator wherever `leaf` receives L3LS, MLAG, EVPN, connected
endpoint, and node-group behavior unless tests prove a narrower branch is
required.

**Rationale**: The repository already uses `DcimDevice.role` as the authoritative
classification mechanism, and PyAVD expects this role to behave as `l3leaf`.

**Alternatives considered**:
- New concrete Border Leaf device node: rejected because it duplicates device
  identity and diverges from the existing role model.
- New PyAVD node type: rejected because PyAVD already models the needed behavior
  with `l3leaf`.

## R2. DCI modeled as Network Link role

**Decision**: Model every DCI connection as the existing `NetworkLink` kind with
`role` set to the stable machine value `dci` and label `DCI`. Ordinary
`NetworkLink` behavior must remain unchanged for links with no role or a
non-DCI role.

**Rationale**: The current Network Link model already owns physical link
identity and connected endpoint behavior. A role discriminator reuses that
surface, avoids duplicate endpoint concepts, and makes DCI intent discoverable
through the existing link workflow.

**Alternatives considered**:
- Standalone DCI link kind: rejected because the active feature explicitly
  requires reuse of `NetworkLink`.
- Endpoint A/B device/interface relationships: rejected because they duplicate
  the existing connected endpoint model.
- Dedicated DCI pool or endpoint IP relationships on the link: rejected because
  DCI addressing must come from `NetworkFabric.dci_pool`.

## R3. Network Link DCI attribute surface

**Decision**: Extend `NetworkLink` with only these DCI-related direct fields:
`role`, `include_in_underlay_protocol`, `endpoint_1_bgp_asn`, and
`endpoint_2_bgp_asn`. `include_in_underlay_protocol` defaults to `true`; ASN
fields remain optional at schema level so existing links remain valid, and the
generator requires them only for DCI-role link eligibility.

**Rationale**: New attributes on existing nodes must be optional or have safe
defaults. The generator can ignore the DCI fields unless `role = dci`, while
still reporting missing ASN values for DCI-role links with actionable context.

**Alternatives considered**:
- Required ASN attributes on all Network Links: rejected because existing
  ordinary link data would become invalid.
- Routing protocol, BFD, MTU, enabled, subnet, pool, link ID, endpoint IP,
  endpoint description, name, or description fields: rejected because the spec
  explicitly excludes them from this phase.
- A JSON/List ASN field: rejected because two typed Number attributes are easier
  to validate, document, and pair with deterministic endpoint ordering.

## R4. DCI IP pool source and /31 allocation

**Decision**: Keep the fabric-level `dci_pool` relationship from
`NetworkFabric` to `CoreIPPrefixPool`. When valid DCI-role links exist in a
fabric, the hostvars generation path requires that pool and allocates one `/31`
prefix per valid link using a stable identifier derived from the Network Link
identity. The generator emits the two host addresses as the PyAVD `ip` list for
the link.

**Rationale**: The link itself must not add DCI-specific pool, addressing,
subnet, or endpoint IP fields. A fabric-level pool matches the existing fabric
pool pattern and gives generators a branch-aware allocation source without
placing allocation source data on each link.

**Alternatives considered**:
- Store endpoint IPs or subnet directly on the link: rejected by scope.
- Reuse the fabric uplink pool: rejected because DCI addressing must come from a
  DCI IP Pool.
- Use a pool name convention only: rejected because a typed relationship is more
  discoverable and validates the source of truth.

## R5. PyAVD l3_edge shape

**Decision**: Extend `generate-avd-device-hostvar` to emit native PyAVD
`l3_edge` input. Each valid DCI-role Network Link emits one deterministic
`l3_edge.p2p_links[]` entry with `nodes`, `interfaces`, `as`, `ip`, and
`include_in_underlay_protocol`. Emit `speed` only when endpoint/interface data
provides a resolvable speed. Do not emit or rely on
`l3_edge.p2p_links_profiles[]` for DCI links.

**Rationale**: `l3_edge` is native eos_designs input and belongs in the existing
hostvars generation path. Profile-free per-link entries keep the modeled
operational settings directly on the DCI link output and avoid shared profile
state.

**Alternatives considered**:
- Separate hostvar-fragment writer: rejected because generated hostvars are
  stored as one validated file per device.
- Custom structured config: rejected because PyAVD exposes native `l3_edge`
  keys for this behavior.
- Default speed when no interface speed is modeled: rejected by the active spec,
  which requires `speed` only when resolvable.

## R6. Generator query and typed workflow

**Decision**: Update `generators/avd_device_hostvar.gql` to fetch DCI candidates
from `NetworkLink` with `role = dci` or fetch candidate Network Links and filter
in typed Python if server-side filtering is unavailable. Regenerate
`generators/generate_avd_device_inputs_query.py` after the query change and keep
production code typed against generated models.

**Rationale**: The project constitution requires typed GraphQL responses and
generated return types. The generator must have link identity, role, underlay
flag, ASN values, connected endpoint interfaces, endpoint device roles, endpoint
fabric, and `NetworkFabric.dci_pool`.

**Alternatives considered**:
- Continue querying the stale standalone link kind: rejected because the kind is
  removed from the supported model.
- Use raw dictionaries for new DCI query data: rejected by type-safety
  requirements.

## R7. Generator validation boundary

**Decision**: Do not create a dedicated check in this phase. Enforce static
schema properties in schema/tests and enforce derived eligibility inside the
hostvars generator while building DCI `l3_edge` data. The generator must exclude
invalid DCI-role links from `l3_edge` output and report actionable context for
each rejected link. Generation should continue for other valid DCI links unless
a non-link-scoped infrastructure failure prevents allocation or validation
globally.

**Rationale**: Endpoint count, device role, interface/device ownership, duplicate
interface pairs, ASN presence, and pool allocation all depend on derived data the
generator must inspect. A dedicated proposed-change check would duplicate that
logic and is explicitly not required by the feature scope.

**Alternatives considered**:
- Global proposed-change check: rejected for this phase because it adds a new
  artifact type and duplicates generator eligibility logic.
- Silent generator skip: rejected because operators need correction context.

## R8. Removal and migration decision

**Decision**: Remove the previous standalone DCI link kind from committed
schemas, generated protocols, generated GraphQL schema, generated query models,
generator logic, menus, docs, and tests. No repository seed data migration is
planned because this branch has no committed object data for that stale kind.
Any local validation branch that contains trial data for the stale kind should
be recreated or manually converted into `NetworkLink` objects with `role = dci`
before schema load.

**Rationale**: The active requirement is a model replacement, not compatibility
with the earlier trial design. Keeping the stale kind would leave two endpoint
models and make operator behavior ambiguous.

**Alternatives considered**:
- Automatic migration generator: rejected because there is no committed
  persistent data to migrate and it would add a new operational artifact.
- Keep both models temporarily: rejected because the feature requires a single
  Network Link source of truth.

## R9. Prefix allocation helper consolidation

**Decision**: Consolidate DCI generation on a single shared
`allocate_p2p_prefix_from_pool` implementation in
`src/solution_arista_avd/addressing.py` unless implementation finds a concrete
behavioral mismatch. If a second helper must remain, document the reason and add
tests proving both helpers are intentionally distinct.

**Rationale**: Duplicate allocation helpers increase the risk of divergent
identifier construction, prefix length handling, and idempotence behavior.
Centralizing the /31 allocation path gives DCI generation the same deterministic
semantics in unit, integration, and live idempotence validation.

**Alternatives considered**:
- Leave both helpers undocumented: rejected because the spec explicitly calls out
  this ambiguity.
- Inline allocation logic in the hostvars generator: rejected because allocation
  behavior is reusable infrastructure logic.

## R10. Validation workflow

**Decision**: Validate in this order: schema check/load on a branch, protocol
regeneration, GraphQL schema export, return-type regeneration, focused unit
tests, PyAVD validation, lint, required integration validation, and required
generator idempotence validation when live validation is allowed.

**Rationale**: This sequence follows the constitution and avoids consuming schema
fields before Infrahub and generated types know about them.

**Alternatives considered**:
- Hand-edit generated protocol or query model files: rejected by constitution.
- Skip integration/idempotence validation: rejected because this feature changes
  generator behavior and generated artifacts.
