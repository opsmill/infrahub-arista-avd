# Quickstart: Validate Device-Design-Driven Generators

Runnable validation guide. Implementation details (final `.gql`/Python) live in `tasks.md` and the implementation phase.

## Prerequisites

- Infrahub reachable (`uv run infrahubctl info` → ✅).
- The 001 schema (`device_designs`) loaded on the working branch.
- **Co-requisite**: seed objects migrated to `device_designs` (the Objects cycle). Without populated designs these generators produce nothing — this is the hard cutover. Land the Objects cycle and this cycle together.
- Author changes with the `infrahub-managing-generators` skill.

## Build & regenerate

For each generator, edit the `.gql`, then regenerate its typed model:

```bash
alias ihctl='uv run infrahubctl'
# after editing each query:
ihctl graphql generate-return-types generators/generate_fabric.gql
ihctl graphql generate-return-types generators/generate_pod.gql
ihctl graphql generate-return-types generators/generate_rack.gql
```

Then implement the `generate()` changes and the shared helper on `GeneratorMixin`.

## Unit validation (fast, no server)

```bash
uv run pytest tests/unit/test_device_design_resolution.py
uv run invoke lint      # ruff (C901 ≤17) + mypy + yamllint
```

Expected: the resolver returns `(template_id, quantity)` per role and `(None, 0)` for an absent role (absence-means-none), including a missing `leaf` design → 0 leaves.

## Generator run + parity (on a branch with populated designs)

Run each generator against a target and confirm the device set matches the pre-refactor fabric:

```bash
ihctl branch create device-design-generators
# (load migrated seed objects onto the branch first)
ihctl generator generate-fabric --target <fabric-name> --branch device-design-generators
ihctl generator generate-pod    --target <pod-name>    --branch device-design-generators
ihctl generator generate-rack   --target <rack-name>   --branch device-design-generators
```

Expected outcomes:

- **Fabric** (SC-003): `super_spine` design × M → M `ss-<fabric>-<idx>` devices (role `super_spine`). Absent design → no super-spines, no error (SC-004).
- **Pod** (SC-003): `spine` design × N → N `spine-<pod>-<idx>` devices; the fabric-super-spine completeness guard reads the fabric `super_spine` design quantity.
- **Rack** (SC-001): `leaf`×2 + `l2leaf`×1 → the same leaf/L2-leaf devices, names, roles, templates, and MLAG pairing as the legacy fields produced; the pod-spine completeness guard reads the pod `spine` design quantity. Standalone-L2LS underlay still switches primary-leaf role to `l2leaf` (US1 scenario 4).

## Idempotence & convergence (SC-002, SC-005)

```bash
# Re-run with no design change → no diff:
ihctl generator generate-rack --target <rack-name> --branch device-design-generators   # run twice
```

- Second run makes no changes (checksum short-circuit / upsert no-op) (SC-002).
- Increase a `leaf` design's `device_quantity` → re-run creates the new leaf + updates MLAG/cabling.
- Remove the `l2leaf` design → re-run cleans up the L2-leaf devices (no orphans) (SC-005).

Run the mandated idempotence gate where live validation is permitted:

```bash
# $infrahub-test-generator-idempotence  (repeated-run, snapshot, no-diff)
```

## Integration & merge gates (per constitution)

- `$infrahub-run-integration-tests` for the generator chain (records tested branch + commit).
- `$infrahub-test-generator-idempotence` evidence (validation branch, scenario, snapshot scope, no-diff).
- `uv run invoke lint` clean.
- Merge via a proposed change with the co-requisite Objects cycle.

## Definition of done (this generator cycle)

- [ ] Three `.gql` queries select `device_designs` (+ cross-tier upstream `device_designs`); legacy field selections removed.
- [ ] `generators/*_query.py` regenerated from the `.gql` files (not hand-edited).
- [ ] Shared `device_design_for()` helper on `GeneratorMixin`; three `generate()` methods read designs per role.
- [ ] Cross-tier completeness guards (pod←fabric, rack←pod) read upstream `device_designs` quantities.
- [ ] Unit tests pass; lint clean; parity + idempotence validated on a branch.
- [ ] Co-requisite Objects cycle ready to land together; Stage-3 schema removal (005 T020) still gated for afterwards.
