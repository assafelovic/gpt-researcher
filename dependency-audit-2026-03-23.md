# Dependency Audit Report -- 2026-03-23

## Summary

This audit covers all package manifests across the gpt-researcher repository, including
the Python core library (`pyproject.toml`, `requirements.txt`, `setup.py`), backend,
multi-agents, evals, and three Node.js sub-projects (frontend/nextjs, docs, docs/discord-bot).

| Area | Critical Vulns | High Vulns | Moderate Vulns | Outdated (Major) | Outdated (Minor/Patch) |
|------|---------------|------------|----------------|-------------------|------------------------|
| Python (core) | 0 | 0 | 0 | 2 | ~8 |
| Python (evals) | 1 | 0 | 0 | 0 | 1 |
| Node (frontend/nextjs) | 0 | 13 | 1 | 5 | ~10 |
| Node (docs) | 0 | 7 | 12 | 2 | ~5 |
| Node (discord-bot) | 0 | 1 | 1 | 1 | ~3 |

---

## 1. Critical & High Security Vulnerabilities

### 1.1 Python -- `evals/hallucination_eval`

| Package | Installed | CVE | Severity | Fix |
|---------|-----------|-----|----------|-----|
| diskcache | 5.6.3 | CVE-2025-69872 | Critical | No patched version available yet (5.6.3 is latest). Monitor for upstream fix. |

**Note:** `diskcache` is a transitive dependency pulled in by `judges>=0.1.0`. Since 5.6.3 is the latest release, no immediate fix exists. Consider pinning or isolating the evals environment.

### 1.2 Node -- `frontend/nextjs` (14 vulnerabilities)

| Package | Advisory | Severity | Fix Strategy |
|---------|----------|----------|-------------|
| **next** 14.x | GHSA-9g9p, GHSA-h25m, GHSA-ggv3, GHSA-3x4c | High | Upgrade to `next@15.x` or `16.x` (MAJOR -- breaking) |
| **serialize-javascript** <=7.0.2 | GHSA-5c6j (RCE) | High | Transitive via `rollup-plugin-terser` and `@ducanh2912/next-pwa`. Replace `rollup-plugin-terser` with `@rollup/plugin-terser@^1.0.0` |
| **@mozilla/readability** <0.6.0 | GHSA-3p6v (DoS via Regex) | High | Upgrade to `^0.6.0` (MAJOR) |
| **glob** 10.2.0-10.4.5 | GHSA-5j98 (command injection) | High | Transitive via `eslint-config-next@14.x`. Upgrade eslint-config-next to `>=15.0.1` |
| **minimatch** 9.0.0-9.0.6 | GHSA-3ppc, GHSA-7r86, GHSA-23c5 (ReDoS) | High | Transitive via `@typescript-eslint`. Upgrade `eslint-config-next` |

### 1.3 Node -- `docs` (Docusaurus) (19 vulnerabilities)

| Package | Advisory | Severity | Fix Strategy |
|---------|----------|----------|-------------|
| **serialize-javascript** <=7.0.2 | GHSA-5c6j (RCE) | High | Upgrade `@docusaurus/core` and `@docusaurus/preset-classic` from `3.7.0` to `>=3.8.0` |
| **minimatch** <=3.1.3 | GHSA-3ppc, GHSA-7r86, GHSA-23c5 (ReDoS) | High | Already pinned at `3.0.5` in resolutions -- needs bump to `>=3.1.5` |
| **webpack-dev-server** <=5.2.0 | GHSA-9jgg, GHSA-4v9v (source code theft) | Moderate | Upgrade Docusaurus to >=3.8.0 |

### 1.4 Node -- `docs/discord-bot` (2 vulnerabilities)

| Package | Advisory | Severity | Fix Strategy |
|---------|----------|----------|-------------|
| **undici** <=6.23.0 (via discord.js) | GHSA-g9mf, GHSA-f269, GHSA-2mjp, GHSA-vrm6, GHSA-v9p9, GHSA-4992 | High | Upgrade `discord.js` to `^14.25.1` (patch) |

---

## 2. Outdated Packages -- Python

### 2.1 Major Version Behind (require testing before upgrade)

