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

### Real output (captured 2026-11-15, not hand-written prose)

`search_regulation("UDI", top_k=3)`:

```json
{"query": "UDI", "count": 3,
 "results": [{"hub_key": "UDI全球标识枢纽", "hub_title": "UDI全球标识枢纽",
   "section": "四体系总览对照", "score": 30.0,
   "links": ["https://udi.nmpa.gov.cn", "https://zwfw.nmpa.gov.cn/...", "..."],
   "as_of": "2026-08-27", "age_days": 80, "freshness": "ok"}],
 "disclaimer": "知识库线索，非法规结论…"}
```

`ask_classification("骨科金属接骨板")`:

```json
{"product": "骨科金属接骨板",
 "recommended_hubs": [
   {"hub_key": "骨科手术器械_全球注册路径汇编", "freshness": "ok"},
   {"hub_key": "注册工程师资料枢纽", "freshness": "ok"},
   {"hub_key": "注册周期费用有效期对比枢纽", "freshness": "ok"}],
 "hint": "分类建议需以目标市场官方分类库为准（NMPA 分类目录 / FDA 产品分类库 / MDR 分类规则），以上仅为知识库线索。"}
```

`kb_freshness()` — the guard reports lag rather than hiding it:

```json
{"policy": {"ok_days": 90, "aging_days": 180},
 "summary": {"hubs": 27, "ok": 27, "aging": 0, "stale": 0, "unknown": 0, "overdue": 27},
 "advice": "27 个枢纽的 next_review 日期已过，需人工复核官方来源后更新 as_of"}
```

`reg_delta(since="2026-09-01")`:

```json
{"since": "2026-09-01", "count": 0, "deltas": [],
 "how_to_produce": "按 sources.json 定时巡检各官方源（只拉元数据）→ 与 registry 比对 → 人工核验 → 追加至 registry.deltas"}
```

> **Honest disclosure**: `overdue: 27` means the next-review dates have elapsed and no human re-verification has been recorded yet. The tool states this in every freshness answer instead of silently claiming freshness. A 2026-11-15 liveness check of the 15 official source channels returned 12 reachable and 3 blocked by anti-bot (NMPA x2 → 412, ISO → 403); reachability is not content freshness, so the dates stay unchanged until a reviewer signs off.

### The 27 hubs (from `list_hubs()`, 2026-11-15)

| # | hub_key | title | sections | links | phase |
|---|---|---|---|---|---|
| 1 | `CN_医疗器械委托生产MAH实务` | 中国医疗器械委托生产（注册人制度）实务 | 10 | 3 | 综合 |
| 2 | `EU_EUDAMED数据库实务` | EUDAMED 欧盟医疗器械数据库实务 | 8 | 5 | 综合 |
| 3 | `EU_MDR上市后监管PMS实务` | EU MDR 上市后监管（PMS）实务 | 9 | 3 | 上市后监管 |
| 4 | `FDA_UDI实施实务` | FDA UDI 实施实务 | 9 | 5 | 综合 |
| 5 | `FDA创伤敷料供应链穿透检查枢纽` | FDA 质量体系核查下的敷料供应链溯源（注册老炮知识库） | 6 | 3 | 质量体系 |
| 6 | `GMP质量体系与验证枢纽` | GMP / 质量体系与验证枢纽 | 8 | 9 | 技术文件 |
| 7 | `UDI全球标识枢纽` | UDI全球标识枢纽 | 2 | 16 | 分类与路径 |
| 8 | `上市后监管枢纽` | 上市后监管枢纽 | 7 | 7 | 上市后监管 |
| 9 | `临床评价枢纽` | 临床评价枢纽 | 8 | 9 | 分类与路径 |
| 10 | `原材料供应商合规枢纽` | 原材料供应商合规枢纽 | 2 | 10 | 综合 |
| 11 | `变更延续管理枢纽` | 变更·延续管理枢纽 | 8 | 5 | 质量体系 |
| 12 | `售后服务枢纽` | 售后服务枢纽 | 8 | 3 | 质量体系 |
| 13 | `审评核查获证枢纽` | 审评核查获证枢纽 | 10 | 8 | 质量体系 |
| 14 | `市场准入与销售枢纽` | 市场准入与销售枢纽 | 9 | 6 | 上市后监管 |
| 15 | `技术文件STED撰写枢纽` | 技术文件STED撰写枢纽 | 2 | 9 | 技术文件 |
| 16 | `枢纽总览_全生命周期7阶段纲领` | 枢纽总览 · 以全生命周期 7 阶段为纲领 | 11 | 0 | 立项与可行性 |
| 17 | `标签与IFU枢纽` | 标签与 IFU 枢纽 | 7 | 5 | 综合 |
| 18 | `注册周期费用有效期对比枢纽` | 注册周期费用有效期对比枢纽 | 2 | 8 | 审评获批 |
| 19 | `注册工程师资料枢纽` | 医疗器械注册工程师 · 资料枢纽（资料索引） | 36 | 62 | 立项与可行性 |
| 20 | `注册检验与申报实操枢纽` | 注册检验与申报实操枢纽 | 12 | 10 | 分类与路径 |
| 21 | `灭菌包装验证枢纽` | 灭菌·包装验证枢纽 | 8 | 7 | 技术文件 |
| 22 | `生物相容性测试规划枢纽` | 生物相容性测试规划枢纽 | 7 | 4 | 综合 |
| 23 | `设计开发控制枢纽` | 设计开发控制枢纽 | 7 | 6 | 立项与可行性 |
| 24 | `软件人因枢纽` | 软件·人因枢纽（IEC 62304 · IEC 62366 · 网络安全） | 10 | 6 | 分类与路径 |
| 25 | `需求调研与立项枢纽` | 需求调研与立项枢纽 | 10 | 5 | 立项与可行性 |
| 26 | `风险管理枢纽` | 风险管理枢纽（ISO 14971） | 7 | 9 | 审评获批 |
| 27 | `骨科手术器械_全球注册路径汇编` | 骨科手术器械 — 全球医疗器械注册路径汇编（含拉美与东南亚） | 15 | 17 | 分类与路径 |

