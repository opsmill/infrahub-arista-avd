# Transform Specification: ContainerLab Topology Generation

> **Workflow**: Infrahub Transform
> **Skill**: Use the `infrahub:transform-creator` skill to implement this spec.

**Feature Branch**: `003-generate-containerlab-topology`
**Created**: 2026-07-16
**Status**: Draft
**Input**: User description: "I want to be able to generate a container lab file from my fabrics: https://github.com/opsmill-holt/infrahub-arista-avd/blob/lab/infrahub-avd/lab/topology.clab.yml — I want to also have ansible pull this container lab file and then run it using the infrahub collection for ansible also supporting interface mappings: https://github.com/opsmill-holt/infrahub-arista-avd/blob/lab/infrahub-avd/lab/configs/eos-intf-mapping/DCS-7050CX3-32S.json"

## Transform Type

- **Approach**: Hybrid (Python data preparation + Jinja2 template rendering)
- **Output Format**: YAML (`topology.clab.yml`, `application/yaml`)
- **Target Nodes**: `NetworkFabric` (one ContainerLab topology file per fabric)

<!--
  Rationale: producing a ContainerLab file is fundamentally rendering existing
  fabric data to a text artifact — the same pattern as the repo's CablingPlan,
  AvdEosConfig, and AvdFabricDoc transforms. It is NOT a Generator (no Infrahub
  objects are created) and needs no new schema (NetworkFabric already acts as an
  artifact target; interface-mapping resources are bundled static files — see
  Assumptions). The Python layer is required for real computation: resolving each
  device's interface-mapping file by device type and translating EOS interface
  names to ContainerLab short names for every link endpoint.
-->

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a deployable ContainerLab topology from a fabric (Priority: P1)

A network engineer selects a fabric in Infrahub and obtains a single `topology.clab.yml`
file describing the entire fabric as a ContainerLab lab: every network device becomes an
Arista cEOS node with a management IP, and every physical connection between devices becomes
a ContainerLab link. The engineer (or an automation pipeline) consumes this file to spin up a
virtual replica of the fabric for validation before touching production hardware.

**Why this priority**: This is the core deliverable. Without a structurally valid ContainerLab
file that reflects the fabric's devices and cabling, none of the downstream automation is
possible. On its own it already delivers value: an engineer can render the file and deploy the
lab manually.

**Independent Test**: Run `infrahubctl transform containerlab_topology --name Fabric-A` (or render
the artifact for a fabric) and confirm the output is valid YAML that `containerlab` accepts,
containing one node per network device and one link per fabric connection.

**Acceptance Scenarios**:

1. **Given** a fabric with super-spine, spine, and leaf devices that have management IPs and
   cabled interfaces, **When** the transform runs for that fabric, **Then** a valid ContainerLab
   YAML file is produced with a `name`, a `mgmt` network block, an `arista_ceos` kind, one node
   per device (with its `kind` and `mgmt-ipv4`), and one `links` entry per device-to-device
   connection.
2. **Given** two fabrics exist, **When** the transform runs for one fabric, **Then** only that
   fabric's devices and links appear in the output (fabrics are isolated per file).
3. **Given** a device has a management IP allocated, **When** the topology is generated, **Then**
   that device's node carries the matching `mgmt-ipv4` value and the `mgmt` subnet covers all node
   addresses.

---

### User Story 2 - Interface-mapping-aware links and binds (Priority: P2)

The generated topology reflects the fact that ContainerLab/cEOS names interfaces differently from
EOS (e.g. `eth49_1` in the lab maps to `Ethernet49/1` on the device). For each device, the
topology binds the correct per-device-type EOS interface-mapping file, and every link endpoint is
expressed using the ContainerLab-side interface name translated from the Infrahub/EOS interface
name via that device's mapping. This makes the lab actually boot with interfaces that match the
device configurations.

**Why this priority**: Without correct interface mapping, links point at interface names cEOS does
not recognise and the rendered device configs do not line up with the virtual interfaces — the lab
comes up broken. It is P2 because a structurally complete file (US1) is a prerequisite, and the
mapping layer is what makes that file correct and deployable.

