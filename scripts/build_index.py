"""Regenerate docs/index.html - the hub that lists every week's themed page.

Each themed week page declares its own theme via a meta tag:

    <meta name="theme-name" content="Lord of the Rings">

so the index can label the archive without a separate manifest to maintain.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEEKS_DIR = ROOT / "docs" / "weeks"
DATA_DIR = ROOT / "data"
INDEX = ROOT / "docs" / "index.html"

# Absolute base URL — link previews require absolute og:image URLs.
SITE = "https://scoducks8.github.io/fantasy-power-rankings"

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.I | re.S)
THEME_RE = re.compile(
    r'<meta\s+name=["\']theme-name["\']\s+content=["\'](.*?)["\']', re.I
)


def discover_weeks() -> list[dict]:
    weeks = []
    for path in sorted(WEEKS_DIR.glob("week-*.html")):
        match = re.fullmatch(r"week-(\d+)", path.stem)
        if not match:
            continue
        source = path.read_text(errors="ignore")
        title = TITLE_RE.search(source)
        theme = THEME_RE.search(source)
        weeks.append(
            {
                "number": int(match.group(1)),
                "href": f"weeks/{path.name}",
                "title": html.unescape(title.group(1).strip()) if title else path.stem,
                "theme": html.unescape(theme.group(1).strip()) if theme else "",
            }
        )
    return sorted(weeks, key=lambda w: w["number"], reverse=True)


def draft_recap() -> dict | None:
    """The draft recap is a one-off page, not a week — surface it separately."""
    path = ROOT / "docs" / "draft-recap.html"
    if not path.exists():
        return None
    source = path.read_text(errors="ignore")
    title = TITLE_RE.search(source)
    return {
        "href": "draft-recap.html",
        "title": html.unescape(title.group(1).strip()) if title else "Draft Recap",
    }


def load_latest() -> dict | None:
    path = DATA_DIR / "latest.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def render(weeks: list[dict], latest: dict | None, recap: dict | None = None) -> str:
    league = (latest or {}).get("league_name", "Fantasy Football")
    esc = html.escape

    if weeks:
        cards = "\n".join(
            f"""      <a class="week-card" href="{esc(w['href'])}">
        <span class="week-num">Week {w['number']}</span>
        <span class="week-theme">{esc(w['theme'] or 'Power Rankings')}</span>
      </a>"""
            for w in weeks
        )
    else:
        cards = (
            '      <p class="empty">No week pages yet. The first one lands '
            "after Week 1 wraps.</p>"
        )

    feature = ""
    if recap:
        feature = f"""    <section class="feature">
      <a class="feature-card" href="{esc(recap['href'])}">
        <span class="feature-kicker">Season preview</span>
        <span class="feature-title">2026 Draft Recap</span>
        <span class="feature-sub">Power rankings, biggest reaches, best values</span>
      </a>
    </section>"""

    podium = ""
    if latest and latest.get("teams"):
        rows = "\n".join(
            f"""        <li>
          <span class="pos">{t['rank']}</span>
          <span class="team">{esc(t['name'])}</span>
          <span class="rec">{t['wins']}-{t['losses']}{f"-{t['ties']}" if t['ties'] else ''}</span>
        </li>"""
            for t in latest["teams"][:3]
        )
        podium = f"""    <section class="podium">
      <h2>Current top three <span class="wk">after Week {latest['week']}</span></h2>
      <ol>
{rows}
      </ol>
    </section>"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(league)} — Power Rankings</title>
<meta name="description" content="Weekly fantasy football power rankings for {esc(league)}." />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="{esc(league)}" />
<meta property="og:url" content="{SITE}/" />
<meta property="og:title" content="{esc(league)} — Power Rankings" />
<meta property="og:description" content="Weekly power rankings. New theme every week." />
<meta property="og:image" content="{SITE}/og-league.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content="{SITE}/og-league.png" />
<link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="hub-header">
    <h1>{esc(league)}</h1>
    <p class="tagline">Weekly power rankings. New theme every week.</p>
  </header>
  <main>
{feature}
{podium}
    <section class="archive">
      <h2>The archive</h2>
      <div class="week-grid">
{cards}
      </div>
    </section>
  </main>
  <footer>
    <p>Rankings weight overall record, recent momentum, scoring, and luck.
       Data pulled from ESPN every Tuesday morning.</p>
  </footer>
</body>
</html>
"""


def main() -> None:
    WEEKS_DIR.mkdir(parents=True, exist_ok=True)
    weeks = discover_weeks()
    INDEX.write_text(render(weeks, load_latest(), draft_recap()))
    print(f"Wrote docs/index.html with {len(weeks)} week(s).")


if __name__ == "__main__":
    main()
