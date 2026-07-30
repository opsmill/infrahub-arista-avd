# Transform Specification: ContainerLab Topology for the Multi-Domain Fabric

> **Workflow**: Infrahub Transform (with a schema prerequisite)
> **Skills**: Use `infrahub-managing-schemas` for the attribute additions, then
> `infrahub-managing-transforms` for the query, transform, and artifact wiring,
> and `infrahub-managing-objects` for the seed-data values.

**Feature Branch**: `atg/quick-windows-bake`
**Feature Directory**: `specs/008-containerlab-multi-domain`
**Created**: 2026-07-30
**Status**: Draft

**Input**: User description: "Ensure that Infrahub generates ContainerLab artifacts for the
multi-domain fabric. Ensure that we can use Ansible to pull the ContainerLab files and spin up
the ContainerLab that matches the current thing. It needs to match the current files in the lab
folder of the repository so we need to account for interfaces and images, all for ContainerLab."

> **Template note**: The `infrahub-speckit` pre-specify hook classified this feature as
> Schema → Transform → Objects and directed the schema template. The schema delta is two
> optional `Text` attributes, and the deliverable is a rendered artifact, so this spec uses
> `spec-transform-template.md` and folds the schema work in as prerequisite requirement group
> FR-001..FR-006. This is a deliberate, recorded deviation from the hook's template override.

---

## Transform Type

- **Approach**: Hybrid — Python (`InfrahubTransform`) for graph traversal and derivation,
  Jinja2 for rendering the topology document.
- **Output Format**: YAML (`application/yaml`) — a ContainerLab topology file.
- **Target Nodes**: `NetworkFabric` (artifact target group `fabrics`), parameterised by
  `name__value`.

### Existing baseline

This feature modifies an existing pipeline rather than creating one. Already in place:

| Component | Path |
|---|---|
| Transform | `transforms/containerlab_topology.py` |
| GraphQL query | `transforms/containerlab_topology.gql` |
| Typed models (hand-written) | `transforms/containerlab_topology_query.py` |
| Jinja2 template | `transforms/templates/containerlab_topology.j2` |
| Unit tests | `tests/unit/test_containerlab_topology.py` |
| Registration | `.infrahub.yml` (query 51-52, transform 166-168, artifact 210-216) |
| Ansible draft | `lab/playbooks/deploy_clab.yml` (relocated to `ansible/deploy_clab.yml`) |
| Parity reference | `lab/topology.clab.yml` |

### Parity reference (the "current thing")

`lab/topology.clab.yml` is the hand-maintained ground truth: topology `infrahub-avd`, mgmt
network `clab-infrahub-avd-mgmt` on `10.0.6.0/24`, two kinds (`arista_ceos` →
`arista/ceos:4.36.0.1F`, `linux` → `lab-server`), 12 cEOS nodes + 2 Linux servers, and 24 links.

`Fabric-L3LS-Multi-Domain` is a **single** `NetworkFabric` containing pods `infrahub-dc1` and
`infrahub-dc2`, so one fabric-scoped artifact already covers both domains. No new target scope
is required.

---

## Clarifications

### Session 2026-07-30

- Q: How strictly must the generated topology match `lab/topology.clab.yml`? → A: Structural
  parity — node count, kinds, images, interface names, link mesh, management subnet. Node names
  stay Infrahub-generated (`spine-infrahub-dc1-1`), not the lab's `ih-dc1-spine1`.
- Q: How should the container image and per-device-type interface mapping be modelled? → A:
  `Text` attributes — `containerlab_image` on `DcimPlatform`, `containerlab_interface_mapping`
  on `DcimDeviceType`. Not `CoreFileObject`.
- Q: Should the two Linux server nodes be included? → A: Yes, with netplan shipped from
  `lab/configs/servers/`; netplan itself is not generated.
