# MedXpert P0-1 时效统一 —— 候选补丁包（未应用）

**性质**：候选 PR 方案。**未修改任何仓库、未提交、未推送。**
**日期**：2026-11-19

---

## 1. 仓库与分支

- 仓库：`zhaoxinghua09-cell/medxpert-reg-connector`
- 基线：`b1c329e`（本地克隆 `/Temp/xlgd_audit/medxpert-reg-connector`）
- 目标分支：待建（建议 `fix/p0-1-freshness-unification`，需批准）
- 补丁生成方式：在**工作副本** `/Temp/xlgd_audit/_mw` 上修改后 `git diff`，原始克隆零改动

---

## 2. 原始问题（FACT，含行号）

| # | 问题 | 位置 |
|---|---|---|
| 1 | `_freshness()` 只看 `as_of`，警告仅覆盖 aging/stale，**完全不看 `next_review`** | `server.py:110-131` |
| 2 | `_hub_meta()` 不返回 `next_review` / `overdue` / `review_status` | `server.py:133-147` |
| 3 | `search_regulation()` 的警告条件是 `freshness in ("aging","stale")` —— **freshness=ok 但已逾期时零警告** | `server.py:330-341` |
| 4 | `kb_freshness()` 自己另算一套 overdue（与 1、2 分叉） | `server.py:427-449` |
| 5 | `kb_freshness()` 直接 `datetime.date.fromisoformat(nr)`，**日期异常会抛异常使工具不可用** | `server.py:437` |
| 6 | `list_hubs()` 不返回 overdue / next_review / review_status | `server.py:291-307` |
| 7 | 未登记枢纽默认 `unknown` 且无 overdue，**不是 fail-closed** | `server.py:146-147` |

**改前实测**（原仓，`load_hubs` 后直接调用工具函数）：

```
list_hubs 有 overdue 字段: False
search 结果有 overdue 字段: False
staleness_notice 出现: False
未登记枢纽 _hub_meta: unknown | overdue 字段存在: False
```

即：27 个枢纽全部 `overdue=true`（`next_review` 为 2026-09-03 / 09-26，today=2026-11-19），
但检索接口一条警告都不会给。

---

## 3. 实际修改文件

| 文件 | 类型 | 说明 |
|---|---|---|
| `medxpert_reg_connector/freshness.py` | **新增** | 统一裁决模块（纯函数，无 MCP/网络依赖） |
| `medxpert_reg_connector/server.py` | 修改 | 6 处：导入统一模块、`_hub_meta` 改走 `review_meta`、search 结果补字段、警告条件改 `needs_warning`、list_hubs 补字段、kb_freshness 去掉重复计算与崩溃点 |

改动量：`1 file changed, 20 insertions(+), 12 deletions(-)`（server.py），外加新增 1 个模块。

---

## 4. 修改前后差异（关键语义）

| 场景 | 改前 | 改后 |
|---|---|---|
| `as_of` 84 天（ok）+ `next_review` 已过 | 无警告 | `overdue=true`、`review_status=overdue`、检索带 `staleness_notice` |
| `next_review` 缺失 | 视为"未逾期" | `overdue=true`（fail-closed），`reason_codes` 含 `next_review_missing` |
| `next_review` 格式异常 | **抛异常** | `overdue=true`，`review_status=overdue` |
| `as_of` 缺失/异常/未来 | `unknown`，不影响放行 | `freshness=unknown/invalid` + `overdue=true`，一律警告 |
| 未登记枢纽 | `unknown` 且无 overdue | `overdue=true`（fail-closed） |
| 三接口一致性 | 各算一套 | 全部来自 `review_meta()` 单一真源 |

---

## 5. 测试命令与结果

```powershell
# 1) 单元（纯函数，12 例：边界/缺失/异常/未来日期/时区）
cd proposals\p26_medxpert_freshness
python test_freshness.py

# 2) 运行时（在补丁副本上，真实 fastmcp 4.2.0 装饰器，7 例）
python test_runtime.py

# 3) 编译检查
python -m py_compile medxpert_reg_connector\server.py medxpert_reg_connector\freshness.py
```

