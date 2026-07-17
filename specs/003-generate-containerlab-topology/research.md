# Phase 0 Research: ContainerLab Topology Generation

All open questions from the spec (soft defaults in Assumptions) are resolved below. No
`NEEDS CLARIFICATION` markers remain.

---

## R1. Interface-mapping resolution — REVISED after inspecting live data

**Live-data finding (2026-07-16)**: Against the seeded fabrics (`Fabric-A`, `Fabric-B`), every
`DcimDevice` created by the generators has **`device_type` = null and `platform` = null**, and
interfaces are named plainly **`Ethernet1` … `Ethernet33`** (no `Ethernet1/N` breakout). The
reference lab's premise (mandatory Arista `DCS-7050*` model files, breakout naming) does not hold
here. Confirmed by direct GraphQL against `http://localhost:8000`.

**Decision (final, confirmed with user)**: Two parts.

1. **This cycle (v1 transform)** — interface names are translated **algorithmically**:
   `Ethernet<N>[/<M>[/<K>]]` → `eth<N>[_<M>[_<K>]]` (e.g. `Ethernet27` → `eth27`, `Ethernet1/1` →
   `eth1_1`). This *is* cEOS's default mapping, so for the plain `Ethernet<N>` interfaces this fabric
   uses today **no `EosIntfMapping.json` bind is required** — nodes carry just `kind` + `mgmt-ipv4`.
   No mapping files, no generation script, no binds.

2. **Next cycle (schema-first)** — the authoritative interface mapping will live as a
   `CoreFileObject` attached to `DcimDeviceType` (mirroring `Avd.HostvarFile`), populated by a
   generator (content is uploaded via the SDK, not seedable as object YAML), and read by the
   transform via `device.device_type` — then bound into each node. This is deliberately **not** done
   here: it is schema + generator + seed data, which the spec-kit flow scopes as its own
   `/speckit.specify` cycle, and the constitution mandates schema-first, branch-based rollout. A
   fresh `inv load` (not a backfill) populates `device_type` on device creation once the generator
   wiring lands.

**Why the split**: For the current `Ethernet<N>` data, an authored/generated mapping file is the
identity map (`ethN` ↔ `EthernetN`) — functionally identical to the algorithmic default — so binds
add nothing until real breakout device types exist. The device-type-file-object design is
architectural future-proofing best delivered as a coherent schema cycle rather than bolted onto the
transform.

**Alternatives considered**:
- *Mandatory device-type-keyed files (original spec)*: impossible against current data (no
  `device_type`); deferred to the schema cycle.
- *Transform generates per-role mapping files + binds (interim approach)*: built and then removed —
  the binds were redundant identity maps for `Ethernet<N>` data, and the user chose to source
  mappings from the device type instead.

---

## R2. Management network & per-node `mgmt-ipv4`

**Decision**: Each node's `mgmt-ipv4` is `device.mgmt_ip.node.address.value` (the `IpamIPAddress`
`address`, mask stripped to a bare host address). The topology `mgmt.ipv4-subnet` is derived from
the management prefix those addresses belong to. The management network name defaults to
`clab-<fabric-name>-mgmt`.

**Rationale**: Matches the reference lab (static `mgmt-ipv4` per node under a shared `mgmt` subnet).
The devices already carry management IPs allocated from the management pool, so the subnet is a
property of the data, not a config knob. Deriving the subnet from the addresses (or the management
`IpamPrefix`) keeps a single source of truth.

**Implementation notes**: Query the management prefix directly if reachable from the address
(`ip_prefix`/`parent` relationship), otherwise compute the covering prefix from the set of `mgmt_ip`
addresses. A device without a `mgmt_ip` is emitted without `mgmt-ipv4` (ContainerLab auto-assigns) —
never a blank/invalid address (spec edge case).

**Alternatives considered**:
- *Hardcode `10.0.6.0/24`* (reference value): rejected — couples output to one lab and breaks for
  fabrics addressed differently.
- *New fabric attribute for the mgmt subnet*: rejected — schema change; the data already implies it.

---

## R3. cEOS kind, image, and startup-config binding

**Decision**: Define a single `arista_ceos` kind for all network devices with: `image` (a sensible
default cEOS reference, overridable), `startup-config` pointing at a per-node config path
(`__clabNodeName__`), and the per-node `binds` mounting the device-type mapping file to
`/mnt/flash/EosIntfMapping.json`. Servers (if present) render as a `linux` kind.

**Rationale**: cEOS is the only supported ContainerLab kind for Arista EOS labs and is what the
reference uses; the AVD role map is already Arista-centric (`l3leaf`, `spine`, `super-spine`), so
every network device virtualises as cEOS regardless of the physical vendor model. The
`startup-config` path lets the Ansible workflow drop in each device's rendered AVD EOS config.

