# MedXpert 全球法规连接器（reg-connector）

MedXpert（美达信医疗）医械线对外接口。将全球医疗器械法规知识库（27 份枢纽资料，**NMPA / FDA / EU MDR / PMDA 及骨科全球注册路径**）封装为**本地只读 MCP Server**，供任意 MCP 客户端（WorkBuddy / Claude Code / Cursor 等）的 agent 直接调用检索。

- 🔒 **本地只读、零网络外发、零凭据**
- 📚 27 枢纽法规知识库，自研中文友好 BM25 近似检索
- 🧰 4 个工具：`list_hubs` / `search_regulation` / `get_hub` / `ask_classification`

> 与已上架的 `medxpert-reg-hub` 知识技能互补：reg-hub 供 agent **读取**知识，reg-connector 供 agent **调用**检索。

## 快速开始

```bash
pip install fastmcp
```

将本仓库克隆到本地，然后在宿主 `mcp.json` 中加入：

```json
{
  "mcpServers": {
    "@nomos/medxpert/reg-connector": {
      "command": "<你的 python 解释器路径>",
      "args": ["<仓库目录>/reg_connector_server.py"],
      "disabled": false,
      "description": "MedXpert 全球法规连接器：本地只读检索全球医疗器械法规知识库 (NMPA/FDA/MDR/PMDA 等 27 枢纽)"
    }
  }
}
```

重载 MCP 连接即可生效。`references/` 需与 `reg_connector_server.py` 同级（开箱即用）；也可用环境变量 `REG_HUB_REFS` 指向自定义知识库目录。

## 工具能力

| 工具 | 入参 | 返回 | 用途 |
|------|------|------|------|
| `list_hubs()` | 无 | 全部枢纽（hub_key / title / sections / official_links / phase） | 列出知识库全景 |
| `search_regulation(query, top_k=5, hub_filter=None)` | 关键词（中/英/法规号，如 `UDI`/`510k`/`MDR PMS`/`委托生产`） | 命中 hub_key/title/section/snippet/score/links | 法规条目检索 |
| `get_hub(hub_key)` | 枢纽 key（先由 `list_hubs` 取得） | 完整正文 + 官方链接 | 取某枢纽全量内容 |
| `ask_classification(product)` | 产品描述（如 `骨科金属接骨板`） | matches + recommended_hubs + hint | 分类与注册路径速查 |

## 调用示例

```python
# 列出全部 27 枢纽
list_hubs()

# 检索 UDI 多国对照
search_regulation("UDI", top_k=3)
# → 命中「UDI全球标识枢纽」四体系对照：中/美/欧/日并行（GS1/MA/阿里健康、GUDID、EUDAMED、KikiDB）

# 骨科接骨板分类与路径
ask_classification("骨科金属接骨板")
# → 推荐枢纽：骨科手术器械_全球注册路径汇编、注册工程师资料枢纽、注册周期费用有效期对比枢纽…
```

## 典型场景

- 注册路径速查（中国 II 类周期/费用、真实注册证示例）
- UDI 中/美/欧/日四体系对照
- 临床评价、风险管理（ISO 14971）资料索引
- 骨科全球注册路径汇编

## 注意事项与边界

1. **返回为知识库线索，非官方结论。** 分类与注册路径须以目标市场官方分类库（NMPA / FDA / MDR）为准。
2. 本地只读、零外发，适合内网 / 合规环境。
3. 知识库更新后需重载 server。
4. 可选 `REG_HUB_REFS` 指向自定义知识库目录。

## 许可与归属

MIT License © 注册老炮@MedXpert。知识版权声明：合成知识与方法论归品牌所有，禁止复制、转售或用于模型训练。
