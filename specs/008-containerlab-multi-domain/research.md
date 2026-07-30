# Phase 0 Research: ContainerLab Topology for the Multi-Domain Fabric

All Technical Context unknowns are resolved. Nothing remains marked NEEDS CLARIFICATION.

---

## R-001 — `opsmill.infrahub` module contract

**Decision**: Use `opsmill.infrahub.artifact_fetch` and `opsmill.infrahub.query_graphql` with the
argument spec and return keys verified against collection **1.8.3**, and pass node **UUIDs** as
`target_id`.

**Rationale**: The existing draft playbook carried a comment admitting its module names were
unverified. They were checked by installing 1.8.3 (latest on Galaxy and GitHub) and exercising it
against the live local Infrahub. The FQCNs are correct; four details are wrong:

| Detail | Draft | Verified |
|---|---|---|
| `artifact_fetch.target_id` | node name | must be a UUID — a name fails with `Unable to find '<artifact>' for '<name>'` |
| artifact body | `.text \| default(.content)` | `.text` only; `.content` does not exist, and the `default()` never fires because `text` is always a present key (`None` for JSON artifacts) |
| graphql variables | `variables:` | `graph_variables:` — a `variables` key is silently ignored, because action plugins do not validate against the module argument spec, then fails at runtime with `Variable '$name' of required type 'String!' was not provided` |
| graphql result | `.results` | `.response` — despite the module's own `RETURN` docstring saying `data` |

Both artifacts consumed here (`application/yaml` topology, `text/plain` EOS config) land in
`.text`, so no `.json` branch is needed.

**Alternatives considered**: Trusting the docstrings — rejected, the `RETURN` docstring for
`query_graphql` is demonstrably wrong about its own top-level key. Using the
`opsmill.infrahub.lookup` lookup plugin instead of `query_graphql` — rejected, a lookup cannot
register results across tasks as cleanly and offers no advantage here.

**Consequence for tasks**: the device-discovery query must select `id`, not just `name`, and the
config-fetch loop must iterate over IDs while still labelling output by name.

---

## R-002 — Where the Linux kind and image come from

**Decision**: Add a `DcimPlatform` named `Linux` with `containerlab_os: linux` and
`containerlab_image: lab-server`, and assign it to the server objects via the `platform`
relationship. No new schema node, no new relationship.

**Rationale**: `ComputePhysicalServer` inherits `DcimGenericDevice`
(`schemas/compute/compute.yml:28-35`), which declares `platform` → `DcimPlatform`
(`schemas/base/dcim.yml:50-55`, cardinality one, optional). So the identical code path that
resolves kind and image for switches resolves them for servers, and FR-017's "no hardcoded kind or
image" holds uniformly.

**Alternatives considered**: A dedicated `ComputeContainerlabSettings` node — rejected as
disproportionate for two scalar values already expressible on an existing relationship. Hardcoding
`linux`/`lab-server` for anything that is not a `DcimDevice` — rejected, it reintroduces exactly
the hardcoding FR-017 removes.

**Discovered constraint**: `device_type` is declared on `DcimPhysicalDevice`/`DcimDevice`, **not**
on `DcimGenericDevice`. Servers therefore cannot carry `containerlab_interface_mapping`. This is
correct rather than a limitation — only cEOS nodes need an `EosIntfMapping.json`. The transform
must not assume every node has a `device_type`.

---

## R-003 — Role coverage

**Decision**: Extend the accepted-role set to `super_spine`, `spine`, `leaf`, `l2leaf`,
`border_leaf`, `l2spine`, `l3spine`. Log a warning for any device whose role is outside the set.

**Rationale**: `schemas/dcim_extensions.yml:38-71` defines 11 role choices; the transform accepts
4. `border_leaf` is the load-bearing omission: `manual_objects/00_lab_l3ls_multi_domain.yml`
assigns it to all four DC1/DC2 border leaves, so today the multi-domain artifact loses those
devices plus every link touching them — the 4 DCI links and 8 spine↔leaf uplinks. `l2spine` and
`l3spine` are added because the Campus and L2LS fabrics use them and currently render partially.

`p`, `pe`, and `rr` are deliberately **excluded**: they belong to the ISIS-LDP fabric, which is
outside this feature's parity target, and admitting them without validating that fabric's
interface naming would be speculative. The warning from FR-023 makes their exclusion visible
rather than silent, which is the actual defect being fixed.

