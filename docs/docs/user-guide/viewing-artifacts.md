---
title: Viewing Artifacts
description: Find, preview, and download the AVD EOS configs and fabric/device documentation.
audience: user
sidebar_position: 5
---

# Viewing Artifacts

Once generators have run on a branch and you've opened a proposed change (see [Provision Your First Fabric](./provision-first-fabric.md) or any of the day-2 how-to pages), the proposed-change CI pipeline renders three artifact types:

| Artifact | Attached to | Content type | Purpose |
|----------|-------------|--------------|---------|
| **AVD EOS Configuration** | Each `DcimDevice` | `text/plain` | The Arista EOS CLI configuration for that device. |
| **AVD Device Documentation** | Each `DcimDevice` | `text/markdown` | Human-readable documentation describing the device. |
| **AVD Fabric Documentation** | Each `NetworkFabric` | `text/markdown` | Fabric-wide topology and design documentation. |

Per-device artifacts (`AVD EOS Configuration`, `AVD Device Documentation`) are rendered as part of the proposed-change CI. If you want to view them outside a proposed change, open them on a device's **Artifacts** tab and click **Regenerate**.

## Finding a device artifact

1. In the Infrahub UI, open **Network → NetworkDevice**.
2. Click a device (for example `leaf-pod-A1-1`).
3. Click the **Artifacts** tab on the device's detail page.
4. You'll see rows for **AVD EOS Configuration** and **AVD Device Documentation**.

## Previewing an artifact

Click the artifact row to open a preview panel. The preview shows:

- The rendered content inline.
- Metadata: content type, last rendered timestamp, size.
- A **Download** button.
- A **Regenerate** button (forces a fresh render even if nothing has changed).

### EOS configuration preview

The EOS config is plain text — paste-ready for a lab switch or a virtual Arista instance. Example excerpt:

```text
!
hostname leaf-pod-A1-1
!
router bgp 65101
   router-id 10.255.1.1
   …
```

### Markdown documentation preview

The fabric and device markdown documents include tables, topology descriptions, and interface lists. They render directly in the Infrahub preview.

## Finding the fabric documentation

1. Open **Network → NetworkFabric**.
2. Click the fabric (`Fabric-A`).
3. Click the **Artifacts** tab.
4. Open **AVD Fabric Documentation**.

## Downloading artifacts

In the preview panel, click **Download**. Content is served with the correct `Content-Type`:

- EOS configs save as `.txt`.
- Markdown docs save as `.md`.

## Regenerating an artifact

Artifacts regenerate automatically when the underlying data changes, but you can force a regeneration from the preview panel's **Regenerate** button. Typical reasons to force a regenerate:

- You edited a device attribute directly in the UI and want to see the config update.
- A previous generator run was interrupted and the artifact is stale.

## What if an artifact is empty or says "no structured config available"?

This means the structured-config generator hasn't run for the fabric yet. See the [troubleshooting page](./troubleshooting.md) for the fix.

## Downstream consumption

The artifacts are also accessible via the Infrahub API and through Ansible playbooks orchestrated by Semaphore at `http://localhost:3000`. For the Ansible side, see the `ansible/` directory in the repository.
