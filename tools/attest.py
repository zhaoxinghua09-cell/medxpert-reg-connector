#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate ATTESTATION.md's per-file hash table and package fingerprint.

Rule (now explicit and reproducible, which it was not before):
    per-file hash      = sha256(raw bytes of the file)
    package fingerprint = sha256( "\n".join(f"{path}:{per_file_hash}"
                             for path in sorted(paths) ) )

Only files that ship in the package or the repo root are listed: the reviewer must be
able to check every row with `sha256sum` and then recompose the fingerprint by hand.

Usage:  python tools/attest.py           # rewrite the table + fingerprint in ATTESTATION.md
        python tools/attest.py --check   # verify the current file, exit 1 on drift
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ATTEST = ROOT / "ATTESTATION.md"
HEADER_RE = re.compile(r"^\| 文件 \| SHA-256 \|$", re.M)
ROW_RE = re.compile(r"^\| ([^|]+?) \| ([0-9a-f]{64}) \|$", re.M)

# Files covered: everything a user receives (repo root docs + package payload).
INCLUDE_GLOBS = [
    "LICENSE",
    "CONTENT-LICENSE",
    "README.md",
    "README.en.md",
    "SKILL.md",
    "CHANGELOG.md",
    "mcp-config.json",
    "server.json",
    "smithery.yaml",
    "manifest.json",
    "agent.json",
    "connector-meta.json",
    "pyproject.toml",
    "MANIFEST.in",
    "requirements.txt",
    "Dockerfile",
    ".dockerignore",
    "glama.json",
    "medxpert_reg_connector/**/*.py",
    "medxpert_reg_connector/data/*.json",
    "medxpert_reg_connector/data/references/*.md",
]


def covered_files() -> list[pathlib.Path]:
    seen: dict[str, pathlib.Path] = {}
    for pattern in INCLUDE_GLOBS:
        for p in ROOT.glob(pattern):
            if p.is_file():
                seen[p.relative_to(ROOT).as_posix()] = p
    return [seen[k] for k in sorted(seen)]


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(rows: list[tuple[str, str]]) -> str:
    seed = "\n".join(f"{rel}:{sha}" for rel, sha in rows)
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def main() -> int:
    check = "--check" in sys.argv
    files = covered_files()
    rows = [(p.relative_to(ROOT).as_posix(), digest(p)) for p in files]
    fp = fingerprint(rows)

    table = "| 文件 | SHA-256 |\n|---|---|\n" + "\n".join(f"| {rel} | {sha} |" for rel, sha in rows) + "\n"
    text = ATTEST.read_text(encoding="utf-8")

    if check:
        old = ROW_RE.findall(text)
        drift = [rel for rel, sha in rows if dict(old).get(rel) != sha]
        missing = [rel for rel, _ in rows if rel not in dict(old)]
        old_fp = re.search(r"包指纹 SHA-256：([0-9a-f]{64})", text)
        ok_fp = bool(old_fp) and old_fp.group(1) == fp
        print(f"files={len(rows)} drift={len(drift)} missing={len(missing)} fingerprint_match={ok_fp}")
        for rel in (drift + missing)[:10]:
            print("  out of date:", rel)
        return 0 if not (drift or missing) and ok_fp else 1

    # Replace the table (everything after the table header line).
    head = text.split("| 文件 | SHA-256 |")[0]
    new_text = head + table
    new_text = re.sub(r"包指纹 SHA-256：[0-9a-f]{64}", f"包指纹 SHA-256：{fp}", new_text)
    ATTEST.write_text(new_text, encoding="utf-8")
    print(f"files={len(rows)} fingerprint={fp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
