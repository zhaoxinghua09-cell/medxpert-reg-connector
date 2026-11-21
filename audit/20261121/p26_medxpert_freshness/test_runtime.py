# -*- coding: utf-8 -*-
"""运行时一致性验证（在打补丁的工作副本上跑）。

验收标准（任务书 P0-1 原文）：
  检索接口和时效接口对同一个枢纽必须给出一致的风险状态，
  不允许出现一边 overdue、一边无警告。

本测试直接调用被打补丁的 MCP 工具函数（真实 fastmcp 4.2.0 装饰器），
而不是只测纯函数。
"""
import json
import sys
from pathlib import Path

WORK = Path(r"C:\Users\Administrator\AppData\Local\Temp\xlgd_audit\_mw")
sys.path.insert(0, str(WORK))

from medxpert_reg_connector import server  # noqa: E402

RESULTS = []


def case(cid, desc, got, want):
    ok = got == want
    RESULTS.append({"id": cid, "desc": desc, "got": str(got), "want": str(want), "pass": ok})
    print(f"{'PASS' if ok else 'FAIL'}  {cid}  {desc}\n       got={got} want={want}")


server.load_hubs()
hubs = json.loads(server.list_hubs())
fresh = json.loads(server.kb_freshness())
search = json.loads(server.search_regulation("UDI", top_k=5))

# I01 两个接口的 overdue 必须一致
kb_overdue = {r["hub_key"]: r["overdue"] for r in fresh["hubs"]}
list_overdue = {h["hub_key"]: h["overdue"] for h in hubs}
case("I01", "list_hubs 与 kb_freshness 的 overdue 完全一致",
     list_overdue == kb_overdue, True)

# I02 核心缺陷：freshness=ok 但 overdue=True 的反例必须存在且被标注
mixed = [r for r in fresh["hubs"] if r["freshness"] == "ok" and r["overdue"]]
case("I02", "存在 freshness=ok 但 overdue=True 的枢纽（原 bug 场景），且已被标注",
     len(mixed) > 0, True)

# I03 检索结果里同样的枢纽必须带 overdue=True
kb = {r["hub_key"]: r for r in fresh["hubs"]}
bad = [r for r in search["results"]
       if kb.get(r["hub_key"], {}).get("overdue") and not r.get("overdue")]
case("I03", "检索结果与时效接口对同一枢纽的 overdue 判定一致（不允许一边逾期一边无警告）",
     len(bad), 0)

# I04 只要命中逾期内容，必须出现 staleness_notice
case("I04", "命中逾期内容时返回 staleness_notice",
     "staleness_notice" in search, True)

# I05 每条命中都带完整六字段
need = {"as_of", "age_days", "freshness", "next_review", "overdue", "verified"}
case("I05", "检索结果每条都含 as_of/age_days/freshness/next_review/overdue/verified",
     all(need <= set(r.keys()) for r in search["results"]), True)

# I06 review_status 是枚举内的值
valid = {"ok", "aging", "stale", "overdue", "unknown", "invalid"}
case("I06", "review_status 取值都在枚举内",
     all(h.get("review_status") in valid for h in hubs), True)

# I07 未知枢纽（不在 registry）也必须 fail-closed，而不是静默 ok
meta = server._hub_meta("__no_such_hub__")
case("I07", "未登记枢纽 → overdue=True（fail-closed）", meta["overdue"], True)

n = sum(1 for r in RESULTS if r["pass"])
print(f"\n{'-'*50}")
print(f"hubs={len(hubs)}  freshness=ok&overdue={len(mixed)}  overdue_total={fresh['summary'].get('overdue')}")
print(f"cases={len(RESULTS)} pass={n} fail={len(RESULTS)-n}")
with open(Path(__file__).with_name("runtime_results.json"), "w", encoding="utf-8") as fh:
    json.dump({"total": len(RESULTS), "pass": n, "results": RESULTS}, fh, ensure_ascii=False, indent=2)
raise SystemExit(0 if n == len(RESULTS) else 1)
