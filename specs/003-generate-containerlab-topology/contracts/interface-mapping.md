# Contract: EOS Interface-Mapping Files

**Location**: `lab/configs/eos-intf-mapping/<model>.json` (static repo resources)
**Keyed by**: device-type model name (`DcimDevice.device_type.node.name.value`)
**Bound into cEOS at**: `/mnt/flash/EosIntfMapping.json`

## File format (cEOS `EosIntfMapping.json`)

```json
{
  "ManagementIntf": {
    "eth0": "Management1"
  },
  "EthernetIntf": {
    "<clab-short-name>": "<EOS-interface-name>",
    "eth1_1": "Ethernet1/1",
    "eth2_1": "Ethernet2/1"
  }
}
```

- `EthernetIntf` maps **ContainerLab short name → EOS interface name** (the direction cEOS needs).
- The transform inverts `EthernetIntf` (EOS name → short name) to translate link endpoints.

## Requirements

- A file MUST exist for every device-type model present on a fabric's devices (FR-013, FR-014).
- Every EOS interface name that appears on a fabric link for that model MUST have an entry
  (otherwise the transform raises a named error — SC-004/SC-005).
- Values MUST match the interface names as modeled in Infrahub for that device type. For the
  currently seeded Dell models the names are `Ethernet1/N` (e.g. `Ethernet1/1` … `Ethernet1/64`),
  so mapping files for `PowerSwitch Z9864F-ON` and `PowerSwitch S5232F-ON` must be authored to match
  — the reference lab's Arista `DCS-7050*` files are examples of the format, not drop-in content.

## Filename ↔ bind-path consistency

The filename on disk and the `binds:` path emitted in the topology MUST use the same
model→filename scheme (exact model string or a documented slug). The transform and the bundled files
MUST agree; a mismatch means the bind mount fails at deploy time.

## Ansible staging (US3)

The deploy workflow ensures these files are present on the lab host at
`configs/eos-intf-mapping/<model>.json` (relative to the topology) before `containerlab deploy`.
Because they are repo-bundled, staging is a copy/sync, not an Infrahub fetch.
