/** @type {import('@docusaurus/types').DocusaurusConfig} */
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);

// Code colours from gptr.dev: red keywords, umber strings, bold ink names.
const codeTheme = (c) => ({
  plain: {color: c.ink, backgroundColor: c.bg},
  styles: [
    {types: ['comment', 'prolog', 'doctype', 'cdata'], style: {color: c.muted}},
    {types: ['keyword', 'selector', 'atrule', 'important', 'tag', 'deleted', 'builtin'], style: {color: c.red}},
    {types: ['string', 'char', 'attr-value', 'regex', 'inserted', 'url'], style: {color: c.str}},
    {types: ['function', 'class-name'], style: {color: c.ink, fontWeight: '600'}},
    {types: ['number', 'boolean', 'constant', 'symbol'], style: {color: c.red}},
    {types: ['punctuation', 'operator'], style: {color: c.muted}},
    {types: ['attr-name', 'property', 'variable', 'parameter'], style: {color: c.ink2}},
  ],
});
const lightCode = codeTheme({bg: '#F6F1E7', ink: '#1A1612', ink2: '#39332B', muted: '#5F574B', red: '#B8381C', str: '#6B5B45'});
const darkCode = codeTheme({bg: '#211C17', ink: '#EEE7D8', ink2: '#CFC6B5', muted: '#A39985', red: '#E0775A', str: '#D6BF94'});

export default {
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
  markdown: {
    mermaid: true,
  },
  themes: ['@docusaurus/theme-mermaid'],
  headTags: [
    {tagName: 'link', attributes: {rel: 'preconnect', href: 'https://fonts.googleapis.com'}},
    {tagName: 'link', attributes: {rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: 'anonymous'}},
  ],
  themeConfig: {
    image: 'img/gptr-social-card.png',
    prism: {
      theme: lightCode,
      darkTheme: darkCode,
    },
    mermaid: {
      theme: {light: 'neutral', dark: 'dark'},
    },
    navbar: {
      title: 'GPT Researcher',
      logo: {
        alt: 'GPT Researcher',
        src: 'img/gptr-logo-black.png',
        srcDark: 'img/gptr-logo-white.png',
      },
      items: [
        {
          to: '/docs/welcome',
          position: 'left',
          label: 'Docs',
          activeBaseRegex: '^/docs/(?!faq/?$)',
        },

        {to: 'blog', label: 'Blog', position: 'left'},
        {
          to: '/docs/faq',
          position: 'left',
          label: 'FAQ',
          activeBaseRegex: '^/docs/faq/?$',
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
          className: 'navbar-github',
        },
      ],
    },
    footer: {
      style: 'light',
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
          editUrl:
            'https://github.com/assafelovic/gpt-researcher/tree/master/docs',
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
        },
        blog: {
          onUntruncatedBlogPosts: 'ignore',
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      },
    ],
  ],
  stylesheets: [
    'https://fonts.googleapis.com/css2?family=Gelasio:wght@400;500;600&family=Instrument+Sans:wdth,wght@75..100,400..700&family=JetBrains+Mono:wght@400;500;600&display=swap',
    {
        href: "https://cdn.jsdelivr.net/npm/katex@0.13.11/dist/katex.min.css",
        integrity: "sha384-Um5gpz1odJg5Z4HAmzPtgZKdTBHZdw8S29IecapCSB31ligYPhHQZMIlWLYQGVoc",
        crossorigin: "anonymous",
    },
  ],

  plugins: [
    [
      require.resolve("@easyops-cn/docusaurus-search-local"),
      {
        hashed: true,
        blogDir:"./blog/"
      },
    ],
  ],
};
