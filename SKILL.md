---
name: medxpert-reg-connector
slug: medxpert-reg-connector
title: MedXpert 全球法规连接器（MCP）
displayName: MedXpert·全球法规连接器
display_name: MedXpert·全球法规连接器
version: 1.0.0
category: knowledge-management
xiaping_category: ["学术研究"]
platforms: [WorkBuddy, QClaw, ima, Claude Code, Cursor]
author: 注册老炮@MedXpert
license: MIT
description: 医疗器械注册法规检索 MCP 连接器，覆盖 MDR/CE、FDA 510(k)、UDI、STED、分类界定、全球注册路径等场景；agent 通过 MCP 本地只读检索 NMPA/FDA/MDR/PMDA 等 27 枢纽法规知识库，无需联网外发、无需凭据。
description_en: An MCP connector for medical device regulatory retrieval, covering MDR/CE, FDA 510(k), UDI, STED, classification, and global registration pathways. Agents query the local read-only NMPA/FDA/MDR/PMDA 27-hub regulation knowledge base via MCP—no network egress, no credentials.
tags: ["医疗器械注册","MCP","reg-connector","NMPA","FDA 510(k)","MDR CE","UDI","STED","分类界定","全球注册","法规连接器","AI Agent"]
agent_created: true
---

# MedXpert 全球法规连接器（MCP）

## 1. 这是什么

reg-connector 是 MedXpert（美达信医疗）医械线的对外接口，把 MedXpert 全球法规知识库（27 份枢纽资料）封装成一个**本地只读 MCP Server**。你的 agent（WorkBuddy / Claude Code / Cursor 等任意 MCP 客户端）装上后，即可直接调用检索——零网络外发、零凭据。

它与已上架 skillhub 的知识技能 **medxpert-reg-hub** 互补：reg-hub 是"AI 读取型知识库"，给 agent 读；reg-connector 是"程序化运行时补全"，给 agent 调。两者配合，既能读又能查。

## 2. 能力清单

基于 FastMCP stdio 协议（依赖 `fastmcp`），提供 4 个工具：

- `list_hubs()` — 返回全部枢纽 JSON：`hub_key / title / sections / official_links / phase`。先调它拿到 key。
- `search_regulation(query: str, top_k: int = 5, hub_filter: str = None)` — 关键词检索（中/英/法规号，如 `UDI`、`510k`、`MDR PMS`、`委托生产`）。返回 `hub_key / title / section / snippet / score / links`。query 为空报错。
- `get_hub(hub_key: str)` — 取某枢纽完整内容（`content + official_links`）。
- `ask_classification(product: str)` — 产品分类与注册路径速查，返回 `matches + recommended_hubs + hint`。product 为空报错。

服务端标识：`SERVER_NAME = "medxpert-reg-connector"`，版本 1.0.0。

## 3. 一键安装（3 步）

① 把包解压/克隆到本地目录，确保 `references/` 与 `reg_connector_server.py` **同级**（开箱即用）。

② 安装依赖：

```bash
pip install fastmcp
```

③ 把下面片段加入宿主的 `mcp.json`（路径改成本地实际路径），重载 MCP 连接即生效。

```json
{
  "mcpServers": {
    "@nomos/medxpert/reg-connector": {
      "command": "<你的 python 解释器路径>",
      "args": ["<medxpert-reg-connector 包目录>/reg_connector_server.py"],
      "disabled": false,
      "description": "MedXpert 全球法规连接器：本地只读检索全球医疗器械法规知识库 (NMPA/FDA/MDR/PMDA 等 27 枢纽)"
    }
  }
}
```

知识库三级回退：① 包内 `references/` ② 环境变量 `REG_HUB_REFS` ③ 脚本同级 `../references`。

## 4. 调用示例

- `search_regulation("UDI")` → 命中 UDI 四体系（NMPA/FDA/EU/MDR）对照，返回枢纽、段落、片段与官方链接。
- `ask_classification("骨科金属接骨板")` → 返回分类匹配、推荐枢纽（如分类界定、技术文件/STED）与检索提示。
- `list_hubs()` → 返回 27 枢纽目录（含 hub_key、标题、章节、官方链接、阶段）。
- `get_hub("UDI全球标识枢纽")` → 取该枢纽完整正文与官方链接（key 为 references 文件名 stem，由 list_hubs 取得）。

## 5. 典型场景

- **注册路径速查**：新产品先用 `ask_classification` 找分类与路径，再 `get_hub` 看细节。
- **UDI 多国对照**：`search_regulation("UDI")` 一次拉齐中/美/欧要求。
- **临床评价·风险管理资料索引**：`search_regulation("临床评价")` / `("风险管理")`，定位知识库对应章节与官方出处。

## 6. 注意事项与边界

1. 返回为**知识库线索，非官方结论**；分类与注册路径须以官方分类库（NMPA/FDA/MDR）为准。
2. **本地只读、零外发**，适合内网/合规环境；不联网、不带凭据。
3. 知识库有更新后，需**重载 server** 才能生效。
4. 可用环境变量 `REG_HUB_REFS` 指向自定义知识库目录。

## 7. 许可与归属

MIT License，© 2026 注册老炮@MedXpert。

知识版权声明：本包所含合成知识与方法论归 MedXpert（美达信医疗）品牌所有，禁止复制、转售或用于模型训练。
