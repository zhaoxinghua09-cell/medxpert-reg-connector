#!/usr/bin/env python3
"""版本一致性门禁：pyproject、清单、运行时三处必须同版。

背景：2026-11-15 出过包内 `__version__` 字面量跟着新版本发布的事故（装到新版本却报
旧版本），同日又发现一侧清单副本没被同步。本门禁把这两类缺陷变成构建期红叉：
只要 pyproject（或它声明的 attr 单一源）、每一个 server.json 的 version 与
packages[].version、以及安装后 importlib.metadata 的版本任一不等，退出码 1。

用法（CI 里先装包再跑，仓库根目录执行）：
    python -m pip install .
    python tools/version_gate.py
仅查静态清单（不装包）：
    python tools/version_gate.py --static-only
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def pyproject_text() -> str:
    return (ROOT / "pyproject.toml").read_text(encoding="utf-8")


def version_ref() -> tuple[str, str, str]:
    """返回 (比对基准的标签, 基准版本或 attr 表达式, 是否 attr 单一源)。"""
    txt = pyproject_text()
    m = re.search(r'^version\s*=\s*"([^"]+)"', txt, re.M)
    if m:
        return "pyproject.toml version", m.group(1), "literal"
    m = re.search(r'^version\s*=\s*\{.*?attr\s*=\s*"([^"]+)"', txt, re.M)
    if m:
        return "pyproject.toml (attr)", m.group(1), "attr"
    raise SystemExit("GATE FAIL: pyproject.toml 里找不到 version")


def dist_name() -> str | None:
    m = re.search(r'^name\s*=\s*"([^"]+)"', pyproject_text(), re.M)
    return m.group(1) if m else None


def manifests() -> list[pathlib.Path]:
    return [p for p in [ROOT / "server.json"] if p.exists()]

def pin_problems() -> list[str]:
    """Every `uses:` must be a full 40-character commit SHA.

    A floating tag (@v4) is a moving target: whatever the tag points at runs with the
    repository's token. This repository learned the cost of that the hard way when a
    workflow silently failed to start because an action was not pinned.
    """
    import re as _re
    bad: list[str] = []
    wf_dir = None
    probe = ROOT
    for _ in range(4):
        cand = probe / ".github" / "workflows"
        if cand.is_dir():
            wf_dir = cand
            break
        probe = probe.parent
    if wf_dir is None:
        print("  PIN SKIP: 未找到 .github/workflows（从 ROOT 向上 4 层），钉版规则未生效")
        return bad
    pat = _re.compile(r"uses:\s*([^\s#]+)")
    sha = _re.compile(r"^[^@]+@[0-9a-f]{40}$")
    wf_files = sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml"))
    checked = 0
    for p in wf_files:
        for lineno, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            m = pat.search(line)
            if not m:
                continue
            ref = m.group(1)
            if ref.startswith("./"):
                continue
            checked += 1
            if not sha.match(ref):
                bad.append(f"{p.name}:{lineno}: {ref} is not pinned to a 40-character SHA")
    print(f"  PIN CHECK: {len(wf_files)} 个 workflow、{checked} 处 uses 已核，浮动 {len(bad)} 处")
    return bad

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--static-only", action="store_true")
    a = ap.parse_args()

    ref_label, ref_value, kind = version_ref()
    checks: list[tuple[str, str]] = []
    for mp in manifests():
        d = json.loads(mp.read_text(encoding="utf-8"))
        checks.append((f"{mp.name} version", d.get("version", "")))
        for pkg in d.get("packages") or []:
            checks.append((f"{mp.name} packages[{pkg.get('identifier')}]", pkg.get("version", "")))

    runtime = None
    if not a.static_only and dist_name():
        try:
            from importlib.metadata import version as v
            runtime = v(dist_name())
        except Exception as e:
            runtime = f"<{type(e).__name__}>"

    print(f"  {'pyproject.toml':<52} {ref_value or '<empty>'}  ({kind})")
    for label, value in checks:
        print(f"  {label:<52} {value or '<empty>'}")
    if runtime is not None:
        print(f"  {'runtime importlib.metadata':<52} {runtime}")

    problems = []
    if kind == "attr":
        # attr 单一源：静态清单只能与运行时互证
        if runtime and not runtime.startswith("<") and runtime != "0.0.0":
            for label, value in checks:
                if value and value != runtime:
                    problems.append(f"{label}: {value} != {runtime}（运行时）")
        elif runtime and not runtime.startswith("<"):
            problems.append(f"runtime: 回退到 {runtime}，说明包未安装或元数据缺失")
    else:
        if runtime is not None and not runtime.startswith("<") and runtime != ref_value:
            problems.append(f"runtime: {runtime} != {ref_value}（{ref_label}）")
        for label, value in checks:
            if not value:
                problems.append(f"{label}: 空值")
            elif value != ref_value:
                problems.append(f"{label}: {value} != {ref_value}（{ref_label}）")

    if runtime is not None and runtime.startswith("<"):
        problems.append(f"runtime: 取不到版本 {runtime}")

    problems += pin_problems()

    if problems:
        print("\nGATE FAIL:")
        for p in problems:
            print("  - " + p)
        return 1
    print("\nGATE PASS: 版本来源一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
