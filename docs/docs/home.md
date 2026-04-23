---
title: Infrahub Arista AVD
description: Infrahub solution for AI datacenter infrastructure management with Arista Validated Design.
audience: landing
slug: /
hide_table_of_contents: true
hide_title: true
---

## Infrahub Arista AVD

An Infrahub solution for AI datacenter infrastructure management. It models network fabric hierarchies (Fabric → Pod → Rack → Device) with full **Arista Validated Design (AVD)** integration, automatic device generation, and configuration rendering.

---

### Choose your guide

<div className="container" style={{padding: 0}}>
  <div className="row">
    <div className="col col--6">
      <div className="card" style={{height: '100%', padding: '1.5rem'}}>
        <h3>👤 User Guide</h3>
        <p>
          For network engineers and operators. Provision fabrics, run the
          service-portal workflows, and view AVD-rendered configurations and
          documentation. No Python required.
        </p>
        <a href="/user-guide/"><strong>Open the User Guide →</strong></a>
      </div>
    </div>
    <div className="col col--6">
      <div className="card" style={{height: '100%', padding: '1.5rem'}}>
        <h3>🛠 Developer Guide</h3>
        <p>
          For contributors. Understand the two-phase AVD generator pipeline,
          extend the integration with new device roles or transform outputs,
          and debug pipeline issues.
        </p>
        <a href="/developer-guide/"><strong>Open the Developer Guide →</strong></a>
      </div>
    </div>
  </div>
</div>

---

## Quick install

If you just want to bring the stack up locally:

```bash
uv sync --all-packages     # Install dependencies
uv run invoke build        # Build the custom Infrahub image (one-time)
uv run invoke start        # Start Infrahub with docker-compose
uv run invoke load         # Load schemas, menus, objects, and repository
```

Then open the Infrahub UI at **`http://localhost:8000`** and the service portal at **`http://localhost:8501`**.

For the full first-fabric walkthrough, follow the [user guide](/user-guide/).
