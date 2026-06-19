# Phase 0 Research: Schema-Driven AVD IP Pools

This research reconciles the spec's assumptions against the actual repository state and resolves every design unknown before Phase 1.

---

## R1 — Which pool relationships already exist?

**Decision**: Treat four of the five pools as *already modeled* (just optional), and add only the loopback prefix pool.

**Finding**: The spec's Background claims `uplink_pool`, `vtep_pool`, `mlag_peer_pool`, and `mlag_l3_pool` "do not exist in the schema." That is **incorrect**. They are all defined in `schemas/l3ls_extensions.yml` (not in `logical_design.yml`, which is why an earlier read missed them):

| Relationship | Node | Peer | Current optional | identifier |
|--------------|------|------|------------------|------------|
| `uplink_pool` | NetworkFabric | `CoreIPPrefixPool` | `true` | `fabric__uplink_pool` |
| `vtep_pool` | NetworkFabric | `CoreIPPrefixPool` | `true` | `fabric__vtep_pool` |
| `mlag_peer_pool` | NetworkPod | `CoreIPAddressPool` | `true` | `pod__mlag_peer_pool` |
| `mlag_l3_pool` | NetworkPod | `CoreIPAddressPool` | `true` | `pod__mlag_l3_pool` |

The generator's `getattr(fabric, "uplink_pool", None)` therefore *does* resolve when data is populated — the literals are hit only when the optional relationship is left empty.

**Rationale**: The real problem is not "missing relationships" but "optional relationships + a missing loopback pool + silent literal fallbacks." Re-defining existing relationships would be a no-op at best and a duplicate-identifier error at worst.

**Alternatives considered**: Re-declaring the four relationships inline in `logical_design.yml` — rejected: violates Constitution I (extensions-only for existing nodes) and collides on `identifier`.

**Spec impact**: spec.md FR-010/FR-011 should read "flip to mandatory" rather than "MUST define"; FR-013/FR-014 are already satisfied (relationships exist and correctly stay optional). FR-012 (loopback pool) is the one genuinely new relationship. This is flagged for a spec amendment.

---

## R2 — Where does the `loopback_ipv4_pool` come from, and what should replace `10.255.0.0/24`?

**Decision**: Add a new **fabric-level** relationship `loopback_pool` (`peer: CoreIPPrefixPool`, `cardinality: one`, mandatory) in `l3ls_extensions.yml`. Seed it with a prefix that does **not** overlap the management subnet.

**Finding**:
- `generate_avd_device_hostvar.py:523` sets `node_config["loopback_ipv4_pool"] = "10.255.0.0/24"` unconditionally — wired to no relationship.
- That literal **collides with the management network**: `objects/04_ipam.yml` defines mgmt prefix `10.255.0.0/24` and `objects/10_fabric.yml` sets `mgmt_gateway: 10.255.0.1`. Device loopbacks and management share the same /24 today — a latent addressing bug.
- pyAVD `loopback_ipv4_pool` expects a **prefix/subnet** (carved into /32s), so `CoreIPPrefixPool` is the correct peer kind (matching `vtep_pool`), not `CoreIPAddressPool`.

**Placement (fabric vs pod)**: fabric-level, because the literal applied uniformly to every device regardless of pod (consistent with the spec Assumption). The pre-existing `pod.loopback_pool` (`CoreIPAddressPool`, `pod__loopback_pool`) in `logical_design.yml` is a *different* relationship, unpopulated in seed data and unread by the hostvar generator; it is left untouched to avoid scope creep.

**Naming**: `loopback_pool` on NetworkFabric, identifier `fabric__loopback_pool`. Reusing the bare name `loopback_pool` is safe — relationship names are scoped per node, and the distinct identifier prevents any clash with `pod__loopback_pool`.

**Non-overlapping prefixes** (existing allocations in `04a_l3ls_pools.yml`: uplink `10.255.252.0/22`, vtep `10.255.1.0/27`, mlag `10.255.4.0/24` & `10.255.5.0/24`; mgmt `10.255.0.0/24`):
- Fabric-A loopback pool → `10.255.2.0/24`
- Fabric-B loopback pool → `10.255.3.0/24`

