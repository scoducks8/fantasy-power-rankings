"""Scaffold a themed week page from that week's data.

    python scripts/new_week.py --week 5 --theme "Lord of the Rings"

Writes docs/weeks/week-5.html with every team's real numbers already in
place and a clearly marked commentary slot per team. The theme colours and
the copy are then hand-edited - that's the part worth doing by hand.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
WEEKS_DIR = ROOT / "docs" / "weeks"

# Absolute base URL — link previews require absolute og:image URLs.
SITE = "https://scoducks8.github.io/fantasy-power-rankings"

# Swap these four values and the whole page changes character.
DEFAULT_PALETTE = {
    "bg": "#0e1116",
    "panel": "#171c24",
    "accent": "#4ade80",
    "text": "#e6e9ef",
}


def movement_badge(move: int) -> str:
    if move > 0:
        return f'<span class="move up">▲ {move}</span>'
    if move < 0:
        return f'<span class="move down">▼ {abs(move)}</span>'
    return '<span class="move flat">—</span>'


def team_block(team: dict) -> str:
    esc = html.escape
    record = f"{team['wins']}-{team['losses']}"
    if team.get("ties"):
        record += f"-{team['ties']}"

    last = team.get("last_result")
    if last:
        result_line = (
            f"{last['result']} {last['score']:.1f}–{last['opponent_score']:.1f} "
            f"vs {esc(last['opponent'])}"
        )
    else:
        result_line = "Bye"

    logo = team.get("logo_local") or ""
    logo_html = (
        f'<img class="logo" src="../{esc(logo)}" alt="">'
        if logo
        else '<div class="logo placeholder"></div>'
    )

    return f"""    <article class="team">
      <div class="rank">{team['rank']}</div>
      {logo_html}
      <div class="body">
        <h3>{esc(team['name'])} {movement_badge(team['movement'])}</h3>
        <p class="stats">
          <span>{record}</span>
          <span>{esc(team.get('streak') or '—')}</span>
          <span>{team['points_for']:.1f} PF</span>
          <span>{result_line}</span>
        </p>
        <!-- COMMENTARY: {esc(team['name'])} -->
        <p class="take">Write this team's take here.</p>
      </div>
    </article>"""


def render(data: dict, theme: str, palette: dict) -> str:
    esc = html.escape
    blocks = "\n".join(team_block(t) for t in data["teams"])

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-name" content="{esc(theme)}">
<title>Week {data['week']}: {esc(theme)}</title>
<meta name="description" content="Week {data['week']} power rankings for {esc(data['league_name'])}." />
<meta property="og:type" content="article" />
<meta property="og:site_name" content="{esc(data['league_name'])}" />
<meta property="og:url" content="{SITE}/weeks/week-{data['week']}.html" />
<meta property="og:title" content="Week {data['week']}: {esc(theme)}" />
<meta property="og:description" content="Power rankings for week {data['week']} of {esc(data['league_name'])}." />
<meta property="og:image" content="{SITE}/og-league.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content="{SITE}/og-league.png" />
<style>
  :root {{
    --bg: {palette['bg']};
    --panel: {palette['panel']};
    --accent: {palette['accent']};
    --text: {palette['text']};
    --muted: #949cab;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
          Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .wrap {{ max-width: 760px; margin: 0 auto; padding: 48px 20px 80px; }}
  .back {{ color: var(--muted); text-decoration: none; font-size: 14px; }}
  .back:hover {{ color: var(--accent); }}
  h1 {{ font-size: clamp(30px, 7vw, 48px); margin: 20px 0 4px;
        letter-spacing: -0.02em; }}
  .kicker {{ color: var(--accent); text-transform: uppercase;
             letter-spacing: 0.12em; font-size: 13px; font-weight: 700;
             margin: 0; }}
  .intro {{ color: var(--muted); margin: 12px 0 40px; font-size: 17px; }}

  .team {{
    display: grid;
    grid-template-columns: 44px 52px 1fr;
    gap: 16px; align-items: start;
    padding: 22px 0; border-top: 1px solid rgba(255,255,255,0.08);
  }}
  .rank {{ font-size: 30px; font-weight: 800; color: var(--accent);
           font-variant-numeric: tabular-nums; line-height: 1.1; }}
  .logo {{ width: 52px; height: 52px; border-radius: 10px;
           object-fit: cover; background: var(--panel); }}
  .logo.placeholder {{ display: block; }}
  .body h3 {{ margin: 0 0 6px; font-size: 20px; letter-spacing: -0.01em; }}
  .stats {{ display: flex; flex-wrap: wrap; gap: 14px; margin: 0 0 10px;
            color: var(--muted); font-size: 14px;
            font-variant-numeric: tabular-nums; }}
  .take {{ margin: 0; }}
  .move {{ font-size: 13px; font-weight: 700; vertical-align: middle; }}
  .move.up {{ color: #4ade80; }}
  .move.down {{ color: #f87171; }}
  .move.flat {{ color: var(--muted); }}

  footer {{ margin-top: 48px; padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.08);
            color: var(--muted); font-size: 14px; }}

  @media (max-width: 480px) {{
    .team {{ grid-template-columns: 34px 40px 1fr; gap: 12px; }}
    .logo {{ width: 40px; height: 40px; }}
    .rank {{ font-size: 24px; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <a class="back" href="../index.html">← All weeks</a>
  <p class="kicker">Week {data['week']} · {esc(data['league_name'])}</p>
  <h1>{esc(theme)}</h1>
  <p class="intro">Write the week's opening paragraph here — the theme
     framing, the big storyline, the one game everybody is still mad about.</p>

{blocks}

  <footer>
    <p>Ranked by overall record, then momentum, then scoring and luck.
       Data as of {esc(data['generated_at'])}.</p>
  </footer>
</div>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--theme", required=True)
    parser.add_argument("--force", action="store_true",
                        help="overwrite an existing page for this week")
    args = parser.parse_args()

    data_path = DATA_DIR / f"week-{args.week}.json"
    if not data_path.exists():
        sys.exit(f"No data for week {args.week}. Run update_week.py first.")

    WEEKS_DIR.mkdir(parents=True, exist_ok=True)
    out = WEEKS_DIR / f"week-{args.week}.html"
    if out.exists() and not args.force:
        sys.exit(f"{out.relative_to(ROOT)} already exists. Pass --force to replace it.")

    data = json.loads(data_path.read_text())
    out.write_text(render(data, args.theme, DEFAULT_PALETTE))
    print(f"Wrote {out.relative_to(ROOT)} — now edit the commentary and palette.")


if __name__ == "__main__":
    main()
