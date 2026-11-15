# Changelog

## 1.3.1 — 2026-11-15

**Content and documentation release. No code or tool-behaviour change.**

### Fixed
- **Two malformed hub titles** visible in `list_hubs()` / `ask_classification`: `FDA创伤敷料供应链穿透检查枢纽` carried the author string inside its H1 (`…（赵兴华 / Steven Zhao·China (ORCID …)知识库）`) and `骨科手术器械_全球注册路径汇编` repeated its name three times (`骨科手术器械 / 骨科手术器械 / 骨科手术器械 — …`). Both now match the curated `registry.json` titles; attribution stays in the blockquote of the first hub.
- **Package fingerprint was not reproducible**: `ATTESTATION.md` claimed a SHA-256 fingerprint but shipped no rule for recomposing it, and its table had already drifted (`server.json` changed after the fingerprint was taken). The rule is now stated in the file and implemented in `tools/attest.py` (`--check` mode for drift detection).

### Changed
- `README.md` gained real captured outputs (not hand-written prose), the full 27-hub table generated from `list_hubs()`, a comparison table against `medxpert-reg-hub`, and an explicit disclosure that 27/27 hubs are currently `overdue` (review clock elapsed, no human re-verification recorded).
- Source-channel liveness recorded: 15 official sources probed on 2026-11-15 — 12 reachable, 3 blocked by anti-bot (NMPA ×2 → 412, ISO → 403). Reachability is not content freshness, so `next_review` dates were deliberately left untouched.

## 1.3.0 — 2026-11-15

**Packaging & agent-readiness release. Tool behaviour unchanged.**

### Fixed
- **Install path was broken**: `uvx` / `pip install medxpert-reg-connector` pointed at a package that had never been published to PyPI. Now buildable and published; `uvx medxpert-reg-connector` works as documented.
- **Knowledge base not shipped**: the wheel contained only the server module, so a clean install returned empty results for every tool. All 27 hubs, `registry.json` and `sources.json` now ship inside `medxpert_reg_connector/data/` (verified: 28 `.md` files present in wheel, `refs` resolving inside `site-packages`).
- **Self-test stale**: `selftest` still asserted 4 tools and failed on every run. Replaced by `tests/selftest_stdio.py`, which asserts the 7-tool contract, annotations, parameter docs, hub count and all freshness tools; runs in CI.
- Version was inconsistent across three places (package 1.2.0 / registry entry 1.0.0 / tag v1.0.0). Now unified at 1.3.0.

### Changed
- Package restructured from a single top-level module to `medxpert_reg_connector/` (entry point `medxpert_reg_connector.server:main`); `python -m medxpert_reg_connector` also works.
- MCP server key is single-track: `medxpert-reg-connector` (the `@nomos/...` alias is retired).
- `fastmcp` dependency range pinned to `>=3.4,<5` (matches the tested runtime).

### Added
- `readOnlyHint` / `destructiveHint` / `idempotentHint` / `openWorldHint` annotations on all 7 tools.
- Schema descriptions for all 9 tool parameters.
- `Dockerfile` and `.dockerignore` (stdio, no host Python needed).
- `.github/workflows/ci.yml` (contract self-test on Python 3.12 / 3.13).
- Bilingual README (English first, Chinese second); `README.en.md` now points at it.

## 1.2.0 — 2026-10-17
- Expanded the real-time update pipeline (EUR-Lex CELLAR, MDCG sources, 3 → 5 automated sources); site/changelog rendering and overdue review sheets. Service interface unchanged.

## 1.1.0
- Freshness guard: `as_of` / `age_days` / `freshness` on every result; added `kb_freshness`, `reg_delta`, `kb_sources`.

## 1.0.0
- Initial release: 4 retrieval tools over 27 hubs.
