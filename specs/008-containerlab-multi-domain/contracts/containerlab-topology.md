# Contract: ContainerLab Topology artifact

**Artifact name**: `ContainerLab Topology`
**Content type**: `application/yaml`
**Target group**: `fabrics` (`NetworkFabric`, which inherits `CoreArtifactTarget`)
**Parameter**: `name: name__value` → GraphQL `$name: String!`
**Transformation**: `containerlab_topology`

Registration is unchanged from the current `.infrahub.yml:210-216`. Only the rendered body changes.

---

## Output shape

```yaml
---
name: <fabric-name>

mgmt:
  network: clab-<fabric-name>-mgmt
  ipv4-subnet: <most-common-device-subnet>

topology:
  kinds:
    <kind-a>:                                   # one entry per distinct platform kind
      image: <platform.containerlab_image>
      startup-config: configs/__clabNodeName__.cfg
    <kind-b>:
      image: <platform.containerlab_image>

  nodes:
    <device-name>:                              # sorted by name
      kind: <platform.containerlab_os>
      mgmt-ipv4: <mgmt_ip, mask stripped>       # omitted when the device has no mgmt_ip
      binds:                                    # key omitted entirely when empty
        - configs/eos-intf-mapping/<file>:/mnt/flash/EosIntfMapping.json:ro
    <server-name>:
      kind: linux
      mgmt-ipv4: <mgmt_ip, mask stripped>
      binds:
        - configs/servers/<server-name>-netplan.yaml:/etc/netplan/netplan.yaml

  links:                                        # globally sorted; endpoints ordered within a link
    - endpoints: ["<dev-a>:<eth-a>", "<dev-b>:<eth-b>"]
```

### Differences from the current output

| Aspect | Current | Contracted |
|---|---|---|
| `kinds` | single hardcoded `arista_ceos` block | one entry per distinct kind, image from the graph |
| `startup-config` | `configs/__clabNodeName__.cfg` at kind level | unchanged in shape; see R-006 for why the directory is correct |
| node `binds` | never emitted | emitted per node when a mapping or netplan file applies |
| server nodes | absent | present as `linux` kind |
| `border_leaf` devices | dropped | present |

---

## Guarantees

1. **Valid YAML**, and a valid ContainerLab topology accepted by `containerlab deploy`.
2. **Deterministic**: two renders of unchanged data are byte-identical.
3. **Referentially closed**: every `endpoints` entry names a device present in `nodes`.
4. **No hardcoded identity**: no kind, image, or mapping filename originates in Python.
5. **Pure data**: no diagnostic comments. Exclusions go to logs (FR-023).

## Non-guarantees

- Node names do **not** match `lab/topology.clab.yml` (`spine-infrahub-dc1-1` vs `ih-dc1-spine1`).
- Topology name is the fabric name, so container names differ from the committed lab's.
- Server-to-server reachability is not guaranteed: shipped netplan encodes VLANs 11/12/19 while
  this fabric models 21/22/29 (R-007).

---

## Second query contract

**Query**: `containerlab_link_endpoints` (`transforms/containerlab_link_endpoints.gql`)
**Variable**: `$ids: [ID!]`
**Batching**: 50 IDs per call
**Returns**: per `NetworkLink`, its `connected_endpoints` with interface `name.value` and the
owning device `name.value`, across both `DcimInterface` and `InterfacePhysical` inline fragments.

A link is **skipped** unless it resolves to exactly two endpoints.

Registered under `queries:` in `.infrahub.yml`; return types generated, not hand-written.
