# Research: Fabric Pool Management

## Decision: Keep this planning slice schema-first

**Rationale**: The feature specification explicitly identifies the work as a schema design contract and names existing schema files as the primary targets. The repository constitution requires schemas to be defined before generators, transforms, object data, or tests reference new graph fields. The existing fabric hierarchy already models `NetworkFabric`, `NetworkPod`, `LocationRack`, IPAM prefixes, IP pools, and DCI links, so this feature should extend those kinds rather than create replacement nodes.

**Alternatives considered**:
- Implement generator-side role resolution first. Rejected because code would reference relationships and role choices that do not exist yet.
- Create replacement fabric or pod nodes. Rejected because FR-001 and FR-002 require extending the current hierarchy.
- Combine schema, object migration, validation checks, and generator allocation in one slice. Rejected because the spec scopes this cycle to the schema contract and because the compatibility migration needs staged validation.

## Decision: Model fabric and pod pools as many-valued collection relationships

**Rationale**: Current schema uses separate single-purpose relationships (`mgmt_pool`, `uplink_pool`, `vtep_pool`, `loopback_pool`, `dci_pool`, `mlag_peer_pool`, and `mlag_l3_pool`). The requested model needs one authoritative collection per scope, with the purpose derived from the backing `IpamPrefix.role`. A many-valued Attribute relationship fits the schema requirement and preserves operator assignment semantics while allowing prefix pools and address pools to coexist in one collection.

The planned relationship names are `fabric_ip_pools` on `NetworkFabric` and `pod_ip_pools` on `NetworkPod`, with labels `Fabric IP Pools` and `Pod IP Pools`. The local generated protocols expose `CoreResourcePool` as the common built-in pool target that can include `CoreIPPrefixPool` and `CoreIPAddressPool`; downstream validation must reject non-IP pool members such as number pools.

**Alternatives considered**:
- Keep separate relationships per role. Rejected because it preserves the type-specific model the feature is replacing.
- Add separate prefix-pool and address-pool collections. Rejected because operators would still manage two collections per scope instead of one role-driven pool collection.
- Create new project-specific pool wrapper nodes. Rejected because existing Infrahub core pool nodes already represent the resources and wrapping them would add migration burden without improving role resolution.
- Use `CoreIPPrefixPool` as the peer. Rejected because management, MLAG, and MLAG peering use `CoreIPAddressPool`.

## Decision: Keep legacy relationships through the migration window

**Rationale**: Existing seed data and generator queries still use the legacy relationship names. Removing those relationships or making new data mandatory in the first schema change would break loaded branches and violate the compatibility requirements. The safe migration is additive first: add the collection relationships, keep old relationships, make currently mandatory legacy prefix-pool relationships optional where needed, then migrate object data and code before a later `state: absent` removal.

**Alternatives considered**:
- Delete legacy relationships immediately. Rejected because existing objects and generated query models still reference them.
- Mark legacy relationships `state: absent` in the first schema change. Rejected because no object/code migration has populated and consumed the new collections yet.
- Keep legacy relationships authoritative indefinitely. Rejected because it does not achieve the role-driven model.

## Decision: Add new role choices while retaining old values

**Rationale**: `IpamPrefix.role` is the source of truth for pool purpose in the new design. New choices are needed for Fabric Supernet, Fabric Point-to-Point, DCI, MLAG, and MLAG Peering. Existing choices must remain valid during migration: `supernet` maps to Fabric Supernet, `pod_leaf_spine` and `pod_super_spine_spine` map to Fabric Point-to-Point, and existing `technical` assignments must be split into DCI, MLAG, or MLAG Peering based on the pool relationship they currently satisfy.

**Alternatives considered**:
- Rename existing role values in place. Rejected because object data references dropdown `name` values directly.
- Remove superseded roles immediately. Rejected because loaded data using those values must remain valid until migration completes.
- Continue using `technical` for DCI and MLAG. Rejected because the role becomes ambiguous and cannot satisfy the required-pool matrix.

## Decision: Treat conditional semantics as validation contract, not pure schema

**Rationale**: Infrahub schema can model relationships, cardinality, optionality, dropdown choices, and basic uniqueness. It cannot fully express conditional requirements such as "DCI pool is required when any DCI-role link exists", "a pod pool must be a subnet of the matching fabric pool", "a pool resource must have exactly one role", or "a /31 MLAG pool may be reused by all racks". These rules should be documented in the contract now and implemented later as proposed-change checks and generator behavior.

**Alternatives considered**:
- Add new schema nodes for every pool requirement state. Rejected because the requirement state is derived from fabric routing, DCI links, pod/rack MLAG settings, and backing prefixes.
- Encode every role as a separate relationship with `max_count: 1`. Rejected because it returns to type-specific relationships and still cannot validate prefix resource role homogeneity.
- Rely on operator discipline only. Rejected because FR-060 and FR-061 require an enforceable validation path for duplicate authoritative pools.

## Decision: Represent MLAG defaults as generator intent constants

**Rationale**: The schema must make MLAG and MLAG Peering roles available and allow pod pool collections to omit explicit MLAG pools when defaults apply. The default pools (`MLAG-Peer-Subnet` at `169.254.0.0/31` and `MLAG-L3-Peering-Subnet` at `192.0.0.0/31`) are allocation behavior, not schema attributes. Later generator work should create or resolve those default pool intents idempotently when required.

**Alternatives considered**:
- Add mandatory default-pool attributes on `NetworkPod`. Rejected because new mandatory fields would break existing data and because defaults are deterministic.
- Add seed default pools to every pod. Rejected because pod existence and MLAG requirements are dynamic.
- Reuse legacy `mlag_peer_pool` and `mlag_l3_pool` as the default mechanism. Rejected because those relationships stop being authoritative after collection migration.

## Decision: Validate schema through YAML contract tests and Infrahub schema check

**Rationale**: The repository already has tests that parse schema YAML to pin DCI schema behavior. This feature should add similar focused tests for role choices, collection relationships, and legacy compatibility, then run `infrahubctl schema check` against the full schema set. Protocol regeneration provides the type-safety handoff for later implementation.

**Alternatives considered**:
- Rely only on `yamllint`. Rejected because lint cannot detect schema contract regressions.
- Rely only on live schema load. Rejected because unit tests provide faster feedback and better failure localization.
- Hand-edit `protocols.py`. Rejected by project constitution and local guidance.
