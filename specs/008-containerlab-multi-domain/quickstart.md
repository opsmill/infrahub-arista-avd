# Quickstart: validating the ContainerLab multi-domain artifact

Runnable validation for this feature. Commands assume repo root unless stated otherwise.

## Prerequisites

| Requirement | Status on this host | Check |
|---|---|---|
| Infrahub reachable | ✅ 1.10.1, SDK 1.22.0 | `uv run infrahubctl info` |
| `containerlab` | ✅ 0.77.0 | `containerlab version` |
| Docker + `arista/ceos:4.36.0.1F` | ✅ present | `docker images \| grep ceos` |
| Docker + `lab-server` | ✅ present | `docker images \| grep lab-server` |
| `opsmill.infrahub` collection | ❌ **absent** | `ansible-galaxy collection list \| grep -i infrahub` |

Only the last blocks stage 4. Stages 1-3 are runnable now.

```bash
ansible-galaxy collection install -r ansible/galaxy-requirements.yml
```

The collection's action plugins also need `infrahub-sdk` importable by the **controller's** Python,
or they raise `infrahub_sdk must be installed to use this plugin`. Note `lab/pyproject.toml` pins
the community `ansible` bundle, which does **not** ship `opsmill.infrahub`.

---

## Stage 1 — Schema and object data

```bash
uv run infrahubctl branch create clab-multi-domain
uv run infrahubctl schema check schemas/ --branch clab-multi-domain
uv run infrahubctl schema load schemas --branch clab-multi-domain
uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py
uv run infrahubctl object load objects/ --branch clab-multi-domain
uv run infrahubctl object load manual_objects/ --branch clab-multi-domain
```

Never load schema onto the default branch: a load runs migrations against live data immediately,
with no preview and no per-step undo.

**Expected**: `schema check` reports zero errors; `protocols.py` shows a diff containing
`containerlab_image` and `containerlab_interface_mapping`.

**Verify the attributes actually carry data** — an unset attribute renders as a missing image and
is the most likely silent failure:

```bash
uv run infrahubctl object get DcimPlatform --branch clab-multi-domain -o csv
```

---

## Stage 2 — Unit tests and lint

```bash
uv run pytest tests/unit/test_containerlab_topology.py -v
uv run pytest tests/unit
uv run invoke lint            # ruff + mypy + yamllint
```

**Expected**: parity assertions from `contracts/parity-matrix.md` pass — 14 nodes, 2 kinds, 24
links, 4 with `dci` role; the determinism test shows byte-identical renders; zero lint findings.

---

## Stage 3 — Live render (required before merging any `.gql` change)

```bash
COLUMNS=500 uv run infrahubctl transform containerlab_topology \
  name=Fabric-L3LS-Multi-Domain --branch clab-multi-domain \
  > /tmp/generated-topology.clab.yml
```

`COLUMNS=500` is needed because `infrahubctl` prints through Rich, which wraps at terminal width
when redirected to a file. This does not affect the server-rendered artifact.

This stage is **mandatory**, not optional. Static checks cannot catch a query/schema mismatch, and
a malformed `.gql` does not fail loudly — `CoreRepository` sync hangs in `error-import`, zero
transform/artifact definitions register, and downstream pipelines time out with no obvious cause.
Run it against **loaded data**: an empty dataset hides union-fragment bugs, because no concrete
instance is ever returned to fail on.

**Verify against the parity matrix:**

```bash
python3 - <<'PY'
import yaml, collections
d = yaml.safe_load(open("/tmp/generated-topology.clab.yml"))
nodes, links = d["topology"]["nodes"], d["topology"]["links"]
kinds = collections.Counter(n["kind"] for n in nodes.values())
print("nodes:", len(nodes), dict(kinds))
print("links:", len(links))
print("mgmt:", d["mgmt"])
print("untranslated:", [e for l in links for e in l["endpoints"] if "Ethernet" in e])
print("no-bind nodes:", [n for n, v in nodes.items() if "binds" not in v])
PY
```

**Expected**: `nodes: 14 {'arista_ceos': 12, 'linux': 2}`, `links: 24`, `ipv4-subnet:
10.0.6.0/24`, `untranslated: []`, and `no-bind nodes: []`.

**Determinism** — run the render twice and diff:

