#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract self-test for medxpert-reg-connector (version read from the package).

Real MCP stdio handshake; asserts the tool contract that the catalogs grade:
  - exactly 7 tools, names stable
  - every tool declares readOnlyHint (safety honesty)
  - every input parameter carries a schema description
  - 27 knowledge hubs load, and the 3 freshness tools answer

Run (repo root, package installed or on sys.path):
    python tests/selftest_stdio.py
Exit code 0 = PASS.
"""
import asyncio
import json
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPECTED_TOOLS = [
    "list_hubs", "search_regulation", "get_hub", "ask_classification",
    "kb_freshness", "reg_delta", "kb_sources",
]


async def main() -> int:
    t = StdioTransport(command=sys.executable, args=["-m", "medxpert_reg_connector"], cwd=str(ROOT))
    failures = []
    async with Client(t) as client:
        tools = await client.list_tools()
        names = [x.name for x in tools]
        if names != EXPECTED_TOOLS:
            failures.append(f"tool list mismatch: {names}")
        print(f"[ok] tools ({len(names)}): {names}")

        no_ann = [x.name for x in tools
                  if not x.annotations
                  or not (getattr(x.annotations, "read_only_hint", None)
                          if hasattr(x.annotations, "read_only_hint")
                          else getattr(x.annotations, "readOnlyHint", None))]
        if no_ann:
            failures.append(f"missing readOnlyHint: {no_ann}")
        print(f"[ok] readOnlyHint declared on {len(tools) - len(no_ann)}/{len(tools)} tools")

        undocumented = []
        for x in tools:
            schema = getattr(x, "input_schema", None) or getattr(x, "inputSchema", None) or {}
            props = (schema.get("properties") or {})
            for p, spec in props.items():
                if not (spec or {}).get("description"):
                    undocumented.append(f"{x.name}.{p}")
        if undocumented:
            failures.append(f"undocumented params: {undocumented}")
        print(f"[ok] all input params documented" if not undocumented else "[FAIL] params")

        r = await client.call_tool("list_hubs", {})
        hubs = json.loads(r.data)
        if len(hubs) != 27:
            failures.append(f"hub count {len(hubs)} != 27")
        print(f"[ok] list_hubs -> {len(hubs)} hubs")

        r = await client.call_tool("search_regulation", {"query": "UDI", "top_k": 3})
        d = json.loads(r.data)
        if not d.get("count"):
            failures.append("search_regulation('UDI') returned no hits")
        print(f"[ok] search_regulation -> {d.get('count')} hits, top1={d['results'][0]['hub_title']}")

        r = await client.call_tool("get_hub", {"hub_key": "风险管理枢纽"})
        d = json.loads(r.data)
        if "title" not in d:
            failures.append("get_hub failed")
        print(f"[ok] get_hub -> {d.get('title')}")

        r = await client.call_tool("ask_classification", {"product": "骨科金属接骨板"})
        d = json.loads(r.data)
        if not d.get("recommended_hubs"):
            failures.append("ask_classification returned no recommended hubs")
        print(f"[ok] ask_classification -> {len(d.get('matches', []))} matches / "
              f"{len(d.get('recommended_hubs', []))} hubs")

        r = await client.call_tool("kb_freshness", {})
        d = json.loads(r.data)
        if d.get("summary", {}).get("hubs") != 27:
            failures.append("kb_freshness summary mismatch")
        print(f"[ok] kb_freshness -> {d['summary']}")

        r = await client.call_tool("reg_delta", {"since": "2026-09-01"})
        d = json.loads(r.data)
        if not isinstance(d.get("count"), int):
            failures.append("reg_delta malformed")
        print(f"[ok] reg_delta -> count={d.get('count')}")

        r = await client.call_tool("kb_sources", {})
        d = json.loads(r.data)
        if not d.get("count"):
            failures.append("kb_sources empty")
        print(f"[ok] kb_sources -> {d.get('count')} official sources")

    if failures:
        print("\n[FAIL]")
        for f in failures:
            print("  - " + f)
        return 1
    print("\n[PASS] MCP contract self-test green")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
