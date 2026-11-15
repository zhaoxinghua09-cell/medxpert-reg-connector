#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Official-source link audit for the 15 registered authorities.

English
-------
Reads medxpert_reg_connector/data/sources.json and issues one GET per source URL.

  OK      2xx - reachable as expected
  BLOCKED 401/403/412/429 - anti-bot or rate limit: the site is up, the robot is
          refused. A known property of NMPA and ISO, not a broken link.
  FAIL    timeout / DNS / 5xx - the real signal that a source moved.

Advisory by default: exit 0 in every case, so a scheduled run cannot fail a
repository it only observes. Pass --strict to make FAIL (not BLOCKED) non-zero.

Usage:
  python tools/check_sources.py
  python tools/check_sources.py --strict

中文
----
对 sources.json 里的官方源做每源一次 GET 巡检。OK=可达；BLOCKED=站点在、但拒绝
机器人（NMPA 与 ISO 的已知行为）；FAIL=超时/域名/5xx，才是"源搬了"的真实信号。
默认只告警不改变状态，--strict 时 FAIL 才置非零。
"""
import argparse
import json
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (compatible; medxpert-link-audit/1.0)"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def probe(url: str, timeout: int = 15):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                      timeout=timeout, context=CTX).status, "OK"
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 412, 429):
            return e.code, "BLOCKED"
        return e.code, "FAIL"
    except Exception:
        return 0, "FAIL"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    data = json.loads((ROOT / "medxpert_reg_connector" / "data" / "sources.json").read_text(encoding="utf-8"))
    counts = {"OK": 0, "BLOCKED": 0, "FAIL": 0}
    for s in data.get("sources", []):
        code, verdict = probe(s["url"])
        counts[verdict] += 1
        print("%-7s %4s  %-22s %s" % (verdict, code or "-", s["id"], s["url"]))
    print("\nsummary: %s of %s" % (counts, counts["OK"] + counts["BLOCKED"] + counts["FAIL"]))
    if a.strict and counts["FAIL"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