| Package | Pinned Min | Latest | Gap | Notes |
|---------|-----------|--------|-----|-------|
| langgraph | `>=0.2.73,<0.3` (pyproject.toml poetry) | 1.1.3 | 0.2.x -> 1.1.x | Major API changes in 1.0. The `[project]` section pins `>=0.2.76` which is better but still 0.x. |
| openai | `>=1.3.3` (requirements.txt) | 2.29.0 | 1.x -> 2.x | openai 2.x is a major release with breaking changes. The `[project]` section pins `>=1.82.0`. |
| duckduckgo-search | `>=4.1.1` | 8.1.1 | 4.x -> 8.x | Many breaking changes across 5.x, 6.x, 7.x, 8.x |

### 2.2 Minor/Patch Behind (safe to bump)

| Package | Pinned Min | Latest | Notes |
|---------|-----------|--------|-------|
| fastapi | `>=0.104.1` | 0.135.2 | Many minor releases with fixes |
| uvicorn | `>=0.24.0.post1` | 0.34.2 | Already pinned higher in `[project]` |
| pymupdf | `>=1.23.6` (requirements.txt) | 1.26.x | Pinned `>=1.26.0` in `[project]`, inconsistent |
| unstructured | `>=0.13` (requirements.txt) | 0.21.5 | Pinned `>=0.17.2` in `[project]`, still behind |
| websockets | `^13.1` (poetry) | 15.0.1 | Pinned `>=15.0.1` in `[project]`, inconsistent |
| json-repair | `^0.29.8` (poetry) | 0.44.0+ | Pinned `>=0.44.0` in `[project]` |
| md2pdf | `>=1.0.1` | 3.1.0 | Major bump available |

### 2.3 Inconsistencies Between Manifest Files

The repository has **three overlapping Python dependency declarations** that are out of sync:

1. **`pyproject.toml [tool.poetry.dependencies]`** -- older pins (e.g., `langgraph >=0.2.73,<0.3`)
2. **`pyproject.toml [project] dependencies`** -- newer pins (e.g., `langgraph >=0.2.76`)
3. **`requirements.txt`** -- mixed old/new pins

This creates confusion about which versions are actually required. The `[project]` section is the most up-to-date.

---

## 3. Outdated Packages -- Node.js

### 3.1 `frontend/nextjs` -- Major Version Behind

| Package | Current Range | Latest | Notes |
|---------|--------------|--------|-------|
| next | `^14.2.28` | 16.2.1 | 2 majors behind. Next 15 dropped Pages Router changes, 16 is React 19. |
| react / react-dom | `^18.0.0` | 19.2.4 | React 19 is a major release |
| zod | `^3.0.0` | 4.3.6 | Zod 4 has breaking schema changes |
| framer-motion | `^9.0.2` | 12.38.0 | 3 majors behind |
| eventsource-parser | `^1.1.2` | 3.0.6 | 2 majors behind |
| rollup (devDep) | `^2.79.2` | 4.x | 2 majors behind, rollup-plugin-terser is deprecated |
| @langchain/langgraph-sdk | `^0.0.1-rc.12` | 1.8.0 | Pre-release to 1.x stable |

### 3.2 `docs` -- Notable Outdated

| Package | Current | Latest | Notes |
|---------|---------|--------|-------|
| @docusaurus/core | 3.7.0 | 3.9.2 | Minor bump, fixes security issues |
| @docusaurus/preset-classic | 3.7.0 | 3.9.2 | Same |
| clsx | `^1.1.1` | 2.1.1 | Major bump |
| minimatch (pinned) | 3.0.5 | 10.2.4 | Very old, ReDoS vulnerable |

### 3.3 `docs/discord-bot` -- Notable Outdated

| Package | Current Range | Wanted | Latest | Notes |
|---------|--------------|--------|--------|-------|
| dotenv | `^16.4.5` | 16.6.1 | 17.3.1 | Latest is major bump |
| express | `^4.17.1` | 4.22.1 | 5.2.1 | Express 5 is a major release |

### 3.4 `multi_agents/package.json`

| Package | Current Range | Latest | Notes |
|---------|--------------|--------|-------|
| @langchain/langgraph-sdk | `^0.0.1-rc.13` | 1.8.0 | Pre-release to stable 1.x |

---

## 4. Deprecated / Unmaintained Packages

