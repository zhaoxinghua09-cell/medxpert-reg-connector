# Changelog

## 1.3.5 — 2026-11-15

**Verifiability and release-process gates. No code or tool-behaviour change.**

### Added
- `server.json` → `packages[0].fileSha256`: the SHA-256 of the wheel PyPI actually serves, so a client that supports the field can verify the download before running it. The hash is read back from `https://pypi.org/pypi/medxpert-reg-connector/<version>/json` after publication, never from a local build — `uv build` is not byte-reproducible (zip timestamps differ run to run), so a locally computed hash would describe a file nobody downloads.
- `tools/release_check.py`: one command that proves the public surfaces agree — version consistency across the 8 manifests, PyPI serving this version, `fileSha256` equal to the served wheel's digest, the registry's newest entry carrying this version, and `websiteUrl` plus every icon URL answering 200. Exits non-zero on any failure; `--offline` runs the manifest check only.
- `tools/check_sources.py` + `.github/workflows/link-audit.yml`: a weekly probe of every URL in `data/sources.json`, classifying each result as OK / BLOCKED (anti-bot: NMPA 412, ISO 403 — the site is up, the robot is refused) / FAIL (timeout, DNS, 5xx — the signal that a source moved). Advisory by default so a monitored repository is never failed by the monitor.
- `docs/RELEASE.md`: the release order as a written procedure, bilingual, including why PyPI must precede the tag and the two prohibitions this project has already paid for (`git reset --hard` discarding uncommitted work; an immutable tag).

### 中文摘要
- `server.json` 增加 `packages[0].fileSha256`：填入 PyPI 真正在分发的那个 wheel 的 SHA-256，支持该字段的客户端可在运行前校验下载物。哈希取自发布后的 PyPI JSON，不取本地构建——`uv build` 不可字节复现（zip 时间戳每次不同），本地算的哈希描述的是没人下载的文件。
- 新增 `tools/release_check.py`：一条命令证明各公开面一致——8 处版本、PyPI 是否已发该版本、`fileSha256` 是否等于线上 wheel 摘要、Registry 最新条目是否已是该版本、`websiteUrl` 与全部图标 URL 是否 200。任一失败即非零退出；`--offline` 只跑清单检查。
- 新增 `tools/check_sources.py` 与每周 `link-audit` 工作流：巡检 `data/sources.json` 全部官方源，结果分 OK / BLOCKED（反爬：NMPA 412、ISO 403，站点在、拒绝机器人）/ FAIL（超时、DNS、5xx，才是"源搬了"）。默认只告警，不让巡检把被巡检的仓库判红。
- 新增 `docs/RELEASE.md`：把发布顺序写成规程，中英双语，说明为何必须先发 PyPI 再打 tag，以及本项目已经付过代价的两条禁令（`git reset --hard` 清空未提交编辑；tag 不可移动）。

## 1.3.4 — 2026-11-15

**Version consistency and a false attestation removed. No code or tool-behaviour change.**

### Fixed
- Three manifests and one skill header still said `1.2.0` while the package had shipped 1.3.1, 1.3.2 and 1.3.3: `connector-meta.json`, `lhm.plugin.json`, `manifest.json`, and the `version:` front-matter of `SKILL.md`. Directory sites read those files, which is why a listing could say 1.2.0 while PyPI said 1.3.3. All four now read from the package version.
- `manifest.json` carried its own per-file hash table and a package fingerprint from 1.2.0, describing a **pre-packaging layout** (`registry.json` / `sources.json` at repo root) that no longer exists — it was attesting files that had been deleted. It is now a pointer to `ATTESTATION.md` and `tools/attest.py`, with an explicit note in English and Chinese that it is no longer a hash source.

### Added
- `tools/version_check.py`: single source of truth is `medxpert_reg_connector/__init__.py __version__`; the check compares pyproject, `connector-meta.json`, `lhm.plugin.json`, `manifest.json`, `server.json` (entry + package), `SKILL.md` front-matter and the newest `CHANGELOG.md` heading, and fails on any mismatch. Wired into CI, so this drift cannot ship again.
- Deliberately excluded: `data/registry.json` → `knowledge_base_version`, which versions the knowledge-base lineage, not the release train.

### 中文摘要
- `connector-meta.json` / `lhm.plugin.json` / `manifest.json` / `SKILL.md` 四处仍写着 `1.2.0`，而包已经发到 1.3.3——目录站正是读这些文件，所以会出现「PyPI 是 1.3.3、展示是 1.2.0」。四处全部改为跟随包版本。
- `manifest.json` 自带的哈希表与包指纹是 1.2.0 时期的**打包前布局**（`registry.json` / `sources.json` 还在仓库根），所证文件早已不存在；现改为指向 `ATTESTATION.md` 与 `tools/attest.py`，并用中英文写明它不再是哈希依据。
- 新增 `tools/version_check.py`，以 `__init__.py __version__` 为唯一真源核对 8 处版本，并接入 CI——这种漂移不会再发出去。
- 刻意排除 `data/registry.json` 的 `knowledge_base_version`：它记的是知识库血统，不是发版序号。

## 1.3.3 — 2026-11-15

**Icon hosting fix. No code or tool-behaviour change.**

### Fixed
- The 1.3.2 icon pointed only at `raw.githubusercontent.com`, which is unreachable from mainland-China networks: measured from this machine the TLS handshake times out after 24 s, while `cdn.jsdelivr.net` serves the same file in 1.1 s. `icons` now lists **two** sources — jsDelivr CDN first, raw GitHub second — so a client can use whichever resolves.

### Verified
- `cdn.jsdelivr.net` served the icon in 1.1 s; `gcore.jsdelivr.net`, the same mirror on another edge, in 1.0 s. `raw.githubusercontent.com` is listed as a secondary entry and was **not** verified from this machine.
- `server.json` re-validates against the 2025-12-11 schema (2 icon entries).
- `tools/attest.py --check` → `files=53 drift=0 fingerprint_match=True payload_fingerprint_match=True`.

## 1.3.2 — 2026-11-15

**Registry metadata and discoverability release. No code or tool-behaviour change.**

### Added
- `server.json` now carries `icons` (SVG, `assets/icon.svg`), so registry clients and directories can render a real card instead of a placeholder.
- `server.json` now carries `_meta` publisher-provided metadata: publisher identity, `payload_fingerprint_sha256`, attestation link, `verify_command`, licence split, `runtime_egress: none`. The fingerprint covers the wheel payload only, so repo-metadata edits cannot silently invalidate the registry entry.
- `tools/attest.py` now computes and records a **payload fingerprint** (files actually shipped inside the wheel) alongside the package fingerprint; `--check` verifies both.
- `assets/icon.svg` added to the covered file set.

### Verified
- `server.json` validates against `https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json` (still the current schema: the official quickstart and 2026-06 registry examples reference it).
- `tools/attest.py --check` → `files=53 drift=0 missing=0 fingerprint_match=True payload_fingerprint_match=True`.

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
