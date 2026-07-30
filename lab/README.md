# ContainerLab from Infrahub

Run the Infrahub AVD reference design as a virtual replica on
[ContainerLab](https://containerlab.dev) (Arista cEOS nodes).

Two flows live here:

- **The `infrahub-avd` lab** (`Makefile` + `topology.clab.yml`) — a committed two-DC topology whose
  cEOS nodes boot straight from the AVD-rendered configs in `avd/intended/configs/`. This is the
  day-to-day lab.
- **The transform-generated topology** (`../ansible/deploy_clab.yml`) — renders a topology for *any*
  Infrahub fabric via the `containerlab_topology` artifact. Use this for fabrics the committed
  topology doesn't cover.

## What's here

| Path | Purpose |
|------|---------|
| `Makefile` | Entry point for every lab operation — install, deploy, build, push, test |
| `topology.clab.yml` | The `infrahub-avd` topology: 2 DCs × (2 spines + 4 leaves) + 2 servers |
| `topology.clab.yml.annotations.json` | Diagram groups/shapes for `make graph`, edited via the VSCode ContainerLab plugin |
| `Dockerfile` | The `lab-server` image used by the two Linux host nodes |
| `avd/` | Ansible/AVD workspace: inventory, `group_vars`, and rendered output |
| `configs/ceos-config/` | Per-node cEOS config bound to `/mnt/flash/ceos-config` |
| `configs/eos-intf-mapping/` | Per-device-type `EosIntfMapping.json` bound into each cEOS node |
| `configs/servers/` | Netplan config for the Linux host nodes |
| `playbooks/` | AVD build/deploy/test playbooks |
| `pyproject.toml`, `uv.lock` | Pinned lab toolchain (Ansible, AVD, ANTA, `ardl`) |

`avd/intended/`, `avd/documentation/`, and `avd/anta/` are committed rather than ignored: the
topology's `startup-config` points at `avd/intended/configs/__clabNodeName__.cfg`, so those renders
are what the nodes actually boot. Committing them also makes fabric changes reviewable as a diff.

## 1. Install the toolchain

uv manages the Python 3.12 interpreter itself, so no system Python 3.12 is needed. Every target
invokes CLIs through `uv run`, so no venv activation is required.

```bash
cd lab
make install        # uv sync + ansible-galaxy install arista.avd
make ceos           # download and import the cEOS image (add version=4.36.0.1F to pin)
```

## 2. Bring the lab up

```bash
make start          # containerlab deploy --reconfigure
make stop           # containerlab save, then destroy --graceful (keeps mgmt net)
make destroy        # containerlab destroy --cleanup
```

Nodes boot from the committed AVD configs, so the fabric comes up converged — no push needed for a
first run.

## 3. Rebuild and push configs

```bash
make build          # re-render structured configs, EOS configs, docs, and ANTA catalogs
make eapi-check     # eAPI push, --check --diff (dry run)
make eapi-deploy    # eAPI push, --diff
make test           # run the ANTA catalogs, writing avd/anta/reports/
```

`make workspace` and `make deploy` target CloudVision instead of eAPI — `workspace` submits a
workspace only, `deploy` also executes change control.

`make clean` removes the regenerated output (`avd/documentation`, `avd/intended/structured_configs`,
`avd/anta/reports`, `avd/anta/avd_catalogs`).

## 4. Verify reachability

```bash
make ping           # all three checks below
```

| Target | Checks |
|--------|--------|
| `ping_vrf10_dc1_to_dc2` | VRF10 routed DC1 → DC2 |
| `ping_vrf10_dc2_to_dc1` | VRF10 routed DC2 → DC1 |
| `ping_vlan19_bridged` | VLAN 19 stretched L2 across the DCI |

## 5. Diagram

```bash
make graph          # containerlab graph --drawio → docs/topology.drawio
```

Reads `topology.clab.yml` plus the sibling annotations file so the generated diagram keeps its
grouping and layout.

## CloudVision onboarding

`CV_TOKEN_BIND` is the single source of truth for the cEOS-side CVaaS bind; `make start` exports it,
so switching patterns never means editing the topology:

| Invocation | Effect |
|------------|--------|
| `make start USE_ZTP=1` | Binds `../ztp` to `/mnt/usb1/ztp`; EOS ZTP reads `ztpConfig.yaml` at boot and pulls the token. The topology must then omit `startup-config:`, or ZTP is bypassed. |
| `make start LAB_ONBOARDING_TOKEN=<file>.tok` | Binds that file to `/mnt/flash/cv-onboarding-token`; TerminAttr reads it directly. |
| Neither | `CV_TOKEN_BIND` is unset, so the topology must not reference it — the default no-CVaaS lab. |

## Generating a topology for another fabric

The `containerlab_topology` transform renders a topology for any fabric (target group `fabrics`).
Render it locally to preview:

```bash
# COLUMNS is set because infrahubctl prints via Rich, which wraps long lines at the terminal
# width — irrelevant to the server-rendered artifact, but needed when saving locally.
COLUMNS=500 uv run infrahubctl transform containerlab_topology name=Fabric-L3LS-MultiPod-A > lab/topology.clab.yml
```

What the render contains:

- **Network devices** with roles `super_spine`, `spine`, `leaf`, `border_leaf`, `l2leaf`,
  `l2spine`, and `l3spine`. The `p` / `pe` / `rr` roles are deliberately excluded — they belong to
  the ISIS-LDP fabric, whose interface naming has not been validated against ContainerLab, so that
  fabric renders without those devices. Every excluded device is logged as a warning rather than
  dropped silently.
- **Server nodes** — the fabric's `ComputePhysicalServer` members, as nodes of the `linux` kind,
  with their leaf-facing links retained.
- **One `kinds` entry per distinct kind** present in the fabric, each with its own image.
- **Per-node `binds`** — the interface-mapping file for cEOS nodes, the netplan file for servers.
  The `binds` key is omitted entirely for nodes with nothing to bind.

Kind, image, and mapping filename all come from schema attributes, so none of them are decided in
Python:

| Attribute | Drives | Example |
|-----------|--------|---------|
| `DcimPlatform.containerlab_os` | node `kind` | `arista_ceos`, `linux` |
| `DcimPlatform.containerlab_image` | kind `image` | `arista/ceos:4.36.0.1F`, `lab-server` |
| `DcimDeviceType.containerlab_interface_mapping` | the `EosIntfMapping.json` bind | `DCS-7050CX3-32S.json` |

Interface names are translated `Ethernet<N>[/<M>]` → `eth<N>[_<M>]`. That matches cEOS's default
mapping for plain `Ethernet<N>` interfaces, but not for breakouts — a config referring to
`Ethernet1/1` needs the device type's `EosIntfMapping.json` bound at
`/mnt/flash/EosIntfMapping.json:ro` for the name to resolve. Server nodes get
`configs/servers/<device-name>-netplan.yaml` at `/etc/netplan/netplan.yaml` instead; the filename is
derived from the Infrahub device name.

### Deploying it

Requires a ContainerLab-capable host and:

```bash
export INFRAHUB_ADDRESS=http://localhost:8000
export INFRAHUB_API_TOKEN=<token>

# From the repository root — the collection is not vendored.
ansible-galaxy collection install -r ansible/galaxy-requirements.yml
```

`lab/pyproject.toml` pins the community `ansible` bundle, which does **not** ship
`opsmill.infrahub`, so the `ansible-galaxy` step is separate from `make install`. The collection's
plugins run on the Ansible controller and import `infrahub-sdk` directly, so `infrahub-sdk` must be
importable by the **controller's** Python or they fail with
`infrahub_sdk must be installed to use this plugin`.

```bash
cd lab
make deploy-from-infrahub FABRIC=Fabric-L3LS-MultiPod-A
```

The playbook lives in `../ansible/` rather than `playbooks/`, because that directory is also the
Semaphore playbook repository. It is two plays: the first fetches the ContainerLab Topology artifact
and each device's AVD EOS Configuration artifact from Infrahub, the second stages them plus this
directory's committed bind sources onto every host in the `clab_hosts` group of
`../ansible/inventory_clab.yml` and runs `containerlab deploy` there. Out of the box that group is
`localhost`; point it at a remote host to drive a separate ContainerLab machine.

Add `--skip-tags deploy` to stage and validate without touching the lab, and
`-e clab_staging_dir=<path>` to change where on the lab host the files land (default
`/opt/containerlab/<fabric>`).

> The exact `opsmill.infrahub` module names can vary by collection version — confirm with
> `ansible-doc -l opsmill.infrahub` and adjust the playbook if needed.

### How the generated topology differs from this lab

Structural parity is the target, not byte equality. These divergences are intentional:

| | This lab | Generated |
|---|---|---|
| Node names | `ih-dc1-spine1` | `spine-infrahub-dc1-1` — the Infrahub device names, no renaming layer |
| Topology name | `infrahub-avd` | the fabric name, so container and management-network names differ |
| `startup-config` dir | `avd/intended/configs/` | `configs/` — where the playbook writes fetched configs |
| `ceos-config` bind | present | absent — serial/system-MAC files are per-lab-device-name and are not modelled in Infrahub |
| CVaaS token bind | available, commented out | absent |

Node counts, kinds, images, management addresses, link counts, interface-name forms, and bind mount
points do match.

**Server-to-server reachability is not expected to work in the generated lab.** The netplan files in
`configs/servers/` encode VLANs 11/12/19 and their addresses, while the multi-domain fabric models
VLANs 21/22/29, and netplan is not generated from Infrahub. The `make ping` targets above belong to
this committed lab, not the generated one.

## Interface mappings from the schema

Per-device-type `EosIntfMapping.json` binds are sourced from Infrahub: the filename comes from the
`DcimDeviceType.containerlab_interface_mapping` attribute (kind `Text`, filename only), and the
container image from `DcimPlatform.containerlab_image`. The transform reads them via
`device.device_type` and `device.platform`; the files themselves stay checked in under
`configs/eos-intf-mapping/`.

Text-filename attributes were chosen over attaching a `CoreFileObject` to `DcimDeviceType`: the
files are lab fixtures that belong in the repository next to the topology that references them, and
a filename attribute needs no generator to populate the object store. Seed values live in
`objects/03_device_type.yml`. Note the mapping filenames intentionally differ from the device type's
`part_number` (`DCS-7050CX3-32S.json` for part number `DCS-7050CX3-32C`), which is the reason the
attribute exists rather than being derived.
