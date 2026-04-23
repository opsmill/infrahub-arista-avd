# Contract: Sidebar Structure

`docs/sidebars.ts` MUST conform to the shape below.

## Required shape

```ts
import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  mainSidebar: [
    'home',                                       // Landing page (audience: landing)
    {
      type: 'category',
      label: 'User Guide',
      collapsed: false,
      link: { type: 'doc', id: 'user-guide/index' },
      items: [
        'user-guide/quick-start',
        'user-guide/provision-first-fabric',
        {
          type: 'category',
          label: 'How To',
          collapsed: false,
          items: [
            'user-guide/how-to/add-network-segment',
            'user-guide/how-to/add-server',
            'user-guide/how-to/create-tenant',
            'user-guide/how-to/regenerate-fabric',
          ],
        },
        'user-guide/viewing-artifacts',
        'user-guide/troubleshooting',
      ],
    },
    {
      type: 'category',
      label: 'Developer Guide',
      collapsed: false,
      link: { type: 'doc', id: 'developer-guide/index' },
      items: [
        'developer-guide/architecture',
        'developer-guide/schemas',
        'developer-guide/generators',
        'developer-guide/transforms',
        {
          type: 'category',
          label: 'AVD Integration',
          collapsed: false,
          items: [
            'developer-guide/avd/overview',
            'developer-guide/avd/hostvars',
            'developer-guide/avd/transforms',
            'developer-guide/avd/artifacts',
            'developer-guide/avd/role-mapping',
            'developer-guide/avd/extending',
            'developer-guide/avd/debugging',
          ],
        },
      ],
    },
  ],
};

export default sidebars;
```

## Rules

1. Exactly one top-level `mainSidebar` array (the existing key — kept for navbar compatibility).
2. The first entry MUST be the landing page (`'home'`), outside both track categories.
3. Exactly two top-level category entries follow, in this order: "User Guide", then "Developer Guide".
4. Each top-level category MUST set `link: { type: 'doc', id: '<track>/index' }` so the label itself is a navigable target.
5. Each top-level category MUST set `collapsed: false` so the active track is visible without an extra click.
6. Sub-categories (e.g. "How To", "AVD Integration") follow the same `type: 'category'` shape and MAY nest one level deeper. Do not nest beyond two levels under a top-level track.
7. Every doc ID listed MUST resolve to an existing `.md` file under `docs/docs/`. The Docusaurus build fails otherwise.

## Adding a new page

To add a page to the user guide:

1. Create the file: `docs/docs/user-guide/<slug>.md` with the appropriate front-matter (see [page-frontmatter contract](./page-frontmatter.md)).
2. Add one line to the User Guide `items:` list at the right `sidebar_position`.

That is the only required change. No navbar, theme, or build-config edits.
