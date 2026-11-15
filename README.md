# MedXpert Global Regulatory Connector (reg-connector)

[![PyPI](https://img.shields.io/pypi/v/medxpert-reg-connector)](https://pypi.org/project/medxpert-reg-connector/)
[![MCP Badge](https://lobehub.com/badge/mcp/zhaoxinghua09-cell-medxpert-reg-connector)](https://lobehub.com/mcp/zhaoxinghua09-cell-medxpert-reg-connector)
[![CI](https://github.com/zhaoxinghua09-cell/medxpert-reg-connector/actions/workflows/ci.yml/badge.svg)](https://github.com/zhaoxinghua09-cell/medxpert-reg-connector/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**Read-only local MCP server for global medical-device regulation** — 27 knowledge hubs (NMPA / FDA / EU MDR / PMDA + orthopedic global registration paths) exposed as 7 tools, with a built-in freshness guard.

> 中英双语说明：本文英文在前、中文在后。`mcp-name: io.github.zhaoxinghua09-cell/medxpert-reg-connector`

---

## English

### What it is

A local, read-only MCP (Model Context Protocol) server over a curated medical-device regulatory knowledge base. Any MCP host — Claude Desktop, Cursor, LobeHub, WorkBuddy — can call its tools directly to look up registration paths, classification clues, UDI cross-jurisdiction mappings, and knowledge freshness.

- **Zero egress, zero credentials, zero side effects** at runtime
- **7 tools**, every one annotated `readOnlyHint: true`
- **27 hubs** shipped inside the wheel — `pip install` is enough, nothing else to download
- **Freshness guard**: every search result carries `as_of` / `age_days` / `freshness`
- **Copyright-safe**: paid standards (ISO/IEC/ASTM/GB) are never stored — only numbers and official lookup entry points

### Install

```bash
# recommended — the knowledge base is bundled, no extra steps
uvx medxpert-reg-connector
# or
pip install medxpert-reg-connector
medxpert-reg-connector
```

Host config (`mcp.json` / `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "medxpert-reg-connector": {
      "command": "python",
      "args": ["-m", "medxpert_reg_connector"]
    }
  }
}
```

Docker (no Python setup on the host):

```bash
docker build -t medxpert-reg-connector .
docker run -i --rm medxpert-reg-connector
```

Optional: point `REG_HUB_REFS` at your own knowledge-base directory to override the bundled one.

### Tools

| Tool | Input | Annotations | Purpose |
|---|---|---|---|
| `list_hubs()` | — | read-only | List all 27 hubs with `phase` and freshness |
| `search_regulation(query, top_k=5, hub_filter=None)` | keywords (zh/en/regulation IDs) | read-only | Retrieve hub / section / snippet / score / links |
| `get_hub(hub_key)` | hub key from `list_hubs` | read-only | Full text of one hub + official links + standards pointers |
| `ask_classification(product)` | product description | read-only | Classification clues + recommended hubs + registration path |
| `kb_freshness()` | — | read-only | Per-hub `as_of` / `age_days` / `freshness` / overdue list |
| `reg_delta(since, jurisdiction, limit)` | date / jurisdiction | read-only | Regulatory change log recorded by the polling pipeline |
| `kb_sources(jurisdiction)` | jurisdiction (optional) | read-only | Official source registry: authority / channel / cadence / copyright class |

### Verified output (real run, 2026-11-15)

```text
search_regulation("UDI", top_k=3)
-> 3 hits, top1 = UDI全球标识枢纽 (CN/US/EU/JP cross-reference: GS1-MA, GUDID, EUDAMED, KikiDB)

kb_freshness()
-> {hubs: 27, ok: 27, aging: 0, stale: 0, unknown: 0, overdue: 27}
```

### Scope and limits

1. Results are **knowledge-base leads, not regulatory conclusions** — always confirm against the target market's official classification database (NMPA / FDA / MDR).
2. Local and read-only; no network egress at runtime (the polling pipeline `refresh_scan.py` is a separate, opt-in script).
3. Paid standards are never ingested — only numbers + official lookup entry points.
4. Reload the server after refreshing the knowledge base.

### License

- **Code**: Apache-2.0 (see [LICENSE](LICENSE)), copyright 赵兴华 / Steven Zhao·China (ORCID 0009-0001-0512-1237).
- **Knowledge base** (`medxpert_reg_connector/data/references/`, methodology, taxonomy): **All Rights Reserved** (see [CONTENT-LICENSE](CONTENT-LICENSE)) — citation with attribution is allowed; copying, redistribution, resale, or training use is not.
- MedXpert / SynomosAI / LGD are project marks; no legal entity or trademark registration is claimed.
- Not regulatory, legal, or registration-agent advice.

---

## 中文

### 这是什么

把经过整理的医疗器械法规知识库封装成本地只读 MCP 服务器。任意 MCP 客户端（Claude Desktop / Cursor / LobeHub / WorkBuddy）都可直接调用其工具，查询注册路径、分类线索、UDI 多辖区对照与知识库时效。

- 运行时**零外发、零凭据、零副作用**
- **7 个工具**，全部声明 `readOnlyHint: true`
- **27 个枢纽**随 wheel 分发——`pip install` 装完即可检索，无需另外克隆
- **时效护栏**：每条检索结果都带 `as_of` / `age_days` / `freshness`
- **版权安全**：付费标准（ISO/IEC/ASTM/GB）永不入库，只存编号与官方查询入口

### 安装

```bash
uvx medxpert-reg-connector        # 推荐：知识库已随包分发
pip install medxpert-reg-connector
medxpert-reg-connector
```

客户端配置见上方 `mcp.json` 片段；也可用仓库内 `Dockerfile` 构建镜像，免装 Python 环境。需要接自建知识库时，用环境变量 `REG_HUB_REFS` 指向自定义目录。

### 工具

7 个工具的分工见上方英文表（入参、注解、用途一致）。核心三件套：

- `list_hubs` / `get_hub` —— 知识库全景与单枢纽全文
- `search_regulation` / `ask_classification` —— 关键词检索与产品分类速查
- `kb_freshness` / `reg_delta` / `kb_sources` —— 时效自检、变更流水、官方源注册表

### 实跑返回（2026-11-15 实测）

```text
search_regulation("UDI", top_k=3)
-> 命中 3 条，top1 = UDI全球标识枢纽（中/美/欧/日四体系：GS1-MA、GUDID、EUDAMED、KikiDB）

kb_freshness()
-> {hubs: 27, ok: 27, aging: 0, stale: 0, unknown: 0, overdue: 27}
```

### 边界

1. 返回为**知识库线索，不是法规结论**——分类与注册路径须以目标市场官方分类库（NMPA 分类目录 / FDA 产品分类库 / MDR 分类规则）为准。
2. 本地只读，运行时不联网（巡检脚本 `refresh_scan.py` 为独立、可选的手动流程）。
3. 付费标准全文不入库，只存编号 + 官方查询入口。
4. 知识库更新后需重载 server。

### 许可与归属

- **代码** Apache-2.0（见 [LICENSE](LICENSE)），版权归「赵兴华 / Steven Zhao·China（ORCID 0009-0001-0512-1237）」。
- **知识库/方法论/分类体系** 保留所有权利（详见 [CONTENT-LICENSE](CONTENT-LICENSE)）：可注明出处引用，不得复制、再分发、转售或用于模型训练。
- MedXpert / SynomosAI / LGD 为项目标识，未申请实体注册与商标注册；出现仅作来源标识，不构成对法人实体或商标权的任何主张。
- 本仓库内容不构成法规意见、法律意见或注册代理服务；关键数据以监管机构最新发布为准。

**联系**：zhaoxinghua09@gmail.com ｜ ORCID 0009-0001-0512-1237