**Independent Test**: For a fabric containing devices of at least two different device types (e.g.
`DCS-7050CX3-32S` and `DCS-7050SX3-48YC8`), render the topology and confirm each node binds the
mapping file matching its device type, and that a spine-to-leaf link's endpoints use the
ContainerLab short names that the mapping files translate back to the EOS interfaces recorded in
Infrahub.

**Acceptance Scenarios**:

1. **Given** a device of type `DCS-7050CX3-32S`, **When** the topology is generated, **Then** its
   node binds `configs/eos-intf-mapping/DCS-7050CX3-32S.json` to `/mnt/flash/EosIntfMapping.json`.
2. **Given** an Infrahub link between `spine1:Ethernet1/1` and `leaf1a:Ethernet49/1`, **When** the
   topology is generated, **Then** the ContainerLab link endpoints are the mapped short names for
   each device (e.g. `spine1:eth1_1` and `leaf1a:eth49_1`) using each endpoint's own device-type
   mapping.
3. **Given** a device whose device type has no matching interface-mapping file, **When** the
   topology is generated, **Then** the transform surfaces a clear, actionable error identifying the
   device type rather than emitting a silently wrong file.

---

### User Story 3 - Ansible pulls the topology and deploys the lab (Priority: P3)

An operator runs an Ansible workflow that uses the Infrahub Ansible collection to pull the
generated ContainerLab topology artifact (together with the interface-mapping files and the
per-device configuration artifacts it references) out of Infrahub onto the lab host, then invokes
ContainerLab to deploy the lab. The operator goes from "fabric defined in Infrahub" to "running
virtual fabric" with a single command, no manual file copying.

**Why this priority**: This automates the last mile. It depends on US1/US2 producing correct
artifacts and is valuable as a convenience/orchestration layer, but the artifacts themselves are
usable manually without it, so it is the lowest priority of the three.

**Independent Test**: With a fabric's artifacts generated in Infrahub, run the Ansible playbook and
confirm it fetches the topology file, the referenced interface-mapping files, and the device
configs into the lab directory, then successfully starts the lab with `containerlab deploy`.

**Acceptance Scenarios**:

1. **Given** a fabric with a generated ContainerLab topology artifact, **When** the Ansible
   workflow runs, **Then** the topology file is retrieved from Infrahub and written to the lab
   directory on the host.
2. **Given** the topology references per-device-type interface-mapping files and per-device startup
   configs, **When** the Ansible workflow runs, **Then** those referenced files are present on the
   host at the paths the topology expects before deployment starts.
3. **Given** the topology and its referenced files are staged, **When** the workflow invokes
   ContainerLab, **Then** the lab deploys and the network-device nodes reach a running state.

---

### Edge Cases

- **Empty fabric / no devices**: A fabric with no network devices produces a valid, well-formed
  file with an empty (or absent) `nodes`/`links` section rather than raising an exception.
- **Device without a management IP**: The node is either emitted without `mgmt-ipv4` (letting
  ContainerLab auto-assign) or the transform reports the gap — it must not emit an invalid/blank
  address.
- **Link endpoint with no interface name**: A connection missing an interface name on one side is
  skipped with a warning rather than producing a malformed endpoint.
- **Interface name not present in the mapping file**: The transform reports which interface on
  which device type could not be mapped, rather than emitting an untranslated EOS name that cEOS
  will reject.
- **Servers / non-EOS endpoints**: Connections to compute/storage servers are rendered as `linux`
  nodes with unmapped short interface names (servers have no EOS interface mapping).
- **Duplicate links**: A bidirectional connection stored from both ends yields exactly one
  ContainerLab `links` entry, not two.
- **Special characters / naming**: Device names are emitted as valid ContainerLab node names
  (fabric/DC prefix preserved) and produce valid YAML.
- **Branch context**: Rendering against a branch reflects that branch's fabric data (added or
  removed devices/links) in the output.

## Requirements *(mandatory)*

### Functional Requirements

#### GraphQL Query

- **FR-001**: A GraphQL query MUST be created in `transforms/containerlab_topology.gql` that
  retrieves all data needed to render a fabric's ContainerLab topology.
- **FR-002**: The query MUST accept a fabric name parameter (e.g. `$name: String!`) matching the
  artifact definition, and MUST scope results to that single fabric.
