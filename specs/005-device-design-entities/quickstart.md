# Quickstart: Validate Device Design Entities Schema

Runnable validation and rollout guide for the schema change. Implementation details (final YAML, generator/object edits) live in `tasks.md` and the follow-on cycles.

## Prerequisites

- Infrahub reachable (`uv run infrahubctl info` → Connection Status ✅).
- Working from repo root on this feature's branch.
- The `infrahub-managing-schemas` skill drives the actual YAML authoring.

## Stage 1 — Additive schema (safe to load anytime)

Author `schemas/device_design.yml` (generic + 3 concrete nodes + container `device_designs` relationships via `extensions`), then validate and roll out on a branch:

```bash
alias ihctl='uv run infrahubctl'

# 1. Validate before load (catches identifier/uniqueness/kind errors)
ihctl schema check schemas/

# 2. Roll out on a dedicated branch (never the default branch)
ihctl branch create device-design-entities
ihctl schema check schemas/ --branch device-design-entities
ihctl schema load schemas --branch device-design-entities

# 3. Regenerate typed protocols after the schema loads
ihctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py
```

**Expected**: schema check passes with zero errors (**SC-001**). In the UI the three concrete design nodes exist (hidden from the menu via `include_in_menu: false`, **SC-002**).

### Identifier-collision fallback (research Decision 5)

If `schema check` reports a duplicate/ambiguous identifier for `device_template` across the inheriting kinds, give each concrete node its own template identifier (`fabric_design__template`, `pod_design__template`, `rack_design__template`) and re-run the check.

## Stage 1 acceptance checks

Create instances on the branch (UI or GraphQL) and confirm behavior:

1. **Create a design** — add a `NetworkRackDeviceDesign` to a rack with `role: leaf`, `device_quantity: 2`, a `device_template`. → created, owned by the rack, `human_friendly_id` renders `"<rack>__leaf"` (**SC-003**, spec US1 scenario 2).
2. **Duplicate role rejected** — add a second `leaf` design to the same rack. → rejected by the uniqueness constraint (**SC-004**, US1 scenario 3).
3. **Cascade on delete** — delete a container that has designs. → its `device_designs` are deleted; the referenced `CoreObjectTemplate` still exists (**SC-005**, US1 scenario 4). Verify the template survives:
   ```bash
   ihctl object get CoreObjectTemplate --branch device-design-entities   # template still listed
   ```
4. **All three tiers** — attach a `super_spine` design to a fabric and a `spine` design to a pod; confirm the same entity shape renders on all tiers (**SC-006**, US2).
5. **Data-only extensibility** — with no further schema edit, add another supported-role design at the data layer. → accepted (**SC-007**, US3).

## Stage 2 — Migrate existing data

Populate `device_designs` from the current container fields **before** removing them (FR-062).

- **Reference repo**: handled by the follow-on Objects cycle (rewrites `objects/*.yml` to declare `device_designs`).
- **Live instance**: run a one-time idempotent SDK helper that, per container, reads each old template/quantity field and upserts the matching design keyed by `(container, role)` HFID. Re-running is a no-op (upsert).

Verify no container lost its design intent:

```bash
# Spot-check: every container that had an old template now has a matching design
ihctl object get NetworkRackDeviceDesign --branch device-design-entities
```

## Stage 3 — Remove old fields (gated)

**Only after** Stage 2 and the follow-on generator + objects cycles are complete (generators no longer read the old fields). Mark the four template relationships and four quantity attributes `state: absent` in `logical_design.yml`, `location_extensions.yml`, `l3ls_extensions.yml`, then:

```bash
ihctl schema check schemas/ --branch device-design-entities
ihctl schema load schemas --branch device-design-entities
ihctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py
```

**Expected**: the removed fields no longer appear on the container nodes; `device_designs` is the sole source of design intent (**SC-006**).

## Local quality gates (per constitution)

```bash
uv run pytest tests/unit          # migration-helper unit tests (if a live helper is added)
uv run invoke lint                # ruff + mypy + yamllint
```

Schema/protocol evidence (schema-check output + regenerated `protocols.py`) and `$infrahub-run-integration-tests` coverage of the schema migration + repository load are required before merge (Constitution Principle IV). Merge the branch via a proposed change — not a direct default-branch load.

## Definition of done (this schema cycle)

- [ ] `schemas/device_design.yml` authored; `schema check` passes (SC-001).
- [ ] All three concrete nodes + container `device_designs` load; protocols regenerated (SC-002).
- [ ] HFID, uniqueness, and cascade behavior verified on-branch (SC-003, SC-004, SC-005).
- [ ] All three tiers express designs through the entity; data-only add works (SC-006, SC-007).
- [ ] `state: absent` removals authored and staged (load gated behind follow-on cycles).
- [ ] Follow-on cycles noted: generator, objects, docs (see spec "Dependencies & Out of Scope").
