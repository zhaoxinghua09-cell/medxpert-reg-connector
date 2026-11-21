# -*- coding: utf-8 -*-
"""统一时效元数据（MedXpert P0-1 候选补丁核心模块）。

设计要点：
1. **单一真源**：as_of / next_review 两个日期由同一函数裁决，不再各算一套。
2. **fail-closed**：日期缺失、格式异常、未来日期，一律判为"不可信"，overdue=True。
3. **可解释**：返回原因码（reason_codes），UI/审计可逐条展示为什么判逾期。
4. 不依赖 MCP、不依赖网络，纯函数，可直接单测。
"""
import datetime
from typing import Optional

POLICY = {"ok_days": 90, "aging_days": 180}

# 判定优先级（数值越大越严重）
SEVERITY = {"ok": 0, "aging": 1, "stale": 2, "overdue": 3, "unknown": 4, "invalid": 5}


def _parse(s) -> Optional[datetime.date]:
    if not s or not isinstance(s, str):
        return None
    try:
        return datetime.date.fromisoformat(s.strip())
    except ValueError:
        return None


def review_meta(hub: dict, today: Optional[datetime.date] = None) -> dict:
    """由枢纽元数据统一计算时效与复核状态。

    hub 键：as_of / next_review / verified（均可缺失）
    返回：as_of, age_days, freshness, next_review, overdue, verified,
          review_status, reason_codes
    """
    today = today or datetime.date.today()
    as_of_raw = hub.get("as_of")
    nr_raw = hub.get("next_review")
    reasons = []

    d = _parse(as_of_raw)
    as_of_valid = d is not None and d <= today and (today - d).days <= 3650
    if not as_of_raw:
        reasons.append("as_of_missing")
    elif d is None:
        reasons.append("as_of_unparseable")
    elif d > today:
        reasons.append("as_of_future")
        as_of_valid = False

    age = (today - d).days if as_of_valid else None
    if age is None:
        freshness = "unknown"
        if as_of_raw and d is None:
            freshness = "invalid"
    elif age <= POLICY["ok_days"]:
        freshness = "ok"
    elif age <= POLICY["aging_days"]:
        freshness = "aging"
    else:
        freshness = "stale"

    nr = _parse(nr_raw)
    if not nr_raw:
        overdue = True                     # 无复核日期 → fail-closed
        reasons.append("next_review_missing")
    elif nr is None:
        overdue = True                     # 日期异常 → 不得当作"未逾期"
        reasons.append("next_review_unparseable")
    else:
        overdue = nr < today
        if overdue:
            reasons.append("next_review_passed")

    if overdue:
        review_status = "overdue"
    elif freshness in ("unknown", "invalid"):
        review_status = "unknown"
    else:
        review_status = freshness

    return {
        "as_of": as_of_raw,
        "age_days": age,
        "freshness": freshness,
        "next_review": nr_raw,
        "overdue": overdue,
        "verified": hub.get("verified", "unknown"),
        "review_status": review_status,
        "reason_codes": reasons,
    }


def needs_warning(meta: dict) -> bool:
    """任一维度不可信即需要警告：逾期 或 aging/stale 或 未知。"""
    return bool(meta.get("overdue")
                or meta.get("freshness") in ("aging", "stale", "unknown", "invalid")
                or meta.get("review_status") in ("overdue", "unknown"))


def warning_text(meta: dict) -> Optional[str]:
    if not needs_warning(meta):
        return None
    bits = []
    if meta.get("overdue"):
        bits.append(f"已过复核日期 {meta.get('next_review') or '(缺失)'}")
    if meta.get("age_days") is None:
        bits.append("无有效 as_of")
    else:
        bits.append(f"内容已 {meta['age_days']} 天未复核")
    return "⚠️ " + "，".join(bits) + "；请以官方最新原文核验后使用。"