### How this differs from `medxpert-reg-hub`

| | `medxpert-reg-connector` (this) | `medxpert-reg-hub` |
|---|---|---|
| Form | MCP server over stdio | agent skill (prompt-side knowledge) |
| How an agent uses it | **calls** tools; the server does the retrieval | **reads** skill text into context |
| Context cost | only the returned hits enter context | the loaded skill text occupies context |
| Freshness signal | per-result `as_of` / `age_days` / `freshness` | none at the protocol level |
| Install | `uvx medxpert-reg-connector` (knowledge base inside the wheel) | skill directory in the host |

They are complementary: use the skill for standing instructions, this server for on-demand lookup.

### Scope and limits

1. Results are **knowledge-base leads, not regulatory conclusions** — always confirm against the target market's official classification database (NMPA / FDA / MDR).
2. Local and read-only; no network egress at runtime (the polling pipeline `refresh_scan.py` is a separate, opt-in script).
3. Paid standards are never ingested — only numbers + official lookup entry points.
4. Reload the server after refreshing the knowledge base.
5. **27 of 27 hubs are flagged `overdue` right now** — the review clock (90 days) has run out and no human re-verification is recorded. Treat every answer as a lead to check, not as current law.

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

### 实跑返回（2026-11-15 抓取，非手写文案）

四个典型调用见上方英文「Real output」小节（`search_regulation("UDI")`、`ask_classification("骨科金属接骨板")`、`kb_freshness()`、`reg_delta("2026-09-01")`），均为当日真实 JSON 返回的节选，字段与结构未改写。

27 个枢纽的完整清单（编号、hub_key、标题、章节数、官链数、阶段）见上方英文表——同一份数据由 `list_hubs()` 直接产生。

> **如实披露**：`overdue: 27` 表示 27 个枢纽的复核日期已过、尚无人工复核记录。工具在每次时效回答中都明说这一点，而不是假装新鲜。2026-11-15 对 15 个官方来源通道做过可用性实测：12 个可达，3 个被反爬拦截（NMPA ×2 → 412、ISO → 403）；可达不等于内容新鲜，因此复核日期在有人签字前不改。

### 与 `medxpert-reg-hub` 的分工

| 对比项 | `medxpert-reg-connector`（本仓） | `medxpert-reg-hub` |
|---|---|---|
| 形态 | stdio 的 MCP 服务器 | agent 技能（提示侧知识） |
| agent 用法 | **调用**工具，检索在服务器侧完成 | **读入**技能文本到上下文 |
| 上下文开销 | 只有命中的片段进入上下文 | 载入的技能文本占用上下文 |
| 时效信号 | 每条结果带 `as_of` / `age_days` / `freshness` | 协议层没有 |
| 安装 | `uvx medxpert-reg-connector`（知识库在 wheel 内） | 装进宿主的技能目录 |

二者互补：常驻指引用技能，按需检索用这个服务器。

### 边界

1. 返回为**知识库线索，不是法规结论**——分类与注册路径须以目标市场官方分类库（NMPA 分类目录 / FDA 产品分类库 / MDR 分类规则）为准。
2. 本地只读，运行时不联网（巡检脚本 `refresh_scan.py` 为独立、可选的手动流程）。
3. 付费标准全文不入库，只存编号 + 官方查询入口。
4. 知识库更新后需重载 server。
5. **当前 27/27 枢纽均为 `overdue`**：90 天复核窗口已过且无人工复核记录。请把每个回答当作待核实的线索，而不是现行法条。

### 许可与归属

- **代码** Apache-2.0（见 [LICENSE](LICENSE)），版权归「赵兴华 / Steven Zhao·China（ORCID 0009-0001-0512-1237）」。
- **知识库/方法论/分类体系** 保留所有权利（详见 [CONTENT-LICENSE](CONTENT-LICENSE)）：可注明出处引用，不得复制、再分发、转售或用于模型训练。
- MedXpert / SynomosAI / LGD 为项目标识，未申请实体注册与商标注册；出现仅作来源标识，不构成对法人实体或商标权的任何主张。
- 本仓库内容不构成法规意见、法律意见或注册代理服务；关键数据以监管机构最新发布为准。

**联系**：zhaoxinghua09@gmail.com ｜ ORCID 0009-0001-0512-1237