- Q: How should the per-server netplan bind filename be sourced? → A: By convention from the
  device name (`configs/servers/<device-name>-netplan.yaml`); rename the two committed lab files
  to match.
- Q: How should devices excluded by role filtering be reported? → A: Python logger warning, one
  per excluded device. The artifact stays pure data.
- Q: What deterministic rule picks the management subnet? → A: Most common subnet among devices,
  ties broken by lowest network address.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Every multi-domain node and link appears in the artifact (Priority: P1)

A network engineer generates the **ContainerLab Topology** artifact for
`Fabric-L3LS-Multi-Domain` and receives a topology containing all 12 switches — including the
four border leaves — and all 20 switch-to-switch links, comprising the 16 spine↔leaf links and
the 4 DCI links that join the two domains.

**Why this priority**: Today `NETWORK_ROLES` in `transforms/containerlab_topology.py` omits
`border_leaf`, so the four border leaves are dropped silently, and with them every DCI link and
eight spine↔leaf uplinks. The artifact currently misrepresents the multi-domain fabric as two
disconnected islands. Without this fix nothing else in the feature is meaningful.

**Independent Test**: Render the artifact for `Fabric-L3LS-Multi-Domain` and assert the node
count is 12 switches and that four links carry `NetworkLink.role == dci`. Deliverable value
even if no other story lands.

**Acceptance Scenarios**:

1. **Given** a fabric whose border leaves carry `role: border_leaf`, **When** the transform
   runs, **Then** those devices appear as nodes and their links appear in `links`.
2. **Given** the four DCI links between DC1 and DC2 border leaves, **When** the transform runs,
   **Then** all four appear with correctly translated interface names (`eth5`, `eth6`).
3. **Given** a fabric containing a device in a role with no ContainerLab representation,
   **When** the transform runs, **Then** the device is excluded and the omission is recorded
   rather than silent.

---

### User Story 2 — Kind, image, and interface mapping come from the graph (Priority: P1)

The topology's node kinds, container images, and per-device-type interface-mapping binds are
derived from Infrahub data rather than hardcoded, so changing a platform's image or a device
type's mapping file is a data change, not a code change.

**Why this priority**: This is the "account for interfaces and images" requirement. cEOS maps
container interfaces to EOS names via `/mnt/flash/EosIntfMapping.json`; without the correct
per-device-type bind, breakout names (`eth1_1`, `eth49_1`) do not resolve and the fabric does
not come up. `DcimPlatform.containerlab_os` already holds `arista_ceos` but is never queried,
and no image attribute exists anywhere in the schema.

**Independent Test**: Load the schema, set the attribute values, render the artifact, and assert
`topology.kinds` carries the image from `DcimPlatform.containerlab_image` and each spine node
binds `DCS-7050CX3-32S.json` while each leaf binds `DCS-7050SX3-48YC8.json`.

**Acceptance Scenarios**:

1. **Given** `DcimPlatform` has `containerlab_os: arista_ceos` and
   `containerlab_image: arista/ceos:4.36.0.1F`, **When** the transform runs, **Then** the
   rendered kind and image match those values with no hardcoded fallback in the output.
2. **Given** a `DcimDeviceType` with `containerlab_interface_mapping` set, **When** the
   transform runs, **Then** each node of that type emits a bind mounting that file at
   `/mnt/flash/EosIntfMapping.json:ro`.
3. **Given** a device type with no mapping value, **When** the transform runs, **Then** the node
   renders without a mapping bind and remains valid ContainerLab YAML.
4. **Given** an interface named `Ethernet49/1`, **When** the transform runs, **Then** the
   endpoint renders as `eth49_1`, matching the mapping file's key.

---

### User Story 3 — Ansible pulls the artifact and brings the lab up (Priority: P1)

An operator runs one Ansible playbook on a ContainerLab-capable host. It fetches the topology
artifact and every device's rendered configuration from Infrahub, stages all files the topology
references, and runs `containerlab deploy`. The lab comes up without any hand-editing.

