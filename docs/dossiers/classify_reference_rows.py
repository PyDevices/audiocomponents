#!/usr/bin/env python3
"""Classify markdown tables in docs/dossiers/ and count reference-figure rows.

A figure row is a data row in a criteria / measured / target /
before-after-reference table. License, circuit-map, and macro-label
tables are counted separately and are not the audit universe.

Re-run from the repo root:

    python3 docs/dossiers/classify_reference_rows.py

Skips `reference-audit-*.md` so the audit report's own tables are not
counted in the universe they document.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def parse_tables(text: str):
    lines = text.splitlines()
    tables = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("|") and i + 1 < len(lines):
            sep = lines[i + 1]
            if re.match(r"^\|[\s:\-|]+\|$", sep):
                header = lines[i]
                j = i + 2
                rows = []
                while j < len(lines) and lines[j].startswith("|"):
                    rows.append(lines[j])
                    j += 1
                tables.append((i + 1, header, rows))
                i = j
                continue
        i += 1
    return tables


def kind(header: str) -> str:
    h = header.lower()
    if "license as read" in h or (
        "source" in h and "where read" in h
    ) or "kind | source" in re.sub(r"\s+", " ", h):
        return "license"
    if any(
        k in h
        for k in (
            "resident notes",
            "midi notes",
            "basis for sharing",
            "channel | voices",
            "card | type",
        )
    ):
        return "structure"
    if (
        re.search(r"label \| (mode|traces)", h)
        or "# | label" in h
        or "# | macro" in h
    ):
        return "macros"
    if "snappy" in h and "lufs" in h:
        return "other"
    return "figures"


def main() -> None:
    print(
        f"{'file':32s} {'lic':>4} {'str':>4} {'mac':>4} "
        f"{'fig':>4} {'oth':>4}  figure-row headers"
    )
    print("-" * 100)
    tot = dict(license=0, structure=0, macros=0, figures=0, other=0)
    fig_detail = []
    files = sorted(
        p
        for p in ROOT.glob("*.md")
        if not p.name.startswith("reference-audit-")
    )
    for p in files:
        counts = dict(license=0, structure=0, macros=0, figures=0, other=0)
        fig_headers = []
        for ln, header, rows in parse_tables(p.read_text()):
            k = kind(header)
            n = len(rows)
            counts[k] += n
            tot[k] += n
            if k == "figures":
                h = re.sub(r"\s+", " ", header.strip())[:90]
                fig_headers.append(f"L{ln}:{n}")
                fig_detail.append((p.name, ln, n, h))
        print(
            f"{p.name:32s} {counts['license']:4d} {counts['structure']:4d} "
            f"{counts['macros']:4d} {counts['figures']:4d} "
            f"{counts['other']:4d}  {', '.join(fig_headers) or '—'}"
        )

    print("-" * 100)
    print(
        f"{'TOTAL':32s} {tot['license']:4d} {tot['structure']:4d} "
        f"{tot['macros']:4d} {tot['figures']:4d} {tot['other']:4d}"
    )
    print()
    print("FIGURE TABLES (the audit universe):")
    grand = 0
    for name, ln, n, h in fig_detail:
        print(f"  {name:32s} L{ln:4d}  n={n:2d}  {h}")
        grand += n
    print(f"\nFIGURE ROWS TOTAL: {grand}")
    print(f"FILES: {len(files)}")


if __name__ == "__main__":
    main()
