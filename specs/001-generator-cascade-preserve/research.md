# Research: Generator Cascade Preservation

## Decision: Treat this as generator reconciliation, not schema work

**Rationale**: The existing data model already represents the relevant hierarchy and data: `NetworkFabric`, `NetworkPod`, `LocationRack`, `DcimDevice`, IPAM pool relationships, generator target checksums, `generation_complete`, `avd_hostvars_ready`, and `AvdArtifact` files. The spec also states that no schema files are expected by default.

**Alternatives considered**:
- Add ownership metadata attributes to devices. Rejected for this slice because it adds schema and migration work without being required to preserve existing non-empty values.
- Add a new generation-run node. Rejected because the current generator chain can reconcile through existing target nodes and artifacts.
- Add an override flag to `NetworkFabric`. Rejected for this slice because a persistent schema flag could be stale or unsafe unless a full operator contract is designed.

## Decision: Continue the cascade explicitly for unchanged downstream targets

**Rationale**: The current chain depends on trigger rules that fire when a downstream target attribute changes, especially `NetworkPod.checksum` and `LocationRack.checksum`. On an already reconciled fabric, a checksum may already match, so no save occurs and no trigger fires. The repository already has a `CoreGeneratorDefinitionRun` helper pattern for direct generator execution by node IDs, so `generate-fabric` can directly run `generate-pod` for unchanged child pods and `generate-pod` can directly run `generate-rack` for unchanged child racks.

**Alternatives considered**:
- Always rewrite checksums even when unchanged. Rejected because it creates noisy mutations and weakens checksum semantics.
- Directly run every downstream target regardless of checksum changes. Rejected because changed targets would also be run by existing triggers, causing duplicate work.
- Remove trigger rules and make the whole cascade direct. Rejected because the existing triggers support independent pod/rack edits and are documented operator behavior.
- Move orchestration entirely into the service portal. Rejected because the Infrahub UI/API `generate-fabric` path must also reconcile.

## Decision: Use fill-only device reconciliation by default

**Rationale**: `GeneratorMixin.create_avd_device()` is the shared path used by fabric, pod, and rack generators. It already detects whether a device exists, but it still builds a full upsert payload. The preservation requirement is best handled once in this helper by fetching existing device state and only adding missing generator-owned fields. This lets generated devices receive missing node IDs, loopbacks, VTEP IPs, ASNs, pod/rack relationships, and AVD group membership while keeping pre-seeded `serial`, `mgmt_ip`, and other non-empty values intact.

**Alternatives considered**:
- Handle preservation separately in each generator. Rejected because fabric, pod, rack, and future generators would drift.
- Assume `allow_upsert=True` preserves existing relationships automatically. Rejected because the current payload can include pool-backed fields such as `mgmt_ip`, which is exactly one of the values the feature must preserve.
- Split create and update into separate code paths. Rejected unless implementation proves it necessary; a single helper can make the ownership rules explicit.

## Decision: Reconcile generated cabling and point-to-point IPs fill-only

**Rationale**: The rack and pod generators already compute deterministic cabling plans from sorted interface maps. The missing behavior is not a new data model; it is a safer write contract for `NetworkLink`, interface `connector`, generated interface attributes, and point-to-point `IpamIPAddress` relationships. The cabling helper should create or reuse the expected generated `NetworkLink` by name, attach an endpoint only when its connector is empty, and log/report a skipped conflict when the endpoint already points at a different non-empty connector. The addressing helper should assign generated point-to-point IPs only to interfaces that lack an IP relationship and preserve non-empty existing IPs, including values that differ from generated intent.

**Alternatives considered**:
- Always replace interface connectors and IPs with generated intent. Rejected because the accepted clarification says non-empty conflicting connectivity values must be preserved in standard generation.
- Skip the whole cabling pair when either side has partial data. Rejected because FR-024 and FR-025 require missing generated-owned data to be populated when enough source intent exists.
- Add schema-backed ownership metadata for every connector and IP relationship. Rejected for this slice because deterministic generated names plus completed-run logs satisfy the current reporting requirement without a migration.
- Treat connectivity reconciliation as a hostvars-only concern. Rejected because hostvars derive uplinks from `InterfacePhysical.connector`/`NetworkLink` and interface IP data; missing graph connectivity must be repaired before hostvars run.

## Decision: Keep hostvar readiness and structured-config cascade rack-owned

**Rationale**: `RackGenerator` already marks `generation_complete`, checks all racks under the fabric, invalidates target hostvar files, and triggers `generate-avd-device-hostvar`. It also detects bootstrap state and expands hostvar targets to the full fabric when any fabric device is missing hostvars. Once unchanged racks are guaranteed to run, this existing behavior satisfies hostvar and structured-config continuation.

**Alternatives considered**:
- Trigger hostvars directly from `generate-fabric`. Rejected because hostvars need completed pod/rack cabling and all rack generation state.
- Trigger structured config directly after hostvars. Rejected because the existing `avd_hostvars_ready` trigger already owns the Phase 1 to Phase 2 transition.

## Decision: Do not expose override mode in this planning slice

**Rationale**: The local GraphQL schema defines `GeneratorDefinitionRequestRunInput` with only `id` and `nodes`; there is no runtime field for arbitrary generator options. A safe override must be deliberate and visible, which means a separate external contract such as distinct override generator definitions, a service-portal workflow, or schema-backed run setting. That is beyond the default preservation fix and would need its own acceptance criteria.

**Alternatives considered**:
- Infer override from branch name or environment variable. Rejected because it is not explicit or safely visible to the operator.
- Add a persisted `override` fabric attribute. Rejected for this slice because it adds schema and lifecycle questions.
- Add duplicate override generator definitions for fabric, pod, and rack. Feasible, but deferred because it expands `.infrahub.yml`, operator UX, documentation, and tests beyond the required P1/P2 behavior.

## Decision: Validation must include repeated reconciliation, not only first generation

**Rationale**: The reported failure occurs on already deployed or partially pre-seeded fabrics. Unit tests should cover unchanged checksum continuation and fill-only device reconciliation, while integration/live tests should prove one explicit fabric run eventually produces pod, rack, hostvars, and structured config outputs without duplicates.

**Alternatives considered**:
- Rely only on existing e2e first-generation tests. Rejected because they do not cover unchanged checksum targets or pre-seeded device attributes.
- Validate only by direct local generator calls. Rejected because the cascade depends on Infrahub trigger/task-worker behavior.
