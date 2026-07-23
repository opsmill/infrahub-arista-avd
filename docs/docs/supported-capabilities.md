---
title: Supported Capabilities
description: What this Arista AVD reference design supports today, what is partial, and what is not yet covered.
---

# Supported Capabilities

This is a **reference design** that covers a defined set of AVD capabilities on Infrahub — it is not a full replacement for every AVD feature. Uncommon or highly customized AVD options may not be modeled. Use the matrix below to check the status of a capability before planning a deployment.

**Status key:** ✅ Supported today · 🟡 Partial / confirm scope · ⬜ Not yet

:::note
Some boundaries below are marked *confirm scope* and are being finalized with the maintainers. Where a row says "confirm", treat the exact edge as undecided rather than guaranteed.
:::

## Fabric generation

| Capability | Status | Notes |
|------------|:------:|-------|
| Generate a full fabric (Fabric → Pod → Rack → Device) from a design | ✅ | Super-spines, spines, and leaves are created from device templates — no per-device host_vars authored manually. |
| Cable devices together automatically | ✅ | Uplinks and device-to-device links created by the generators. |
| Regenerate idempotently | ✅ | Checksum-based change detection skips work when nothing changed; re-running is safe. |

## Addressing & numbering

| Capability | Status | Notes |
|------------|:------:|-------|
| Allocate loopback, interconnect, and management prefixes/IPs from pools | ✅ | Drawn from branch-aware pools so parallel work does not collide. |
| Allocate DCI point-to-point /31 prefixes from a fabric DCI pool | ✅ | `NetworkFabric.dci_pool` is the authoritative source for generated DCI `l3_edge` addressing. |
| Allocate BGP ASNs and node IDs from pools | ✅ | Assigned automatically during generation. |

## Services (VLAN / EVPN / VRF / MLAG / LAG / routing)

| Capability | Status | Notes |
|------------|:------:|-------|
| Model VLANs and L2 domains | ✅ | Defined in the source of truth and rendered into config. |
| Fabric-level EVPN settings | ✅ | Fabric EVPN overlay configuration. Exact EVPN depth is being confirmed. |
| EVPN Multi-Domain Gateway on Border Leafs | 🟡 | Models Fabric-owned `EvpnDomain` objects with domain-owned local `EvpnGatewayGroup` children for `border_leaf` devices, then emits pyAVD EVPN Gateway hostvars for All-Active Multihoming only. Pods remain selected context and must point at the group's local domain. MLAG, Anycast IP, route-server, and route-reflector gateway models are not included. |
| EVPN L3 VRFs | 🟡 | Wired into the PyAVD hostvar generator and produce config. The maintainers flagged "we don't do VRF and route targets" — **confirm** whether the exclusion is VRF-lite, route-leaking, or explicit route targets. |
| MLAG (domain + peer) | 🟡 | Modeled and wired into hostvars; **confirm** supported scope. |
| Server LAG | 🟡 | Modeled and wired into hostvars; **confirm** supported scope. |
| BGP peer groups | 🟡 | Wired into hostvars and produce config; **confirm** supported scope. |
| DCI links between Border Leafs | ✅ | `NetworkLink` objects with `role=dci` reuse shared physical endpoints and generate PyAVD `l3_edge.p2p_links`; external networks and EVPN Gateway are out of scope for this phase. |
| Route targets | 🟡 | Modeled but AVD-derived (not fed as input). |
| Prefix lists, route maps, static routes | 🟡 | Reconciled *from* AVD output via the backfill generator, not authored as inputs. |

## Rendering & artifacts

| Capability | Status | Notes |
|------------|:------:|-------|
| Render Arista EOS device configurations (PyAVD) | ✅ | Deploy-ready per-device EOS CLI, as downloadable artifacts. |
| Fabric and per-device documentation (Markdown) | ✅ | Generated from the same source of truth as the config. |
| Cabling plan (CSV) | ✅ | One row per connection for the field/cabling team. |
| Computed interface descriptions | ✅ | Consistent, auto-maintained interface descriptions. |
| ANTA test catalog (per device, YAML) | ✅ | Catalog **generation** is included (gated by the fabric `anta_enabled` flag). Execution is not yet included — see below. |

## Validation (ANTA)

| Capability | Status | Notes |
|------------|:------:|-------|
| ANTA test-catalog generation | ✅ | The `avd_anta_catalog` transform, gated by `anta_enabled`. |
| ANTA execution / block-merge-on-failure | ⬜ | Running the tests and blocking merges on failure is on the roadmap. |

## Deployment

| Capability | Status | Notes |
|------------|:------:|-------|
| Deploy configurations to devices | ✅ | Through the bundled Ansible runner or CloudVision (CVP/CVaaS). |

## Interfaces & change management

| Capability | Status | Notes |
|------------|:------:|-------|
| Self-service portal (Streamlit) for guided provisioning | ✅ | Alongside the Infrahub Web UI, GraphQL API, and MCP. |
| Branches, proposed changes, approvals, full lineage | ✅ | Standard Infrahub platform change management. |
| Approval rules that vary by service type | ⬜ | You can require approvals, but per-service approval rules are on the roadmap. |

## Brownfield & coverage

| Capability | Status | Notes |
|------------|:------:|-------|
| Self-serve brownfield import | 🟡 | Modeling an existing fabric and importing configs via Infrahub Sync is done today in a **guided engagement**, not as a download-and-try path. |
| Every AVD feature | ⬜ | This reference design covers a defined set of AVD inputs and scenarios, implemented per customer; uncommon or highly custom options may not be modeled. |
