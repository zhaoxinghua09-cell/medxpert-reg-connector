# EVIDENCE-INDEX — medxpert-reg-connector

## 现状

| 级 | 结果 | 证据位置 | 说明 |
|---|---|---|---|
| L1 自我复现 | **有** | `tests/selftest_stdio.py`、`tools/check_sources.py`、`tools/attest.py`、`tools/release_check.py`、`tools/version_{check,gate}.py`、`.github/workflows/{ci,link-audit,version-gate}.yml` | 有 stdio 自检、来源新鲜度检查、链接审计、版本门禁与发布检查 |
| L2 异体审查 | **0（已取证，不成立）** | `安全审计报告.md`、`ATTESTATION.md` | 2026-11-18 核对：报告写明"审计方式：静态人工审查（本机 `skills-security-check` 仅含 SKILL.md、无独立扫描脚本；按流程等价检查项**逐项自评**）"，结论 P2 低风险。**自评，不计 L2**；`ATTESTATION.md` 同为自证 |
| L3 第二实现 | **0** | — | 无独立实现 |
| L3.5 外部语料 | **0** | — | 27 个"枢纽"文档为自行编纂，未与官方数据库抽样比对 |
| L4 外部节点 | **0** | — | 已上 PyPI / LobeHub / Smithery（`smithery.yaml`、`lhm.plugin.json`），无第三方使用证据可指认 |

## 已知不硬的地方

1. **27 个枢纽的"内容对不对"没有机器判据。** `check_sources.py` 检查的是**来源可访问性与新鲜度**，不是条文与官方文本的一致性。
2. **`ATTESTATION.md` 是自证。** 自身声明不构成外部证据，除非其中写明可独立验证的第三方式（例如可复跑的校验步骤 + 公开哈希）。
3. **中英版本并行维护。** `README.md` 与 `README.en.md` 双份，条款引用以中文为准，英文滞后时易误引。

## 维护约定

- 任何枢纽文档更新 → 同步 `sources.json` 的 `as_of` → 更新本表 L1 行。
- 引入外部审查 → 先落审查者标识与范围，再升 L2。
- 等级只降不升。
