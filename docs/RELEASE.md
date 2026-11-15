# Release Procedure / 发布规程

## English

The order below is not a preference. Each step exists because publishing in the
wrong order has already produced a red run or a wrong artifact.

1. **Branch.** `git fetch origin main && git reset --hard origin/main`, then
   `git checkout -b release/vX.Y.Z`. Never work on `main` directly.
2. **Bump one version.** `medxpert_reg_connector/__init__.py` is the single
   source of truth; `python tools/version_check.py` must show all 8 locations
   agreeing. A version that lives in eight files drifts in eight places.
3. **Contract test.** `python tests/selftest_stdio.py` — 7 tools, annotations,
   argument descriptions, 27 hubs, 15 sources.
4. **Attest.** `python tools/attest.py` recomputes the package fingerprint
   (source tree) and the payload fingerprint (wheel contents only). Commit
   `ATTESTATION.md` and `server.json` together.
5. **PR.** CI must be green, including the version-consistency step.
6. **PyPI first, always.** Run the publish workflow by `workflow_dispatch`. The
   registry validates the package against PyPI, so tagging first returns
   `400 … was not found`.
7. **Then the hash.** Read the wheel sha256 from
   `https://pypi.org/pypi/medxpert-reg-connector/<version>/json` and write it into
   `server.json` → `packages[0].fileSha256`. It must come from the published
   wheel: `uv build` is **not** byte-reproducible (zip timestamps differ run to
   run), so a locally built hash would describe a file nobody downloads.
8. **Tag.** `git tag vX.Y.Z && git push origin vX.Y.Z` — only after
   `python tools/release_check.py --offline` prints ALL PASS.
9. **Registry.** Run the registry workflow by `workflow_dispatch`; confirm the
   new entry carries `icons`, `_meta` and the new `fileSha256`.
10. **GitHub Release.** Notes from `CHANGELOG.md`, bilingual, English first.
11. **Proof from the artifact.** Install into a throwaway venv from `pypi.org`
    (never from `dist/`), run the contract test, and paste the output into the
    execution report.

Two prohibitions, both learned the hard way:

- `git reset --hard` silently discards uncommitted edits. Commit or stash first;
  this has erased finished work twice.
- A tag is immutable. A wrong tag cannot be moved; a new version is the only
  correction.

## 中文

下面的顺序不是偏好。每一步都因为"顺序错"已经产生过一次红色流水线或错误产物。

1. **分支**：先 `git fetch origin main && git reset --hard origin/main`，再
   `git checkout -b release/vX.Y.Z`。不在 `main` 上直接改。
2. **只改一处版本真源**：`medxpert_reg_connector/__init__.py`；
   `python tools/version_check.py` 必须显示 8 处一致。版本号写在 8 个文件里，
   就会在 8 个地方漂移。
3. **契约测试**：`python tests/selftest_stdio.py`——7 工具、注解、参数说明、
   27 枢纽、15 源。
4. **取证**：`python tools/attest.py` 重算包指纹（源码树）与载荷指纹（仅 wheel
   内文件），`ATTESTATION.md` 与 `server.json` 一并提交。
5. **PR**：CI 全绿，含版本一致性步骤。
6. **先发 PyPI**：用 `workflow_dispatch` 跑发布工作流。Registry 会先拿 PyPI 校验
   包，先推 tag 必回 `400 … was not found`。
7. **再写哈希**：从
   `https://pypi.org/pypi/medxpert-reg-connector/<version>/json` 取 wheel 的
   sha256，写入 `server.json` → `packages[0].fileSha256`。必须取自已发布的
   wheel：`uv build` **不可字节复现**（zip 时间戳每次不同），本地算出的哈希
   描述的是没人下载的那个文件。
8. **打 tag**：`python tools/release_check.py --offline` 打印 ALL PASS 之后，
   才 `git tag vX.Y.Z && git push origin vX.Y.Z`。
9. **Registry**：用 `workflow_dispatch` 跑注册工作流，核对新条目带 `icons`、
   `_meta` 与新 `fileSha256`。
10. **GitHub Release**：说明取自 `CHANGELOG.md`，中英双语，英文在前。
11. **从产物取证**：从 `pypi.org` 装进干净 venv（绝不用 `dist/`），跑契约测试，
    输出贴进执行报告。

两条禁令，都是踩出来的：

- `git reset --hard` 会静默清掉未提交编辑。先 commit 或 stash。已经清空过两次。
- tag 不可移动。打错了只能发新版本，改不回来。
