# Phase 1 Data Model: ContainerLab Topology for the Multi-Domain Fabric

Two new attributes and one new object. Everything else already exists and is read-only here.

---

## Schema changes

### `DcimPlatform` — `schemas/base/dcim.yml`

New attribute, placed immediately after the existing `containerlab_os` (`order_weight: 1900`) so
the two ContainerLab fields sit together in the UI.

| Field | Value |
|---|---|
| `name` | `containerlab_image` |
| `kind` | `Text` |
| `optional` | `true` |
| `order_weight` | `1950` |

**Validation rules**

- `optional: true` is mandatory. Attributes default to `optional: false`, and a required attribute
  without a default would invalidate every already-loaded `DcimPlatform` on the next load.
- snake_case name, 3-32 chars — satisfied.
- No `default_value`. A platform with no ContainerLab representation should read as null, not as a
  misleading placeholder image.

### `DcimDeviceType` — `schemas/base/dcim.yml`

| Field | Value |
|---|---|
| `name` | `containerlab_interface_mapping` |
| `kind` | `Text` |
| `optional` | `true` |
| `order_weight` | `1700` (after the existing `weight` at 1600) |

**Validation rules**

- `optional: true`, same reasoning — most device types have no mapping file.
- Holds a **filename only** (`DCS-7050CX3-32S.json`), not a path. The transform owns the
  `configs/eos-intf-mapping/` prefix and the `/mnt/flash/EosIntfMapping.json` mount point, so the
  data stays portable if the lab layout changes.
- No uniqueness constraint. Two device types legitimately share a mapping file.

### Not changed, and why

- **No new node or generic.** Both attributes hang off nodes that `schemas/base/dcim.yml` already
  owns, so no `extensions:` block and no cross-file load-order dependency is created.
- **No `CoreFileObject`.** Confirmed decision: mapping files stay on disk in `lab/`, and only the
  filename is modelled.
- **No `NetworkFabric` → management-prefix relationship.** Considered for subnet derivation and
  rejected in research R-005.
- **No attribute on `ComputePhysicalServer`.** The netplan filename is derived from the device
  name by convention (R-007).

---

## Object data changes

### `objects/03_device_type.yml`

| Object | Kind | Change |
|---|---|---|
| `EOS` | `DcimPlatform` | set `containerlab_image: arista/ceos:4.36.0.1F` (already has `containerlab_os: arista_ceos`) |
| `Linux` | `DcimPlatform` | **new** — `containerlab_os: linux`, `containerlab_image: lab-server`, manufacturer as appropriate |
| `Arista 7050CX3-32C` | `DcimDeviceType` | set `containerlab_interface_mapping: DCS-7050CX3-32S.json` |
| `Arista 7050SX3-48YC8C` | `DcimDeviceType` | set `containerlab_interface_mapping: DCS-7050SX3-48YC8.json` |

Note the deliberate part-number/filename mismatch: the device types are `…-32C` / `…-48YC8C` while
the mapping files shipped in `lab/configs/eos-intf-mapping/` are `…-32S.json` / `…-48YC8.json`.
The attribute records the **actual filename on disk**, so it must not be "corrected" to match the
part number.

### Server platform assignment

The two `ComputePhysicalServer` objects (`dc1-server`, `dc2-server`, in
`manual_objects/15a_servers_l3ls_multi_domain.yml`) must resolve to the `Linux` platform, either
directly or through their `TemplateComputePhysicalServer` templates in
`objects/11b_l3ls_multi_domain_server_templates.yml`. Assigning it on the template is preferable so
future servers inherit it.

---

## Entities read by the transform

Read-only. Listed with the traversal the query must perform.

| Entity | Read for | Path from fabric |
|---|---|---|
| `NetworkFabric` | topology name, artifact target | root (`name__value` parameter) |
| `NetworkPod` | traversal to devices and racks | `children` → `... on NetworkPod` |
| `LocationRack` | traversal to leaves | `children.racks` |
| `DcimDevice` | node name, role, mgmt IP, device type | `…devices` and `…racks.devices` |
| `DcimDeviceType` | `containerlab_interface_mapping` | `device.device_type` |
| `DcimPlatform` | `containerlab_os` (kind), `containerlab_image` | `device.device_type.platform` **and** `device.platform` |
| `IpamIPAddress` | `mgmt-ipv4`, subnet derivation | `device.mgmt_ip` |
| `DcimInterface` / `InterfacePhysical` | EOS interface names → `eth*` | `device.interfaces`, and via link endpoints |
| `NetworkLink` | links; `role: dci` distinguishes inter-domain | `interface.connector` → resolved in the second query |
| `ComputePhysicalServer` | `linux` node, mgmt IP, netplan bind | fabric → rack → servers |

### Platform resolution order

A device's platform is reachable two ways, and they differ by node type:

- Switches: `device.device_type.platform` — device types carry the platform in this repo.
- Servers: `device.platform` — `ComputePhysicalServer` has no `device_type` (R-002).

The transform must try `device_type.platform` first, then fall back to the device's own `platform`,
and warn if neither yields a `containerlab_os`.

---

## Derived values (not stored)

| Value | Rule |
|---|---|
| Node kind | `platform.containerlab_os` |
| Node image | `platform.containerlab_image`, grouped into one `kinds:` entry per distinct kind |
| `mgmt-ipv4` | `mgmt_ip.address` with the mask stripped |
| `mgmt.ipv4-subnet` | Most common device subnet; ties broken by lowest network address (R-005) |
| `mgmt.network` | `clab-<fabric-name>-mgmt` |
| Topology name | fabric name — so `Fabric-L3LS-Multi-Domain`, not `infrahub-avd` |
| Interface name | `Ethernet<N>[/<M>]` → `eth<N>[_<M>]`; `/` → `_` for any remaining segments |
| Mapping bind | `configs/eos-intf-mapping/<containerlab_interface_mapping>:/mnt/flash/EosIntfMapping.json:ro` |
| Netplan bind | `configs/servers/<device-name>-netplan.yaml:/etc/netplan/netplan.yaml` |
| Startup config | kind-level `configs/__clabNodeName__.cfg` (R-006) |

---

## Invariants

1. A node appears exactly once even when reachable via both pod and rack.
2. A link is emitted only when **both** endpoints resolved to emitted nodes.
3. Link endpoints are ordered within each link, and links are globally sorted — two levels of
   ordering, both required for byte-identical output.
4. Nodes are emitted in sorted name order.
5. Every node has a kind; a node whose kind cannot be resolved is excluded with a warning rather
   than emitted with a null kind.
6. `binds` is omitted entirely when a node has none — never rendered as an empty list.