**Alternatives considered**: pod-level loopback pool (rejected — overkill for uniform behavior; revisit only if per-pod loopback ranges become a requirement). `CoreIPAddressPool` peer (rejected — AVD expects a prefix).

---

## R3 — How to make `uplink_pool`/`vtep_pool`/`loopback_pool` mandatory without breaking existing data?

**Decision**: Ship the optionality flip **together with** the seed-data backfill in the same change, so a fresh `inv load` is internally consistent. Order operations as: (a) add the new pool objects + references, (b) flip `optional: false`, (c) regenerate protocols, (d) load.

**Finding**: Per the schema migration rule, adding a mandatory relationship to nodes that already have instances fails for instances lacking the value. In seed data:
- **Fabric-A** sets `uplink_pool` and `vtep_pool` ✅ but has no loopback pool.
- **Fabric-B** sets *neither* `uplink_pool` nor `vtep_pool`, and no loopback pool ❌ — would fail the moment they become mandatory.

So the backfill must add: `Fabric-A-Loopback-Pool`, `Fabric-B-Loopback-Pool`, `Fabric-B-Uplink-Pool`, `Fabric-B-VTEP-Pool` (objects in `04a_l3ls_pools.yml`) and the corresponding references in `10_fabric.yml`.

**Rationale**: For this repository the authoritative state is the seed data loaded fresh, so the two-step "add optional → populate → tighten" dance collapses into one consistent commit. The plan still documents the two-step path for any *live* deployment that already has fabrics (FR-060).

**Alternatives considered**: Keep relationships optional and enforce only in the generator (rejected — the spec explicitly wants data-layer enforcement / "fail loudly"; SC-003 requires the platform to reject an unaddressed fabric). Provide a relationship `default_value` (rejected — relationships do not take literal defaults, and a default pool would reintroduce the hidden-fallback problem this feature removes).

---

## R4 — Does the `mlag_l3_pool` → `mlag_l_3_pool` Pydantic mangling need a schema change?

**Decision**: No schema rename. Keep `mlag_l3_pool`; the generator's existing `getattr(pod, "mlag_l_3_pool", None) or getattr(pod, "mlag_l3_pool", None)` already handles it.

**Finding**: The auto-generated protocol mangles `l3` → `l_3`. Renaming the relationship to dodge this would be a destructive migration (three-step rename, breaks `identifier` and seed references) for cosmetic benefit. The spec's wish to "avoid perpetuating the getattr dance" is a generator-cycle cleanup concern, not a schema change.

**Rationale**: Lowest-risk; preserves existing data and identifiers. A single typed accessor helper can be introduced in the generator cycle if desired.

---

## R5 — Protocol regeneration

**Decision**: Run `infrahubctl protocols --out src/solution_arista_avd/protocols.py` after the schema edit and before the generator cycle consumes the new relationship.

**Rationale**: Constitution Principle I requires protocol regeneration on schema change; Principle III requires typed access. The new `NetworkFabric.loopback_pool` relationship must appear in `protocols.py` so the downstream generator reads it type-safely rather than via `getattr`.

---

## Resolved unknowns summary

| Unknown | Resolution |
|---------|-----------|
| Do the four pool relationships exist? | Yes, in `l3ls_extensions.yml`, optional (R1) |
| What replaces `10.255.0.0/24`? | New fabric `loopback_pool` (CoreIPPrefixPool), seeded `10.255.2.0/24` / `10.255.3.0/24` (R2) |
| Loopback pool placement | Fabric-level (R2) |
| Migration safety | Backfill seed data in same change; flip optional→mandatory (R3) |
| `mlag_l3_pool` mangling | No schema change (R4) |
| Protocols | Regenerate after edit (R5) |

No `[NEEDS CLARIFICATION]` markers remain.
