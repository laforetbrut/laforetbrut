"""Self-hosted SVG cards for the profile README (stats overview and repository cards).

@author vyrriox
"""
from __future__ import annotations

import re
from html import escape
from pathlib import Path

ACCENT = "#FF7B29"
BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
FONT = 'font-family="Segoe UI, Helvetica, Arial, sans-serif"'

LANG_COLORS = {
    "Lua": "#6b8cff", "JavaScript": "#f1e05a", "Java": "#b07219", "Python": "#3572A5",
    "PHP": "#4F5D95", "Blade": "#f7523f", "TypeScript": "#3178c6", "CSS": "#563d7c",
    "HTML": "#e34c26", "Rust": "#dea584", "Kotlin": "#A97BFF",
}

STAR_PATH = ("M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97"
             ".719 4.192a.75.75 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194"
             "L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z")
REPO_PATH = ("M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5"
             "h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1"
             "v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1"
             "-.4.2l-1.45-1.087a.25.25 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z")


EMOJI = re.compile("[\U0001F000-\U0001FFFF☀-➿️]")


def _clean(text: str) -> str:
    text = EMOJI.sub("", text).replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ")
    return re.sub(r"\s+", " ", text).strip()


def _wrap(text: str, width: int, max_lines: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if len(candidate) <= width:
            line = candidate
            continue
        lines.append(line)
        line = word
        if len(lines) == max_lines:
            break
    if len(lines) < max_lines and line:
        lines.append(line)
    if len(lines) == max_lines and " ".join(lines) != " ".join(words):
        lines[-1] = lines[-1].rstrip(".,;:") + "..."
    return lines


def repo_card(name: str, description: str, stars: int, language: str | None) -> str:
    w, h = 420, 150
    desc = "".join(
        f'<tspan x="20" dy="{0 if i == 0 else 19}">{escape(l)}</tspan>'
        for i, l in enumerate(_wrap(_clean(description) or "No description.", 52, 3))
    )
    lang = ""
    if language:
        color = LANG_COLORS.get(language, MUTED)
        lang = (f'<circle cx="26" cy="{h - 22}" r="6" fill="{color}"/>'
                f'<text x="38" y="{h - 18}" fill="{MUTED}" font-size="13">{escape(language)}</text>')
    star_x = 140 if language else 20
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" {FONT}>\n'
        f'<style>.card{{animation:fade .6s ease-in-out forwards;opacity:0}}@keyframes fade{{to{{opacity:1}}}}</style>\n'
        f'<g class="card"><rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>\n'
        f'<rect x="0.5" y="0.5" width="4" height="{h - 1}" rx="2" fill="{ACCENT}"/>\n'
        f'<path d="{REPO_PATH}" fill="{MUTED}" transform="translate(20 20)"/>\n'
        f'<text x="44" y="33" fill="{ACCENT}" font-size="16" font-weight="600">{escape(name)}</text>\n'
        f'<text x="20" y="62" fill="{TEXT}" font-size="13">{desc}</text>\n'
        f'{lang}<path d="{STAR_PATH}" fill="{MUTED}" transform="translate({star_x} {h - 30})"/>'
        f'<text x="{star_x + 22}" y="{h - 18}" fill="{MUTED}" font-size="13">{stars}</text></g>\n'
        f'</svg>\n'
    )


def link_card(title: str, subtitle: str) -> str:
    w, h = 420, 150
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" {FONT}>\n'
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{BORDER}" stroke-dasharray="6 5"/>\n'
        f'<text x="{w / 2}" y="72" text-anchor="middle" fill="{ACCENT}" font-size="17" font-weight="600">{escape(title)} &#8594;</text>\n'
        f'<text x="{w / 2}" y="96" text-anchor="middle" fill="{MUTED}" font-size="13">{escape(subtitle)}</text>\n'
        f'</svg>\n'
    )


def stats_card(items: list[tuple[str, str]]) -> str:
    w, h = 850, 130
    col = w / len(items)
    cells = []
    for i, (label, value) in enumerate(items):
        cx = col * i + col / 2
        if i:
            cells.append(f'<line x1="{col * i:.1f}" y1="30" x2="{col * i:.1f}" y2="{h - 30}" stroke="{BORDER}"/>')
        cells.append(
            f'<g style="animation:rise .5s ease-out {i * 0.12:.2f}s forwards;opacity:0">'
            f'<text x="{cx:.1f}" y="66" text-anchor="middle" fill="{ACCENT}" font-size="32" font-weight="700">{escape(value)}</text>'
            f'<text x="{cx:.1f}" y="94" text-anchor="middle" fill="{MUTED}" font-size="13">{escape(label)}</text></g>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" {FONT}>\n'
        f'<style>@keyframes rise{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}</style>\n'
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>\n'
        f'{"".join(cells)}\n</svg>\n'
    )


def _fmt_date(iso: str) -> str:
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{months[int(iso[5:7]) - 1]} {int(iso[8:10])}" if iso else ""


def streak_card(current: int, longest: int, total: int, since: str) -> str:
    w, h = 850, 190
    since_label = f"since {_fmt_date(since)}" if current else "no active streak"

    def side(x: float, value: str, label: str) -> str:
        return (f'<text x="{x}" y="92" text-anchor="middle" fill="{TEXT}" font-size="30" font-weight="700">{value}</text>'
                f'<text x="{x}" y="124" text-anchor="middle" fill="{MUTED}" font-size="14">{label}</text>')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" {FONT}>\n'
        f'<style>.ring{{stroke-dasharray:252;stroke-dashoffset:252;animation:draw 1.2s ease-out forwards}}'
        f'@keyframes draw{{to{{stroke-dashoffset:0}}}}</style>\n'
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>\n'
        f'{side(w / 6, f"{total:,}", "Contributions, last 12 months")}\n'
        f'<line x1="{w / 3:.1f}" y1="35" x2="{w / 3:.1f}" y2="{h - 35}" stroke="{BORDER}"/>\n'
        f'<circle cx="{w / 2}" cy="80" r="40" fill="none" stroke="{BORDER}" stroke-width="5"/>\n'
        f'<circle class="ring" cx="{w / 2}" cy="80" r="40" fill="none" stroke="{ACCENT}" stroke-width="5" '
        f'transform="rotate(-90 {w / 2} 80)"/>\n'
        f'<text x="{w / 2}" y="91" text-anchor="middle" fill="{TEXT}" font-size="30" font-weight="700">{current}</text>\n'
        f'<text x="{w / 2}" y="146" text-anchor="middle" fill="{ACCENT}" font-size="15" font-weight="600">Current streak</text>\n'
        f'<text x="{w / 2}" y="166" text-anchor="middle" fill="{MUTED}" font-size="12">{since_label}</text>\n'
        f'<line x1="{2 * w / 3:.1f}" y1="35" x2="{2 * w / 3:.1f}" y2="{h - 35}" stroke="{BORDER}"/>\n'
        f'{side(5 * w / 6, str(longest), "Longest streak, days")}\n'
        f'</svg>\n'
    )


def write(path: Path, svg: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
