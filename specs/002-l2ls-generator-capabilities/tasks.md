---
description: "Task list for L2LS Generator Capabilities — Generator cycle"
---

# Tasks: L2LS Generator Capabilities (Generator cycle)

**Input**: Design documents from `/specs/002-l2ls-generator-capabilities/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md,
contracts/generator-contract.md, quickstart.md; **feature 001 schema + seed merged/loaded**.

**Tests**: Included (spec + constitution mandate). Generator changes are validated
with unit tests, the comparison harness, and `$infrahub-test-generator-idempotence`.

**Scope**: Generator behavior only. Target is **feature-level parity** — hostnames
and environment-specific values need not match the example. All new behavior is
gated on `underlay_routing_protocol == none` so other fabrics are untouched.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 / US3 / US4 (maps to spec.md user stories)

## Path Conventions

Infrahub reference-design repo: `generators/`, `objects/`, `src/solution_arista_avd/`,
`tests/`, `docs/` at repository root.

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Create the working branch and confirm feature-001 schema + `Fabric-L2LS` seed are present: `uv run infrahubctl branch create l2ls-gen-capabilities`; `alias ihctl='uv run infrahubctl'`
- [X] T002 [P] Capture a green baseline: `uv run pytest tests/unit -q` and `uv run invoke lint` (record the pre-existing `test_cv_integration` failure so it is not attributed to this cycle)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: These block the user-story hostvar/MLAG work.

- [ ] T003 Update `generators/avd_device_hostvar.gql` to fetch the now-optional `mac_vrf_vni_base` and the `Evpn.L2Vlan` `rack_tags`/`avd_tags`; regenerate the typed model: `uv run infrahubctl graphql generate-return-types generators/avd_device_hostvar.gql` → `generators/generate_avd_device_hostvar_query.py` (do NOT hand-edit)
- [X] T004 Factor the l2leaf MLAG peer-link carving in `generators/generate_rack.py` (`_assign_l2leaf_mlag_peer_interfaces`) into a shared, deterministic, idempotent helper usable by both the rack (l2leaf) and pod (l2spine) generators

**Checkpoint**: Typed query + shared carving helper ready.

---

## Phase 3: User Story 1 - Topology, MLAG both tiers, MSTP (Priority: P1) 🎯 MVP

**Goal**: Generation creates the l2spine/l2leaf topology, forms MLAG on **both** tiers (with peer-link carving), aggregates leaf uplinks into LACP Port-Channels, and applies per-tier MSTP priorities.

**Independent Test**: Generate the fabric; confirm a spine MLAG pair and each leaf MLAG pair exist with carved peer interfaces, leaf uplinks aggregate to a Port-Channel, and hostvars carry MSTP priorities (l2spine 4096 / l2leaf 16384).

### Tests for User Story 1

- [X] T005 [P] [US1] Unit test in `tests/unit/test_generate_pod.py`: for underlay `none`, the pod generator forms an l2spine MLAG pair and carves peer-link interfaces deterministically (highest ports, no collision, idempotent on re-run)

### Implementation for User Story 1

- [X] T006 [US1] In `generators/generate_pod.py`, create the l2spine MLAG domain + carve peer-link interfaces (reuse the T004 helper), gated on `underlay_routing_protocol == none`, using `allow_upsert=True` and deterministic natural keys
- [X] T007 [US1] Verify/extend leaf uplink LACP Port-Channel aggregation and per-tier MSTP priority rendering; add an assertion in `tests/unit/test_generate_avd_device_hostvar.py` that l2spine/l2leaf hostvars carry the fabric's MSTP priorities

**Checkpoint**: L2LS topology with MLAG on both tiers, uplink port-channels, and MSTP renders.

---

## Phase 4: User Story 2 - Tag-scoped pure-Layer-2 VLANs (Priority: P1)

**Goal**: Overlay-free tenant VLANs render as tag-scoped pure-L2 VLANs — VNI base omitted, `l2vlans[].tags` emitted, and per-node `filter.tags` on leaves — with no VXLAN/BGP/EVPN.

**Independent Test**: Build hostvars; confirm the tenant emits no `mac_vrf_vni_base`, each l2vlan carries its tags, each leaf carries `filter.tags`, and RACK1 leaves get VLANs 10/20 while RACK2 leaves get 10/30.

### Tests for User Story 2

- [X] T008 [P] [US2] Unit test in `tests/unit/test_generate_avd_device_hostvar.py`: `_build_tenants_hostvars` omits `mac_vrf_vni_base` when unset, emits it when set (overlay tenant unchanged), and emits `l2vlans[].tags` from `rack_tags`/`avd_tags`
- [ ] T009 [P] [US2] Unit test in `tests/unit/test_generate_avd_device_hostvar.py`: the node-config builder emits `filter.tags` for l2leaf nodes from their rack's `avd_tags`

### Implementation for User Story 2

- [X] T010 [US2] In `generators/generate_avd_device_hostvar.py` `_build_tenants_hostvars`, only set `mac_vrf_vni_base` when the tenant value is not `None` (line ~1265)
- [X] T011 [US2] In the l2vlans builder (`generators/generate_avd_device_hostvar.py` ~lines 1314-1324), fetch `rack_tags`/`avd_tags` and set `l2v_data["tags"]` reusing the SVI tag helper (`_build_svi_tags` → generalize to `_build_tags`)
- [X] T012 [US2] In the node-config builder (`generators/generate_avd_device_hostvar.py` ~line 1672), emit `node_config["filter"] = {"tags": [...]}` for leaf nodes from the rack's `avd_tags` (and rack name)

**Checkpoint**: Tag-scoped, overlay-free VLANs render; no VNI/VXLAN.

---

## Phase 5: User Story 3 - Host access ports + dual-homed firewall (Priority: P2)

**Goal**: Host endpoints render as access ports (VLAN + edge PortFast); the firewall renders as a trunk Port-Channel dual-homed to both spines.

**Independent Test**: Generate the fabric; confirm host leaf ports are access ports on the correct VLAN with edge PortFast, and the firewall is a trunk Port-Channel on both spines allowing the fabric VLANs.

### Tests for User Story 3

- [ ] T013 [P] [US3] Unit test in `tests/unit/test_generate_avd_device_hostvar.py`: a host access adapter renders `mode: access`, the access VLAN, and `spanning_tree_portfast: edge`
- [ ] T014 [P] [US3] Unit test: a firewall endpoint dual-homed to both spines renders as a trunk Port-Channel allowing the fabric VLANs (or, if the escape-hatch path is chosen, `avd_custom_hostvars` carries the firewall block on both spines)

### Implementation for User Story 3

- [ ] T015 [US3] In `generators/generate_avd_device_hostvar.py`, wire `spanning_tree_portfast` into the connected-endpoint/adapter build for host access ports
- [~] T016 [US3] (DROPPED per request — firewall excluded) Add the firewall dual-homed-to-spines cabling in the server-cabling path (`generators/generate_server_cabling.py`) — attach the endpoint to both spines and render a trunk Port-Channel; native if reasonable, else the documented `avd_custom_hostvars` fallback on the spines; idempotent (`allow_upsert=True`)
- [~] T017 [US3] (DROPPED per request — firewall excluded) Reshape `objects/13h_fabric_l2ls_servers.yml`: named host endpoints on leaf access ports (per-color access profiles) + a `FIREWALL` endpoint modeled for dual-homing to the spines

**Checkpoint**: Endpoints and the firewall render correctly.

---

## Phase 6: User Story 4 - Conformance & idempotence verification (Priority: P2)

**Goal**: Prove feature-level parity, pure-L2, zero PyAVD violations, idempotence, and no regression.

**Independent Test**: Run the comparison harness + idempotence path against the generated fabric and confirm the criteria.

- [X] T018 [US4] Render the L2LS device configs and assert the pure-L2 invariant: no `interface Vxlan`, `router bgp`, or EVPN address-family in any L2LS config; zero PyAVD validation violations
- [ ] T019 [US4] Run `uv run python scripts/compare_avd_examples.py` for `l2ls-fabric`; confirm feature-section parity (MLAG, MSTP, VLAN, trunk, access, port-channel), tolerating hostname/address normalization
- [ ] T020 [US4] Validate idempotence with `$infrahub-test-generator-idempotence` — repeated generation produces no object churn and no config drift (spine MLAG, carved interfaces, firewall cabling)
- [X] T021 [US4] Regression: `uv run pytest tests/unit -q` and confirm existing overlay fabrics (Fabric-A/C/Campus/ISIS-LDP) render unchanged (contract C6)

**Checkpoint**: Conformance and idempotence proven.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T022 [P] Lint gate: `uv run invoke lint` (ruff/mypy/yamllint) clean; regenerate `src/solution_arista_avd/protocols.py` only if a schema touch was required
- [ ] T023 [P] Docs: update `docs/docs/developer-guide/avd/role-mapping.md` (spine MLAG under underlay none) and `docs/docs/developer-guide/avd/hostvars.md` (overlay-free tenant, l2vlan tags, node `filter.tags`)
- [ ] T024 Update `docs/docs/supported-capabilities.md`: mark the L2LS firewall endpoint delivered and record the native-vs-`avd_custom_hostvars` choice from T016 (FR-019 carryover)
- [ ] T025 Run the full `quickstart.md` validation (Steps 1-6) and confirm all cycle validation-criteria checkboxes pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: after Setup; T003 (typed query) blocks US2; T004 (carving helper) blocks US1.
- **US1 (Phase 3)**: after T004.
- **US2 (Phase 4)**: after T003. Independent of US1 (different code paths: MLAG creation vs hostvar tenant/node builders).
- **US3 (Phase 5)**: after T003 (hostvar path). Benefits from US1 (spines exist) for firewall cabling validation.
- **US4 (Phase 6)**: after US1–US3 (verifies the whole).
- **Polish (Phase 7)**: after Phase 6.

### User Story Dependencies

- **US1 (P1)**: spine/leaf MLAG + MSTP — independent core.
- **US2 (P1)**: pure-L2 tag scoping — independent of US1 (hostvar builders).
- **US3 (P2)**: endpoints/firewall — hostvar + cabling; firewall validation wants US1's spines.
- **US4 (P2)**: verification — depends on all.

### Within Each User Story

- Contract/unit tests first (fail-then-pass), then implementation.
- Idempotence (`allow_upsert`, deterministic keys) is mandatory for every new create.

### Parallel Opportunities

- T002 baseline runs alongside setup.
- Test tasks T005, T008, T009, T013, T014 are `[P]`.
- US1 (generate_pod.py) and US2 (hostvar builders) touch different files → parallelizable after Phase 2.
- Docs tasks T022, T023 are `[P]`.

---

## Parallel Example: Foundational + first tests

```bash
# Phase 2 foundational (different files):
Task: "Update avd_device_hostvar.gql + regenerate query model (T003)"
Task: "Factor shared MLAG carving helper (T004)"

# First tests across stories (independent):
Task: "Pod l2spine MLAG + carving test (T005)"
Task: "VNI omission + l2vlan tags test (T008)"
Task: "filter.tags node-config test (T009)"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Setup → Foundational (T003/T004) → US1 (spine MLAG both tiers + MSTP).
2. **STOP and VALIDATE**: MLAG pairs + carving + MSTP render; idempotent.

### Incremental Delivery

1. Setup + Foundational → ready.
2. US1 (topology/MLAG) → validate.
3. US2 (pure-L2 tag scoping) → validate.
4. US3 (endpoints + firewall) → validate.
5. US4 (conformance + idempotence) → Polish.
6. Then the Transform/integration cycle (`/speckit-specify` again) delivers the fabric-selectable integration suite.

### Notes

- `[P]` = different files, no dependencies.
- Gate every new behavior on `underlay_routing_protocol == none` (contract C6).
- Never hand-edit `generate_avd_device_hostvar_query.py` — regenerate (T003).
- Every new create uses `allow_upsert=True` + deterministic natural keys (constitution II).