| Package | Location | Issue | Recommendation |
|---------|----------|-------|----------------|
| `rollup-plugin-terser` | frontend/nextjs devDeps | Deprecated, last release 2022 | Replace with `@rollup/plugin-terser` |
| `rollup-plugin-postcss` | frontend/nextjs devDeps | Unmaintained (last update 2021) | Consider `postcss-cli` or bundler-native PostCSS |
| `rollup-plugin-typescript2` | frontend/nextjs devDeps | Deprecated in favor of `@rollup/plugin-typescript` | Already have `@rollup/plugin-typescript` -- remove duplicate |
| `rollup-plugin-peer-deps-external` | frontend/nextjs devDeps | Low maintenance | Consider `@rollup/plugin-node-resolve` external option |
| `rollup ^2.79.2` | frontend/nextjs devDeps | Rollup 2 is EOL | Upgrade to Rollup 4 (requires plugin updates) |
| `htmldocx ^0.0.6` | pyproject.toml | Last release 2023, 0.0.6 only version | No alternative readily available; monitor |
| `file-loader` / `url-loader` | docs | Deprecated in webpack 5 (use asset modules) | Docusaurus handles this internally |
| `nodemon` | discord-bot deps | Listed as regular dep, should be devDep | Move to devDependencies |
| `trim ^0.0.3` | docs | Ancient package, pinned for vuln fix | Already at safe version via resolution |

---

## 5. Docker Image Concerns

| File | Issue | Recommendation |
|------|-------|----------------|
| `Dockerfile` | Uses `python:3.12-slim-bookworm` | Consider bumping to 3.13 (used in Dockerfile.fullstack) |
| `Dockerfile` | `apt-key add` is deprecated | Switch to signed-by keyring approach |
| `Dockerfile.fullstack` | Uses `node:slim` without version pin | Pin to `node:20-slim` or `node:22-slim` for reproducibility |
| Both | geckodriver pinned at `v0.36.0` | Latest is 0.36.0, but verify periodically |

---

## 6. Recommended Actions

### Immediate (Security fixes, no breaking changes)

1. **Upgrade `@docusaurus/core` and `@docusaurus/preset-classic`** from `3.7.0` to `3.9.2` in `docs/package.json`
2. **Update `minimatch` resolution** in `docs/package.json` from `3.0.5` to `3.1.5`
3. **Upgrade `discord.js`** to `^14.25.1` in `docs/discord-bot/package.json` (fixes undici vulns)
4. **Run `npm audit fix`** in `frontend/nextjs` (fixes minimatch in eslint chain)

### Short-term (Minor version bumps, low risk)

5. **Bump `fastapi`** minimum from `>=0.104.1` to `>=0.135.0` in requirements.txt
6. **Consolidate Python dependency versions** -- reconcile `[tool.poetry.dependencies]`, `[project]`, and `requirements.txt`
7. **Replace `rollup-plugin-terser`** with `@rollup/plugin-terser` in frontend (fixes serialize-javascript RCE)
8. **Remove `rollup-plugin-typescript2`** (duplicate of `@rollup/plugin-typescript`)
9. **Move `nodemon`** from dependencies to devDependencies in discord-bot

### Medium-term (Major bumps, require testing)

10. **Upgrade Next.js** from 14 to 15 (or 16) -- significant effort, React 19 migration
11. **Upgrade `langgraph`** upper bound from `<0.3` to allow 1.x
12. **Evaluate `openai` 2.x** migration when upstream stabilizes
13. **Upgrade Rollup** from 2 to 4 in frontend build pipeline
14. **Upgrade `duckduckgo-search`** to 8.x (API changes required)

### Low Priority (Maintenance)

15. Pin `node:slim` to a specific version in `Dockerfile.fullstack`
16. Replace deprecated `apt-key add` with signed-by keyring in Dockerfiles
17. Bump `Dockerfile` base from Python 3.12 to 3.13

---

## 7. Applied Fixes in This PR

The following safe, non-breaking updates were applied:

- `docs/package.json`: Bumped `@docusaurus/core` and `@docusaurus/preset-classic` from `3.7.0` to `3.9.2`
- `docs/package.json`: Updated `minimatch` resolution from `3.0.5` to `3.1.5`, direct dep from `3.0.5` to `3.1.5`
- `docs/discord-bot/package.json`: Updated `discord.js` to `^14.25.1`
- `docs/discord-bot/package.json`: Moved `nodemon` from dependencies to devDependencies

---

*Generated 2026-03-23 by dependency audit script.*
