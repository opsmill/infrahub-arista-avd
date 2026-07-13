import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const siteUrl = process.env.DOCUSAURUS_URL ?? 'https://opsmill.github.io';
const baseUrl = process.env.DOCUSAURUS_BASE_URL ?? '/infrahub-arista-avd/';

const config: Config = {
  title: 'Infrahub Arista AVD',
  tagline: 'AI datacenter infrastructure management with Infrahub and Arista Validated Design',
  favicon: 'img/favicon.ico',

  url: siteUrl,
  baseUrl,

  organizationName: 'opsmill',
  projectName: 'infrahub-arista-avd',

  onBrokenLinks: 'throw',
  onDuplicateRoutes: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          editUrl: 'https://github.com/opsmill/infrahub-arista-avd/tree/main/docs',
          routeBasePath: '/',
          sidebarCollapsed: true,
          sidebarPath: './sidebars.ts',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themes: ['@docusaurus/theme-mermaid'],

  plugins: [
    function suppressMermaidWebpackWarnings() {
      return {
        name: 'suppress-mermaid-webpack-warnings',
        configureWebpack() {
          return {
            ignoreWarnings: [
              (warning) => {
                const resource =
                  (warning.module as {resource?: string} | undefined)
                    ?.resource ?? '';

                return (
                  /vscode-languageserver-types/.test(resource) &&
                  /Critical dependency: require function is used/.test(
                    warning.message ?? '',
                  )
                );
              },
            ],
          };
        },
      };
    },
  ],

  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },

  themeConfig: {
    navbar: {
      logo: {
        alt: 'Infrahub',
        src: 'img/infrahub-hori.svg',
        srcDark: 'img/infrahub-hori-dark.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'mainSidebar',
          position: 'left',
          label: 'Documentation',
        },
        {
          href: 'https://github.com/opsmill/infrahub-arista-avd',
          position: 'right',
          className: 'header-github-link',
          'aria-label': 'GitHub repository',
        },
      ],
    },
    footer: {
      copyright: `Copyright © ${new Date().getFullYear()} - <b>Infrahub</b> by OpsMill.`,
    },
    prism: {
      theme: prismThemes.oneDark,
      additionalLanguages: ['bash', 'python', 'markup-templating', 'django', 'json', 'toml', 'yaml'],
    },
    mermaid: {
      theme: {light: 'neutral', dark: 'dark'},
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
