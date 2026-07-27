# Quickstart: Validate Generator Cascade Preservation

## Prerequisites

- Install project dependencies: `uv sync --all-packages`.
- Load or connect to an Infrahub environment according to local project guidance.
- Use a non-main branch for generator cascade validation, because trigger rules are branch-scoped.
- Ensure `.env` is sourced before local `infrahubctl` commands when using local CLI access:

```bash
set -a; source .env; set +a
```

## Local Unit Validation

Run focused unit tests after implementation:

```bash
uv run pytest tests/unit/test_generate_fabric.py tests/unit/test_generate_pod.py tests/unit/test_generator_mixin.py tests/unit/test_generate_rack.py tests/unit/test_cabling.py tests/unit/test_addressing.py
```

Expected outcomes:

- Fabric generator schedules unchanged non-fabric pod targets directly.
- Pod generator schedules unchanged rack targets directly.
- Changed targets still rely on checksum-trigger updates and are not directly scheduled a second time.
- Existing device `serial` and non-empty `mgmt_ip` are preserved.
- Missing generator-owned device values are populated.
- Missing generated uplink connector relationships and interface IP relationships are populated.
- Non-empty conflicting connector and IP values are preserved and reported as skipped conflicts.
- Repeated reconciliation does not duplicate devices, groups, ASNs, loopback interfaces, or artifacts.

## Full Local Quality Gates

Run the standard local checks before integration validation:

```bash
uv run pytest tests/unit
uv run invoke lint
```

If any GraphQL query is changed, regenerate its return model before running tests. If any schema is changed, run schema validation and regenerate protocols first.

## Reproduced Pre-Seeded Fabric Scenario

Create or use a branch containing an existing fabric with:

- Existing pods and racks.
- At least one device already named as the generator would create it.
- Pre-populated non-empty `serial`.
- Pre-populated non-empty `mgmt_ip`.
- Missing one or more generated fields such as node ID, loopback, VTEP IP, ASN, AVD group membership, hostvars, or structured config.
- Missing one or more generated uplinks, connector relationships, interface attributes, or point-to-point IP assignments.
- At least one intentionally conflicting non-empty connector or IP value, if validating skipped-conflict reporting.

Run only `generate-fabric` for the target fabric on that branch.

Expected outcomes:

- Pod, rack, hostvar, and structured-config stages all complete from the single fabric kickoff.
- The pre-existing `serial` value is unchanged.
- The pre-existing `mgmt_ip` relationship is unchanged.
- Missing generated fields are now present.
- Missing generated uplinks, connector relationships, interface attributes, and point-to-point IP relationships are now present where source intent existed.
- Conflicting non-empty connector and IP values are unchanged and appear in the completed run outcome as skipped conflicts.
- All expected devices have hostvars and structured configs.
- A second run produces no duplicate objects, links, IP addresses, or relationships.

## Integration Validation

For generator code changes, use the required project integration skill:

```text
$infrahub-run-integration-tests
```

The validation report must include the tested branch and commit.

## Generator Idempotence Validation

For generator cascade or generator-owned data changes, use the required idempotence skill when live validation is permitted:

```text
$infrahub-test-generator-idempotence
```

The report must cover a repeated `generate-fabric` run against the pre-seeded-device scenario and confirm no drift on the second run.
The snapshot scope should include generated connectivity kinds such as `NetworkLink`, `InterfacePhysical`, and `IpamIPAddress` so missing-uplink reconciliation and conflict preservation are covered.

## Override Mode

No override-mode validation is required for this slice because the current external generator-run contract does not expose runtime options. If a future task adds an explicit override contract, add separate tests proving only generator-owned fields are overwritten.

## Validation Evidence

- Focused unit validation passed on 2026-07-27:
  `uv run pytest tests/unit/test_generate_fabric.py tests/unit/test_generate_pod.py tests/unit/test_generator_mixin.py tests/unit/test_generate_rack.py tests/unit/test_cabling.py tests/unit/test_addressing.py`
  (`79 passed`).
- Targeted changed-file lint passed on 2026-07-27:
  `uv run ruff check src/solution_arista_avd/cabling.py src/solution_arista_avd/addressing.py tests/unit/test_cabling.py tests/unit/test_addressing.py`.
- Targeted type check passed on 2026-07-27:
  `uv run mypy --show-error-codes src/solution_arista_avd/cabling.py src/solution_arista_avd/addressing.py`.
- Full unit validation passed on 2026-07-27:
  `uv run pytest tests/unit` (`478 passed`).
- Full lint validation passed on 2026-07-27:
  `uv run invoke lint`.
- Remote integration validation with `$infrahub-run-integration-tests` remains
  pending. A remote validation run was started against a temporary validation
  commit and stopped before completion at operator request.
- Live generator idempotence validation with `$infrahub-test-generator-idempotence`
  passed on 2026-07-27 for branch `emdash/pre-seed-devices-b7sa2` at commit
  `2485c0829be374036b41d334d5fe3fb0131852a2`. The shared live validation lab
  was rebuilt to a known state, then a fresh validation branch
  `idempotence-generate-fabric-20260727-1920` was created. Scenario:
  run `generate-fabric name=Fabric-L3LS-Multi-Domain`, wait for the cascade, set
  `spine-infrahub-dc1-1.serial` to `PRESEEDED-SERIAL-2485C08`, then run
  `generate-fabric name=Fabric-L3LS-Multi-Domain` twice. Snapshot scope:
  `NetworkPod`, `LocationRack`, `DcimDevice`, `InterfacePhysical`,
  `InterfaceLag`, `InterfaceVirtual`, `NetworkLink`, `IpamIPAddress`,
  `RoutingAsn`, `MlagDomain`, `AvdArtifact`, `AvdHostvarFile`, and
  `AvdStructuredConfigFile`. Both measured snapshots had SHA256
  `72d02e11c564f05693576d144c34b12ae8f0eaa2680c07d5e27771afc97c6eed` and
  compared identical. Final counts included 12 devices, 12 hostvar files,
  12 structured config files, 64 IP addresses, and the pre-seeded serial was
  preserved.
