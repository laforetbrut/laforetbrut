#!/usr/bin/env python3
"""Rotate the Minecraft quote block in README.md."""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
QUOTES_FILE = ROOT / "scripts" / "quotes.json"

QUOTE_MARK = re.compile(r"<!-- QUOTE_START -->.*?<!-- QUOTE_END -->", re.DOTALL)


def rotate_quote(content: str) -> str:
    quotes = json.loads(QUOTES_FILE.read_text(encoding="utf-8"))
    q = random.choice(quotes)
    block = (
        f"> ⛏ *\"{q['en']}\"*\n"
        f"> — **{q['author']}**, {q['context_en']}\n\n"
        f"> ⛏ *\"{q['fr']}\"*\n"
        f"> — **{q['author']}**, {q['context_fr']}"
    )
    return QUOTE_MARK.sub(
        f"<!-- QUOTE_START -->\n{block}\n<!-- QUOTE_END -->", content
    )


def main() -> int:
    if not README.exists():
        print("README.md not found", file=sys.stderr)
        return 1
    content = README.read_text(encoding="utf-8")
    new_content = rotate_quote(content)
    if new_content != content:
        README.write_text(new_content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
