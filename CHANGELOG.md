# Changelog

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
