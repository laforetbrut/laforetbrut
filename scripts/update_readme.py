#!/usr/bin/env python3
"""Rotate the Minecraft quote, refresh CurseForge stats, languages, activity graph and SVG cards.

@author vyrriox
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import cards

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
QUOTES_FILE = ROOT / "scripts" / "quotes.json"
CF_PROJECTS_FILE = ROOT / "scripts" / "cf_projects.json"

QUOTE_MARK = re.compile(r"<!-- QUOTE_START -->.*?<!-- QUOTE_END -->", re.DOTALL)
CF_MARK = re.compile(r"<!-- CURSEFORGE_START -->.*?<!-- CURSEFORGE_END -->", re.DOTALL)
LANG_MARK = re.compile(r"<!-- LANGUAGES_START -->.*?<!-- LANGUAGES_END -->", re.DOTALL)
ACTIVITY_SVG = ROOT / "assets" / "activity.svg"
CARDS_DIR = ROOT / "assets" / "cards"
CARD_REPOS = [
    "laforetbrut/v-core-framework-fivem", "laforetbrut/v-phone-fivem", "laforetbrut/v-hud-fivem",
    "laforetbrut/v-sport-fivem", "laforetbrut/v-park-fivem",
    "Team-Arcadia/Arcadia-V2-Client", "Team-Arcadia/Arcadia-Admin-Pannel", "Team-Arcadia/Arcadia-Games",
    "Team-Arcadia/Arcadia-Dungeon", "Team-Arcadia/Arcadia-RsPolymorph", "Team-Arcadia/Arcadia-LootBox",
]

GH_USER = "laforetbrut"
GH_ORG = "Team-Arcadia"
GH_API = "https://api.github.com"
LANG_LOGOS = {
    "Java": "openjdk", "PHP": "php", "Blade": "laravel", "JavaScript": "javascript",
    "Python": "python", "Lua": "lua", "TypeScript": "typescript", "HTML": "html5",
    "CSS": "css", "Rust": "rust", "Shell": "gnubash", "Kotlin": "kotlin",
}

CFWIDGET_BASE = "https://api.cfwidget.com"
BADGE_COLOR = "FF7B29"
BADGE_BG = "0d1117"
TOP_N = 5


def rotate_quote(content: str) -> str:
    quotes = json.loads(QUOTES_FILE.read_text(encoding="utf-8"))
    q = random.choice(quotes)
    block = (
        f"> *\"{q['en']}\"*\n"
        f"> **{q['author']}**, {q['context_en']}\n\n"
        f"> *\"{q['fr']}\"*\n"
        f"> **{q['author']}**, {q['context_fr']}"
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


def update_curseforge(content: str, projects: list[dict]) -> str:
    block = build_curseforge_block(projects)
    return CF_MARK.sub(
        f"<!-- CURSEFORGE_START -->\n{block}\n<!-- CURSEFORGE_END -->",
        content,
    )


def gh_request(url: str, body: dict | None = None) -> dict | list | None:
    headers = {"User-Agent": "vyrriox-profile-readme/1.0", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"github request failed for {url}: {e}", file=sys.stderr)
        return None


def list_public_repos(owner: str, kind: str) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        batch = gh_request(f"{GH_API}/{kind}/{owner}/repos?type=public&per_page=100&page={page}")
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(r for r in batch if not r.get("private") and not r.get("fork"))
        if len(batch) < 100:
            break
        page += 1
    return repos


def fmt_count(n: int) -> str:
    return f"{n / 1_000:.1f}k" if n >= 1_000 else str(n)


def shield(label: str, value: str, color: str, style: str, logo: str | None) -> str:
    url = (f"https://img.shields.io/badge/{url_encode(label.replace('-', '--'))}-{url_encode(value)}-{color}"
           f"?style={style}&labelColor={BADGE_BG}")
    if logo:
        url += f"&logo={logo}&logoColor=white"
    return f"![{label}]({url})"


def build_languages_block(repos: list[dict]) -> str | None:
    totals: dict[str, int] = {}
    for r in repos:
        langs = gh_request(r["languages_url"])
        if not isinstance(langs, dict):
            continue
        for name, size in langs.items():
            totals[name] = totals.get(name, 0) + int(size)
    grand = sum(totals.values())
    if not grand:
        return None
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:6]
    return "\n".join(
        shield(name, f"{size * 100 / grand:.2f}%", BADGE_COLOR if i == 0 else "30363d",
               "flat-square", LANG_LOGOS.get(name))
        for i, (name, size) in enumerate(top)
    )


def fetch_contribution_days() -> list[tuple[str, int]]:
    query = ("query($login:String!){user(login:$login){contributionsCollection{contributionCalendar"
             "{weeks{contributionDays{date contributionCount}}}}}}")
    data = gh_request(f"{GH_API}/graphql", {"query": query, "variables": {"login": GH_USER}})
    try:
        weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    except (TypeError, KeyError):
        return []
    return [(d["date"], d["contributionCount"]) for w in weeks for d in w["contributionDays"]]


def build_activity_svg(days: list[tuple[str, int]], span: int = 31) -> str:
    days = days[-span:]
    w, h = 850, 300
    left, right, top, bottom = 50, 20, 50, 45
    pw, ph = w - left - right, h - top - bottom
    peak = max((c for _, c in days), default=0) or 1
    step = pw / max(len(days) - 1, 1)
    pts = [(left + i * step, top + ph - c / peak * ph) for i, (_, c) in enumerate(days)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{left},{top + ph} {line} {left + pw},{top + ph}"
    total = sum(c for _, c in days)
    font = 'font-family="Segoe UI, Helvetica, Arial, sans-serif"'

    parts = []
    for k in range(5):
        y = top + ph * k / 4
        val = round(peak * (4 - k) / 4)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + pw}" y2="{y:.1f}" stroke="#21262d"/>')
        parts.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end">{val}</text>')
    for i, (date, _) in enumerate(days):
        if i % 5 == 0 or i == len(days) - 1:
            parts.append(f'<text x="{pts[i][0]:.1f}" y="{h - 20}" text-anchor="middle">{date[8:10]}/{date[5:7]}</text>')
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#ffffff"/>' for x, y in pts)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
        f'<defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="#{BADGE_COLOR}" stop-opacity="0.45"/>'
        f'<stop offset="100%" stop-color="#{BADGE_COLOR}" stop-opacity="0"/></linearGradient></defs>\n'
        f'<rect width="{w}" height="{h}" rx="8" fill="#0d1117"/>\n'
        f'<text x="{w / 2}" y="30" text-anchor="middle" fill="#{BADGE_COLOR}" {font} font-size="18" font-weight="600">'
        f'Contributions, last {len(days)} days ({total})</text>\n'
        f'<g fill="#8b949e" {font} font-size="11">{"".join(parts)}</g>\n'
        f'<polygon points="{area}" fill="url(#fill)"/>\n'
        f'<polyline points="{line}" fill="none" stroke="#{BADGE_COLOR}" stroke-width="2.5" stroke-linejoin="round"/>\n'
        f'{dots}\n</svg>\n'
    )


def build_cards(user_repos: list[dict], org_repos: list[dict], days: list[tuple[str, int]],
                cf_projects: list[dict]) -> None:
    by_name = {f"{r['owner']['login']}/{r['name']}": r for r in user_repos + org_repos}
    for full_name in CARD_REPOS:
        repo = by_name.get(full_name)
        if repo:
            svg = cards.repo_card(repo["name"], repo.get("description") or "", repo.get("stargazers_count", 0),
                                  repo.get("language"))
            cards.write(CARDS_DIR / f"{repo['name'].lower()}.svg", svg)

    cards.write(CARDS_DIR / "more-fivem.svg",
                cards.link_card("All FiveM repositories", "Tous les repos FiveM"))

    if not user_repos and not org_repos:
        return
    stars = sum(r.get("stargazers_count", 0) for r in user_repos + org_repos)
    items = [("GitHub stars earned", fmt_count(stars))]
    if days:
        items.append(("Contributions, last 12 months", fmt_count(sum(c for _, c in days))))
    items.append(("Public repositories", str(len(user_repos) + len(org_repos))))
    if cf_projects:
        items.append(("CurseForge downloads", fmt_downloads(sum(p["downloads"] for p in cf_projects))))
    cards.write(CARDS_DIR / "stats.svg", cards.stats_card(items))


def update_github(content: str, cf_projects: list[dict]) -> str:
    user_repos = list_public_repos(GH_USER, "users")
    org_repos = list_public_repos(GH_ORG, "orgs")

    langs = build_languages_block(user_repos + org_repos)
    if langs:
        content = LANG_MARK.sub(f"<!-- LANGUAGES_START -->\n{langs}\n<!-- LANGUAGES_END -->", content)

    days = fetch_contribution_days()
    if days:
        ACTIVITY_SVG.parent.mkdir(exist_ok=True)
        ACTIVITY_SVG.write_text(build_activity_svg(days), encoding="utf-8")

    build_cards(user_repos, org_repos, days, cf_projects)
    return content


def main() -> int:
    if not README.exists():
        print("README.md not found", file=sys.stderr)
        return 1
    content = README.read_text(encoding="utf-8")
    content = rotate_quote(content)
    cf_projects = fetch_cf_projects()
    content = update_curseforge(content, cf_projects)
    content = update_github(content, cf_projects)
    README.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
