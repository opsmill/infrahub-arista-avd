# Quickstart: ContainerLab Topology Generation

How to build, register, render, and deploy the ContainerLab topology transform.

## Prerequisites

- Infrahub running (`inv start`) with a fabric seeded (`inv load`) — e.g. `Fabric-A`.
- `uv sync --all-packages`.

## 1. Files to create

```
transforms/containerlab_topology.gql          # query (see contracts/graphql-query.md)
transforms/containerlab_topology_query.py      # Pydantic models mirroring the response
transforms/containerlab_topology.py            # ContainerLabTopology(InfrahubTransform)
transforms/templates/containerlab_topology.j2  # renders the YAML (see contracts/artifact-output.md)
lab/configs/eos-intf-mapping/<model>.json      # one per seeded device-type model
lab/playbooks/deploy_clab.yml                  # Ansible pull + containerlab deploy
```

## 2. Register in `.infrahub.yml`

```yaml
queries:
  - name: containerlab_topology
    file_path: "./transforms/containerlab_topology.gql"

python_transforms:
  - name: containerlab_topology
    class_name: ContainerLabTopology
    file_path: "./transforms/containerlab_topology.py"

artifact_definitions:
  - name: "containerlab_topology"
    artifact_name: "ContainerLab Topology"
    parameters:
      name: "name__value"
    content_type: "application/yaml"
    targets: "fabrics"
    transformation: "containerlab_topology"
```

## 3. Render locally

```bash
# Render the transform for one fabric (params are positional: name=<fabric>).
# COLUMNS widens the Rich console so long bind lines are not wrapped when saving.
COLUMNS=500 uv run infrahubctl transform containerlab_topology name=Fabric-A > /tmp/topology.clab.yml
python -c "import yaml; yaml.safe_load(open('/tmp/topology.clab.yml'))"
containerlab --topo /tmp/topology.clab.yml validate   # on a host with containerlab
```

**Expect**: one `arista_ceos` node per network device (each with a `mgmt-ipv4` and an
`EosIntfMapping.json` bind), one `links` entry per fabric connection, and every link endpoint using
ContainerLab short interface names.

## 4. Test

```bash
pytest tests/unit/test_containerlab_topology.py     # mapping resolution, translation, dedup, edges
uv run infrahubctl transform ...                    # + YAML-driven Resources Testing Framework case
inv lint                                            # ruff + mypy + yamllint all green
```

Key unit cases: (a) two device types → correct per-node mapping bind; (b) `Ethernet1/1` translated
to the model's short name on both link ends; (c) bidirectional link appears once; (d) device without
mgmt IP → node without `mgmt-ipv4`; (e) unknown device type / unmapped interface → named error;
(f) empty fabric → valid file.

## 5. Deploy via Ansible (US3)

```bash
cd lab
# Pulls the topology artifact + per-device configs from Infrahub, stages mapping files, deploys
uv run ansible-playbook -i avd/inventory.yml playbooks/deploy_clab.yml
```

**Expect**: topology + referenced files staged on the lab host, `containerlab deploy` runs, and the
cEOS nodes reach a running state (SC-007).

## Definition of done

- `infrahubctl transform` produces `containerlab`-valid YAML for a seeded fabric (SC-001).
- Node/link counts and mapping binds match the fabric (SC-002/SC-003), 0 untranslated EOS names
  (SC-004), multi-device-type renders clean and missing mappings fail loudly (SC-005).
- Artifact definition renders per fabric in the `fabrics` group (SC-006).
- Ansible workflow deploys the lab end-to-end (SC-007).
- Unit + transform tests pass; `inv lint` green.
