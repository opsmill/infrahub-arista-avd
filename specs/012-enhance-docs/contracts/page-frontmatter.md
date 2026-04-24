# Contract: Page Front-Matter

Every Markdown file under `docs/docs/` MUST satisfy this contract. Violations are review-blockers.

## Schema

```yaml
---
title: string                    # REQUIRED — page title (browser tab + H1 fallback)
description: string              # REQUIRED — one-sentence summary used in search/previews
audience: user | developer | landing  # REQUIRED — must match directory placement
sidebar_position: integer        # REQUIRED for non-landing pages — order within category
slug: string                     # OPTIONAL — URL override; avoid unless renaming a published page
hide_table_of_contents: boolean  # OPTIONAL — default false; true only on index/landing pages
keywords: list[string]           # OPTIONAL — supplemental search terms
---
```

## Examples

### User-guide page

```yaml
---
title: Add a Network Segment
description: Create a VRF, VLAN, and SVI on a fabric using the service portal.
audience: user
sidebar_position: 1
---
```

### Developer-guide page

```yaml
---
title: Hostvars Reference
description: The pyAVD-compatible hostvars structure produced per device role.
audience: developer
sidebar_position: 2
---
```

### Landing page

```yaml
---
title: Infrahub Arista AVD
description: Infrahub solution for AI datacenter infrastructure management with Arista Validated Design.
audience: landing
hide_table_of_contents: true
slug: /
---
```

## Validation

- Build-time: Docusaurus `npm run build` enforces required Docusaurus front-matter (`title`, `slug` uniqueness). It does **not** enforce custom fields like `audience`.
- Review-time: A reviewer MUST check that `audience` matches the directory and that `sidebar_position` exists on non-landing pages.
- Optional future: a small `tools/check-docs-frontmatter.ts` script could enforce `audience` programmatically; out of scope for this feature.
