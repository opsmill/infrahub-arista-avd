# Quickstart: Validate the Schema-Driven IP Pools change

Run from the repo root with Infrahub up (`inv start`).

## 1. Validate the schema edit

```bash
uv run infrahubctl schema check schemas/
```

Expect zero errors. (SC-001) A duplicate-`identifier` error here means the `loopback_pool` identifier collided — it must be `fabric__loopback_pool`.

## 2. Load schema + objects fresh

```bash
inv load
```

Expect a clean load. (SC-005) If Fabric-B fails with a missing-mandatory-relationship error, the seed-data backfill (`04a_l3ls_pools.yml` + `10_fabric.yml`) is incomplete — every fabric must reference `uplink_pool`, `vtep_pool`, and `loopback_pool`.

## 3. Confirm enforcement (SC-003)

In the UI or via GraphQL, attempt to create a `NetworkFabric` with no `loopback_pool` → the platform must reject it. Creating a `NetworkPod` without MLAG pools must still succeed (FR-021).

## 4. Regenerate protocols (Constitution I & III)

```bash
infrahubctl protocols --out src/solution_arista_avd/protocols.py
```

Confirm `NetworkFabric` in `src/solution_arista_avd/protocols.py` now exposes `loopback_pool`.

## 5. Lint

```bash
inv lint-yaml      # schema + object YAML
```

(`ruff`/`mypy` targets are unaffected — no Python edited this cycle except generated `protocols.py`.)

## 6. Sanity: no literal addressing (SC-004 / SC-006)

After load, the data model is the sole source for all five pyAVD pools. The generator still contains the `10.250` / `10.251` / `10.255` literals — **removing them is the next (generator) cycle.** This cycle's done-criterion is: every fabric has all three mandatory pools linked and the schema enforces them.

## Done when

- [ ] `infrahubctl schema check schemas/` passes
- [ ] `inv load` completes with both fabrics fully pool-linked
- [ ] A fabric cannot be saved without `uplink_pool` / `vtep_pool` / `loopback_pool`
- [ ] `protocols.py` regenerated with `NetworkFabric.loopback_pool`
- [ ] Loopback pool prefixes (`10.255.2.0/24`, `10.255.3.0/24`) do not overlap mgmt `10.255.0.0/24`
