/** @type {import('@docusaurus/types').DocusaurusConfig} */
const math = require('remark-math');
const katex = require('rehype-katex');

module.exports = {
  title: 'GPT Researcher',
  tagline: 'The leading autonomous AI research agent',
  url: 'https://docs.gptr.dev',
  baseUrl: '/',
  onBrokenLinks: 'ignore',
  //deploymentBranch: 'master',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',
  organizationName: 'assafelovic',
  trailingSlash: false,
  projectName: 'gpt-researcher',
  themeConfig: {
    navbar: {
      title: 'GPT Researcher',
      logo: {
        alt: 'GPT Researcher',
        src: 'img/gptr-logo.png',
      },
      items: [
        {
          type: 'doc',
          docId: 'welcome',
          position: 'left',
          label: 'Docs',
        },

        {to: 'blog', label: 'Blog', position: 'left'},
        {
          type: 'doc',
          docId: 'faq',
          position: 'left',
          label: 'FAQ',
        },
        {
            href: 'mailto:assaf.elovic@gmail.com',
            position: 'left',
            label: 'Contact',
        },
        {
          href: 'https://github.com/assafelovic/gpt-researcher',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Community',
          items: [
            {
              label: 'Discord',
              href: 'https://discord.gg/8YkBcCED5y',
            },
            {
              label: 'Twitter',
              href: 'https://twitter.com/assaf_elovic',
            },
            {
              label: 'LinkedIn',
              href: 'https://www.linkedin.com/in/assafe/',
            },
          ],
        },
        {
          title: 'Company',
          items: [
            {
              label: 'Homepage',
              href: 'https://gptr.dev',
            },
            {
              label: 'Contact',
              href: 'mailto:assafelovic@gmail.com',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} GPT Researcher.`,
    },
  },
  presets: [
    [
      '@docusaurus/preset-classic',
      {
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          // Please change this to your repo.
          editUrl:
            'https://github.com/assafelovic/gpt-researcher/tree/master/docs',
          remarkPlugins: [math],
          rehypePlugins: [katex],
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      },
    ],
  ],
  stylesheets: [
    {
        href: "https://cdn.jsdelivr.net/npm/katex@0.13.11/dist/katex.min.css",
        integrity: "sha384-Um5gpz1odJg5Z4HAmzPtgZKdTBHZdw8S29IecapCSB31ligYPhHQZMIlWLYQGVoc",
        crossorigin: "anonymous",
    },
  ],

  plugins: [
    // ... Your other plugins.
    [
      require.resolve("@easyops-cn/docusaurus-search-local"),
      {
        // ... Your options.
        // `hashed` is recommended as long-term-cache of index file is possible.
        hashed: true,
        blogDir:"./blog/"
        // For Docs using Chinese, The `language` is recommended to set to:
        // ```
        // language: ["en", "zh"],
        // ```
        // When applying `zh` in language, please install `nodejieba` in your project.
      },
    ],
  ],
};
