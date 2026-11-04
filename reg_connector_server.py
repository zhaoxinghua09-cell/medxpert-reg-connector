#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedXpert 全球法规连接器 · MCP Server  v1.2.0
=============================================
把本地法规知识库（27 枢纽）封装成本地只读 MCP Server，
供 WorkBuddy / Agent / 小艺 Skill 直接调用检索全球医疗器械法规知识。

v1.1.0 新增「时效护栏」——法规/标准会更新，静态快照必须自证新鲜度：
- 检索结果强制注入 as_of / age_days / freshness / copyright / verified
- kb_freshness  报告全库新鲜度与逾期枢纽
- reg_delta     列出巡检发现的法规变更（读 registry.json deltas）
- kb_sources    列出官方源注册表（通道/频率/版权等级）

v1.2.0 扩展「实时更新能力」（服务接口不变，周边管线增强）：
- EU 法规变更纳入全自动：cellar_query.py 经 CELLAR SPARQL 取立法 + MDR/IVDR 合并版本
- 台账 → 官网：render_site.py 渲染知识库总览页 / 变更月报 / freshness.json
- 复核排期：gen_review_sheet.py 生成逾期枢纽人工复核工作表（md/csv）
- 自动源 3 → 5（+EUR-Lex CELLAR +MDCG）；巡检基线改存完整 items，杜绝假候选

设计红线（版权）：
- 付费标准（ISO/IEC/ASTM/GB）全文永不入库，只存编号 + 官方查询入口
- 本库为「法规导航器 + 时效护栏」，权威真源永远以官方原文为准