- **FR-003**: The query MUST retrieve, for the fabric and all its devices: fabric name; each
  device's name, role, and device-type identifier (model name, e.g. `DCS-7050CX3-32S`); each
  device's management IP address; each device's interfaces with their names; and the
  device-to-device (and device-to-server) connections/links with the interface on each end.

#### Transform Logic

- **FR-004**: The transform MUST be implemented as a hybrid Python (`InfrahubTransform` subclass)
  data-preparation step feeding a Jinja2 template, OR as a Python transform that renders the YAML
  directly — whichever the plan selects — because interface-name translation and device-type→
  mapping resolution require real logic beyond simple substitution.
- **FR-005**: The transform MUST set `query = "containerlab_topology"` to reference the GraphQL
  query.
- **FR-006**: The transform MUST return valid ContainerLab topology YAML containing: a top-level
  `name` (the fabric name), a `mgmt` block (network name + IPv4 subnet), a `topology.kinds` block
  defining the `arista_ceos` kind (image, startup-config path, per-kind binds) and a `linux` kind
  for servers, a `topology.nodes` map (one entry per device/server), and a `topology.links` list
  (one entry per unique connection).
- **FR-007**: For each network device, the transform MUST emit a node under the `arista_ceos` kind
  carrying the device's `mgmt-ipv4` and a `binds` entry mounting that device type's interface-
  mapping file to `/mnt/flash/EosIntfMapping.json`.
- **FR-008**: The transform MUST resolve the interface-mapping file for a device from its device
  type (model), and MUST translate each Infrahub/EOS interface name to its ContainerLab short name
  using that mapping when emitting link endpoints.
- **FR-009**: The transform MUST de-duplicate bidirectional connections so each physical link
  appears exactly once in `links`.
- **FR-010**: The transform MUST render server endpoints as `linux` nodes and MUST NOT attempt EOS
  interface-name translation for them.

#### Jinja2 Template *(if using the hybrid approach)*

- **FR-011**: If a template is used, it MUST be created at
  `transforms/templates/containerlab_topology.j2` and MUST produce YAML that `containerlab` parses
  without error.
- **FR-012**: The template MUST render the `mgmt`, `kinds`, `nodes`, and `links` sections in a
  stable, deterministic order so repeated renders of unchanged data produce identical output.

#### Interface Mapping Resources

- **FR-013**: Per-device-type EOS interface-mapping files (e.g. `DCS-7050CX3-32S.json`,
  `DCS-7050SX3-48YC8.json`) MUST be available to the transform for name translation and MUST be
  referenced by the topology's binds. These are bundled as static repository resources (see
  Assumptions).
- **FR-014**: The set of supported device types MUST cover every device-type model present on the
  fabric's devices; an unmapped device type MUST fail loudly (per US2 acceptance scenario 3).

#### Artifact & Registration

- **FR-015**: The transform MUST be registered in `.infrahub.yml` under `python_transforms` (or
  `jinja2_transforms` if implemented purely as a template).
- **FR-016**: The query MUST be registered in `.infrahub.yml` under `queries`.
- **FR-017**: An artifact definition MUST be created in `.infrahub.yml` with content type
  `application/yaml`.
- **FR-018**: The artifact definition MUST target the fabric group (`fabrics`) and map the
  parameter `name: name__value`.

#### Ansible Deployment Workflow

- **FR-019**: An Ansible workflow MUST use the Infrahub Ansible collection (`opsmill.infrahub`) to
  fetch the generated ContainerLab topology artifact for a fabric from Infrahub onto the lab host.
- **FR-020**: The workflow MUST ensure the files the topology references — the per-device-type
  interface-mapping files and the per-device startup configurations — are present at the paths the
  topology expects before deployment.
- **FR-021**: The workflow MUST invoke ContainerLab to deploy the fetched topology and MUST report
  success/failure of the deployment to the operator.

### Key Files

