# Tasks: AVD Example Designs (Generator + Objects)

**Input**: Design documents from `/specs/006-avd-example-designs/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/generator-hostvars.md`, `contracts/seed-objects.md`, `.specify/memory/constitution.md`

**Tests**: Required by the constitution (Test-Required Quality) and the spec. Test tasks are listed before the implementation they validate.

**Depends on**: feature `005-avd-example-fabrics` (schema: roles, EVPN inputs, underlay modes) being present in the working tree.

**Organization**: Tasks are grouped by user story (US1–US7 from spec.md). Each scenario is an independently demonstrable increment where dependencies allow.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Different files, no dependency on incomplete tasks
- **[Story]**: `US1`–`US7` for story-phase tasks only
- Every task names an exact repository file path

**Shared-file note**: `generators/generate_avd_device_hostvar.py` is edited by US2/US3/US4/US6; `generators/generate_rack.py` by US4/US5; `tests/unit/test_generate_avd_device_hostvar.py` by several stories. Cross-story edits to the same file are **not** `[P]` and MUST be sequenced.

**Design note**: pyAVD 6.3 has no `design.type` (research R1) — behavior is `type` + built-in `node_type_keys`. No task sets a design type.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm scope and inspect the generators/conventions before edits.

- [X] T001 Confirm the generator+objects scope and delivery models in `specs/006-avd-example-designs/plan.md`
- [X] T002 [P] Review generator authoring rules from the `infrahub-managing-generators` skill
- [X] T003 [P] Review object-population rules from the `infrahub-managing-objects` skill
- [X] T004 [P] Inspect the topology generators and cabling helpers in `generators/generate_pod.py` and `generators/generate_rack.py`
- [X] T005 [P] Inspect the hostvars assembly (`_build_hostvars`) and per-device path in `generators/generate_avd_device_hostvar.py`
- [X] T006 [P] Inspect the existing Fabric-C seed-design file set as the template pattern in `objects/` (e.g. `objects/10a_fabric_c_fabric.yml`, `objects/11a_fabric_c_rack.yml`, `objects/12a_fabric_c_evpn.yml`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared test scaffolding and seed-design conventions all stories rely on.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [X] T007 Ensure the `005` schema is loaded on the working branch and confirm the new roles/inputs are queryable in `specs/006-avd-example-designs/quickstart.md`
- [X] T008 [P] Add reusable hostvars fixture builders (fabric/pod/device with new inputs: `evpn_vlan_aware_bundles`, `evpn_gateway`, underlay `none`/`isis-ldp`, super-spine) in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T009 [P] Add a test asserting the hostvar generator never emits a `design`/`design.type` key (research R1) in `tests/unit/test_generate_avd_device_hostvar.py`
- [ ] T010 Record the seed-design pool/ASN/name isolation convention (numbering, distinct pools) in `specs/006-avd-example-designs/contracts/seed-objects.md`

**Checkpoint**: Test scaffolding and conventions ready.

---

## Phase 3: User Story 1 - Single-DC L3LS seed design renders (Priority: P1) 🎯 MVP

**Goal**: A loadable Single-DC L3LS seed design that renders end to end (no generator change).

**Independent Test**: Load the seed design, run the generator chain, confirm all devices render valid EOS config with eBGP underlay + EVPN symmetric IRB; re-run is a no-op.

### Tests for User Story 1

- [X] T011 [P] [US1] Add an integration assertion that the Single-DC L3LS seed design loads and renders EOS config for all devices in `tests/integration/test_e2e_pipeline.py`

### Implementation for User Story 1

- [X] T012 [US1] Author the Single-DC L3LS seed design (manufacturer, device types, pools, management, templates, fabric, racks, EVPN services) as numbered files in `objects/` (Fabric-C style, unique names/pools)
- [X] T013 [US1] Validate US1: load objects, run the generator chain, confirm render and idempotence; record evidence in `specs/006-avd-example-designs/quickstart.md`

**Checkpoint**: Baseline scenario demonstrable; validates the load→generate→render harness.

---

## Phase 4: User Story 2 - Multi-Pod 5-stage Clos renders (Priority: P1)

**Goal**: Super-spines render as EVPN route servers; tenants render as vlan-aware bundles.

**Independent Test**: Load a two-pod fabric with super-spines and `evpn_vlan_aware_bundles`, generate, confirm route-server super-spines and vlan-aware-bundle tenants.

### Tests for User Story 2

- [X] T014 [P] [US2] Add hostvars tests: `role == super_spine` renders `evpn_role: server` in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T015 [P] [US2] Add hostvars tests: `fabric.evpn_vlan_aware_bundles` true renders tenants as vlan-aware bundles; unchanged when false in `tests/unit/test_generate_avd_device_hostvar.py`

### Implementation for User Story 2

- [X] T016 [US2] Consume `evpn_vlan_aware_bundles` and derive super-spine `evpn_role: server` in `generators/generate_avd_device_hostvar.py`
- [X] T017 [US2] Add `evpn_vlan_aware_bundles` (and any needed fields) to `generators/avd_device_hostvar.gql` and regenerate the typed model in `generators/generate_avd_device_inputs_query.py`
- [X] T018 [US2] Author the 5-stage Clos seed design (super-spines + two pods + tenant with route targets, `evpn_vlan_aware_bundles: true`) as numbered files in `objects/`
- [X] T019 [US2] Validate US2: generate and confirm route-server + vlan-aware-bundle rendering and idempotence; record evidence in `specs/006-avd-example-designs/quickstart.md`

**Checkpoint**: 5-stage Clos demonstrable.

---

## Phase 5: User Story 3 - Dual-DC L3LS with EVPN DC Gateway renders (Priority: P1)

**Goal**: Two DCs joined by DCI links; gateway leaves render EVPN DC Gateway next-hop-self.

**Independent Test**: Load two fabrics + `dci` NetworkLinks with `evpn_gateway` leaves, generate, confirm inter-DC `l3_edge` and gateway next-hop-self.

### Tests for User Story 3

- [X] T020 [P] [US3] Add hostvars tests: `device.evpn_gateway` true renders EVPN DC Gateway next-hop-self; unchanged when false in `tests/unit/test_generate_avd_device_hostvar.py`

### Implementation for User Story 3

- [X] T021 [US3] Render `evpn_gateway` next-hop-self behavior in `generators/generate_avd_device_hostvar.py`
- [X] T022 [US3] Add `evpn_gateway` to `generators/avd_device_hostvar.gql` and regenerate the typed model in `generators/generate_avd_device_inputs_query.py`
- [ ] T023 [US3] Author the Dual-DC seed design (two fabrics + border leaves with `evpn_gateway: true` + `dci` NetworkLinks + `dci_pool`) as numbered files in `objects/`
- [ ] T024 [US3] Validate US3: generate and confirm DCI `l3_edge` + gateway rendering and idempotence; record evidence in `specs/006-avd-example-designs/quickstart.md`

**Checkpoint**: Dual-DC demonstrable — MVP (P1) complete.

---

## Phase 6: User Story 4 - Standalone L2LS fabric renders (Priority: P2)

**Goal**: Standalone L2 leaf-spine (no EVPN/underlay) with optional L3-on-spine variant.

**Independent Test**: Load an L2LS design (2 spines, 4 leaves, MLAG both tiers, underlay `none`), generate, confirm pure-L2 EOS + VLAN tag filtering; switch to `l3spine` and confirm SVI routing.

### Tests for User Story 4

- [X] T025 [P] [US4] Add hostvars tests: `underlay_routing_protocol == none` omits underlay emission and requires no underlay pools in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T026 [P] [US4] Add topology tests for the L2LS branch (`l2spine`/`l3spine` device + cabling creation) in `tests/unit/test_generate_rack.py`

### Implementation for User Story 4

- [X] T027 [US4] Add the standalone L2LS topology branch (`l2spine`/`l3spine`, MLAG, port-channel/uplink cabling) in `generators/generate_rack.py` (and `generators/generate_pod.py` if spine-tier changes are needed)
- [X] T028 [US4] Handle `underlay_routing_protocol == none` (omit underlay, skip underlay pools) in `generators/generate_avd_device_hostvar.py`
- [X] T029 [US4] Author the L2LS seed design (`l2spine`/`l2leaf`, optional `l3spine` variant, underlay `none`, VLANs with tag filtering) as numbered files in `objects/`
- [X] T030 [US4] Validate US4: generate both variants, confirm L2 + L3-spine rendering, existing L3LS unchanged, idempotence; record evidence in `specs/006-avd-example-designs/quickstart.md`

**Checkpoint**: L2LS demonstrable.

---

## Phase 7: User Story 5 - Campus fabric renders (Priority: P2)

**Goal**: Three-tier campus with OSPF, hierarchical IDF, and escape-hatch access features.

**Independent Test**: Load a campus design (l3spine core + IDF access incl. aggregation/edge tier), generate, confirm OSPF underlay, spine SVI routing, and access features.

### Tests for User Story 5

- [X] T031 [P] [US5] Add topology tests for the campus hierarchical IDF (aggregation leaf feeding edge leaves) in `tests/unit/test_generate_rack.py`
- [X] T032 [P] [US5] Add hostvars tests for campus escape-hatch access features (dot1x/PoE/port-profiles/in-band mgmt) merged correctly in `tests/unit/test_generate_avd_device_hostvar.py`

### Implementation for User Story 5

- [X] T033 [US5] Add the campus topology branch (`l3spine` core + hierarchical IDF via parent/uplink relationships, OSPF underlay) in `generators/generate_rack.py`
- [X] T034 [US5] Author the campus seed design (core spines + IDF access incl. aggregation/edge, OSPF) with `avd_custom_hostvars` for dot1x/PoE/port-profiles/in-band management as numbered files in `objects/`
- [X] T035 [US5] Validate US5: generate and confirm OSPF + SVI routing + access features + hierarchical IDF and idempotence; record evidence in `specs/006-avd-example-designs/quickstart.md`

**Checkpoint**: Campus demonstrable — P2 complete.

---

## Phase 8: User Story 6 - ISIS-LDP IPVPN WAN renders (Priority: P3)

**Goal**: MPLS core with ISIS-LDP underlay + BGP VPN-IPv4 overlay via directly-seeded devices + escape hatch.

**Independent Test**: Load an ISIS-LDP IPVPN seed design (P/PE/RR), generate, confirm ISIS-LDP underlay, MPLS L3VPN/VPN-IPv4, per-customer VRFs, PE-CE routing.

### Tests for User Story 6

- [X] T036 [P] [US6] Add hostvars tests: `underlay_routing_protocol == isis-ldp` emits the pyAVD ISIS-LDP underlay value in `tests/unit/test_generate_avd_device_hostvar.py`

### Implementation for User Story 6

- [X] T037 [US6] Handle `underlay_routing_protocol == isis-ldp` emission in `generators/generate_avd_device_hostvar.py`
- [X] T038 [US6] Author the ISIS-LDP IPVPN seed design: directly-seeded `p`/`pe`/`rr` devices + interfaces + links, in the `avd_devices` group (not `fabrics`/`racks`), with `avd_custom_hostvars` for MPLS/LDP, VPN-IPv4 overlay, per-customer VRFs, and PE-CE OSPF, as numbered files in `objects/`
- [X] T039 [US6] Validate US6: generate and confirm ISIS-LDP + MPLS L3VPN rendering offline and idempotence; record evidence in `specs/006-avd-example-designs/quickstart.md`

**Checkpoint**: ISIS-LDP IPVPN demonstrable.

---

## Phase 9: User Story 7 - CV-Pathfinder SD-WAN renders (Priority: P3)

**Goal**: SD-WAN with path groups, DPS, application-aware virtual topologies via directly-seeded devices + escape hatch, rendered offline.

**Independent Test**: Load a CV-Pathfinder seed design (pathfinders + edge/transit routers), generate, confirm WAN roles, path groups, DPS, and application-aware policies render without live CVaaS.

### Tests for User Story 7

- [X] T040 [P] [US7] Add hostvars tests for CV-Pathfinder escape-hatch payloads (path groups, DPS, virtual topologies) merged correctly in `tests/unit/test_generate_avd_device_hostvar.py`

### Implementation for User Story 7

- [X] T041 [US7] Author the CV-Pathfinder seed design: directly-seeded `wan_router`/`wan_rr` devices + interfaces + links, in the `avd_devices` group, with `avd_custom_hostvars` for path groups (MPLS/INTERNET), DPS/flow tracking, application-aware virtual topologies, WAN HA, STUN, and CVaaS metadata, as numbered files in `objects/`
- [X] T042 [US7] Validate US7: generate and confirm SD-WAN rendering offline (no live CVaaS) and idempotence; record evidence in `specs/006-avd-example-designs/quickstart.md`

**Checkpoint**: All seven scenarios demonstrable.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Registration, regeneration, docs, and project-wide validation.

- [X] T043 Register any new/changed generator and query definitions and confirm existing ones in `.infrahub.yml`
- [X] T044 Regenerate protocol classes from the loaded branch (`infrahubctl protocols --branch <branch>`), not hand-edited, in `src/solution_arista_avd/protocols.py`
- [X] T045 [P] Update the per-scenario status (mark all seven supported) in `docs/docs/supported-capabilities.md`
- [X] T046 [P] Document each seed design (load/generate steps, native-vs-escape-hatch) in `docs/docs/developer-guide/avd/overview.md` and `docs/docs/developer-guide/avd/hostvars.md`
- [ ] T047 [P] Document generator debugging for the new designs in `docs/docs/developer-guide/avd/debugging.md`
- [X] T048 Run `uv run infrahubctl object load objects/ --branch <branch>` and confirm all seven designs load with no reference/validation errors; record in `specs/006-avd-example-designs/quickstart.md`
- [X] T049 Run `uv run pytest tests/unit` and address failures
- [ ] T050 Run `uv run invoke lint` and address ruff/mypy/yamllint findings
- [ ] T051 Run docs build/typecheck (`npm run typecheck` and `npm run build` from `docs/`) and address failures
- [ ] T052 Review changed objects, specs, and docs for private lab hostnames/tokens and remove any findings in `specs/006-avd-example-designs/quickstart.md`
- [ ] T053 Run `$infrahub-run-integration-tests` for the generator/object changes and record the tested branch/commit in `specs/006-avd-example-designs/quickstart.md`
- [ ] T054 Run `$infrahub-test-generator-idempotence` for the generator changes across all seven designs (or document the approved alternative) in `specs/006-avd-example-designs/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **US1 (Phase 3)**: Depends on Foundational; no generator change.
- **US2 (Phase 4)**, **US3 (Phase 5)**: Depend on Foundational; both edit `generate_avd_device_hostvar.py` and the hostvar query — sequence same-file edits.
- **US4 (Phase 6)**: Depends on Foundational; edits `generate_rack.py` and `generate_avd_device_hostvar.py`.
- **US5 (Phase 7)**: Depends on US4 (shares the `generate_rack.py` topology-branch work and reuses `l3spine`).
- **US6 (Phase 8)**: Depends on Foundational; edits `generate_avd_device_hostvar.py` (sequence with US2/US3/US4).
- **US7 (Phase 9)**: Depends on Foundational; mostly seed data + escape hatch.
- **Polish (Phase 10)**: Depends on all desired stories (protocol regen and integration/idempotence run last).

### Within Each User Story

- Tests before implementation.
- Seed objects and generator changes can proceed together, but the scenario is only "done" once it renders and is idempotent.
- GraphQL query changes precede typed-model regeneration.

---

## Parallel Opportunities

- Setup: T002–T006 in parallel.
- Foundational: T008, T009 in parallel (same file — author as distinct test functions, then commit together).
- Per-story test tasks marked [P] can be drafted in parallel with that story's seed-object authoring.
- WAN seed designs (US6 T038, US7 T041) touch only `objects/` and can be authored in parallel with each other.
- Polish docs: T045, T046, T047 (different files) in parallel.
- **Not parallel**: all edits to `generators/generate_avd_device_hostvar.py` (US2/US3/US4/US6) and `generators/generate_rack.py` (US4/US5) — sequence them.

---

## Parallel Example: User Story 2

```text
Task: "T014 [P] [US2] super-spine renders evpn_role: server in tests/unit/test_generate_avd_device_hostvar.py"
Task: "T015 [P] [US2] evpn_vlan_aware_bundles renders vlan-aware bundles in tests/unit/test_generate_avd_device_hostvar.py"
```

## Parallel Example: WAN seed designs

```text
Task: "T038 [US6] ISIS-LDP IPVPN seed design (p/pe/rr + escape hatch) in objects/"
Task: "T041 [US7] CV-Pathfinder seed design (wan_router/wan_rr + escape hatch) in objects/"
```

---

## Implementation Strategy

### MVP First (User Stories 1–3, all P1)

1. Complete Setup + Foundational.
2. US1 (baseline seed), US2 (route-server + vlan-aware), US3 (gateway + dual-DC).
3. **STOP and VALIDATE**: three DC-family scenarios render and are idempotent; existing designs unchanged.
4. This is a shippable increment on its own.

### Incremental Delivery

1. Setup + Foundational → scaffolding.
2. P1 (US1–US3) → DC family → validate/demo.
3. P2 (US4–US5) → L2LS + campus → validate/demo.
4. P3 (US6–US7) → ISIS-LDP + CV-Pathfinder → validate/demo (splittable into a dedicated feature).
5. Polish → registration, regen, docs, integration + idempotence validation.

### Parallel Team Strategy

- One implementer owns `generate_avd_device_hostvar.py` rendering (US2/US3/US4/US6) sequentially.
- Another owns `generate_rack.py` topology branches (US4/US5).
- Seed-object authors work per scenario in `objects/` in parallel.
- Docs (T045–T047) parallelize at the end.

---

## Notes

- pyAVD 6.3 has no `design.type` — behavior is `type` + `node_type_keys` (research R1). No task sets a design type.
- `src/solution_arista_avd/protocols.py` and `*_query.py` are regenerated (T044, T017/T022), never hand-edited.
- Every device must resolve to a valid AVD node type; unmapped roles abort generation (no silent skip).
- Existing L3LS/Fabric-A/B/C output must not change (regression-guarded in each story's validation).
- Idempotence (Constitution II) is the highest risk: all writes upsert, deterministic ordering, and `$infrahub-test-generator-idempotence` per design (T054).
- Scenarios 6–7 may be split into their own feature if their depth warrants (per `005` R8).
```
