import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  mainSidebar: [
    'home',
    'architecture',
    'schemas',
    'generators',
    'transforms',
    {
      type: 'category',
      label: 'AVD Integration',
      collapsed: false,
      items: ['avd/README'],
    },
  ],
};

export default sidebars;
