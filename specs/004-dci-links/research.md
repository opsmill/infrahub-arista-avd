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

## R2. Network Link reuse in Infrahub schema

**Decision**: Preserve Network Link behavior through the same `DcimConnector`
generic that `NetworkLink` already inherits. Define `NetworkDciLink` as a
concrete Network node that inherits `DcimConnector`, then add only DCI-specific
fields. Do not duplicate `connected_endpoints`.

**Rationale**: The local Infrahub schema reference documents node
`inherit_from` as generic-kind inheritance, and generics do not themselves use
`inherit_from`. `NetworkLink` gets its physical endpoint behavior from
`DcimConnector`, including the extension-defined `name`, `medium`, and
`connected_endpoints` behavior. Having `NetworkDciLink` inherit the same generic
is the schema-safe equivalent of inheriting Network Link behavior.

**Alternatives considered**:
- `NetworkDciLink inherit_from: [NetworkLink]`: rejected during planning because
  `inherit_from` is documented for generic kinds, not concrete nodes.
- Duplicate `connected_endpoints` on `NetworkDciLink`: rejected because it
  creates a parallel endpoint model.
- Endpoint A/B device/interface relationships: rejected by the feature scope.

## R3. DCI link direct schema surface

**Decision**: `NetworkDciLink` directly adds only
`include_in_underlay_protocol` and the two BGP ASN values required to build the
PyAVD `as` list. Use `include_in_underlay_protocol` as a Boolean defaulting to
`true`. Use two integer ASN attributes with clear labels and order weights; the
generator maps them to endpoint order after normalizing the inherited endpoint
pair.

**Rationale**: The feature explicitly limits DCI-specific schema fields to
underlay participation and BGP ASN values. Other endpoint and physical details
come from inherited link behavior or related endpoint/interface objects.

**Alternatives considered**:
- Routing protocol, BFD, MTU, enabled, subnet, pool, link ID, endpoint IP, or
  endpoint description fields: rejected because the spec explicitly excludes
  them from this phase.
- A single untyped JSON/List ASN field: rejected because two Number attributes
  are easier to validate, document, and map into PyAVD.

## R4. DCI IP pool source and /31 allocation

**Decision**: Add a fabric-level `dci_pool` relationship from `NetworkFabric` to
`CoreIPPrefixPool`. When DCI links exist in a fabric, the hostvars generation
path requires that pool and allocates one `/31` prefix per valid DCI link using
a stable identifier derived from the DCI link identity. The generator then emits
the two host addresses as the PyAVD `ip` list for the link.

**Rationale**: The DCI link itself must not add a DCI-specific pool,
addressing, subnet, or endpoint IP field. A fabric-level pool matches the
existing fabric pool pattern and gives generators a branch-aware allocation
source without placing allocation source data on each link.

**Alternatives considered**:
- Store endpoint IPs or subnet directly on `NetworkDciLink`: rejected by scope.
- Reuse the fabric uplink pool: rejected because DCI addressing must come from a
  DCI IP Pool.
- Use a pool name convention only: rejected because a typed relationship is more
  discoverable and validates the source of truth.

## R5. PyAVD `l3_edge` shape

**Decision**: Extend `generate-avd-device-hostvar` to emit native PyAVD
`l3_edge` input. Each valid DCI link emits one deterministic
`l3_edge.p2p_links[]` entry with `nodes`, `interfaces`, `as`, `ip`, `speed`,
and `include_in_underlay_protocol` directly on the link entry. Do not emit or
rely on `l3_edge.p2p_links_profiles[]` for DCI links.

**Rationale**: `l3_edge` is native eos_designs input. The local pyavd 6.3.0
validation accepted the required profile-free DCI shape with zero violations,
so no structured-config escape hatch is needed. The repository already validates
and saves PyAVD hostvars in this generator path.

**Alternatives considered**:
- Separate hostvar-fragment writer: rejected because generated hostvars are
  stored as one validated file per device.
- Custom structured config: rejected because PyAVD exposes native `l3_edge`
  keys for this behavior.

## R6. DCI link speed source

**Decision**: Use a documented DCI default speed of `100g` unless implementation
finds an existing typed interface speed source before tasks are generated. Do
not add a DCI-specific speed field to `NetworkDciLink`.

**Rationale**: The current schema search did not find an existing interface
speed attribute, and the feature requires `speed` in every generated
`l3_edge.p2p_links[]` entry while explicitly prohibiting DCI-specific speed on
the link.

**Alternatives considered**:
- Add `speed` on `NetworkDciLink`: rejected because the feature says speed is
  not a direct DCI-specific attribute.
- Omit per-link speed: rejected because the expected generator output requires
  it.

## R7. Generator validation boundary

**Decision**: Do not create a dedicated check in this phase. Enforce static
schema properties in schema/tests and enforce derived eligibility inside the
hostvars generator while building DCI `l3_edge` data. The generator must exclude
or fail invalid DCI links with actionable context.

**Rationale**: The user explicitly scoped out a dedicated check when constraints
can be handled in schema and generators. Endpoint count, device role,
interface/device ownership, duplicate interface pairs, ASN presence, and pool
allocation all depend on derived data the generator must inspect.

**Alternatives considered**:
- Global proposed-change check: rejected for this phase because it adds a new
  artifact type and duplicates generator eligibility logic.
- Silent generator skip: rejected because operators need correction context.

## R8. Typed implementation workflow

**Decision**: Implement schema changes first on an Infrahub branch, regenerate
`src/solution_arista_avd/protocols.py`, update
`generators/avd_device_hostvar.gql`, export the GraphQL schema, regenerate
`generators/generate_avd_device_inputs_query.py`, and keep production generator
code typed against generated models.

**Rationale**: The project constitution and Infrahub skills require schema-first
changes, generated protocols/return types instead of hand edits, and typed
GraphQL response handling.

**Alternatives considered**:
- Hand-edit generated protocol or query model files: rejected by constitution.
- Use raw dictionaries for new DCI query data: rejected by type-safety
  requirements.

## R9. Operator visibility

**Decision**: Add a DCI Links menu entry and update supported capabilities,
schema docs, AVD role mapping docs, hostvars docs, and AVD overview docs.

**Rationale**: `NetworkDciLink` is user-facing, and the capability matrix must
show what this phase supports while making external networks and EVPN Gateway
out of scope.

**Alternatives considered**:
- Rely on automatic menu inclusion: rejected because this repository manages
  navigation through `menus/menu.yml`.
