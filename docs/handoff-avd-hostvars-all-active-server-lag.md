# Handoff: all-active server LAG adapter shaping

Updated: 2026-07-16

## Follow-up: switch-side Port-Channel ID ownership

The current fixture/test branch now models the EVPN all-active knob on the
switch-side LAGs, not on the server bond:

- server side: `server-b2-1-aa-esi-1` has `Bond1` with members `Ethernet1` and
  `Ethernet2`; `Bond1.evpn_ethernet_segment` is explicitly `false`.
- switch side: each leaf has `InterfaceLag` `Port-Channel1117` with
  `evpn_ethernet_segment: true`.
- leaf physical ports `Ethernet1/1/17` are members of their local
  `Port-Channel1117`.

This produces the expected structured config:

```json
"Port-Channel1117": {
  "evpn_ethernet_segment": {
    "identifier": "0000:0000:86a1:bb40:bf02",
    "route_target": "86:a1:bb:40:bf:02"
  },
  "lacp_id": "86a1.bb40.bf02"
}
```

The remaining design issue is **where the switch-side Port-Channel ID comes
from and which system owns it**.

Today the test fixture hard-codes `Port-Channel1117` in Infrahub. pyAVD would
also derive `1117` from the adapter's local `switch_ports` value
`Ethernet1/1/17`, but that value is not currently backfilled from structured
config into Infrahub. This means the data is correct for the fixture, but the
workflow still needs a general rule for production/server-cabling generated
data.

Two implementation paths are reasonable:

1. **Infrahub-owned LAG ID, propagated to pyAVD**
   - Add or use an explicit switch-side LAG identifier in Infrahub, probably by
     modeling the switch `InterfaceLag` during server cabling.
   - The server cabling generator should create/update one switch-side
     `InterfaceLag` per leaf for the chosen port-channel and attach the
     physical switchport as `lag_members`.
   - Hostvar generation should pass the chosen ID/name to pyAVD instead of
     relying on pyAVD's default derivation from `switch_ports`.
   - This is more deterministic and makes Infrahub the source of truth, but it
     requires clear allocation rules for the port-channel ID.

2. **pyAVD-owned LAG ID, backfilled into Infrahub**
   - Continue allowing pyAVD to derive the ID from `switch_ports`.
   - Extend structured-config backfill to read `port_channel_interfaces` and the
     related `ethernet_interfaces[].channel_group.id`.
   - Backfill/create the matching switch-side `InterfaceLag` in Infrahub and
     relate the member physical interfaces to it.
   - This avoids duplicating pyAVD's ID derivation logic in Infrahub, but it
     makes Infrahub learn the switch LAG only after structured config
     generation.

Recommendation: prefer **Infrahub-owned LAG ID** if operators are expected to
reason about or edit port-channel objects before config generation. Prefer
**pyAVD-owned/backfilled ID** only if the project wants pyAVD to stay the
canonical allocator for generated switch Port-Channels.

Concrete follow-up tasks:

- Decide whether `InterfaceLag.name` alone is enough, or whether the schema
  needs an explicit numeric `lag_id`/`channel_group_id` for switch-side LAGs.
- Update `ServerCablingGenerator` so dual-attached server cabling creates the
  switch-side `InterfaceLag` objects, not only server-side `Bond1`, if choosing
  the Infrahub-owned path.
- Alternatively, extend `BackfillStructuredConfigGenerator` to process
  `port_channel_interfaces` and `ethernet_interfaces[].channel_group.id`, if
  choosing the backfill path.
- Add integration coverage that starts with a cabled dual-attached server and
  verifies the final Infrahub graph has switch-side `InterfaceLag` objects with
  stable IDs and `evpn_ethernet_segment: true`.
- Keep the EVPN all-active boolean on the switch-side LAG; the server-side bond
  is only a grouping signal for endpoint ports.

## Goal

Split the server LAG / all-active multihoming behavior out of the lab parity
bridge into a focused PR. The PR should make topology-derived AVD hostvars emit
the full `servers[].adapters[]` shape for dual-homed/all-active server bonds
without relying on the fabric-level `avd_custom_hostvars.servers` override.

## Current model and code path

The current schemas already contain the minimum model needed for the first
implementation:

- `ComputePhysicalServer` inherits `DcimGenericDevice`, so servers have
  component `interfaces`.
- Server NICs are `InterfacePhysical`.
- `InterfaceLag` exists in `schemas/lag/lag.yml`, with `lacp_mode`,
  `lacp_rate`, `lag_members`, and the reverse `InterfacePhysical.lag`
  relationship.
- Leaf server-facing ports are not created dynamically per server. They are
  pre-created by the leaf object template:
  - `objects/06_device_template.yml`
  - `arista-7050sx3-48yc8c-leaf-switch`
  - `Ethernet[1-48]`
  - profile `profile-interface-server`
- `objects/05_profiles.yml` marks `profile-interface-server` with
  `role: server` and `mtu: 1500`.

The server cabling flow is:

1. `RackGenerator.create_leaf_switches()` creates each leaf from the leaf object
   template.