**Alternatives considered**: Accepting every role — rejected, it would emit nodes for roles with
no validated ContainerLab representation and mask genuine modelling errors. Inferring from
`platform.containerlab_os` presence instead of role — attractive, and a plausible future
direction, but it changes the semantics for all six fabrics at once; deferred.

---

## R-004 — Typed models for the second query

**Decision**: Create `transforms/containerlab_link_endpoints.gql`, register it in `.infrahub.yml`,
and generate `transforms/containerlab_link_endpoints_query.py` with
`uv run infrahubctl graphql generate-return-types`. Leave `containerlab_topology_query.py`
hand-written for now, and narrow the `pyproject.toml` lint exclusion so it is actually linted.

**Rationale**: The inline `_LINK_ENDPOINTS_QUERY` string literal violates the project rule to keep
GraphQL in `.gql` files with generated return types. Fixing it for the new query is cheap and
self-contained. Regenerating the *existing* module is the correct end state but not safe to bundle
here: the generated models discriminate unions the hand-written models flatten
(`NetworkBuildingBlock | NetworkPod` for fabric children, `DcimPhysicalDevice | DcimDevice` for
rack devices), so every traversal in the transform would change shape in the same commit that
fixes the border-leaf bug. Separating them keeps the behavioural fix reviewable.

A related wart is fixed now at no risk: `pyproject.toml:66` excludes `**/*_query.py` from linting
on the assumption that all such files are generated, which silently exempts the hand-written
module. Narrowing that exclusion to the genuinely generated files brings it under ruff and mypy.

**Alternatives considered**: Regenerating both now — rejected per above. Leaving the inline string
— rejected, it is a stated FR and a constitution principle. Deleting
`transforms/container_lab_topology.py` (the dead orphan) — accepted and folded in; nothing imports
it and `pyproject.toml:67` already documents it as a historical misnaming.

---

## R-005 — Deterministic management subnet

**Decision**: Choose the subnet shared by the most devices; break ties by lowest network address.

**Rationale**: The current implementation returns the first masked address found while iterating a
dict, so insertion order decides — a mixed-subnet fabric can render differently between runs,
breaking SC-006. Most-common-wins is robust to a single mis-addressed device, which lowest-address
ordering is not: one device on `10.0.1.0/24` would displace a 12-device `10.0.6.0/24` management
range.

**Alternatives considered**: Lowest network address alone — simpler but silently wrong in the
stray-device case. Reading a management prefix from the fabric — conceptually the cleanest, since
`10.0.6.0/24` is already modelled as a management prefix and the fabric carries `mgmt_gateway`,
but there is no relationship from `NetworkFabric` to that prefix today, so it would require a
third schema change for no parity benefit. Recorded as a future improvement.

---

## R-006 — Startup-config path alignment

**Decision**: The kind-level `startup-config` must point at the directory the playbook writes into
(`configs/<node-name>.cfg`), not `avd/intended/configs/__clabNodeName__.cfg`.

**Rationale**: This is a live inconsistency between two files that are supposed to cooperate. The
committed `lab/topology.clab.yml` boots from `avd/intended/configs/`, which is correct **for the
committed lab** because those renders are checked in. But `deploy_clab.yml` writes fetched configs
to `lab/configs/<device>.cfg`, and `lab/.gitignore` ignores `/configs/*.cfg` precisely because they
are runtime artifacts. So a generated topology that kept the committed path would boot from files
the playbook never populates — and, worse, from configs belonging to differently-named devices.

Since node names are Infrahub-generated (`spine-infrahub-dc1-1`, not `ih-dc1-spine1`), the
committed renders are not reusable anyway. `__clabNodeName__` still works as the substitution
token; only the directory changes.

**Alternatives considered**: Having the playbook write into `avd/intended/configs/` — rejected, it
would overwrite committed, reviewable renders with fetched ones and conflate the two flows the
`lab/README.md` deliberately separates.

---

## R-007 — Netplan filename convention and file rename

**Decision**: Bind `configs/servers/<device-name>-netplan.yaml`, and rename the two committed
files to `dc1-server-netplan.yaml` / `dc2-server-netplan.yaml`.

