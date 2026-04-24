---
title: Add a Server
description: Provision a physical server into a compute rack and trigger the AVD cascade.
audience: user
sidebar_position: 2
---

# Add a Server

Provisions a new physical server into a compute rack. The workflow runs on a branch, cables the server to the adjacent leaf switches, cascades through the AVD pipeline to update affected device configs, and opens a proposed change.

Prerequisites:
- A running stack with seed data loaded ([Quick Start](../quick-start.md)).
- A provisioned fabric with at least one **compute** rack ([Provision Your First Fabric](../provision-first-fabric.md)).
- At least one `TemplateComputePhysicalServer` template defined (seeded with the project).

## Open the service portal

Navigate to **`http://localhost:8501`**. From the sidebar, open **Add Server**.

## Fill the form

| Field | Description |
|-------|-------------|
| **Server Name** | Hostname for the new server, e.g. `compute-pod-a2-3-1`. |
| **Rack** | Dropdown of compute racks only (racks with `rack_type = "compute"`). Shown as `<rack-name> (<pod-name>)`. |
| **Server Template** | Dropdown of available `TemplateComputePhysicalServer` templates. Determines the server's interface count, role, and other defaults. |

The branch used for the change is shown in the sidebar under **Select Branch**. By default it's `main`; use the **Create branch** link in the sidebar to create and select a new branch first if you want the change isolated.

## Submit

Click **Add Server**. The portal performs:

1. **Create branch** named `add-server-<server-name>` (if you weren't already on a non-default branch).
2. **Create the server** (`ComputePhysicalServer`) in the chosen rack, using the template's interface layout and marking status `provisioning`.
3. **Add the server to the `servers` group** — this triggers the server-cabling generator and the AVD cascade.
4. **Wait ~60 seconds** for the generator chain to run: server cabling, hostvar regeneration, and structured config updates for the affected leaf switches.
5. **Create a proposed change** summarising the new server.

You'll see two buttons:
- **View Server** — opens the new `ComputePhysicalServer` object in Infrahub.
- **View Proposed Change** — opens the proposed change.

## Review and merge

In the proposed change:

1. **Data tab** — confirm the new server exists with its interfaces and cabling.
2. **Artifacts tab** — the leaves this server cables into should have updated EOS configurations reflecting the new access/trunk ports.
3. Approve and **Merge**.

## If the wait times out

The portal waits a fixed 60 seconds for the generator chain to finish. On a busy machine the chain can take longer. If the proposed change shows no updated device configs:

1. Open the proposed change's branch in the Infrahub UI.
2. Navigate to **Actions → Tasks** and check the status of the hostvar and structured-config generator runs.
3. If they haven't started, trigger **`generate-avd-device-hostvar`** on the affected leaves manually, then **`generate-avd-device-structured-config`** on the fabric.

See [Common Issues](../troubleshooting.md) for more.

## Source

Service-portal implementation: [`service_catalog/pages/2_Add_Server.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/service_catalog/pages/2_Add_Server.py).
