# Contract: Artifact Output (`topology.clab.yml`)

**Transform**: `transforms/containerlab_topology.py` (`ContainerLabTopology`, `python_transforms`)
**Content type**: `application/yaml`
**Artifact definition** (`.infrahub.yml`):

```yaml
artifact_definitions:
  - name: "containerlab_topology"
    artifact_name: "ContainerLab Topology"
    parameters:
      name: "name__value"
    content_type: "application/yaml"
    targets: "fabrics"
    transformation: "containerlab_topology"
```

`transformation:` MUST exactly equal the `python_transforms[].name` (`containerlab_topology`) or the
artifact fails to render.

## Output shape (ContainerLab topology)

```yaml
name: <fabric-name>

mgmt:
  network: clab-<fabric-name>-mgmt
  ipv4-subnet: <derived-management-prefix>

topology:
  kinds:
    arista_ceos:
      image: arista/ceos:<version>
      startup-config: <per-node config path using __clabNodeName__>
      binds: []                       # per-kind binds if any
    linux:                            # only when servers present
      image: <server-image>

  nodes:
    <device-name>:
      kind: arista_ceos
      binds:
        - configs/eos-intf-mapping/<model>.json:/mnt/flash/EosIntfMapping.json:ro
      mgmt-ipv4: <device-mgmt-ip>     # omitted if device has no mgmt IP
    # ... one entry per device (deterministic order)

  links:
    - endpoints: ["<nodeA>:<clab-short-ifaceA>", "<nodeB>:<clab-short-ifaceB>"]
    # ... one entry per unique link (deterministic order)
```

## Output guarantees (map to Success Criteria)

| Guarantee | Criterion |
|-----------|-----------|
| Parses as valid ContainerLab YAML | SC-001 |
| Exactly one node per network device; one link per connection (deduped) | SC-002 |
| Every cEOS node carries `mgmt-ipv4` (when a mgmt IP exists) + a mapping bind | SC-003 |
| All endpoint interface names are ContainerLab short names (0 untranslated EOS names) | SC-004 |
| Multiple device types render without error; missing mapping fails with a named error | SC-005 |
| Deterministic byte-identical output for unchanged inputs | FR-012 |

## Local validation

- `infrahubctl transform containerlab_topology --name <fabric>` → prints YAML.
- `... | containerlab --topo - validate` (or write to file and `containerlab inspect`) → accepted.
