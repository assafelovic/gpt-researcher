Thanks for taking the time to put this together — it's genuinely appreciated.

GPT-Researcher is open-source software designed to be run by the operator within their own trusted environment. The backend intentionally does **not** ship with built-in authentication or network-level access controls — it's meant to be deployed behind the operator's own auth / reverse-proxy and network boundaries. Reports whose impact depends on reaching the backend directly as an untrusted, unauthenticated client therefore fall **outside the project's intended threat model** rather than representing a vulnerability in the project itself.

We're documenting this explicitly in a `SECURITY.md` (threat model + a private channel for genuine, content-level vulnerabilities). Closing this as out-of-scope under that model.

If you'd like to contribute an **optional** hardening layer (e.g. opt-in API-key auth on the endpoints), a PR or a [Discussions](https://github.com/assafelovic/gpt-researcher/discussions) thread is very welcome. 🙏
