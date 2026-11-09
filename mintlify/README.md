# GPT Researcher docs on Mintlify

This directory contains the GPT Researcher documentation and blog migrated from the Docusaurus site in [`docs/`](../docs) to [Mintlify](https://mintlify.com).

## Preview locally

```bash
npm i -g mint
cd mintlify
mint dev
```

Then open http://localhost:3000.

## Checks

```bash
mint validate
mint broken-links
```

## Deploying

1. Create a Mintlify project at https://dashboard.mintlify.com and connect this repository with `mintlify` as the docs directory.
2. Point `docs.gptr.dev` at Mintlify under **Settings → Custom domain**.

The `/docs/:slug*` redirect in `docs.json` keeps existing Docusaurus URLs such as `/docs/gpt-researcher/gptr/config` working after the domain moves.

## Structure

- `docs.json` holds the site config and navigation, mirroring `docs/sidebars.js`.
- Doc pages keep their Docusaurus paths without the `/docs` prefix, e.g. `gpt-researcher/gptr/config.mdx`.
- Blog posts live in `blog/<slug>.mdx` under the Blog tab.
- Images from `docs/static/img` and page-local `img/` folders live in `images/`.