**Why this priority**: This is the second half of the user's request. A correct artifact that
cannot be deployed delivers nothing. The existing `lab/playbooks/deploy_clab.yml` is a draft
with unverified module names, is wired into no `Makefile` target, and stages neither the
interface-mapping nor the netplan files the topology binds.

**Independent Test**: Run the playbook in check mode against a fabric and confirm every file
referenced by a `binds` or `startup-config` entry has a corresponding staging task.

**Acceptance Scenarios**:

1. **Given** Infrahub holds a generated topology artifact, **When** the playbook runs, **Then**
   the topology file and every referenced bind and startup-config file are present on disk
   before `containerlab deploy` is invoked.
2. **Given** the playbook has completed, **When** the operator inspects the lab, **Then** node
   count and link count match the artifact.
3. **Given** a device's configuration artifact is missing in Infrahub, **When** the playbook
   runs, **Then** it fails with a message naming the device rather than deploying a partial lab.

---

### User Story 4 — Servers are present so reachability can be proven (Priority: P2)

The two Linux server nodes appear in the generated topology with their management addresses,
netplan binds, and dual-homed links to the access leaves, so end-to-end reachability across the
fabric can be tested.

**Why this priority**: Servers are what make the lab provable rather than merely booted. They
are lower priority than P1 because the switch fabric is independently valuable, but the lab
folder's reachability checks depend on them.

**Independent Test**: Render the artifact and assert two `linux`-kind nodes exist, each with two
links to distinct access leaves.

**Acceptance Scenarios**:

1. **Given** `ComputePhysicalServer` nodes exist in the fabric's racks, **When** the transform
   runs, **Then** each appears as a `linux`-kind node with its management address.
2. **Given** server cabling exists, **When** the transform runs, **Then** each server's two
   links to its access leaves appear with translated interface names.
3. **Given** a server node, **When** the transform runs, **Then** it emits a netplan bind
   mounting the server's network configuration at `/etc/netplan/netplan.yaml`.

---

### User Story 5 — Output is deterministic and typed (Priority: P3)

Repeated renders of unchanged data produce byte-identical output, and all GraphQL access uses
registered queries with generated return types.

**Why this priority**: Non-deterministic artifacts create phantom diffs in proposed changes and
make review noisy. The inline GraphQL string literal also violates the project's typed-query
principle. Correctness-neutral but required by the constitution.

**Independent Test**: Render twice from identical data and diff; grep the transform for inline
GraphQL string literals.

**Acceptance Scenarios**:

1. **Given** unchanged fabric data, **When** the artifact is generated twice, **Then** the two
   outputs are byte-identical.
2. **Given** a fabric whose devices sit in more than one management subnet, **When** the
   transform runs, **Then** the chosen management subnet is selected deterministically, not by
   dictionary iteration order.
3. **Given** the transform needs link endpoints, **When** it queries Infrahub, **Then** it uses
   a registered `.gql` file with generated return types rather than an inline string.

---

### Edge Cases

- A fabric with no devices renders a structurally valid topology with empty `nodes`/`links`.
- A device with no `mgmt_ip` renders without `mgmt-ipv4` rather than failing.
- A device whose `device_type` has no `platform` falls back to a documented default kind, or is
  excluded with the omission recorded.
- A `NetworkLink` with fewer or more than two connected endpoints is skipped.
- A link whose peer device was excluded by role filtering is skipped, not rendered dangling.
- Devices reachable both through a pod and through a rack are emitted once.
- No device carries a masked management address, so no management subnet can be derived.
- Two device types resolve to the same mapping filename — the bind is still correct per node.
- A device type's mapping filename is set but the file is absent on the deploy host; the
  playbook must fail loudly rather than let ContainerLab create a directory at the bind path.
- Interface names in three segments (`Ethernet1/1/1`) translate consistently.
- More than 50 links exist, exercising endpoint-query batching.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Schema (prerequisite — use `infrahub-managing-schemas`)

