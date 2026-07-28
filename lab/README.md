# ContainerLab from Infrahub

Generate a [ContainerLab](https://containerlab.dev) topology from an Infrahub fabric and deploy it
as a virtual replica (Arista cEOS nodes).

## What's here

| Path | Purpose |
|------|---------|
| `playbooks/deploy_clab.yml` | Pull the topology + configs from Infrahub and `containerlab deploy` |
| `topology.clab.yml` | The generated topology (written by the deploy playbook, git-ignored) |

## 1. Generate the topology (Infrahub artifact)

The topology is produced by the `containerlab_topology` transform, exposed as the **"ContainerLab
Topology"** artifact for every fabric (target group `fabrics`). Render it locally to preview:

```bash
# COLUMNS is set because infrahubctl prints via Rich, which wraps long lines at the terminal
# width — irrelevant to the server-rendered artifact, but needed when saving locally.
COLUMNS=500 uv run infrahubctl transform containerlab_topology name=Fabric-L3LS-MultiPod-A > lab/topology.clab.yml
```

Each network device (super_spine / spine / leaf / l2leaf) becomes an `arista_ceos` node with its
management IP; interface names are translated `Ethernet<N>[/<M>]` → `eth<N>[_<M>]` — cEOS's default
mapping, so no `EosIntfMapping.json` bind is needed for the plain `Ethernet<N>` interfaces the fabric
uses today.

## 2. Deploy with Ansible

On a ContainerLab-capable host with the `opsmill.infrahub` collection installed:

```bash
cd lab
uv run ansible-playbook playbooks/deploy_clab.yml -e fabric=Fabric-L3LS-MultiPod-A
```

The playbook fetches the ContainerLab Topology artifact and each device's AVD EOS Configuration
artifact from Infrahub, stages them, and runs `containerlab deploy`.

> The exact `opsmill.infrahub` module names can vary by collection version — confirm with
> `ansible-doc -l opsmill.infrahub` and adjust the playbook if needed.

## Planned: per-device-type interface mappings

Per-device-type `EosIntfMapping.json` files (bound into each node) are planned as a separate
schema-first cycle: a `CoreFileObject` attached to `DcimDeviceType`, populated by a generator and
read by the transform via `device.device_type`. Until then, the algorithmic translation above is
used (and is correct for the current `Ethernet<N>` interfaces).
