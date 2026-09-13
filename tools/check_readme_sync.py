#!/usr/bin/env python3
"""
check_readme_sync.py - cheap canary for README.md / README.ru.md drift.

This does NOT check translation quality or content equivalence - it checks
one thing only: do both files have the same number of "##" section headers?
If someone adds a section to one README and forgets the other, this catches
it immediately instead of silently, at the cost of a false-positive-safe,
very cheap check (a mismatched count means "go look", not "translation is
wrong" - the count could match by coincidence while wording drifted, or
differ for a legitimate reason someone decides to accept).

This is deliberately minimal - a real translation-diff tool would need to
understand meaning, which is a much bigger and more fragile job than the
toolkit's existing philosophy of small, stdlib-only, self-testing scripts
calls for.

No dependencies beyond the Python standard library.

Usage
-----
    python3 check_readme_sync.py
    python3 check_readme_sync.py --en README.md --ru README.ru.md
    python3 check_readme_sync.py --selftest
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

# Anchored at line start, "##" then required whitespace - this deliberately
# does NOT match "### sub-heading" lines: after the literal "##", the next
# character in a "###" line is "#", not whitespace, so \s+ fails there and
# (thanks to the ^ line anchor under MULTILINE) the engine cannot shift over
# to try matching from the third "#" instead. Only genuine "## " level-2
# section headers are counted.
HEADER_RE = re.compile(r"^##\s+(.*)$", re.MULTILINE)


def extract_headers(text: str) -> list[str]:
    return [h.strip() for h in HEADER_RE.findall(text)]


def check(en_path: pathlib.Path, ru_path: pathlib.Path) -> int:
    missing = [p for p in (en_path, ru_path) if not p.exists()]
    if missing:
        print(f"ERROR: missing file(s): {', '.join(str(p) for p in missing)}")
        return 2

    en_headers = extract_headers(en_path.read_text(encoding="utf-8"))
    ru_headers = extract_headers(ru_path.read_text(encoding="utf-8"))

    if len(en_headers) == len(ru_headers):
        print(f"OK: {en_path.name} and {ru_path.name} both have {len(en_headers)} sections.")
        return 0

    print(f"MISMATCH: {en_path.name} has {len(en_headers)} section(s), "
          f"{ru_path.name} has {len(ru_headers)}.")
    print(f"\n{en_path.name} sections:")
    for h in en_headers:
        print(f"  - {h}")
    print(f"\n{ru_path.name} sections:")
    for h in ru_headers:
        print(f"  - {h}")
    print("\nA count mismatch usually means one file gained or lost a section "
          "the other didn't. Compare by eye before committing.")
    return 1


def selftest() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = pathlib.Path(tmp_str)
        en = tmp / "README.md"
        ru = tmp / "README.ru.md"

        # Matching section counts, including a "###" sub-heading that must
        # NOT be counted as a top-level section.
        en.write_text(
            "# Title\n\n## Tools\n\n### `tools/example.py`\ntext\n\n## Status\ntext\n",
            encoding="utf-8")
        ru.write_text(
            "# Заголовок\n\n## Инструменты\n\n### `tools/example.py`\nтекст\n\n## Статус\nтекст\n",
            encoding="utf-8")
        assert check(en, ru) == 0, "matching section counts (with a ### sub-heading) must report OK"
        assert len(extract_headers(en.read_text(encoding="utf-8"))) == 2, \
            "### sub-heading must not be counted as a ## section"

        # Now break sync: drop a section from the Russian file only.
        ru.write_text("# Заголовок\n\n## Инструменты\nтекст\n", encoding="utf-8")
        assert check(en, ru) == 1, "a real mismatch must be caught, not silently passed"

        # Missing file must be reported, not silently treated as zero sections.
        missing = tmp / "does_not_exist.md"
        assert check(en, missing) == 2, "a missing file must be reported explicitly"

    print("SELFTEST OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Cheap canary for README.md / README.ru.md drift")
    parser.add_argument("--en", default=pathlib.Path("README.md"), type=pathlib.Path)
    parser.add_argument("--ru", default=pathlib.Path("README.ru.md"), type=pathlib.Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    return check(args.en, args.ru)


if __name__ == "__main__":
    sys.exit(main())