- **FR-001**: `DcimPlatform` MUST gain a `containerlab_image` attribute of kind `Text`,
  `optional: true`, placed adjacent to the existing `containerlab_os` (`order_weight: 1900`) in
  `schemas/base/dcim.yml`.
- **FR-002**: `DcimDeviceType` MUST gain a `containerlab_interface_mapping` attribute of kind
  `Text`, `optional: true`, holding the interface-mapping filename for that device type.
- **FR-003**: Both new attributes MUST be `optional: true`; a mandatory attribute without a
  default would invalidate every already-loaded `DcimPlatform` and `DcimDeviceType` instance.
- **FR-004**: Attribute names MUST be snake_case and `order_weight` MUST follow the file's
  existing progression so UI field order stays stable.
- **FR-005**: `infrahubctl schema check schemas/` MUST pass, and
  `src/solution_arista_avd/protocols.py` MUST be regenerated rather than hand-edited.
- **FR-006**: Schema changes MUST be validated on a dedicated branch, not the default branch.

#### Object data (use `infrahub-managing-objects`)

- **FR-007**: The `EOS` platform in `objects/03_device_type.yml` MUST set
  `containerlab_image: arista/ceos:4.36.0.1F`, matching `lab/topology.clab.yml`.
- **FR-008**: Arista device types MUST set `containerlab_interface_mapping` to the filenames the
  lab folder already ships — spines `DCS-7050CX3-32S.json`, leaves `DCS-7050SX3-48YC8.json`.
- **FR-009**: Object data MUST be added to existing numbered files, preserving load order.
- **FR-010**: A platform representing the Linux server image MUST supply the `linux` kind and
  `lab-server` image through the same schema path, so no kind or image is hardcoded.

#### GraphQL query

- **FR-011**: `transforms/containerlab_topology.gql` MUST additionally retrieve, per device,
  `device_type.platform.containerlab_os`, `device_type.platform.containerlab_image`, and
  `device_type.containerlab_interface_mapping`.
- **FR-012**: The query MUST retrieve the fabric's `ComputePhysicalServer` members with their
  management addresses and interfaces.
- **FR-013**: The query MUST retrieve each `NetworkLink`'s `role` so DCI links are
  distinguishable.
- **FR-014**: A registered `.gql` file MUST replace the inline link-endpoint query string in
  `transforms/containerlab_topology.py`, with return types generated by
  `infrahubctl graphql generate-return-types` and not hand-written.
- **FR-015**: Both new queries MUST be registered under `queries:` in `.infrahub.yml`.

#### Transform logic

- **FR-016**: Role filtering MUST include `border_leaf` alongside the existing `super_spine`,
  `spine`, `leaf`, and `l2leaf`, and MUST cover `l2spine` and `l3spine`.
- **FR-017**: Node kind MUST derive from `DcimPlatform.containerlab_os` and image from
  `DcimPlatform.containerlab_image`; the module-level `CEOS_KIND` and `CEOS_IMAGE` constants
  MUST NOT determine rendered output.
- **FR-018**: Each node MUST emit a bind for its device type's interface-mapping file when the
  attribute is set, mounted read-only at `/mnt/flash/EosIntfMapping.json`.
- **FR-019**: `ComputePhysicalServer` members MUST render as nodes of the Linux kind with their
  management address and a netplan bind, and their links to leaves MUST be retained rather than
  dropped.
- **FR-019a**: The netplan bind source MUST be derived by convention from the device name as
  `configs/servers/<device-name>-netplan.yaml`, mounted at `/etc/netplan/netplan.yaml`. The two
  committed files MUST be renamed to `dc1-server-netplan.yaml` and `dc2-server-netplan.yaml` to
  match the Infrahub device names. No schema attribute is added for this.
