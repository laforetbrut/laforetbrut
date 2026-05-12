#!/usr/bin/env python3
"""Rotate Minecraft quote + refresh recent commits in README.md."""
from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
QUOTES_FILE = ROOT / "scripts" / "quotes.json"

QUOTE_MARK = re.compile(r"<!-- QUOTE_START -->.*?<!-- QUOTE_END -->", re.DOTALL)
BUILD_MARK = re.compile(
    r"<!-- CURRENTLY_BUILDING_START -->.*?<!-- CURRENTLY_BUILDING_END -->",
    re.DOTALL,
)

GH_USER = "laforetbrut"
GH_ORG = "Team-Arcadia"
MAX_ITEMS = 6


def rotate_quote(content: str) -> str:
    quotes = json.loads(QUOTES_FILE.read_text(encoding="utf-8"))
    q = random.choice(quotes)
    en = q["en"].replace('"', '\\"')
    fr = q["fr"].replace('"', '\\"')
    block = (
        f"> ⛏ *\"{q['en']}\"*\n"
        f"> — **{q['author']}**, {q['context_en']}\n\n"
        f"> ⛏ *\"{q['fr']}\"*\n"
        f"> — **{q['author']}**, {q['context_fr']}"
    )
    return QUOTE_MARK.sub(
        f"<!-- QUOTE_START -->\n{block}\n<!-- QUOTE_END -->", content
    )


def gh_api(path: str) -> object | None:
    """Call gh api and return parsed JSON, or None on failure."""
    result = subprocess.run(
        ["gh", "api", path],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        print(f"gh api {path} failed: {result.stderr}", file=sys.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def fetch_recent_commits() -> list[dict]:
    """Use GitHub Search API to find recent commits authored by the user."""
    query = f"author:{GH_USER}"
    encoded = urllib.parse.quote(query, safe=":")
    path = f"search/commits?q={encoded}&sort=author-date&order=desc&per_page=30"
    payload = gh_api(path)
    if not payload or "items" not in payload:
        return []

    items: list[dict] = []
    seen_repos: set[str] = set()
    for item in payload["items"]:
        repo = item.get("repository", {}).get("full_name", "")
        if not repo or repo in seen_repos:
            continue
        seen_repos.add(repo)
        commit = item.get("commit", {})
        message = (commit.get("message") or "").splitlines()[0].strip()
        sha_full = item.get("sha", "")
        sha = sha_full[:7]
        html_url = item.get("html_url", "")
        if not (repo and message and sha and html_url):
            continue
        items.append({"repo": repo, "msg": message, "sha": sha, "url": html_url})
        if len(items) >= MAX_ITEMS:
            break
    return items


def update_currently_building(content: str) -> str:
    items = fetch_recent_commits()
    if items:
        lines = [
            f"- [`{it['sha']}`]({it['url']}) **{it['repo']}** — {it['msg']}"
            for it in items
        ]
        block = "\n".join(lines)
    else:
        block = "- _No recent public activity / Aucune activité publique récente_"

    return BUILD_MARK.sub(
        f"<!-- CURRENTLY_BUILDING_START -->\n{block}\n<!-- CURRENTLY_BUILDING_END -->",
        content,
    )


def main() -> int:
    if not README.exists():
        print("README.md not found", file=sys.stderr)
        return 1
    content = README.read_text(encoding="utf-8")
    content = rotate_quote(content)
    content = update_currently_building(content)
    README.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