**Rationale**: Infrahub's server objects are `dc1-server` / `dc2-server`
(`manual_objects/15a_servers_l3ls_multi_domain.yml`), while the committed files are named for the
lab's `dc1-server1` / `dc2-server1`. Deriving the filename from the node name keeps the transform
free of a third schema attribute and mirrors how `startup-config` already uses the node name. The
rename is a two-file `git mv` with one referencing line each.

**Alternatives considered**: A `containerlab_netplan_file` Text attribute — explicit, but adds a
schema attribute serving exactly two objects. A kind-level templated bind using
`__clabNodeName__` — appealing, but ContainerLab applies kind-level binds to every node of that
kind, which is fine here yet still requires the same rename, so it buys nothing while being less
explicit per node.

**Risk noted**: the netplan contents encode VLANs 11/12/19 and addresses matching the committed
lab, whereas this fabric models VLANs 21/22/29. The files are shipped as-is per the confirmed
decision not to generate netplan, so server-to-server reachability inside the generated lab is
**not** expected to work end-to-end without further data alignment. This is a bounded, documented
divergence, not a regression — servers do not reach each other in the generated lab today either,
because they are absent entirely.

---

## R-009 — Query shape, template division of labour, and test tiering

**Decision**: Select `ComputePhysicalServer` as a **separate top-level query field** rather than an
inline fragment; pre-shape kind grouping and bind lists in **Python**, not Jinja2; keep parity tests
in the existing pytest file and add a `graphql-query-smoke` entry for the new `.gql`.

**Rationale** — four findings from the transform reference material, each changing the approach:

1. **Two root kinds, not a union.** Inline fragments apply to a *single* field whose `peer:` is a
   generic with divergent inheritors. `DcimDevice` and `ComputePhysicalServer` are distinct root
   kinds, so they are selected as sibling top-level fields in one operation. Fragments are still
   required where a relationship's peer *is* generic — including the existing
   `... on DcimInterface` / `... on InterfacePhysical` endpoint selection. Getting this wrong is
   not a soft failure: selecting a subtype field directly on a generic field rejects the **entire
   query**, and during repository import it stops schema sync outright.

2. **Never discriminate on `__typename` against a generic name.** `__typename` resolves to the
   concrete kind, so a branch comparing it to the generic never fires. Discriminate on field
   presence instead. The existing `node.typename != "DcimDevice"` check compares against a
   concrete kind and is therefore fine, but the new server traversal must not repeat the pattern
   against a generic.

3. **Pre-shape in Python.** Grouping devices into one `kinds:` entry per distinct kind is
   aggregation, which belongs in Python — the transform should hand the template a ready list of
   kinds and per-node bind lists. Beyond being clearer, it keeps the template portable: a pure
   Jinja2 transform runs under the SDK's filter allowlist where `groupby`, `map`, `select` and
   `to_nice_yaml` all fail at render time with `No filter named 'X'`.

4. **A malformed `.gql` fails silently.** Bad queries under a synced repository leave
   `CoreRepository` in `error-import`, register zero transform/artifact definitions, and time out
   downstream pipelines with no obvious root cause. This upgrades two things from nice-to-have to
   required: registering the new query under `queries:` (R-004), and running the live dry-run in
   quickstart Stage 3 before merging any `.gql` change. Static checks cannot catch a query/schema
   mismatch, and an empty dataset masks fragment bugs because no concrete instance is returned to
   fail on.

**Test tiering**: the SDK's YAML Resources Testing Framework offers
`python-transform-unit-process`, which feeds a fixture as the registered query's response. It
cannot cover this transform end-to-end, because `transform()` also calls `self.client` for link
endpoints and that second fetch has no fixture slot. The pure helpers are already module-level
functions, so parity and determinism assertions stay in `tests/unit/test_containerlab_topology.py`
— which also matches repo convention, as the repo currently has no `test_*.yml` files. A
`graphql-query-smoke` entry for the new query is worth adding specifically to guard failure mode 4.

**Alternatives considered**: A single query with fragments over a common device generic — rejected,
the two kinds do not share a generic that carries the needed attributes. Registering a second query
on the transform class — impossible: `query` is a single string and `python_transforms` accepts no
`query:` key, so `self.client.execute_graphql` is the sanctioned mechanism for extra reads.