- **FR-019b**: The Linux kind and its `lab-server` image MUST be sourced from a `DcimPlatform`
  assigned to the servers via the `platform` relationship that `ComputePhysicalServer` inherits
  from `DcimGenericDevice`. No new schema node or relationship is required. Note that
  `device_type` is not available on that generic, so servers carry no interface mapping — which
  is correct, as only cEOS nodes need one.
- **FR-020**: Interface translation MUST remain `Ethernet<N>[/<M>]` → `eth<N>[_<M>]`, matching
  the keys in the shipped mapping files.
- **FR-021**: Management-subnet derivation MUST select the subnet shared by the most devices,
  breaking ties by lowest network address, and MUST NOT depend on dictionary iteration order.
  This keeps a single mis-addressed device from displacing the real management range.
- **FR-022**: Nodes and links MUST be emitted in a stable sorted order, preserving the existing
  intra-link endpoint ordering and global link sort.
- **FR-023**: Devices excluded by role filtering MUST emit one logger warning each, naming the
  device and its role, so exclusions are diagnosable rather than silent. The rendered artifact
  MUST remain pure data, carrying no diagnostic comments, so parity and determinism assertions
  stay simple.
- **FR-024**: All graph access MUST use generated typed models; untyped dictionary access is
  prohibited in production code.
- **FR-025**: Ruff complexity MUST stay within C901 max-complexity 17; helpers MUST be split
  rather than growing one render function.
- **FR-026**: The dead generated module `transforms/container_lab_topology.py` MUST be removed
  or replaced by a properly named generated module, and the hand-written
  `containerlab_topology_query.py` MUST no longer be silently excluded from linting by the
  `**/*_query.py` glob in `pyproject.toml`.

#### Jinja2 template

- **FR-027**: `transforms/templates/containerlab_topology.j2` MUST render multiple kinds, each
  with its own image, rather than a single hardcoded kind block.
- **FR-028**: The kind-level `startup-config` path MUST match the directory the Ansible playbook
  writes device configurations into; the current `avd/intended/configs/` reference points at
  committed files the playbook never populates.
- **FR-029**: The template MUST emit per-node `binds` lists, omitting the key entirely when a
  node has no binds.
- **FR-030**: Rendered output MUST parse as valid YAML and as a valid ContainerLab topology.

#### Artifact registration

- **FR-031**: The existing `containerlab_topology` artifact definition MUST remain fabric-scoped
  (`targets: fabrics`, `parameters: {name: name__value}`, `content_type: application/yaml`); no
  new target group is needed because the multi-domain fabric is a single `NetworkFabric`.

#### Ansible deployment

- **FR-032**: The deploy playbook (`ansible/deploy_clab.yml`) MUST use the parameters and return keys that
  `opsmill.infrahub` 1.8.3 actually provides. The module names in the current draft are correct;
  the parameters and return keys are not. Verified against the collection and proven against a
  live Infrahub:
  - `artifact_fetch.target_id` MUST be a node **UUID**; passing a node name fails with
    "Unable to find '<artifact>' for '<name>'". The device- and fabric-discovery queries MUST
    therefore select `id`.
  - `artifact_fetch` returns only `json` and `text`. `content` does not exist, and
    `text | default(content)` never falls through because `text` is always present (`None` for
    JSON artifacts). Both artifacts consumed here (`application/yaml` and `text/plain`) land in
    `text`.
  - `query_graphql` takes **`graph_variables`**, not `variables`. A `variables` key is silently
    ignored — action plugins do not validate against the module argument spec — and surfaces
    later as "Variable '$name' of required type 'String!' was not provided".
  - `query_graphql` registers its result under **`response`**, not `data` or `results`, despite
    the module's own `RETURN` docstring saying `data`.
