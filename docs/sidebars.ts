import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  mainSidebar: [
    'home',
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
