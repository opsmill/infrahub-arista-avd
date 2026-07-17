# Phase 1 Data Model: ContainerLab Topology Generation

This transform is **read-only** — it introduces no new Infrahub schema. It consumes existing nodes
and produces an in-memory topology model that is rendered to YAML. Two model layers are described:
(A) the Infrahub source entities it reads, and (B) the intermediate topology model it builds before
rendering.

---

## A. Infrahub source entities (read-only)

### NetworkFabric *(target node)*
- `name.value` → topology `name` and the unit of one output file.
- `children` → `NetworkPod` edges (the traversal root for devices/racks).
- Must be a member of the `fabrics` group (artifact target).

### DcimDevice
| Field | Path | Use |
|-------|------|-----|
| name | `name.value` | ContainerLab node name |
| role | `role.value` | Classify network device vs server-adjacent; all network roles → `arista_ceos` |
| device type | `device_type.node.name.value` | Selects the interface-mapping file |
| management IP | `mgmt_ip.node.address.value` | Node `mgmt-ipv4` (mask stripped) |
| interfaces | `interfaces.edges[].node` | Interface names + `connector` → links |

Roles: `super_spine`, `spine`, `leaf`, `l2leaf` (all render as cEOS network nodes).

### NetworkInterface (DcimInterface / InterfacePhysical)
- `name.value` → interface name (`Ethernet1/1`-style), translated to ContainerLab short name.
- `connector.node.id` → the `NetworkLink` this interface participates in.

### NetworkLink
- Identified by id; `connected_endpoints.edges[].node` yields exactly two endpoints, each with
  `name.value` (interface) and `device.node.name.value`.
- One link → one ContainerLab `links` entry (dedup by link id).

### IpamIPAddress
- `address.value` → management address; the covering management prefix informs `mgmt.ipv4-subnet`.

### Server / Compute unit *(optional)*
- Cabled compute/storage endpoint → `linux` node; raw short interface name, no EOS translation.

### EOS interface mapping *(static file, not an Infrahub node)*
- `lab/configs/eos-intf-mapping/<model>.json`: `{ "EthernetIntf": { "<clab-short>": "<EOS-name>" }, "ManagementIntf": { "eth0": "Management1" } }`.
- The transform reads this and inverts `EthernetIntf` to translate EOS → ContainerLab short names.

---

## B. Intermediate topology model (built in Python, then rendered)

```
ClabTopology
├── name: str                      # fabric name
├── mgmt: MgmtNetwork
│   ├── network: str               # e.g. "clab-<fabric>-mgmt"
│   └── ipv4_subnet: str           # derived from management prefix
├── kinds: dict[str, ClabKind]
│   ├── "arista_ceos": {image, startup_config_path, kind_binds}
│   └── "linux": {image}           # only if servers present
├── nodes: list[ClabNode]          # deterministic order (by name)
│   └── ClabNode
│       ├── name: str
│       ├── kind: "arista_ceos" | "linux"
│       ├── mgmt_ipv4: str | None
│       └── binds: list[str]        # cEOS: "<mapping-file>:/mnt/flash/EosIntfMapping.json:ro"
└── links: list[ClabLink]          # deterministic order
    └── ClabLink
        └── endpoints: [str, str]   # "<node>:<clab-short-iface>", each translated per endpoint's model
```

### Derived / computed fields
- **`node.binds` (cEOS)**: from `device.device_type` → mapping filename. Missing mapping → error
  naming the device type (FR-014).
- **`link.endpoints`**: each `"<device>:<EOS-iface>"` → `"<node>:<clab-short>"` via that device's
  inverted mapping. Missing translation → error naming device type + interface (FR-008, edge case).
- **`mgmt.ipv4_subnet`**: covering prefix of all `mgmt_ip` addresses (or the management `IpamPrefix`).

---

## C. Validation rules (from requirements)

| Rule | Source | Enforcement |
|------|--------|-------------|
| Output parses as valid ContainerLab YAML | SC-001 | `yaml.safe_load` round-trip in tests + `containerlab` validate |
| One node per network device; one link per connection | SC-002 | dedup by link id; node keyed by device name |
| Every cEOS node has a mapping bind | SC-003, FR-007 | assert during build |
| No untranslated EOS interface names in output | SC-004, FR-008 | translation is mandatory; unmapped → raise |
| Unmapped device type fails loudly | SC-005, FR-014 | raise with device-type name |
| Bidirectional links appear once | FR-009 | keyed on link id |
| Servers → `linux`, no EOS translation | FR-010 | branch on role/kind |
| Deterministic ordering | FR-012 | sort nodes/links by name before render |
| Empty fabric → valid empty-ish file | edge case | guard empty `nodes`/`links` |
| Device without mgmt IP → node without `mgmt-ipv4` | edge case | conditional field |

---

## D. State transitions

None — the transform is stateless and idempotent. Output is a pure function of the queried fabric
data plus the bundled mapping files. Re-running against unchanged inputs yields byte-identical YAML.