| 组 | 用例 | 结果 |
|---|---|---|
| `test_freshness.py` | 12 | **12/12 PASS** |
| `test_runtime.py`（补丁副本） | 7 | **7/7 PASS** |
| `py_compile` | 2 文件 | exit 0 |

运行时实测输出：

```
hubs=27  freshness=ok&overdue=27  overdue_total=27
I01 list_hubs 与 kb_freshness 的 overdue 完全一致  PASS
I02 存在 freshness=ok 但 overdue=True 的枢纽，且已被标注  PASS
I03 检索结果与时效接口对同一枢纽的 overdue 判定一致  PASS
I04 命中逾期内容时返回 staleness_notice  PASS
I05 每条命中含 as_of/age_days/freshness/next_review/overdue/verified  PASS
I06 review_status 取值都在枚举内  PASS
I07 未登记枢纽 → overdue=True（fail-closed）  PASS
```

---

## 6. 验收标准对照（任务书原文）

> 检索接口和时效接口对同一个枢纽给出一致的风险状态，不允许出现一边 overdue、一边无警告。

- I01 + I03 直接验证该条：**通过**。
- 任务书第 6 项（`as_of` 未超 90 天但 `next_review` 已过期）→ F01/F02 + I02：**通过**。
- 任务书第 7 项（日期异常、时区、未来日期、缺失字段）→ F05/F07/F08/F09/F10/F11：**通过**。
- 任务书第 1 项（增加 review_status / overdue）→ 字段已加：**通过**。
- 任务书第 2 项（检索返回六字段）→ I05：**通过**。
- 任务书第 3 项（overdue=true 即使 freshness=ok 也警告）→ I04：**通过**。
- 任务书第 4 项（unknown/缺失/异常 fail-closed）→ F05/F06/F07/F08 + I07：**通过**。
- 任务书第 5 项（四接口统一元数据函数）→ 四接口均调用 `_hub_meta()`→`review_meta()`：**通过**。
- 任务书第 8 项（README 示例与接口输出一致）→ **未做**，见 §7。

---

## 7. 未做的事（必须写清）

1. **README 真实示例未同步**：README 里的接口输出样例仍是旧字段。需要等补丁合并后重新截取真实输出，否则就是"文档与实现不一致"——我不做假的示例。
2. **未跑真实 MCP transport（stdio / HTTP）**：本轮是直接调用被装饰的函数，未通过 MCP 协议端到端。这属于 **NOT VERIFIED**。
3. **`_freshness()` 保留未删**：作为兼容壳，避免其他模块导入失败；建议后续单开一个小 PR 删除。
4. **`as_of` 带时间戳（`2026-11-10T00:00:00Z`）目前判 invalid**：应在数据生产侧规范化为纯日期，避免误判。这是设计取舍，不是 bug。

---

## 8. 剩余风险

| 风险 | 级别 | 说明 |
|---|---|---|
| fail-closed 会让 27/27 枢纽全部报逾期 | P1（可用性） | 这是**预期行为**：数据确实逾期。但会让调用方看到大量警告，需要配合数据侧复核 |
| 上游若存在 `next_review` 与 `as_of` 语义不同的枢纽 | P2 | 需人工抽查 2-3 个枢纽确认语义 |
| 补丁未在 CI 跑 | P1 | 仍需提交 PR 后由 CI 验证 |

---

## 9. 是否需要独立复核 / 审批

- **独立复核**：需要。理由：改的是"何时警告用户"的判定逻辑，属于安全相关语义；建议由非作者复核 §4 的六个场景。
- **Steven Zhao 审批**：需要。合并、推送、建分支均须单独批准。本包只到"补丁可应用 + 测试可复现"为止。

---

## 10. 如何应用（待批准后）

```powershell
git checkout -b fix/p0-1-freshness-unification
git apply proposals/p26_medxpert_freshness/freshness.patch
Copy-Item proposals/p26_medxpert_freshness/freshness.py medxpert_reg_connector/
python test_freshness.py
python test_runtime.py     # 需先把 WORK 指向本仓
```

补丁由 `git diff` 生成，基线 `a77c4b4`（server.py blob）。