```bash
diff <(COLUMNS=500 uv run infrahubctl transform containerlab_topology name=Fabric-L3LS-Multi-Domain) \
     <(COLUMNS=500 uv run infrahubctl transform containerlab_topology name=Fabric-L3LS-Multi-Domain) \
  && echo "deterministic"
```

**Regression check on the other fabrics** — this transform serves six fabrics, so confirm none
render empty:

```bash
for f in Fabric-L3LS-MultiPod-A Fabric-L3LS Fabric-L2LS Fabric-Campus Fabric-ISIS-LDP; do
  echo "== $f"
  COLUMNS=500 uv run infrahubctl transform containerlab_topology name="$f" 2>&1 | head -5
done
```

`Fabric-ISIS-LDP` is expected to render without its `p`/`pe`/`rr` devices — those roles are
deliberately excluded (R-003), and the exclusion should appear as a logged warning.

---

## Stage 4 — Deploy from Infrahub

Requires the collection from Prerequisites.

> **This stage fetches the artifact stored in Infrahub, not the local working tree.** Infrahub syncs
> its repository from git (`docker-compose.override.yml` mounts `./:/upstream`), so uncommitted
> transform changes are invisible here. Until the change is committed, synced, and the artifact
> regenerated, Ansible will faithfully deploy the *previous* topology. Verified: the stored artifact
> was 12 nodes / 16 links / no binds while the local render was already 14 / 24 / binds present.

The playbook lives in `ansible/` (also the Semaphore playbook repository) and runs as two plays:
Infrahub work on `localhost`, then staging and `containerlab deploy` on the `clab_hosts` group from
`ansible/inventory_clab.yml`. That inventory must be passed explicitly, because `ansible/ansible.cfg`
pins `inventory` to the dynamic Infrahub plugin.

```bash
cd lab
export INFRAHUB_ADDRESS=http://localhost:8000
export INFRAHUB_API_TOKEN=<token>

make deploy-from-infrahub FABRIC=Fabric-L3LS-Multi-Domain
# or directly:
uv run ansible-playbook -i ../ansible/inventory_clab.yml ../ansible/deploy_clab.yml \
  -e fabric=Fabric-L3LS-Multi-Domain
```

Stage and validate without deploying:

```bash
... --skip-tags deploy
```

**Expected**: the topology and all bind sources are staged **on the lab host** before
`containerlab deploy` runs, then 14 containers start.

Note that `--check` alone is a weak test: the "write the topology" task is skipped, so the later bind
assertions read whatever `topology.clab.yml` already exists rather than the fetched artifact. Use
`--skip-tags deploy` for a real staging test.

```bash
containerlab inspect --topo topology.clab.yml
docker ps --format '{{.Names}}' | grep clab- | wc -l    # expect 14
```

**Confirm the interface mapping took effect** — this is what the mapping bind exists for:

```bash
docker exec clab-<topology>-<a-spine> Cli -c "show interfaces status" | head -20
```

Expect `Ethernet1/1`-style names. Seeing `eth1_1` instead means the mapping bind is missing or
pointed at a file absent on disk.

### Known limitation

Server-to-server reachability is **not** expected to work. The shipped netplan encodes VLANs
11/12/19 while this fabric models 21/22/29 (R-007). The `make ping` targets belong to the committed
lab flow, not this generated one.

---

## Cleanup

```bash
cd lab && make destroy
uv run infrahubctl branch delete clab-multi-domain
```

## Troubleshooting

| Symptom | Cause |
|---|---|
| `transform()` receives `data=None` | `query =` on the class doesn't match a `queries:` name in `.infrahub.yml` — `collect_data()` skips silently |
| Artifact missing after repo sync | `infrahubctl object load` does **not** ingest queries, transforms, or artifact definitions; the repository must sync |
| `Cannot query field 'x' on type 'Y'` | A subtype field selected directly on a generic/union field — needs an `... on Concrete` inline fragment |
| `Variable '$name' … never used` | `NoUnusedVariables` is enforced; a declared-but-unreferenced variable is rejected before execution |
| Node boots with no config | `startup-config` directory doesn't match where the playbook wrote configs (R-006) |
| ContainerLab creates a directory at a bind path | The bind source file is absent; it fails confusingly at boot rather than at deploy |
