# Contract: Schema Extension Delta

The "contract" for a schema feature is the exact YAML the implementation must produce. This is the authoritative shape; `/speckit.tasks` and `/speckit.implement` derive their edits from it.

## 1. `schemas/l3ls_extensions.yml` — NetworkFabric relationships

Under `extensions.nodes` → `- kind: NetworkFabric` → `relationships:`

**Modify** the two existing pool relationships to be mandatory (only `optional` changes):

```yaml
        - name: uplink_pool
          label: Uplink IP Pool
          peer: CoreIPPrefixPool
          kind: Attribute
          cardinality: one
          optional: false          # was: true
          identifier: "fabric__uplink_pool"
          description: "IP prefix pool for P2P uplink addressing"
          order_weight: 10400
        - name: vtep_pool
          label: VTEP Loopback Pool
          peer: CoreIPPrefixPool
          kind: Attribute
          cardinality: one
          optional: false          # was: true
          identifier: "fabric__vtep_pool"
          description: "IP prefix pool for VTEP loopback addresses"
          order_weight: 10500
```

**Add** the new loopback prefix pool relationship:

```yaml
        - name: loopback_pool
          label: Loopback IP Pool
          peer: CoreIPPrefixPool
          kind: Attribute
          cardinality: one
          optional: false
          identifier: "fabric__loopback_pool"
          description: "IP prefix pool for device loopback (loopback0) addressing"
          order_weight: 10600
```

NetworkPod relationships (`mlag_peer_pool`, `mlag_l3_pool`) are **unchanged**.

## 2. `objects/04a_l3ls_pools.yml` — new pool objects

Append `IpamPrefix` + `CoreIPPrefixPool` documents for:

- `Fabric-A-Loopback-Pool` — resource `10.255.2.0/24`, `default_prefix_length: 32`
- `Fabric-B-Loopback-Pool` — resource `10.255.3.0/24`, `default_prefix_length: 32`
- `Fabric-B-Uplink-Pool` — resource `10.254.252.0/22`, `default_prefix_length: 31`
- `Fabric-B-VTEP-Pool` — resource `10.254.1.0/27`, `default_prefix_length: 32`

Follow the exact document shape already used for `Fabric-A-Uplink-Pool` / `Fabric-A-VTEP-Pool` in the same file (kind, `default_member_type: prefix`, `default_prefix_type: IpamPrefix`, `ip_namespace: default`, `resources:` list). Each `CoreIPPrefixPool` resource must reference an `IpamPrefix` defined in the same file with an appropriate `role`.

## 3. `objects/10_fabric.yml` — fabric references

- Fabric-A `data`: add `loopback_pool: "Fabric-A-Loopback-Pool"`.
- Fabric-B `data`: add
  ```yaml
      uplink_pool: "Fabric-B-Uplink-Pool"
      vtep_pool: "Fabric-B-VTEP-Pool"
      loopback_pool: "Fabric-B-Loopback-Pool"
  ```

## 4. `src/solution_arista_avd/protocols.py` — regenerate

```bash
infrahubctl protocols --out src/solution_arista_avd/protocols.py
```

`NetworkFabric` protocol must gain a `loopback_pool` relationship attribute after regeneration.

## Acceptance (maps to spec Success Criteria)

| Contract item | Verifies |
|---------------|----------|
| §1 relationships | SC-001 (schema check), SC-002 (UI fields), SC-003 (mandatory enforced) |
| §2 + §3 seed data | SC-005 (loads with all pools populated) |
| §1 + §2 + §3 | SC-004 (all 5 pyAVD pools traceable to a relationship), SC-006 (no literal addressing after load) |
| §4 protocols | Constitution III (typed access for the generator cycle) |
