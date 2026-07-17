# Plan: Enable EVPN A/A ESI on Server LAG Hostvars

## Summary
- Add a boolean knob on `InterfaceLag` to mark a server LAG as EVPN all-active ESI.
- Keep existing connected-endpoint adapter generation unchanged.
- When the knob is enabled, emit `ethernet_segment: { short_esi: auto }` only if the adapter spans 2+ unique switches and the leaf is not using MLAG.
- Support only `short_esi: auto` for now.

## Key Changes
- In `schemas/lag/lag.yml`, add `evpn_ethernet_segment` as a default-false Boolean attribute on `InterfaceLag`.
- In `generators/avd_device_hostvar.gql`, fetch `InterfaceLag.evpn_ethernet_segment { value }` next to `lacp_mode`.
- Regenerate `generators/generate_avd_device_inputs_query.py`.
- In `generate_avd_device_hostvar.py`, update the existing `endpoint.lag.node` handling:
  - Preserve current `port_channel` generation.
  - Map LACP modes as `active→active`, `passive→passive`, `disabled→on`.
  - If `lag.evpn_ethernet_segment.value is True`, MLAG is not active, and `len(set(adapter["switches"])) >= 2`, add:
    ```yaml
    ethernet_segment:
      short_esi: auto
    ```
  - Do not add ESI for MLAG-backed adapters or single-switch adapters.

## Tests
- Add unit coverage for:
  - LAG without the knob: existing Port-Channel output unchanged.
  - LAG with knob enabled, no MLAG, multi-switch adapter: emits `ethernet_segment.short_esi: auto`.
  - LAG with knob enabled but MLAG active: does not emit ESI.
  - LAG with knob enabled but single-switch adapter: does not emit ESI.
  - `lacp_mode: disabled` maps to pyAVD `port_channel.mode: on`.
  - Generated hostvars with ESI validate with pyAVD input validation.
- Validate with:
  - `uv run infrahubctl schema check schemas/lag/lag.yml`
  - `uv run infrahubctl graphql generate-return-types generators/avd_device_hostvar.gql --schema schema.graphql`
  - `uv run pytest tests/unit/test_hostvar_ordering.py tests/unit/test_generate_avd_device_hostvar.py`
  - `uv run ruff check generators/generate_avd_device_hostvar.py tests/unit/test_hostvar_ordering.py tests/unit/test_generate_avd_device_hostvar.py`

## Assumptions
- Attribute name: `evpn_ethernet_segment`.
- The PR does not change how connected-endpoint adapters are grouped.
- The target branch’s existing adapter generation is responsible for producing multi-switch adapters when applicable.
- Manual short ESI values are out of scope; only `auto` is supported.

## Worktree note
- This repository has a Git worktree caveat documented in `CLAUDE.md`: if this worktree is used with the task-worker container, bind-mount the parent `.git` directory into the worker because the worktree `.git` file points outside the container mount.
