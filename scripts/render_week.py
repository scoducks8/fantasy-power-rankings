"""Weekly power rankings page.

Full-bleed hero built around the week's best performance, the results board,
ranked team write-ups, scoring by position, and the season rank line.

    python scripts/render_week.py --week 1 --theme "Lord of the Rings"

Writes docs/weeks/week-N.html from data/week-N.json. Edit the copy in the
generated file afterwards — the takes and the framing are hand-written.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
SITE = "https://scoducks8.github.io/fantasy-power-rankings"

POS_COLOR = {"QB": "#3987e5", "RB": "#d95926", "WR": "#199e70",
             "TE": "#c98500", "K": "#d55181", "D/ST": "#9085e9"}
POS_ORDER = ["QB", "RB", "WR", "TE", "K", "D/ST"]

e = html.escape
PLACEHOLDER = False


def _ph(seed, kind="av"):
    import hashlib, base64
    hue = int(hashlib.md5(seed.encode()).hexdigest()[:6], 16) % 360
    ini = "".join(w[0] for w in seed.split()[:2]).upper() or "?"
    if kind == "hs":
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">'
               f'<rect width="300" height="300" fill="hsl({hue},22%,18%)"/>'
               f'<circle cx="150" cy="115" r="56" fill="hsl({hue},26%,32%)"/>'
               f'<path d="M40 300c0-64 49-110 110-110s110 46 110 110z" fill="hsl({hue},26%,32%)"/>'
               f'<text x="150" y="285" font-size="30" fill="hsl({hue},30%,70%)" '
               f'text-anchor="middle" font-family="sans-serif">{ini}</text></svg>')
    else:
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96">'
               f'<rect width="96" height="96" rx="18" fill="hsl({hue},30%,26%)"/>'
               f'<text x="48" y="60" font-size="34" font-weight="700" '
               f'fill="hsl({hue},45%,78%)" text-anchor="middle" '
               f'font-family="sans-serif">{ini}</text></svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def img(url, seed, kind="av"):
    return _ph(seed, kind) if PLACEHOLDER else url


def short_names(teams):
    """First names, with a last initial only where two managers collide."""
    first = {}
    for t in teams:
        first.setdefault(t["owner"].split()[0], []).append(t)
    out = {}
    for name, group in first.items():
        for t in group:
            parts = t["owner"].split()
            out[t["team_id"]] = (f'{name} {parts[-1][0]}.' if len(group) > 1 and len(parts) > 1
                                 else name)
    return out


def render(data, history, theme="Week One"):
    teams = data["teams"]
    mus = data["matchups"]
    SH = short_names(teams)
    hi = max(teams, key=lambda t: t["points_for"])
    best = max((s for t in teams for s in t["starters"]), key=lambda s: s["points"])
    best_team = next(t for t in teams if best in t["starters"])
    close, blow = mus[0], mus[-1]
    show_move = len(history) > 1

    # matchup strip
    strip = ""
    for m in mus:
        hw = m["winner"] == "HOME"
        strip += f'''        <div class="res{' tight' if m['margin']<10 else ''}">
          <div class="rr {'w' if not hw else ''}"><span>{e(m['away'])}</span><b>{m['away_score']:.1f}</b></div>
          <div class="rr {'w' if hw else ''}"><span>{e(m['home'])}</span><b>{m['home_score']:.1f}</b></div>
          <div class="rm">by {m['margin']:.1f}</div>
        </div>'''

    # team write-ups
    cards = ""
    for t in teams:
        top = t["top_scorer"]
        seg = "".join(
            f'<span style="width:{t["positional"].get(p,0)/t["points_for"]*100:.2f}%;'
            f'background:{POS_COLOR[p]}"></span>'
            for p in POS_ORDER if t["positional"].get(p, 0) > 0)
        chip = ""
        if show_move and t["movement"]:
            up = t["movement"] > 0
            chip = (f'<span class="mv {"up" if up else "dn"}">'
                    f'{"▲" if up else "▼"}{abs(t["movement"])}</span>')
        cards += f'''      <article class="w{' lead' if t['rank']==1 else ''}">
        <header>
          <span class="wr">{t['rank']}</span>
          <img class="wav" src="{e(img(t['logo'], t['owner']))}" alt="" loading="lazy">
          <div class="wt"><h3>{e(t['name'])}{chip}</h3><span>{e(t['owner'])}</span></div>
          <span class="wp">{t['points_for']:.1f}
            <i>{t['wins']}-{t['losses']} · {'+' if t['points_for']-t['projected_total']>=0 else ''}{t['points_for']-t['projected_total']:.1f} vs proj</i>
          </span>
        </header>
        <div class="wbar">{seg}</div>
        <div class="wmain">
          <figure><img src="{e(img(top['headshot'], top['name'], 'hs'))}" alt="" loading="lazy">
            <figcaption><b>{top['points']:.1f}</b><span>{e(top['name'])}</span></figcaption></figure>
          <p>Write this team's take here.</p>
        </div>
      </article>'''

    # positional chart
    mx = max(t["points_for"] for t in teams)
    prow = ""
    for t in sorted(teams, key=lambda x: -x["points_for"]):
        segs = "".join(
            f'<span style="width:{t["positional"].get(p,0)/mx*100:.2f}%;background:{POS_COLOR[p]}"></span>'
            for p in POS_ORDER if t["positional"].get(p, 0) > 0)
        prow += (f'<div class="prow"><div class="plbl">{e(SH[t["team_id"]])}</div>'
                 f'<div class="ptrack">{segs}</div>'
                 f'<div class="pval">{t["points_for"]:.1f}</div></div>')
    legend = "".join(f'<span><i style="background:{POS_COLOR[p]}"></i>{p}</span>'
                     for p in POS_ORDER)

    # rank line
    weeks = [h["week"] for h in history]
    n = len(teams)
    W, H, L, R, T, B = 760, 320, 30, 104, 18, 24
    span = max(1, (weeks[-1] - weeks[0]) or 1)
    fx = lambda w: L + (0 if len(weeks) == 1 else (w - weeks[0]) / span * (W - L - R))
    fy = lambda r: T + (r - 1) / (n - 1) * (H - T - B)
    svg = "".join(f'<line x1="{L}" y1="{fy(r):.1f}" x2="{W-R}" y2="{fy(r):.1f}" '
                  f'stroke="#1c2330"/>' for r in range(1, n + 1))
    for t in teams:
        pts = [(fx(h["week"]), fy(h["ranks"][str(t["team_id"])])) for h in history]
        d = " ".join(f'{"M" if i==0 else "L"}{a:.1f},{b:.1f}' for i, (a, b) in enumerate(pts))
        col = "#9fb0ff" if t["rank"] == 1 else "#39425c"
        svg += (f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.5" stroke-linecap="round"/>'
                f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="4.5" fill="{col}"/>'
                f'<text x="{pts[-1][0]+11:.1f}" y="{pts[-1][1]+4:.1f}" fill="#9aa6b2" '
                f'font-size="11.5">{e(SH[t["team_id"]])}</text>')
    svg += "".join(f'<text x="{L-9}" y="{fy(r)+4:.1f}" fill="#6b7683" font-size="10" '
                   f'text-anchor="end">{r}</text>' for r in (1, 6, 12) if r <= n)

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="theme-name" content="{e(theme)}" />
<title>Week {data['week']}: {e(theme)}</title>
<meta property="og:image" content="{SITE}/og-league.png" />
<meta name="twitter:card" content="summary_large_image" />
<style>
:root{{--bg:#080a0e;--card:#111420;--card2:#0c0f18;--ink:#f2f5f9;--muted:#98a2b1;
 --dim:#68717f;--line:#1b2231;--accent:#9fb0ff;--up:#13d18b;--down:#ff6b6b}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
 font:500 16px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial;
 -webkit-font-smoothing:antialiased}}
img{{max-width:100%}}
.bar{{position:sticky;top:0;z-index:30;background:rgba(8,10,14,.93);
 backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}}
.bar-in{{max-width:1040px;margin:0 auto;padding:11px 20px;display:flex;
 justify-content:space-between;align-items:center;gap:16px}}
.bm{{font-size:12.5px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--accent)}}
.bn{{display:flex;gap:16px;overflow-x:auto;scrollbar-width:none}}
.bn::-webkit-scrollbar{{display:none}}
.bn a{{color:var(--muted);text-decoration:none;font-size:13px;font-weight:600;white-space:nowrap}}

/* hero */
.hero{{position:relative;overflow:hidden;border-bottom:1px solid var(--line)}}
.hero-in{{max-width:1040px;margin:0 auto;padding:44px 20px 36px;
 display:grid;grid-template-columns:1fr 300px;gap:36px;align-items:center}}
.hk{{margin:0 0 12px;font-size:12px;font-weight:800;letter-spacing:.18em;
 text-transform:uppercase;color:var(--accent)}}
h1{{margin:0;font-size:clamp(32px,5.6vw,58px);line-height:1.02;letter-spacing:-.03em;font-weight:800}}
.hs{{margin:16px 0 0;color:#c9cfdb;font-size:17.5px;max-width:56ch}}
.hero figure{{margin:0;position:relative}}
.hero figure img{{width:100%;border-radius:18px;border:1px solid var(--line);
 background:var(--card2);display:block}}
.hcap{{position:absolute;left:0;right:0;bottom:0;padding:16px;border-radius:0 0 18px 18px;
 background:linear-gradient(transparent,rgba(8,10,14,.94))}}
.hcap b{{display:block;font-size:30px;font-weight:800;letter-spacing:-.02em;
 font-variant-numeric:tabular-nums;line-height:1}}
.hcap span{{display:block;margin-top:3px;font-size:13px;color:var(--muted)}}

.wrap{{max-width:1040px;margin:0 auto;padding:0 20px 80px}}
section{{padding:46px 0 0}}
.sk{{margin:0 0 6px;font-size:12px;font-weight:800;letter-spacing:.16em;
 text-transform:uppercase;color:var(--accent)}}
h2{{margin:0;font-size:clamp(23px,4.4vw,34px);letter-spacing:-.025em;font-weight:800}}
.sl{{margin:9px 0 22px;color:var(--muted);max-width:66ch}}

/* results strip */
.strip{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.res{{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:12px 14px}}
.res.tight{{border-color:rgba(251,191,36,.4)}}
.rr{{display:flex;justify-content:space-between;gap:10px;padding:4px 0;
 font-size:13.5px;color:var(--muted)}}
.rr span{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.rr b{{font-variant-numeric:tabular-nums;font-weight:700}}
.rr.w{{color:var(--ink)}} .rr.w b{{color:var(--up)}}
.rm{{margin-top:7px;padding-top:7px;border-top:1px solid var(--line);
 font-size:11.5px;color:var(--dim)}}

/* write-ups */
.ws{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.w{{background:var(--card);border:1px solid var(--line);border-radius:15px;padding:15px}}
.w.lead{{grid-column:1/-1;border-color:rgba(159,176,255,.42)}}
.w header{{display:grid;grid-template-columns:26px 40px 1fr auto;gap:10px;align-items:center}}
.wr{{font-size:21px;font-weight:800;color:var(--accent);font-variant-numeric:tabular-nums}}
.wav{{width:40px;height:40px;border-radius:11px;object-fit:cover;
 border:1px solid var(--line);background:var(--card2)}}
.wt h3{{margin:0;font-size:15.5px;font-weight:700;letter-spacing:-.01em}}
.wt span{{font-size:12px;color:var(--muted)}}
.wp{{font-size:19px;font-weight:800;font-variant-numeric:tabular-nums;text-align:right}}
.wp i{{display:block;font-style:normal;font-size:10.5px;font-weight:600;color:var(--dim);
 letter-spacing:.01em;margin-top:2px;white-space:nowrap}}
.mv{{margin-left:7px;font-size:11px;font-weight:800}}
.mv.up{{color:var(--up)}} .mv.dn{{color:var(--down)}}
.wbar{{display:flex;gap:2px;height:6px;margin:11px 0 0;border-radius:3px;overflow:hidden}}
.wbar span{{display:block}}
.wmain{{display:grid;grid-template-columns:84px 1fr;gap:13px;margin-top:13px;align-items:start}}
.wmain figure{{margin:0}}
.wmain figure img{{width:84px;height:84px;border-radius:12px;object-fit:cover;
 object-position:top center;border:1px solid var(--line);background:var(--card2)}}
.wmain figcaption{{margin-top:5px}}
.wmain figcaption b{{display:block;font-size:15px;font-variant-numeric:tabular-nums}}
.wmain figcaption span{{font-size:11px;color:var(--dim);line-height:1.3;display:block}}
.wmain p{{margin:0;color:#c9cfdb;font-size:14.5px;line-height:1.6}}
.w.lead .wmain{{grid-template-columns:120px 1fr}}
.w.lead .wmain figure img{{width:120px;height:120px}}

/* charts */
.chart{{background:var(--card);border:1px solid var(--line);border-radius:15px;padding:20px}}
.lg{{display:flex;flex-wrap:wrap;gap:15px;margin-bottom:16px;font-size:12px;color:var(--muted)}}
.lg span{{display:inline-flex;align-items:center;gap:6px}}
.lg i{{width:11px;height:11px;border-radius:3px;display:block}}
.prow{{display:grid;grid-template-columns:74px 1fr 52px;gap:11px;align-items:center;padding:5px 0}}
.plbl{{font-size:12.5px;color:var(--muted);text-align:right;white-space:nowrap;
 overflow:hidden;text-overflow:ellipsis}}
.ptrack{{display:flex;gap:2px;height:20px}}
.ptrack span{{display:block;border-radius:2px}}
.ptrack span:first-child{{border-radius:5px 2px 2px 5px}}
.ptrack span:last-child{{border-radius:2px 5px 5px 2px}}
.pval{{font-size:13px;font-variant-numeric:tabular-nums;color:var(--muted);font-weight:700}}
.cnote{{margin:14px 0 0;font-size:12.5px;color:var(--dim)}}

footer{{margin-top:56px;padding-top:22px;border-top:1px solid var(--line);
 color:var(--dim);font-size:13px}}

@media (max-width:900px){{
  .hero-in{{grid-template-columns:1fr;gap:24px}}
  .hero figure{{max-width:280px}}
  .strip{{grid-template-columns:1fr 1fr}}
  .ws{{grid-template-columns:1fr}}
  .w.lead .wmain{{grid-template-columns:84px 1fr}}
  .w.lead .wmain figure img{{width:84px;height:84px}}
}}
@media (max-width:560px){{
  .strip{{grid-template-columns:1fr}}
  .prow{{grid-template-columns:58px 1fr 46px}}
  td.tm i{{display:none}}
  th:nth-child(6),td:nth-child(6){{display:none}}
}}
</style>
</head>
<body>
<div class="bar"><div class="bar-in">
  <div class="bm">Chach Champions</div>
  <nav class="bn"><a href="#scores">Scores</a><a href="#teams">Rankings</a><a href="#positions">Positions</a><a href="#season">Season</a></nav>
</div></div>

<header class="hero"><div class="hero-in">
  <div>
    <p class="hk">Week {data['week']} · {e(theme)}</p>
    <h1>Opening weekend, and the board already looks nothing like the draft.</h1>
    <p class="hs">Write the week's framing here — the theme, the storyline, the game
      everyone is still arguing about on Tuesday morning.</p>
  </div>
  <figure>
    <img src="{e(img(best['headshot'], best['name'], 'hs'))}" alt="{e(best['name'])}" />
    <figcaption class="hcap"><b>{best['points']:.1f}</b>
      <span>{e(best['name'])} · {e(SH[best_team['team_id']])}'s best</span></figcaption>
  </figure>
</div></header>

<div class="wrap">
  <section id="scores">
    <p class="sk">The slate</p><h2>Week {data['week']} results</h2>
    <p class="sl">Closest game first. Gold border means it was decided by under ten.</p>
    <div class="strip">
{strip}
    </div>
  </section>

  <section id="teams">
    <p class="sk">Power rankings</p><h2>Every team, ranked</h2>
    <p class="sl">The bar under each name splits that team's score by position.</p>
    <div class="ws">
{cards}
    </div>
  </section>

  <section id="positions">
    <p class="sk">Where the points came from</p><h2>Scoring by position</h2>
    <p class="sl">Long orange means the backfield carried it. Long green means the
      receivers did.</p>
    <div class="chart"><div class="lg">{legend}</div>{prow}</div>
  </section>

  <section id="season">
    <p class="sk">The long view</p><h2>Power ranking by week</h2>
    <p class="sl">Rank one at the top. One column today; by October this is the chart
      that shows who is actually trending.</p>
    <div class="chart">
      <svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="rank by week">{svg}</svg>
      <p class="cnote">One week in — every Tuesday adds a column.</p>
    </div>
  </section>

  <footer><p>Data pulled from ESPN every Tuesday morning.
    <a href="../index.html" style="color:var(--muted)">← All weeks</a></p></footer>
</div>
</body>
</html>
'''


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--theme", default="")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing page for this week")
    ap.add_argument("--placeholders", action="store_true",
                    help="local stand-in images, for previewing without CDN access")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    globals()["PLACEHOLDER"] = a.placeholders

    root = HERE.parent
    data_path = root / "data" / f"week-{a.week}.json"
    if not data_path.exists():
        sys.exit(f"No data for week {a.week}. Run update_week.py first.")
    data = json.load(open(data_path))

    hist_path = root / "data" / "history.json"
    history = (json.loads(hist_path.read_text()) if hist_path.exists()
               else [{"week": a.week,
                      "ranks": {str(t["team_id"]): t["rank"] for t in data["teams"]}}])

    out = Path(a.out) if a.out else root / "docs" / "weeks" / f"week-{a.week}.html"
    if out.exists() and not a.force:
        sys.exit(f"{out} already exists. Pass --force to replace it.")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(data, history, a.theme or f"Week {a.week}"))
    print(f"Wrote {out} — now edit the hero copy and the twelve takes.")


if __name__ == "__main__":
    main()