- **FR-032a**: The playbook's prerequisites MUST document that `infrahub-sdk` has to be
  importable by the Ansible controller's Python, since the action plugins raise
  "infrahub_sdk must be installed to use this plugin". `lab/pyproject.toml` pins the community
  `ansible` bundle, which does **not** ship `opsmill.infrahub`, so the collection must be
  installed separately — it is absent from this host and from `lab/`.
- **FR-033**: The playbook MUST fetch the **ContainerLab Topology** artifact for the named
  fabric and write it to the topology path.
- **FR-034**: The playbook MUST fetch each device's **AVD EOS Configuration** artifact and write
  it to the directory the topology's `startup-config` references.
- **FR-035**: The playbook MUST stage every file the topology binds — interface-mapping files
  and server netplan files — before invoking ContainerLab.
- **FR-036**: The playbook MUST fail with an actionable message when a required artifact or bind
  source is missing, rather than deploying a partial lab.
- **FR-037**: The playbook MUST be reachable from a `lab/Makefile` target, consistent with the
  existing target naming.
- **FR-038**: The playbook MUST be idempotent — re-running against unchanged data MUST NOT
  produce a different lab state.

#### Tests

- **FR-039**: Unit tests MUST cover role inclusion (notably `border_leaf`), kind/image
  derivation from platform data, mapping-bind emission and its absence, server node and link
  emission, deterministic subnet derivation, and interface-name translation including breakout
  and three-segment forms.
- **FR-040**: A test MUST assert structural parity against `lab/topology.clab.yml`: node count
  by kind, link count by category, and the set of translated interface names.
- **FR-041**: A determinism test MUST assert two renders of identical input are byte-identical.
- **FR-042**: The existing assertion that pins the absence of binds MUST be replaced, not
  deleted silently, since binds are now expected.
- **FR-043**: Integration coverage MUST confirm the artifact generates for the multi-domain
  fabric and contains the border leaves and DCI links.

#### Documentation

- **FR-044**: `lab/README.md` MUST be updated: remove the "Planned: interface mappings from the
  schema" section as implemented, and document the Makefile target and required environment.
- **FR-045**: `docs/docs/` MUST gain ContainerLab coverage, since it currently has none, with
  `docs/sidebars.ts` updated if navigation changes.
- **FR-046**: `docs/docs/viewing-artifacts.md` MUST accurately describe the ContainerLab
  artifact alongside the existing artifacts.

### Key Entities

- **NetworkFabric** — artifact target; supplies topology name and management gateway.
  `Fabric-L3LS-Multi-Domain` holds both domains.
- **NetworkPod** — `infrahub-dc1` / `infrahub-dc2`; the domain boundary. Carries `evpn_domain`.
- **LocationRack** — `DC1_BORDER`, `DC1_ACCESS`, `DC2_BORDER`, `DC2_ACCESS`; groups leaves.
- **DcimDevice** — becomes a topology node. Supplies `name`, `role`, `mgmt_ip`, `device_type`.
- **DcimDeviceType** — gains `containerlab_interface_mapping`; selects the mapping bind.
- **DcimPlatform** — carries `containerlab_os` (kind) and the new `containerlab_image`.
- **DcimInterface / InterfacePhysical** — supplies EOS interface names for translation.
- **NetworkLink** — becomes a topology link; `role: dci` marks inter-domain links.
- **ComputePhysicalServer** — becomes a Linux-kind node with a netplan bind.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The artifact for the multi-domain fabric contains 12 switch nodes and 20
  switch-to-switch links, of which exactly 4 are the inter-domain links. The before-state depends
  on whether `manual_objects/00_lab_l3ls_multi_domain.yml` is loaded: without it every leaf carries
  `role: leaf` and no DCI links exist, so the old transform rendered 12 nodes / 16 links; with it
  loaded, the four border leaves and all 12 links touching them were dropped.
- **SC-002**: Every node that needs one carries an interface-mapping bind, and no rendered
  interface name fails to resolve inside its node.
- **SC-003**: With servers included, the artifact contains 14 nodes and 24 links, matching
  `lab/topology.clab.yml` exactly on both counts.
