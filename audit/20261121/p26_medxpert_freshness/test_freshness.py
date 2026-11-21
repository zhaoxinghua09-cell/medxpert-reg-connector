# -*- coding: utf-8 -*-
"""MedXpert 时效统一 —— 边界测试（对应任务书 P0-1 第 6、7 项）。"""
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from freshness import needs_warning, review_meta, warning_text  # noqa: E402

TODAY = datetime.date(2026, 11, 19)
RESULTS = []


def case(cid, desc, got, want):
    ok = got == want
    RESULTS.append({"id": cid, "desc": desc, "got": str(got), "want": str(want), "pass": ok})
    print(f"{'PASS' if ok else 'FAIL'}  {cid}  {desc}\n       got={got} want={want}")


# F01 核心 bug 复现：as_of 未超 90 天，但 next_review 已过期
m = review_meta({"as_of": "2026-08-27", "next_review": "2026-09-03"}, TODAY)
case("F01", "as_of 84 天(ok) 但 next_review 已过 → overdue=True",
     (m["freshness"], m["overdue"], m["review_status"]), ("ok", True, "overdue"))
case("F02", "同一状态必须触发警告", needs_warning(m), True)

# F03 正常新鲜
m = review_meta({"as_of": "2026-11-10", "next_review": "2027-02-10"}, TODAY)
case("F03", "as_of 9 天 + 未过复核日 → ok / 不警告",
     (m["freshness"], m["overdue"], needs_warning(m)), ("ok", False, False))

# F04 aging
m = review_meta({"as_of": "2026-05-01", "next_review": "2027-01-01"}, TODAY)
case("F04", "as_of 202 天 → stale，需警告", (m["freshness"], needs_warning(m)), ("stale", True))

# F05 缺 as_of
m = review_meta({"next_review": "2027-01-01"}, TODAY)
case("F05", "缺 as_of → freshness=unknown 且警告",
     (m["freshness"], m["review_status"], needs_warning(m)), ("unknown", "unknown", True))

# F06 缺 next_review → fail-closed
m = review_meta({"as_of": "2026-11-10"}, TODAY)
case("F06", "缺 next_review → overdue=True（fail-closed）",
     (m["overdue"], m["review_status"], "next_review_missing" in m["reason_codes"]),
     (True, "overdue", True))

# F07 日期格式异常
m = review_meta({"as_of": "2026/11/10", "next_review": "2027-01-01"}, TODAY)
case("F07", "as_of 格式异常 → freshness=invalid 且警告",
     (m["freshness"], needs_warning(m)), ("invalid", True))

# F08 next_review 格式异常 → 不得视为未逾期
m = review_meta({"as_of": "2026-11-10", "next_review": "next week"}, TODAY)
case("F08", "next_review 异常 → overdue=True",
     m["overdue"], True)

# F09 未来日期
m = review_meta({"as_of": "2026-12-25", "next_review": "2027-06-01"}, TODAY)
case("F09", "as_of 在未来 → age_days=None 且标记 as_of_future",
     (m["age_days"], "as_of_future" in m["reason_codes"]), (None, True))

# F10 时区/带时间戳
m = review_meta({"as_of": "2026-11-10T00:00:00Z", "next_review": "2027-01-01"}, TODAY)
case("F10", "带时间戳的 as_of → 当前实现判 invalid（应在上游规范化）",
     m["freshness"], "invalid")

# F11 极旧日期
m = review_meta({"as_of": "2015-01-01", "next_review": "2016-01-01"}, TODAY)
case("F11", "超 10 年的 as_of → unknown（超出可信界）",
     m["freshness"], "unknown")

# F12 警告文案包含两个维度
m = review_meta({"as_of": "2026-08-27", "next_review": "2026-09-03"}, TODAY)
case("F12", "警告文案同时给出逾期与天数",
     ("已过复核日期" in warning_text(m), "84 天" in warning_text(m)), (True, True))

n = sum(1 for r in RESULTS if r["pass"])
print(f"\n{'-'*50}\ncases={len(RESULTS)} pass={n} fail={len(RESULTS)-n}")
raise SystemExit(0 if n == len(RESULTS) else 1)
