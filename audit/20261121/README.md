# audit/20261121 — MedXpert 时效门禁审计产物

性质：**只读审计与候选方案**，未修改主分支、未发布。

## 内容

- `p26_medxpert_freshness/` — 法规检索时效统一候选补丁
  - `freshness.py` — 统一元数据函数（`as_of` / `age_days` / `freshness` / `next_review` / `overdue` / `verified`）
  - `freshness.patch` — 对 `kb_freshness()` 与 `search_regulation()` 两套判断的合并补丁
  - `test_freshness.py`（12/12）、`test_runtime.py`（运行时 7/7）
  - `runtime_results.json` — 实跑结果

## 核心问题（FACT）

原实现中 `kb_freshness()` 用 `next_review` 判逾期，`search_regulation()` 用 `as_of` 的 freshness 判是否告警，**两套口径不一致**：可出现"检索接口无警告、时效接口判定 overdue"的矛盾状态。

## 复现

```bash
cd audit/20261121/p26_medxpert_freshness && python test_freshness.py && python test_runtime.py
```

## 边界

- 补丁未应用到 main；未知日期、缺失字段、未来日期一律 fail-closed。
- 本目录结论不代表法律意见，仅为工具链审计记录。
