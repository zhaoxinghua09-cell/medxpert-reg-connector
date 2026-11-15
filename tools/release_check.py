#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Release gate: prove the published artifacts match what this repository claims.

English
-------
Run this BEFORE tagging and AFTER PyPI has accepted the upload. It answers one
question: does every public surface say the same version, and does the hash we
publish in server.json describe the wheel that PyPI actually serves?

Checks, in order:
  1. version consistency across the 8 manifests      (tools/version_check.py)
  2. PyPI serves this version and the wheel is readable
  3. server.json packages[0].fileSha256 == PyPI wheel sha256   (skipped if unset)
  4. registry.modelcontextprotocol.io newest entry version == local version
  5. websiteUrl and every icons[].src answer 200

Usage:
  python tools/release_check.py            # full, needs network
  python tools/release_check.py --offline  # check 1 only

Exit code 0 = every check PASSED, 1 = at least one FAILED.
A FAILED check is not a warning: it is a reason not to publish.

中文
----
发布门禁：证明线上发布物与本仓库的声明一致。打 tag 之前、PyPI 接收之后运行。
它只回答一个问题：每个公开面说的是不是同一个版本，写进 server.json 的哈希
描述的是不是 PyPI 真正在分发的那个 wheel。
任一检查 FAILED 都不是提示，而是"不要发布"的理由。
"""
import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = "medxpert-reg-connector"
NAME = "io.github.zhaoxinghua09-cell/medxpert-reg-connector"
UA = {"User-Agent": "medxpert-release-check/1.0"}


def local_version() -> str:
    ns = {}
    exec((ROOT / "medxpert_reg_connector" / "__init__.py").read_text(encoding="utf-8"), ns)
    return ns["__version__"]


def server_json() -> dict:
    return json.loads((ROOT / "server.json").read_text(encoding="utf-8"))


def http(url: str, timeout: int = 20):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)


def check_version_consistency() -> bool:
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "version_check.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout.strip())
    return r.returncode == 0


def check_pypi(version: str):
    """Return (ok, wheel_sha256)."""
    try:
        d = json.load(http("https://pypi.org/pypi/%s/%s/json" % (PKG, version)))
    except urllib.error.HTTPError as e:
        print("[FAIL] pypi: %s not found (%s) - publish to PyPI first" % (version, e.code))
        return False, ""
    except Exception as e:
        print("[FAIL] pypi: %s" % type(e).__name__)
        return False, ""
    wheels = [f for f in d["urls"] if f["filename"].endswith(".whl")]
    if not wheels:
        print("[FAIL] pypi: no wheel for this version")
        return False, ""
    w = wheels[0]
    print("[PASS] pypi: %s %s B sha256=%s" % (w["filename"], w["size"], w["digests"]["sha256"]))
    return True, w["digests"]["sha256"]


def check_file_hash(sj: dict, digest: str) -> bool:
    """Compare the digest we publish with the wheel PyPI serves.

    Where it lives matters: the official registry rejects `packages[].fileSha256`
    for PyPI packages ("only for MCPB packages"), even though the 2025-12-11 schema
    marks it optional for every package type. So for PyPI the digest goes in
    `_meta` → publisher-provided → `wheel_sha256`, which the registry preserves.
    Whichever of the two fields is present is the one checked.
    """
    declared = sj.get("packages", [{}])[0].get("fileSha256", "")
    if not declared:
        declared = (sj.get("_meta", {})
                    .get("io.modelcontextprotocol.registry/publisher-provided", {})
                    .get("wheel_sha256", ""))
    if not declared:
        print("[SKIP] wheel digest: not published in server.json")
        return True
    if declared == digest:
        print("[PASS] published wheel digest matches the wheel PyPI serves")
        return True
    print("[FAIL] published digest %s != pypi %s" % (declared, digest))
    return False


def check_registry(version: str) -> bool:
    try:
        d = json.load(http(
            "https://registry.modelcontextprotocol.io/v0/servers?search=medxpert-reg-connector"))
    except Exception as e:
        print("[FAIL] registry unreachable: %s" % type(e).__name__)
        return False
    servers = [s.get("server", s) for s in d.get("servers", [])]
    ours = [s for s in servers if s.get("name") == NAME]
    if not ours:
        print("[FAIL] registry: our entry is absent")
        return False
    newest = max(ours, key=lambda s: s.get("version", ""))
    if newest.get("version") == version:
        print("[PASS] registry newest entry is %s" % version)
        return True
    print("[FAIL] registry newest entry is %s, local is %s - run the registry workflow, then re-run"
          % (newest.get("version"), version))
    return False


def check_urls(sj: dict) -> bool:
    ok = True
    try:
        r = http(sj.get("websiteUrl"), timeout=20)
        print("[PASS] websiteUrl: %s %s" % (r.status, sj.get("websiteUrl")))
    except Exception as e:
        print("[FAIL] websiteUrl: %s %s" % (type(e).__name__, sj.get("websiteUrl")))
        ok = False
    # The first icon is the one clients render, so it must answer. Later entries are
    # declared fallbacks; a fallback that is unreachable from a given network is a
    # WARN, not a FAIL - otherwise this gate fails forever from mainland China,
    # where raw.githubusercontent.com is blocked, and stops meaning anything.
    for idx, icon in enumerate(sj.get("icons", [])):
        url = icon.get("src")
        if not url:
            continue
        label = "icon[0] (primary)" if idx == 0 else "icon[%d] (fallback)" % idx
        try:
            r = http(url, timeout=20)
            print("[PASS] %s: %s %s" % (label, r.status, url))
        except Exception as e:
            if idx == 0:
                print("[FAIL] %s: %s %s" % (label, type(e).__name__, url))
                ok = False
            else:
                print("[WARN] %s unreachable from this network (%s): %s" % (label, type(e).__name__, url))
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="skip network checks")
    a = ap.parse_args()
    v = local_version()
    sj = server_json()
    print("local version = %s" % v)
    results = [check_version_consistency()]
    if not a.offline:
        ok_pypi, digest = check_pypi(v)
        results.append(ok_pypi)
        results.append(check_file_hash(sj, digest))
        results.append(check_registry(v))
        results.append(check_urls(sj))
    passed = all(results)
    print("\nRESULT: %s" % ("ALL PASS" if passed else "FAILED"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
