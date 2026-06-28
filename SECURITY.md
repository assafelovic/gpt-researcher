# Security Policy

## Reporting a vulnerability

If you believe you've found a security issue that falls within the threat model
described below, please report it privately rather than opening a public issue:

- Use GitHub's [private vulnerability reporting](https://github.com/assafelovic/gpt-researcher/security/advisories/new), **or**
- Email the maintainer at **assaf.elovic@gmail.com** with details and, ideally, a proof of concept.

We aim to acknowledge reports within a few business days. Please give us a
reasonable window to investigate and ship a fix before any public disclosure.

## Threat model — please read before reporting

GPT-Researcher is **open-source software that you, the operator, run in your own
environment.** Understanding the intended deployment model avoids duplicate
reports for behavior that is by design.

### The backend is not a hardened, multi-tenant service

The backend server (FastAPI + WebSocket, `/ws` and the REST endpoints) ships
**without built-in authentication or network access controls, by design.** It is
intended to be run locally or behind infrastructure that the operator controls.

If you expose the server directly to untrusted clients, you are responsible for
placing it behind your own authentication, reverse proxy, and network
boundaries. Accordingly, the following are considered **operator-configuration
concerns and out of scope** as project vulnerabilities:

- Lack of authentication/authorization on REST or WebSocket endpoints.
- Actions that an authorized operator can already perform being reachable by an
  *unauthenticated* client (e.g. supplying `source_urls`/`document_urls`,
  configuring MCP servers/commands, uploading files). These are intended
  capabilities for a trusted user; restricting who can reach them is the
  operator's responsibility.
- Server-side request forgery (SSRF) or local file access via user-supplied
  URLs/paths on an endpoint you have chosen to expose without auth.
- Remote code execution via user-supplied MCP `command`/`args`: configuring MCP
  servers is an intended feature for the trusted operator; do not expose the
  endpoint that accepts MCP configs to untrusted clients.

If you want to run GPT-Researcher in a shared or public setting, add an
authentication/authorization layer in front of it. Contributions of an
**optional** hardening layer (e.g. opt-in API-key auth) are welcome via PR.

### What we DO treat as in-scope vulnerabilities

Issues that affect a user running the tool as intended — independent of who can
reach the endpoint — are in scope, for example:

- **Cross-site scripting / unsafe rendering** of untrusted *content* (web pages
  the tool scrapes, or LLM output) in the frontends.
- **Denial of service from processing untrusted content**, e.g. decompression
  bombs from scraped responses.
- Vulnerabilities in dependencies that are reachable through normal use.
- Path traversal, injection, or memory-safety issues triggered by normal
  research inputs.

Reports in this category are very welcome — please use the private channel above.

## Supported versions

Security fixes are applied to the latest release on the `master` branch. Please
make sure you can reproduce an issue on the latest version before reporting.
