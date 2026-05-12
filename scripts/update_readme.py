#!/usr/bin/env python3
"""Rotate the Minecraft quote + refresh CurseForge stats in README.md."""
from __future__ import annotations

import json
import random
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
QUOTES_FILE = ROOT / "scripts" / "quotes.json"
CF_PROJECTS_FILE = ROOT / "scripts" / "cf_projects.json"

QUOTE_MARK = re.compile(r"<!-- QUOTE_START -->.*?<!-- QUOTE_END -->", re.DOTALL)
CF_MARK = re.compile(r"<!-- CURSEFORGE_START -->.*?<!-- CURSEFORGE_END -->", re.DOTALL)

CFWIDGET_BASE = "https://api.cfwidget.com"
BADGE_COLOR = "FF7B29"
BADGE_BG = "0d1117"
TOP_N = 5


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


def fetch_json(url: str) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": "vyrriox-profile-readme/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"fetch failed for {url}: {e}", file=sys.stderr)
        return None


def fetch_cf_projects() -> list[dict]:
    projects = json.loads(CF_PROJECTS_FILE.read_text(encoding="utf-8"))
    out: list[dict] = []
    for p in projects:
        url = f"{CFWIDGET_BASE}/{p['url_path']}"
        data = fetch_json(url)
        if not data:
            continue
        downloads = (data.get("downloads") or {}).get("total", 0) or 0
        title = p.get("label") or data.get("title") or p["url_path"]
        cf_id = data.get("id")
        url_field = data.get("urls", {}).get("curseforge") or f"https://www.curseforge.com/{p['url_path']}"
        out.append({
            "id": cf_id,
            "title": title,
            "downloads": int(downloads),
            "url": url_field,
        })
    return out


def fmt_downloads(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def url_encode(s: str) -> str:
    return urllib.parse.quote(s, safe="")


def make_badge(label: str, value: str, logo: str | None = None) -> str:
    parts = [
        f"https://img.shields.io/badge/{url_encode(label)}-{url_encode(value)}-{BADGE_COLOR}",
        f"style=for-the-badge",
        f"labelColor={BADGE_BG}",
    ]
    if logo:
        parts.append(f"logo={logo}")
        parts.append("logoColor=white")
    return parts[0] + "?" + "&".join(parts[1:])


def build_curseforge_block(projects: list[dict]) -> str:
    if not projects:
        return "_No CurseForge data available right now / Aucune donnée CurseForge pour le moment._"

    total_downloads = sum(p["downloads"] for p in projects)
    total_count = len(projects)
    top = sorted(projects, key=lambda p: p["downloads"], reverse=True)[:TOP_N]

    header_badges = [
        f"![Total Downloads]({make_badge('Total Downloads', fmt_downloads(total_downloads), 'curseforge')})",
        f"![Projects]({make_badge('Projects', str(total_count), 'curseforge')})",
    ]
    header = " ".join(header_badges)

    rows = []
    for p in top:
        title = p["title"]
        badge_value = fmt_downloads(p["downloads"]) + " dl"
        rows.append(f"[![{title}]({make_badge(title, badge_value, 'curseforge')})]({p['url']})")

    return header + "\n\n" + "\n".join(rows)


def update_curseforge(content: str) -> str:
    projects = fetch_cf_projects()
    block = build_curseforge_block(projects)
    return CF_MARK.sub(
        f"<!-- CURSEFORGE_START -->\n{block}\n<!-- CURSEFORGE_END -->",
        content,
    )


def main() -> int:
    if not README.exists():
        print("README.md not found", file=sys.stderr)
        return 1
    content = README.read_text(encoding="utf-8")
    content = rotate_quote(content)
    content = update_curseforge(content)
    README.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