运行：python reg_connector_server.py   （stdio 模式）
依据：MCP 协议 2024-11-05 · fastmcp
版权：© MedXpert · ORCID 0009-0001-0512-1237
"""

import json
import os
import re
import sys
import datetime
from pathlib import Path

from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
_BUNDLED = Path(__file__).resolve().parent / "references"
_SIBLING = Path(__file__).resolve().parent.parent / "references"


def _resolve_refs_dir() -> Path:
    env_dir = os.environ.get("REG_HUB_REFS")
    if env_dir:
        p = Path(env_dir)
        if p.is_dir():
            return p.resolve()
    for cand in (_BUNDLED, _SIBLING, Path(__file__).resolve().parent):
        if (cand / "README.md").is_file() or any(cand.glob("*.md")):
            return cand.resolve()
    return _BUNDLED.resolve()


REFS_DIR = _resolve_refs_dir()
_BASE = Path(__file__).resolve().parent
REGISTRY_PATH = _BASE / "registry.json"
SOURCES_PATH = _BASE / "sources.json"

SERVER_NAME = "medxpert-reg-connector"
SERVER_VERSION = "1.2.0"
SERVER_DESC = (
    "MedXpert 全球法规连接器：本地只读检索全球医疗器械法规知识库 "
    "(NMPA/FDA/MDR/PMDA 等 27 枢纽 + 骨科实证)，返回片段、官方链接、时效标注(as_of/新鲜度)与待核验提示。"
    "注意：本库为法规导航器，法规标准实时更新，关键结论请以官方最新原文为准；付费标准全文受版权保护不入库。"
)

mcp = FastMCP(SERVER_NAME, version=SERVER_VERSION, instructions=SERVER_DESC)

# ---------------------------------------------------------------------------
# 时效护栏
# ---------------------------------------------------------------------------
FRESHNESS_POLICY = {"ok_days": 90, "aging_days": 180}

_REGISTRY = {}


def _load_registry() -> dict:
    global _REGISTRY
    if not _REGISTRY:
        try:
            _REGISTRY = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        except Exception:
            _REGISTRY = {"schema": "reg-nav/1.0", "hubs": {}, "standards_index": {}, "deltas": []}
    return _REGISTRY


def _freshness(as_of: str):
    """由 as_of 计算 age_days 与 freshness 档位。"""
    if not as_of:
        return {"age_days": None, "freshness": "unknown", "warning": "该枢纽无时效标注，请以官方原文为准"}
    try:
        d = datetime.date.fromisoformat(as_of)
    except Exception:
        return {"age_days": None, "freshness": "unknown", "warning": "时效标注格式异常"}
    age = (datetime.date.today() - d).days
    if age <= FRESHNESS_POLICY["ok_days"]:
        f = "ok"
    elif age <= FRESHNESS_POLICY["aging_days"]:
        f = "aging"
    else:
        f = "stale"
    warning = None
    if f == "aging":
        warning = f"本枢纽内容已 {age} 天未复核，法规可能已有更新，请以官方原文为准。"
    elif f == "stale":
        warning = f"⚠️ 本枢纽内容已 {age} 天未复核，很可能已过期，务必以官方最新原文核验后使用。"
    return {"age_days": age, "freshness": f, "warning": warning}


def _hub_meta(hub_key: str) -> dict:
    """取枢纽的时效/版权元数据（registry 优先，回退默认）。"""
    reg = _load_registry().get("hubs", {})
    h = reg.get(hub_key)
    if h:
        fr = _freshness(h.get("as_of"))
        return {
            "as_of": h.get("as_of"),
            "verified": h.get("verified", "unknown"),
            "copyright": h.get("copyright", "unknown"),
            "standards_ref": h.get("standards_ref", []),
            **fr,
        }
    return {"as_of": None, "verified": "unknown", "copyright": "unknown",
            "standards_ref": [], **_freshness(None)}


# ---------------------------------------------------------------------------
# 知识库加载
# ---------------------------------------------------------------------------
HUB_FILES = {}


def _extract_title(content: str, filename: str) -> str:
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return m.group(1).strip() if m else filename.replace(".md", "")


def _split_sections(content: str) -> list:
    sections = []
    lines = content.splitlines()
    cur_title = "(前言)"
    cur_body = []
    for ln in lines:
        if re.match(r"^#{2,4}\s+", ln):
            if cur_body or cur_title != "(前言)":
                sections.append((cur_title, "\n".join(cur_body).strip()))
            cur_title = re.sub(r"^#{2,4}\s+", "", ln).strip()
            cur_body = []
        else:
            cur_body.append(ln)
    if cur_body or cur_title != "(前言)":
        sections.append((cur_title, "\n".join(cur_body).strip()))
    return [s for s in sections if s[1]]


def _extract_links(content: str) -> list:
    return re.findall(r"https?://[^\s\)\]\>\"']+", content)


def load_hubs() -> None:
    if not REFS_DIR.is_dir():
        raise RuntimeError(f"知识库目录不存在: {REFS_DIR}，请设置 REG_HUB_REFS 指向含 .md 的知识库目录")
    for p in sorted(REFS_DIR.glob("*.md")):
        if p.name == "README.md":
            continue
        try:
            content = p.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            content = p.read_text(encoding="gb18030", errors="replace")
        HUB_FILES[p.stem] = {
            "title": _extract_title(content, p.name),
            "path": p,
            "content": content,
            "sections": _split_sections(content),
            "links": list(dict.fromkeys(_extract_links(content))),
        }


# ---------------------------------------------------------------------------
# 检索核心：中文友好 BM25 近似（无第三方依赖）
# ---------------------------------------------------------------------------
STOPWORDS = {
    "的", "了", "和", "与", "或", "及", "在", "是", "为", "对", "于", "以",
    "这", "那", "个", "中", "上", "下", "等", "之", "也", "而", "并", "其",
    "a", "an", "the", "to", "of", "and", "or", "in", "on", "for", "with",
}


def _tokenize(text: str) -> list:
    text = text.lower()
    tokens = []
    for w in re.findall(r"[a-z0-9][a-z0-9\-\.\']{1,}", text):
        tokens.append(w)
    for seg in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        if len(seg) <= 4:
            tokens.append(seg)
        else:
            for i in range(len(seg) - 1):
                tokens.append(seg[i: i + 2])
    return [t for t in tokens if t and t not in STOPWORDS and len(t) > 1]


def _build_index():
    index = {}
    for key, hub in HUB_FILES.items():
        for si, (stitle, sbody) in enumerate(hub["sections"]):
            text = stitle + "\n" + sbody
            for tok in set(_tokenize(text)):
                tf = text.lower().count(tok)
                index.setdefault(tok, []).append((key, si, tf))
    return index


_INDEX = {}


def _ensure_index():
    global _INDEX
    if not _INDEX:
        _INDEX = _build_index()
    return _INDEX


def search(query: str, top_k: int = 5, hub_filter: str = None) -> list:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []
    index = _ensure_index()
    scores = {}
    for tok in q_tokens:
        for key, si, tf in index.get(tok, []):
            if hub_filter and key != hub_filter:
                continue
            scores[(key, si)] = scores.get((key, si), 0) + (1.0 + 0.5 * tf)
    if not scores:
        return []
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    results = []
    for (key, si), score in ranked:
        hub = HUB_FILES[key]
        stitle, sbody = hub["sections"][si]
        snippet = re.sub(r"\s+", " ", sbody).strip()
        if len(snippet) > 400:
            snippet = snippet[:400] + "…"
        meta = _hub_meta(key)
        results.append({
            "hub_key": key,
            "hub_title": hub["title"],
            "section": stitle,
            "snippet": snippet,
            "score": round(score, 2),
            "links": hub["links"][:8],
            # —— 时效护栏 ——
            "as_of": meta["as_of"],
            "age_days": meta["age_days"],
            "freshness": meta["freshness"],
            "verified": meta["verified"],
            "copyright": meta["copyright"],
        })
    return results


# ---------------------------------------------------------------------------
# MCP 工具
# ---------------------------------------------------------------------------
@mcp.tool()
def list_hubs() -> str:
    """列出法规知识库全部枢纽（主题）及覆盖范围、时效状态，返回 JSON 数组。"""
    hubs = []
    for key in sorted(HUB_FILES.keys()):
        hub = HUB_FILES[key]
        meta = _hub_meta(key)
        hubs.append({
            "hub_key": key,
            "title": hub["title"],
            "sections": len(hub["sections"]),
            "official_links": len(hub["links"]),
            "phase": _phase_of(hub["content"]),
            "as_of": meta["as_of"],
            "freshness": meta["freshness"],
            "age_days": meta["age_days"],
        })
    return json.dumps(hubs, ensure_ascii=False, indent=2)


@mcp.tool()
def search_regulation(query: str, top_k: int = 5, hub_filter: str = None) -> str:
    """
    在法规知识库中检索关键词（支持中文/英文/法规号，如 'UDI'、'510k'、'MDR PMS'、'委托生产'）。
    返回命中的枢纽、小节、摘要片段、官方链接、相关度得分与时效标注(as_of/freshness)。
    """
    if not query or not query.strip():
        return json.dumps({"error": "query 不能为空"}, ensure_ascii=False)
    results = search(query, top_k=top_k, hub_filter=hub_filter)
    if not results:
        return json.dumps(
            {"query": query, "count": 0, "hint": "未命中，可尝试更短关键词或切换市场缩写（NMPA/FDA/MDR/PMDA）"},
            ensure_ascii=False, indent=2,
        )
    warned = [r for r in results if r["freshness"] in ("aging", "stale")]
    payload = {
        "query": query,
        "count": len(results),
        "results": results,
        "disclaimer": "本库为法规导航器，法规标准实时更新；引用前请以官方最新原文核验。",
    }
    if warned:
        payload["staleness_notice"] = (
            f"⚠️ {len(warned)} 条命中内容已超复核周期（freshness: aging/stale），"
            "很可能已有法规更新，请务必核验官方原文后再引用。"
        )
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
def get_hub(hub_key: str) -> str:
    """按 hub_key 取某一枢纽的完整整理内容（含全部小节与官方链接、时效与标准指针）。先调用 list_hubs 查看可用 hub_key。"""
    hub = HUB_FILES.get(hub_key)
    if not hub:
        keys = list(HUB_FILES.keys())
        return json.dumps(
            {"error": f"未找到枢纽 {hub_key}，可用: {keys[:10]} ...（共 {len(keys)} 个）"},
            ensure_ascii=False,
        )
    meta = _hub_meta(hub_key)
    stds = []
    for s in meta.get("standards_ref", []):
        info = _load_registry().get("standards_index", {}).get(s, {})
        stds.append({
            "standard": s,
            "copyright": info.get("copyright", "unknown"),
            "official_query": info.get("official_query", ""),
            "note": info.get("note", ""),
        })
    return json.dumps({
        "hub_key": hub_key,
        "title": hub["title"],
        "content": hub["content"],
        "official_links": hub["links"],
        "as_of": meta["as_of"],
        "age_days": meta["age_days"],
        "freshness": meta["freshness"],
        "verified": meta["verified"],
        "copyright": meta["copyright"],
        "staleness_warning": meta.get("warning"),
        "standards_ref": stds,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def ask_classification(product: str) -> str:
    """
    产品分类与注册路径速查：输入产品描述（如 '骨科金属接骨板'、'一次性使用输液器'），
    返回相关枢纽、分类线索、官方链接与注册路径建议。
    """
    if not product or not product.strip():
        return json.dumps({"error": "product 不能为空"}, ensure_ascii=False)
    results = search(product, top_k=4)
    priority_keys = [
        "骨科手术器械_全球注册路径汇编",
        "注册工程师资料枢纽",
        "注册周期费用有效期对比枢纽",
        "市场准入与销售枢纽",
        "注册检验与申报实操枢纽",
    ]
    related = []
    for key in priority_keys:
        if key in HUB_FILES:
            m = _hub_meta(key)
            related.append({"hub_key": key, "title": HUB_FILES[key]["title"],
                            "as_of": m["as_of"], "freshness": m["freshness"]})
    return json.dumps({
        "product": product,
        "matches": results,
        "recommended_hubs": related,
        "hint": "分类建议需以目标市场官方分类库为准（NMPA 分类目录 / FDA 产品分类库 / MDR 分类规则），以上仅为知识库线索。",
    }, ensure_ascii=False, indent=2)


# --------------------------- 时效工具（v1.1.0 新增） ---------------------------
@mcp.tool()
def kb_freshness() -> str:
    """
    报告知识库新鲜度：全库统计 + 逐枢纽 as_of/age_days/freshness/next_review，
    并列出逾期未复核的枢纽。法规会更新，调用知识前建议先查新鲜度。
    """
    reg = _load_registry()
    hubs = reg.get("hubs", {})
    rows = []
    overdue = []
    c = {"ok": 0, "aging": 0, "stale": 0, "unknown": 0}
    today = datetime.date.today()
    for key in sorted(HUB_FILES.keys()):
        h = hubs.get(key, {})
        meta = _hub_meta(key)
        nr = h.get("next_review")
        is_overdue = bool(nr and datetime.date.fromisoformat(nr) < today)
        c[meta["freshness"]] = c.get(meta["freshness"], 0) + 1
        rows.append({
            "hub_key": key,
            "as_of": meta["as_of"],
            "age_days": meta["age_days"],
            "freshness": meta["freshness"],
            "next_review": nr,
            "overdue": is_overdue,
            "poll_sources": h.get("poll_sources", []),
        })
        if is_overdue:
            overdue.append(key)
    return json.dumps({
        "schema": reg.get("schema"),
        "knowledge_base_version": reg.get("knowledge_base_version"),
        "generated_at": reg.get("generated_at"),
        "today": today.isoformat(),
        "policy": FRESHNESS_POLICY,
        "summary": {"hubs": len(rows), **c, "overdue": len(overdue)},
        "overdue_hubs": overdue,
        "hubs": rows,
        "advice": ("逾期枢纽应按 sources.json 的巡检频率复核官方源，核验后更新 references 与 registry 的 as_of。"
                   if overdue else "全部枢纽在复核周期内。"),
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def reg_delta(since: str = None, jurisdiction: str = None, limit: int = 50) -> str:
    """
    列出巡检发现的法规变更流水（读 registry.deltas）。可选按起始日期(since, YYYY-MM-DD)
    与辖区(jurisdiction: CN/US/EU/JP/GLOBAL)过滤。无巡检记录时返回空并提示如何产生。
    """
    deltas = _load_registry().get("deltas", [])
    rows = deltas
    if since:
        rows = [d for d in rows if d.get("date", "") >= since]
    if jurisdiction:
        j = jurisdiction.upper()
        rows = [d for d in rows if d.get("jurisdiction", "").upper() == j]
    rows = rows[-limit:]
    return json.dumps({
        "since": since,
        "jurisdiction": jurisdiction,
        "count": len(rows),
        "deltas": rows,
        "how_to_produce": ("按 sources.json 定时巡检各官方源（只拉元数据）→ 与 registry 比对 → 人工核验 → "
                           "追加至 registry.deltas 并更新对应 hub 的 as_of。详见 DOC_时效性架构.md。"),
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def kb_sources(jurisdiction: str = None) -> str:
    """
    列出官方源注册表（sources.json）：各源权威机构、巡检通道(api/rss/page/sparql/catalog)、
    巡检频率、是否可全自动、版权等级。可选按辖区过滤。
    """
    try:
        src = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        return json.dumps({"error": f"无法读取 sources.json: {e}"}, ensure_ascii=False)
    items = src.get("sources", [])
    if jurisdiction:
        j = jurisdiction.upper()
        items = [s for s in items if s.get("jurisdiction", "").upper() == j]
    return json.dumps({
        "schema": src.get("schema"),
        "rules": src.get("rules"),
        "copyright_classes": src.get("copyright_classes"),
        "count": len(items),
        "sources": items,
    }, ensure_ascii=False, indent=2)


def _phase_of(content: str) -> str:
    phase_map = [
        ("立项", "立项与可行性"),
        ("分类", "分类与路径"),
        ("技术文件", "技术文件"),
        ("质量体系", "质量体系"),
        ("注册检验", "注册申报"),
        ("审评", "审评获批"),
        ("上市后", "上市后监管"),
    ]
    for kw, phase in phase_map:
        if kw in content[:800]:
            return phase
    return "综合"


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def main() -> None:
    try:
        load_hubs()
        _load_registry()
    except RuntimeError as e:
        print(f"[reg-connector] FATAL: {e}", file=sys.stderr)
        sys.exit(1)
    n = len(HUB_FILES)
    reg = _REGISTRY
    print(f"[reg-connector] v{SERVER_VERSION} 已加载 {n} 份枢纽资料 from {REFS_DIR}", file=sys.stderr)
    print(f"[reg-connector] 时效台账: {len(reg.get('hubs', {}))} 枢纽 / "
          f"{len(reg.get('standards_index', {}))} 标准指针（生成于 {reg.get('generated_at')}）", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