**Image default**: use the reference lab's cEOS image as the documented default
(`arista/ceos:4.36.0.1F`); it is a single constant, trivially overridable later (env/param) without
reshaping the transform.

**Alternatives considered**:
- *Per-role kinds*: rejected — unnecessary; role is captured by which config/mapping is bound, not a
  distinct kind.

---

## R4. Link discovery, endpoint pairing, and de-duplication

**Decision**: Reuse the `CablingPlan` pattern: walk the fabric via GraphQL
(`NetworkFabric → children(NetworkPod) → devices + racks.devices → interfaces → connector`),
collect unique `NetworkLink` IDs, then fetch each link's two `connected_endpoints` with device
name + interface name. Emit one `links` entry per link (endpoints are inherently deduped by keying
on the link ID). Translate each endpoint's interface name via that endpoint device's own mapping.

**Rationale**: This traversal is proven in-repo for exactly this fabric shape, and keying on the
`NetworkLink` id makes bidirectional-storage dedup automatic (spec FR-009 / edge case).

**Implementation notes**: A link whose endpoint is a server device is rendered with the server's
`linux` node name and its raw short interface name (no EOS translation, FR-010). A link with a
missing endpoint interface name is skipped with a warning (edge case).

**Alternatives considered**:
- *Single deep GraphQL query returning endpoints inline*: viable and cleaner if the schema exposes
  `connected_endpoints` with device+name in one shot; the plan permits either — the two-step
  approach is the safe, known-working fallback. Implementation chooses based on query validation.

---

## R5. Transform type — Python vs Jinja2 vs Hybrid

**Decision**: Hybrid. A Python `InfrahubTransform` performs the real logic (traversal, mapping-file
load + inverse, interface translation, dedup, subnet derivation) and produces a structured topology
dict; a Jinja2 template (`containerlab_topology.j2`) renders the YAML. `transform()` returns the
rendered string.

**Rationale**: Per the skill's "before writing Python" ladder, string-formatting alone would favour
pure Jinja2 — but this transform *parses* mapping JSON, *computes* an inverse map, *translates*
names, *dedupes*, and *derives* a subnet. That is legitimate Python work. Keeping rendering in a
template keeps the YAML readable and diff-friendly and preserves deterministic ordering (FR-012).
Rendering via `yaml.safe_dump` of the built dict is an acceptable alternative to the template if
ordering is pinned; the template is preferred for reviewability and to match repo convention.

---

## R6. Ansible pull-and-deploy workflow (`opsmill.infrahub` + ContainerLab)

**Decision**: A playbook (`lab/playbooks/deploy_clab.yml`) that: (1) uses the `opsmill.infrahub`
collection to retrieve the fabric's ContainerLab topology artifact from Infrahub and write it to the
lab directory; (2) ensures the referenced interface-mapping files (repo-bundled) and per-device
startup configs (AVD EOS config artifacts, also pulled from Infrahub) are staged at the paths the
topology expects; (3) invokes `containerlab deploy` and reports the result. The existing `lab/`
Makefile-style ergonomics are preserved.

**Rationale**: Mirrors the reference lab's structure (`lab/` with `ansible.cfg`, `playbooks/`, and a
`configs/eos-intf-mapping/` tree bound into nodes). The `opsmill.infrahub` collection is the
supported way to read artifacts/inventory from Infrahub; ContainerLab is the deploy engine.

**Implementation notes**: Artifact retrieval keys off the artifact definition name and the fabric
target. The playbook is host-side tooling and is intentionally outside the Python lint/test targets;
its acceptance is functional (US3 / SC-007). Exact module/lookup names in `opsmill.infrahub` are
confirmed against the installed collection during implementation (validated by `ansible-galaxy
collection list` / collection docs), not guessed into the transform.

**Alternatives considered**:
- *Skip Ansible, use the Makefile `containerlab deploy` directly*: rejected — the user explicitly
  wants Ansible + the Infrahub collection to pull the file.

---

## Resolved field paths (verified against schema)

| Datum | GraphQL path |
|-------|--------------|
| Fabric name | `NetworkFabric.name.value` |
| Device name | `DcimDevice.name.value` |
| Device role | `DcimDevice.role.value` (`super_spine`/`spine`/`leaf`/`l2leaf`) |
| Device-type model | `DcimDevice.device_type.node.name.value` |
| Management IP | `DcimDevice.mgmt_ip.node.address.value` (`Ipam.IPAddress.address`) |
| Interface name | interface `name.value` (`Ethernet1/1`-style) |
| Link | `NetworkLink` via `interface.connector.node.id`; endpoints via `connected_endpoints` |
| Target group | `fabrics` (exists in `objects/01_groups.yml`) |