| File | Purpose |
|------|---------|
| `transforms/containerlab_topology.gql` | GraphQL query fetching fabric devices, device types, mgmt IPs, and links |
| `transforms/containerlab_topology.py` | Python transform: device-type→mapping resolution, interface-name translation, topology assembly |
| `transforms/containerlab_topology_query.py` | Pydantic query models matching the GraphQL response |
| `transforms/templates/containerlab_topology.j2` | Jinja2 template rendering the ContainerLab YAML *(if hybrid)* |
| `transforms/common.py` | Shared response-normalisation / interface-mapping helpers *(if applicable)* |
| `lab/configs/eos-intf-mapping/*.json` | Per-device-type EOS interface-mapping files (bundled resources) |
| `lab/playbooks/deploy_clab.yml` (or similar) | Ansible playbook pulling the artifact and deploying the lab |
| `.infrahub.yml` | Transform, query, and artifact-definition registration |

### Key Entities *(include if feature involves data)*

- **NetworkFabric**: The top-level fabric; the target node and the unit of one ContainerLab file.
- **DcimDevice**: A network device (super_spine / spine / leaf) — becomes an `arista_ceos` node;
  contributes its device type, management IP, and interfaces.
- **Device Type / model**: Identifies which EOS interface-mapping file applies to a device.
- **NetworkInterface / NetworkLink**: Interfaces and the connections between them — become
  ContainerLab `links`, with interface names translated to ContainerLab short names.
- **Management IP (IpamIPAddress)**: Supplies each node's `mgmt-ipv4` and informs the `mgmt` subnet.
- **Server (Compute unit)**: Cabled compute/storage endpoint — becomes a `linux` node.
- **EOS interface mapping**: Per-device-type map of ContainerLab short names to EOS interface names.
- **ContainerLab topology file** *(output)*: One `topology.clab.yml` per fabric.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Rendering the transform for a fabric (`infrahubctl transform containerlab_topology
  --name <fabric>` or the artifact) produces YAML that `containerlab` validates without error.
- **SC-002**: The output contains exactly one node per network device and one `links` entry per
  unique fabric connection (no duplicated bidirectional links).
- **SC-003**: 100% of network-device nodes carry a `mgmt-ipv4` matching the device's Infrahub
  management IP and a `binds` entry mounting the interface-mapping file for their device type.
- **SC-004**: For every link, both endpoint interface names are ContainerLab short names that the
  relevant device-type mapping translates back to the EOS interface names recorded in Infrahub
  (0 untranslated EOS names in the output).
- **SC-005**: The transform completes without raising exceptions for fabrics containing devices of
  multiple device types, and fails with a clear, device-type-identifying message when a required
  interface-mapping file is missing.
- **SC-006**: The artifact definition automatically produces an up-to-date topology file for every
  fabric in the target group.
- **SC-007**: The Ansible workflow, run against a fabric with generated artifacts, stages the
  topology plus its referenced files and deploys a lab whose network-device nodes reach a running
  state — with no manual file copying.

## Assumptions

- **Interface-mapping storage**: The per-device-type EOS interface-mapping JSON files are bundled as
  static repository resources under `lab/configs/eos-intf-mapping/` (mirroring the reference lab)
  and read by the transform. They are NOT stored as Infrahub objects. If the interface mappings
  should instead be modelled and managed inside Infrahub (per device type), that is a schema change
  and a separate `/speckit.specify` cycle.
- **One file per fabric**: Each `NetworkFabric` yields one ContainerLab topology file. Multi-fabric
  / DCI interconnect between separate fabrics is out of scope for this cycle unless represented as
  links within a single fabric's data.
- **cEOS image and management subnet**: The Arista cEOS image reference and the ContainerLab
  management network/subnet default to sensible values (e.g. the reference lab's cEOS image and a
  management subnet derived from the devices' management-IP prefix); these can be made configurable
  later without changing the feature's shape.
- **Startup configs**: Per-device startup configurations referenced by the topology are the
  existing AVD EOS configuration artifacts already produced by this repo; the Ansible workflow
  stages them alongside the topology.
- **Servers included**: Compute/storage servers cabled to leaf devices are represented as `linux`
  nodes when present; a fabric without servers simply omits them.
- **Ansible collections**: The deployment workflow relies on the `opsmill.infrahub` collection for
  artifact retrieval and on `containerlab` being installed on the lab host, consistent with the
  reference lab's `arista.avd` + ContainerLab tooling.