- **SC-004**: No container image, node kind, or mapping filename appears as a literal in
  transform code; each is traceable to a schema attribute.
- **SC-005**: One operator command brings the lab up from Infrahub data on a ContainerLab host,
  with no manual file editing between fetch and deploy.
- **SC-006**: Two consecutive renders of unchanged data are byte-identical.
- **SC-007**: `uv run pytest tests/unit` passes; `uv run invoke lint` (ruff, mypy, yamllint)
  reports zero findings.
- **SC-008**: `infrahubctl schema check schemas/` passes with zero validation errors.
- **SC-009**: A reviewer can compare the generated topology against `lab/topology.clab.yml` and
  account for every difference as an intended, documented divergence.

---

## Assumptions

1. **Structural, not textual, parity.** Node names stay Infrahub-generated
   (`spine-infrahub-dc1-1`), not the lab folder's `ih-dc1-spine1`. Parity means node count,
   kinds, images, interface names, link mesh, and management subnet. Confirmed with the user.
2. **Interface mappings are Text filenames, not file objects.** The mapping JSON stays in
   `lab/configs/eos-intf-mapping/` and the schema stores only the filename. The
   `CoreFileObject`-on-`DcimDeviceType` approach sketched in the transform docstring is
   deliberately not taken. Confirmed with the user.
3. **Server netplan is shipped from `lab/`, not generated.** Generating netplan from Infrahub
   would yield VLANs 21/22/29 per the fabric's `EvpnSvi` data, whereas the committed netplan
   uses VLANs 11/12/19 — so generating it would change the reachability checks. Confirmed with
   the user.
4. **DCI links remain hand-authored data.** No generator creates `role: dci` links; they live in
   `manual_objects/00_lab_l3ls_multi_domain.yml`. This feature consumes them and does not add a
   generator.
5. **Management IPs come from `manual_objects/`.** `create_avd_device` allocates management
   addresses from a pool, so the `.11`–`.16`/`.21`–`.26` assignments matching the lab depend on
   the pinned `manual_objects` data being loaded.
6. **The topology name derives from the fabric name**, so it will read
   `Fabric-L3LS-Multi-Domain` rather than `infrahub-avd`. This changes container names and is
   an accepted divergence from the lab folder.

## Out of Scope

- Renaming Infrahub devices to the lab folder's `ih-*` names.
- A generator for DCI links or for management-IP pinning.
- Generating server netplan, VLAN, or SVI data.
- Reusing the committed `lab/avd/intended/configs/` renders; configs come from Infrahub.
- CloudVision onboarding, the ZTP token bind, and `topology.clab.yml.annotations.json` layout.
- Building or publishing the `lab-server` container image.
- The standalone `lab/avd/` ansible-avd flow, which stays group_vars-driven.

## Dependencies

- Infrahub 1.10.1, `infrahub-sdk` 1.22.0 — both confirmed available.
- `opsmill.infrahub` collection 1.8.3 on the deploy host, with `infrahub-sdk` importable by the
  controller's Python. **Currently absent** from this host, from the configured collection paths,
  and from `lab/`; `ansible/requirements.yml` declares it but nothing has installed it. Installing
  it is a prerequisite for validating the deployment path.
- `containerlab` — confirmed present (0.77.0).
- Docker with `arista/ceos:4.36.0.1F` and `lab-server` — both confirmed present.
- `manual_objects/00_lab_l3ls_multi_domain.yml` loaded, for border-leaf roles, DCI links, and
  pinned management IPs.

## Environment Notes

`opsmill.infrahub.object_file_fetch` exists in 1.8.3 (params `kind`, `node_id`/`hfid`, `dest`).
It is the module the deferred `CoreFileObject`-on-`DcimDeviceType` approach would need, should the
interface-mapping decision be revisited later. Not used by this feature, which stores only
filenames.
