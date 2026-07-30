# Contract: Parity matrix vs `lab/topology.clab.yml`

The assertable definition of "matches the current files in the lab folder". Every row is either a
**must match** (validation fails otherwise) or a **documented divergence** (validation asserts the
divergence is exactly as described).

## Must match

| Property | Expected | Source of truth |
|---|---|---|
| cEOS nodes | 12 | 6 per domain × 2 |
| Linux server nodes | 2 | `dc1-server`, `dc2-server` |
| Total nodes | 14 | |
| Distinct kinds | 2 | `arista_ceos`, `linux` |
| cEOS image | `arista/ceos:4.36.0.1F` | `DcimPlatform.containerlab_image` |
| Server image | `lab-server` | `DcimPlatform.containerlab_image` |
| Management subnet | `10.0.6.0/24` | derived from device mgmt IPs |
| Spine↔leaf links (DC1) | 8 | 2 spines × 4 leaves |
| Spine↔leaf links (DC2) | 8 | 2 spines × 4 leaves |
| DCI links | 4 | `NetworkLink.role == dci` |
| Server↔leaf links | 4 | 2 servers × 2 access leaves |
| Total links | 24 | |
| Spine uplink interface form | `eth1_1` … `eth4_1` | breakout, `Ethernet<N>/1` |
| Leaf uplink interface form | `eth49_1`, `eth50_1` | breakout, `Ethernet49-50/1` |
| DCI interface form | `eth5`, `eth6` | plain, `Ethernet5/6` |
| Server-facing leaf port | `eth1` | plain, `Ethernet1` |
| Spine mapping bind | `DCS-7050CX3-32S.json` | `DcimDeviceType.containerlab_interface_mapping` |
| Leaf mapping bind | `DCS-7050SX3-48YC8.json` | `DcimDeviceType.containerlab_interface_mapping` |
| Mapping mount point | `/mnt/flash/EosIntfMapping.json:ro` | |
| Netplan mount point | `/etc/netplan/netplan.yaml` | |
| Switch management IPs | present on all 12 | `manual_objects/` pinned values |

## Documented divergences

| Property | Lab folder | Generated | Why |
|---|---|---|---|
| Node names | `ih-dc1-spine1` | `spine-infrahub-dc1-1` | Confirmed decision: structural parity, no device renaming |
| Topology name | `infrahub-avd` | `Fabric-L3LS-Multi-Domain` | Derived from the fabric name |
| Management network name | `clab-infrahub-avd-mgmt` | `clab-Fabric-L3LS-Multi-Domain-mgmt` | Follows the topology name |
| `startup-config` dir | `avd/intended/configs/` | `configs/` | R-006 — the playbook writes here; committed renders are for differently-named devices |
| `ceos-config` kind bind | present | absent | Serial/system-MAC files are per-lab-device-name; not modelled in Infrahub |
| Netplan filenames | `dc1-server1-netplan.yaml` | `dc1-server-netplan.yaml` | R-007 — derived from the Infrahub device name; files renamed |
| CVaaS token bind | commented out | absent | Out of scope |
| Server VLANs/addresses | 11/12/19 | shipped as-is | Fabric models 21/22/29; netplan is not generated (R-007). Server-to-server reachability is therefore not claimed. |
| Server `mgmt-ipv4` | `10.0.6.100` / `.101` | **omitted** | `mgmt_ip` is a `DcimDevice`-only extension (`schemas/dcim_extensions.yml:35`), so `ComputePhysicalServer` has no such field, and `manual_objects/15a` sets no `primary_address`. The transform reads `primary_address` and omits `mgmt-ipv4` when absent, so ContainerLab assigns from the mgmt subnet. Verified against live data. |
| Switch management IPs (exact values) | `.11`–`.16`, `.21`–`.26` | pool-allocated | Only pinned when `manual_objects/00_lab_l3ls_multi_domain.yml` is loaded; otherwise `create_avd_device` allocates from `Fabric-L3LS-Multi-Domain-Mgmt-Pool` in allocation order. |

## How this is asserted

- **Unit** — `tests/unit/test_containerlab_topology.py` parses the rendered YAML and asserts the
  "must match" counts, kinds, images, bind mount points, and interface-name forms from fixtures.
  This is the tier that runs in CI.
- **Determinism** — render twice from identical input, assert byte equality.
- **Live dry-run** — `uv run infrahubctl transform containerlab_topology name=Fabric-L3LS-Multi-Domain`
  against loaded data. Required before merging any `.gql` change: static checks cannot catch a
  query/schema mismatch, and an empty dataset hides union-fragment bugs because no concrete
  instance is returned to fail on.
- **Integration** — `tests/integration/test_e2e_pipeline.py` generates the artifact per fabric and
  asserts border leaves and DCI links are present.