2. Template expansion pre-creates the `role=server` leaf interfaces.
3. `ServerCablingGenerator.generate()` finds:
   - server interfaces on the `ComputePhysicalServer`;
   - leaf devices in the same rack;
   - existing leaf `InterfacePhysical` objects with `role__value="server"`.
4. `build_server_cabling_plan()` maps server NICs round-robin across leaves at
   the first free common interface index.
5. `connect_interface_maps()` creates a `NetworkLink` and sets it as the
   `connector` on both physical interfaces.
6. `_assign_vlans()` copies the server interface/profile VLAN relationships onto
   the paired leaf interface.
7. `_create_server_port_channel()` creates one server-side `InterfaceLag`
   named `Bond1` for dual-homed servers and assigns the cabled server physical
   interfaces to that LAG.

The leaf-side Port-Channel is not modeled as an Infrahub `InterfaceLag` today.
AVD is expected to generate the switch-side Port-Channel and EVPN Ethernet
Segment from the `servers[].adapters[]` hostvars.

## Lab bridge behavior to review

Lab commit:

```text
cf0d9ce Bridge AVD hostvars to lab pyAVD parity
```

Current hostvar code in `generators/generate_avd_device_hostvar.py` detects a
remote server interface with `endpoint.lag.node` and adds:

```yaml
ethernet_segment:
  short_esi: auto
port_channel:
  mode: active
  description: <server-name>
```

However, that implementation is only a partial bridge if it sees only the
current leaf's local server-facing interface. True all-active output needs the
single adapter to include all bond members across all leaves, for example:

```yaml
servers:
  - name: dc1-server1
    adapters:
      - switches: [leaf-infrahub-dc1-2-1, leaf-infrahub-dc1-2-2]
        switch_ports: [Ethernet1, Ethernet1]
        endpoint_ports: [eth1, eth2]
        mode: trunk
        vlans: "11,19"
        native_vlan: 4092
        spanning_tree_portfast: edge
        ethernet_segment:
          short_esi: auto
        port_channel:
          mode: active
          description: dc1-server1
```

The lab data currently also has a full `servers:` payload under
`NetworkFabric.avd_custom_hostvars`, so parity may be coming from the custom
hostvars override instead of topology-derived server LAG shaping.

## Recommended implementation

Keep this PR generator-only if possible. Do not add new schema unless the
current `InterfaceLag` model proves insufficient.

In `extract_connected_endpoints()` or a helper below it:

1. For every leaf interface with `role == "server"`, resolve the remote server
   interface through `connector.connected_endpoints`.
2. If the remote server interface has `lag.node`, use the server-side
   `InterfaceLag` as the adapter grouping key.
3. Fetch/resolve all members of that LAG through `InterfaceLag.lag_members` or
   reverse `InterfacePhysical.lag`.
4. For every member:
   - follow its `connector`;
   - find the opposite leaf-side `InterfacePhysical`;
   - collect server port name, leaf hostname, and leaf port name.
5. Sort the collected triples deterministically and keep
   `switches`, `switch_ports`, and `endpoint_ports` in lockstep.
6. Emit one adapter per server-side LAG.
7. Emit `ethernet_segment: {short_esi: auto}` only when the adapter spans two or
   more leaf switches.
8. Map `InterfaceLag.lacp_mode` to pyAVD values:

   ```python
   {"active": "active", "passive": "passive", "disabled": "on"}
   ```

   pyAVD validates `active`, `passive`, and `on`; it rejects `disabled`.
9. Preserve the existing VLAN logic, but make sure all members of a LAG produce
   consistent VLAN mode and VLAN lists. Fail clearly if members disagree.

## Files likely touched

- `generators/avd_device_hostvar.gql`
  - Add enough LAG member data to build the full adapter.
- `generators/generate_avd_device_inputs_query.py`
  - Regenerate/update generated models for any query additions.
- `generators/generate_avd_device_hostvar.py`
  - Add LAG member resolution and adapter shaping.
- `tests/unit/test_hostvar_ordering.py`
  - Add deterministic multi-leaf LAG adapter tests.
- `tests/unit/test_generate_avd_device_hostvar.py`
  - Add pyAVD validation tests for `servers[].adapters[]`.

## Tests to add

- Single-homed server remains a single adapter with no `ethernet_segment`.
- Dual-homed server with two NICs in the same server `InterfaceLag` emits one
  adapter with two switches, two switch ports, and two endpoint ports.
- LACP `disabled` maps to pyAVD `on`.
- Adapter output is identical across different GraphQL/interface ordering.
- VLAN mismatch across LAG members fails with a clear error.
- pyAVD `validate_inputs()` accepts the generated hostvars.

## Validation

Minimum local validation:

```bash
uv run pytest tests/unit/test_hostvar_ordering.py tests/unit/test_generate_avd_device_hostvar.py
uv run ruff check generators/generate_avd_device_hostvar.py tests/unit/test_hostvar_ordering.py tests/unit/test_generate_avd_device_hostvar.py
```

Before PR:

```bash
uv run invoke lint
uv run pytest tests/unit
```

Live validation should cable a dual-homed server, trigger AVD hostvar generation
twice, and confirm the second run is a no-op.
