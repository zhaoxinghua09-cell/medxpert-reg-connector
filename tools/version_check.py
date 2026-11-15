#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check that every manifest carries the same version as the package.

Why this exists: on 2026-11-15 the package was at 1.3.3 on PyPI and in the official
MCP Registry, while connector-meta.json / lhm.plugin.json / manifest.json / SKILL.md
still said 1.2.0. Directory sites read those files, so they advertised a version that
had three releases of water under the bridge. A single-source version plus a check that
fails CI is cheaper than noticing this one release late each time.

Single source of truth: medxpert_reg_connector/__init__.py  __version__

Intentionally NOT checked:
  medxpert_reg_connector/data/registry.json "knowledge_base_version" — it versions the
  knowledge-base lineage, not the release train. It moves only when the content moves.

The ninth location is not a file but a value: server.py's SERVER_VERSION is imported
and compared at runtime, because 1.3.1-1.3.4 shipped with a literal "1.3.0" there and
kept announcing the wrong version in every MCP handshake.

Usage:  python tools/version_check.py   # exit 1 on any mismatch
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def source_version() -> str:
    text = (ROOT / "medxpert_reg_connector" / "__init__.py").read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not m:
        raise SystemExit("cannot find __version__ in medxpert_reg_connector/__init__.py")
    return m.group(1)


def toml_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^\s*version\s*=\s*"([^"]+)"', text, re.M)
    if not m:
        raise SystemExit("cannot find version in pyproject.toml")
    return m.group(1)


def json_field(rel: str, *keys: str) -> str:
    obj = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    for k in keys[:-1]:
        obj = obj[k]
    return obj[keys[-1]]


def yaml_front_matter_version(rel: str) -> str:
    text = (ROOT / rel).read_text(encoding="utf-8")
    m = re.search(r"^version:\s*([0-9][0-9A-Za-z.\-]*)\s*$", text, re.M)
    if not m:
        raise SystemExit(f"cannot find version front-matter in {rel}")
    return m.group(1)


def changelog_top_version() -> str:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^## ([0-9][0-9A-Za-z.\-]*)", text, re.M)
    if not m:
        raise SystemExit("cannot find a release heading in CHANGELOG.md")
    return m.group(1)


def server_runtime_version() -> str:
    """What the MCP handshake actually advertises, read from a real import.

    A literal in server.py is invisible to a file-level check but decides what every
    client sees in serverInfo.version; that is exactly how 1.3.1-1.3.4 kept
    announcing 1.3.0. Importing it makes the value, not the text, the thing checked.
    """
    import subprocess
    code = (
        "from medxpert_reg_connector.server import SERVER_VERSION as v; "
        "from medxpert_reg_connector import __version__ as w; "
        "print(v); raise SystemExit(0 if v == w else 3)"
    )
    r = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "").strip().splitlines()
    if r.returncode not in (0, 3) or not out:
        raise SystemExit("cannot import medxpert_reg_connector.server: %s" % (r.stderr or "")[-200:])
    if r.returncode == 3:
        raise SystemExit("server.py advertises %s which differs from __version__" % out[-1])
    return out[-1]


def main() -> int:
    want = source_version()
    probes = [
        ("pyproject.toml", toml_version()),
        ("connector-meta.json", json_field("connector-meta.json", "version")),
        ("lhm.plugin.json", json_field("lhm.plugin.json", "version")),
        ("manifest.json", json_field("manifest.json", "version")),
        ("server.json", json_field("server.json", "version")),
        ("server.json packages[0]", json_field("server.json", "packages", 0, "version")),
        ("SKILL.md", yaml_front_matter_version("SKILL.md")),
        ("CHANGELOG.md", changelog_top_version()),
        ("server.py handshake (SERVER_VERSION)", server_runtime_version()),
    ]
    bad = [(where, got) for where, got in probes if got != want]
    for where, got in probes:
        print(f"{'ok  ' if got == want else 'MISMATCH'} {where}: {got}")
    print(f"source: medxpert_reg_connector/__init__.py __version__ = {want}")
    if bad:
        print(f"FAIL: {len(bad)} manifest(s) disagree with {want}")
        return 1
    print(f"PASS: {len(probes)} manifests agree on {want}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