**Minor**: `self.root_directory` is the prescribed idiom for locating templates; the current
`Path(__file__).parent / "templates"` works and is not worth churning. Current
`autoescape=jinja2.select_autoescape()` is equivalent to the documented `autoescape=False` for
`.j2` files — it must **not** be changed to unconditional `True`, which would corrupt YAML output.

---

## R-010 — Endpoint device names must be selected on the generic (found during implementation)

**Decision**: In `containerlab_link_endpoints.gql`, select the endpoint's owning device name on the
`DcimGenericDevice` generic — `device { node { name { value } } }` — not through an
`... on DcimDevice` fragment.

**Rationale**: This was a live defect, not a design question. `DcimInterface.device` peers
`DcimGenericDevice` (`schemas/base/dcim.yml:226-232`), and `ComputePhysicalServer` inherits
`DcimGenericDevice` but **not** `DcimDevice`. Narrowing the selection to `DcimDevice` therefore
returned no name for server endpoints, `_parse_endpoint` returned `None`, and every server-facing
link was discarded. Observed directly: with all 24 `NetworkLink` objects present in the graph and
server interfaces correctly connected, the render produced only 20 links until the fragment was
removed. `name` is declared on the generic, so selecting it there covers every inheritor.

**Why the unit tests could not catch it**: the defect lived entirely in the `.gql` selection. The
Python helpers were correct and their fixtures already used the post-fix response shape, so the
suite stayed green throughout. This is the concrete case R-009's mandatory live dry-run exists to
catch. A regression guard now asserts on the query *text* — that no `device` selection narrows to
`DcimDevice` — since that is the only tier able to see the bug.

**Alternatives considered**: Adding a third `... on ComputePhysicalServer` fragment — rejected, it
enumerates inheritors and would silently miss the next one. Resolving server links from the primary
query instead of the endpoint query — rejected, the endpoint query is what establishes both ends of
a link.

---

## R-011 — Generated endpoint types are committed but not yet on the extraction path

**Decision**: Generate and commit `transforms/containerlab_link_endpoints_query.py`, but keep
`fetch_link_endpoints` on its tolerant dict traversal for now.

**Rationale**: The generated model discriminates the endpoint union on `__typename` with exactly
three members — `DcimEndpoint`, `DcimInterface`, `InterfacePhysical`. Because `__typename` resolves
to the **concrete** kind, an endpoint of any other kind (an `InterfaceLag`, for instance — servers
carry `Bond1` and leaves carry `Port-Channel<N>`) has no matching union member and raises a
`ValidationError`. That converts today's behaviour, where a single unparseable endpoint is skipped
and the rest of the topology still renders, into a whole-artifact failure. For a lab topology that
trade is the wrong way round.

Committing the generated file still delivers most of the value: the query is registered, its types
are generated rather than hand-written, and a malformed `.gql` is caught at repo sync instead of
silently at render time.

**Follow-up**: adopt the generated model once the union covers every kind reachable through
`connected_endpoints`, or once the codegen emits a permissive fallback member. Tracked alongside the
`containerlab_topology_query.py` conversion in the plan's Complexity Tracking.

**Naming note**: `generate-return-types` derives the output filename from the GraphQL *operation*
name, and snake-cases `ContainerLab` to `container_lab`. The operation is therefore named
`ContainerlabLinkEndpointsQuery`, which yields `containerlab_link_endpoints_query.py` — matching the
repo's `<name>_query.py` convention and keeping regeneration stable. The original
`ContainerLabLinkEndpoints` produced `container_lab_link_endpoints.py`, the same misnaming that
created the dead `container_lab_topology.py` orphan this change deletes.

---

## R-008 — Post-design Constitution re-evaluation

**Outcome**: No new violations introduced by the Phase 1 design.

- Principle I holds: `data-model.md` adds only two optional attributes and one platform object.
- Principle III improves: one inline query is eliminated and one file moves from unlinted to
  linted; the remaining debt is scoped and recorded.
- Principle IV is unchanged from the pre-research gate — still PARTIAL, still dependent on a
  maintainer-approved exception for the unavailable integration-test skill.
- Principles II and V hold unchanged.

Both Complexity Tracking entries remain accurate after design. No entries were added or removed.
