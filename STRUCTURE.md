# STRUCTURE — 分层与改动代价

## 四层

| 层 | 文件 | 内容 |
|---|---|---|
| L1 内容 | `medxpert_reg_connector/data/references/*.md`（27 个枢纽 + `README.md`）、`data/registry.json` | 按生命周期 7 阶段组织的法规实务文档 |
| L2 溯源 | `data/sources.json`、`tools/check_sources.py` | 每条来源的地址与新鲜度；离线可跑 |
| L3 接口 | `server.py`、`server.json`、`mcp-config.json`、`smithery.yaml`、`lhm.plugin.json` | MCP 服务与各注册表清单 |
| L4 检验 | `tests/selftest_stdio.py`、`tools/{release_check,version_gate,attest}.py`、`.github/workflows/{ci,link-audit,version-gate}.yml` | 自检、链接审计、版本与发布门禁 |

## 改动代价

| 你想做 | 改哪里 | 必须重跑 | 必须同步 |
|---|---|---|---|
| 改一个枢纽内容 | `data/references/*.md` | `check_sources.py`、`link-audit.yml` | `sources.json` 的 `as_of`、`CHANGELOG.md` |
| 加一个枢纽 | 同上 + `registry.json` | 同上 | 27 → 28 的计数说明（README 与 `manifest.json`） |
| 改工具契约 | `server.py` | `selftest_stdio.py` | `server.json`、`mcp-config.json`、各注册表清单 |

## 边界

本仓是**内容 + 只读检索**；判定归 `lcas`，路径估算归 `medxpert-ortho-mcp`，证据链归 `uibc-core`。
三个 MCP 共用一套"数据带日期、来源可查"的约定。
