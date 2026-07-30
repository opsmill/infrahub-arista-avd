# ContainerLab from Infrahub

Run the Infrahub AVD reference design as a virtual replica on
[ContainerLab](https://containerlab.dev) (Arista cEOS nodes).

Two flows live here:

- **The `infrahub-avd` lab** (`Makefile` + `topology.clab.yml`) — a committed two-DC topology whose
  cEOS nodes boot straight from the AVD-rendered configs in `avd/intended/configs/`. This is the
  day-to-day lab.
- **The transform-generated topology** (`playbooks/deploy_clab.yml`) — renders a topology for *any*
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
| `playbooks/` | AVD build/deploy/test playbooks, plus the transform-driven `deploy_clab.yml` |
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

Each network device (super_spine / spine / leaf / l2leaf) becomes an `arista_ceos` node with its
management IP; interface names are translated `Ethernet<N>[/<M>]` → `eth<N>[_<M>]` — cEOS's default
mapping, so the plain `Ethernet<N>` interfaces the fabric uses today need no mapping bind.

Then deploy on a ContainerLab-capable host with the `opsmill.infrahub` collection installed:

```bash
cd lab
uv run ansible-playbook playbooks/deploy_clab.yml -e fabric=Fabric-L3LS-MultiPod-A
```

The playbook fetches the ContainerLab Topology artifact and each device's AVD EOS Configuration
artifact from Infrahub, stages them, and runs `containerlab deploy`.

> The exact `opsmill.infrahub` module names can vary by collection version — confirm with
> `ansible-doc -l opsmill.infrahub` and adjust the playbook if needed.

## Planned: interface mappings from the schema

The `infrahub-avd` lab binds checked-in per-device-type `EosIntfMapping.json` files from
`configs/eos-intf-mapping/`. Sourcing those from Infrahub instead — a `CoreFileObject` attached to
`DcimDeviceType`, populated by a generator and read by the transform via `device.device_type` —
remains a separate schema-first cycle, and is what the transform-generated flow above would need to
cover non-default interface naming.
