"""Matchup preview page for the coming week, in the clean theme.

    python3 scripts/render_preview.py --week 6

Reads data/copy-preview-week-N.json and the latest rankings (week N-1).
Writes docs/weeks/preview-week-N.html.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from render_week import asset, load_skin, SITE  # noqa: E402

ROOT = HERE.parent
e = html.escape


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    a = ap.parse_args()
    wk = a.week
    copy = json.loads((ROOT / "data" / f"copy-preview-week-{wk}.json").read_text())
    data = json.loads((ROOT / "data" / f"week-{wk - 1}.json").read_text())
    by_id = {t["team_id"]: t for t in data["teams"]}

    def side(t):
        rec = f'{t["wins"]}-{t["losses"]}' + (f'-{t["ties"]}' if t.get("ties") else "")
        img = e(asset(t.get("logo_local", ""), t.get("logo", ""), t["owner"]))
        return (f'<div class="pv-side"><img src="{img}" alt="">'
                f'<span class="nm">{e(t["name"])}</span>'
                f'<span class="pv-rk">No. {t["rank"]} &middot; {rec}</span></div>')

    cards = ""
    for g in copy["games"]:
        A, B = by_id[g["a"]], by_id[g["b"]]
        tag = '<p class="pv-tag">Game of the week</p>' if g.get("gotw") else ""
        cards += f'''<article class="pv{' gotw' if g.get('gotw') else ''}">
  {tag}<div class="pv-teams">{side(A)}<span class="pv-vs">vs</span>{side(B)}</div>
  <p class="pv-text">{e(g["text"])}</p>
</article>'''

    css = """
.pvs{display:grid;gap:14px}
.pv{background:var(--surface);border:1px solid var(--hair);border-radius:14px;padding:16px 18px}
.pv.gotw{box-shadow:inset 3px 0 0 var(--gold)}
.pv-tag{margin:0 0 10px;font:600 12px/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;color:var(--gold)}
.pv-teams{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;gap:12px}
.pv-side{display:grid;grid-template-columns:36px minmax(0,1fr);column-gap:10px;align-items:center;min-width:0}
.pv-side img{grid-row:span 2;width:36px;height:36px;border-radius:50%;object-fit:cover}
.pv-side .nm{font:600 15px/1.25 var(--sans);overflow-wrap:anywhere}
.pv-side .pv-rk{font:400 13px/1.3 var(--sans);color:var(--muted)}
.pv-vs{font:500 13px/1 var(--sans);color:var(--muted)}
.pv-text{margin:14px 0 0;font-family:var(--serif);font-size:17px;line-height:1.6}
@media (max-width:520px){
  .pv-teams{grid-template-columns:minmax(0,1fr);gap:8px}
  .pv-vs{display:none}
}
"""
    og_img = f"og-preview-week-{wk}.png"
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="theme-name" content="Clean" />
<meta name="color-scheme" content="light dark" />
<title>Week {wk} preview &middot; {e(data["league_name"])}</title>
<meta name="description" content="{e(copy["og_description"])}" />
<meta property="og:type" content="article" />
<meta property="og:site_name" content="{e(data["league_name"])}" />
<meta property="og:url" content="{SITE}/weeks/preview-week-{wk}.html" />
<meta property="og:title" content="{e(copy["og_title"])}" />
<meta property="og:description" content="{e(copy["og_description"])}" />
<meta property="og:image" content="{SITE}/{og_img}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content="{SITE}/{og_img}" />
<style>{load_skin("clean")}{css}</style>
</head>
<body>
<nav class="top"><div class="top-in">
  <a class="brand" href="../index.html"><span class="full">{e(data["league_name"])}</span><span class="short">CCL</span></a>
  <div class="links"><a href="week-{wk - 1}.html">Week {wk - 1} rankings</a></div>
</div></nav>
<main>
  <header class="intro">
    <p class="kicker">Week {wk} preview</p>
    <h1>{e(copy["headline"])}</h1>
    <p class="dek">{e(copy["standfirst"])}</p>
  </header>
  <section id="matchups">
    <h2>Matchups</h2>
    <div class="pvs">{cards}</div>
  </section>
  <footer class="foot"><p>Records and ranks are through week {wk - 1}.
    <a href="../index.html">All weeks</a></p></footer>
</main>
</body>
</html>
'''
    out = ROOT / "docs" / "weeks" / f"preview-week-{wk}.html"
    out.write_text(page)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
