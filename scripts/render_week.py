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
ROOT_DATA = HERE.parent / "data"
SITE = "https://scoducks8.github.io/fantasy-power-rankings"

POS_COLOR = {"QB": "#3987e5", "RB": "#d95926", "WR": "#199e70",
             "TE": "#c98500", "K": "#d55181", "D/ST": "#9085e9"}
POS_ORDER = ["QB", "RB", "WR", "TE", "K", "D/ST"]

e = html.escape
PLACEHOLDER = False
SKIN = "default"


def load_skin(name: str) -> str:
    """A skin is just a stylesheet using the same class names.

    The markup never changes between weeks; only the look does. That keeps a
    themed week from forking the generator.
    """
    path = HERE / "skins" / f"{name}.css"
    if not path.exists():
        raise SystemExit(f"No skin at {path}")
    return path.read_text()


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


def asset(local: str, remote: str, seed: str, kind: str = "av") -> str:
    """Prefer the copy cached in the repo; the page lives one level down."""
    if PLACEHOLDER:
        return _ph(seed, kind)
    return f"../{local}" if local else (remote or "")


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


def load_copy(week: int, path: str = "") -> dict:
    """Hand-written copy for the week, kept beside the data.

    The generator owns numbers and layout; this file owns the words. Keeping
    them apart means re-running the generator never eats your writing.
    """
    path = Path(path) if path else ROOT_DATA / f"copy-week-{week}.json"
    return json.loads(path.read_text()) if path.exists() else {}


LABELS = {
    "nav_scores": "Scores", "nav_teams": "Rankings",
    "nav_positions": "Positions", "nav_season": "Season",
    "sk_scores": "The slate", "h2_scores": "Week {week} results",
    "sk_teams": "Power rankings", "h2_teams": "Every team, ranked",
    "sk_positions": "Where the points came from", "h2_positions": "Scoring by position",
    "sk_season": "The long view", "h2_season": "Power ranking by week",
    "lede_season": ("Rank one at the top. One column tonight; by October this is the "
                    "chart that shows who is actually trending."),
    "cnote": "One week in. Every Monday night adds a column.",
    "margin": "by {margin}",
    "power_label": "",     # e.g. "Combat" shows the power score on each card
    "power_scale": "pct",  # "pct" = 0-100, "combat" = RuneScape 3-126
}


def power_display(ps: float, scale: str) -> str:
    if scale == "combat":
        return str(round(3 + ps * 123))
    return str(round(ps * 100))


def render(data, history, theme="Week One", copy=None):
    copy = copy or {}
    takes = copy.get("takes", {})
    LB = {**LABELS, **copy.get("labels", {})}
    wk = data["week"]
    lab = lambda k, **kw: e(LB[k].format(week=wk, **kw))
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
          <div class="rm">{lab("margin", margin=f"{m['margin']:.1f}")}</div>
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
        pw = (f'<span class="ps">{e(LB["power_label"])} '
              f'<b>{power_display(t.get("power_score", 0), LB["power_scale"])}</b></span>'
              if LB["power_label"] else "")
        cards += f'''      <article class="w{' lead' if t['rank']==1 else ''}">
        <header>
          <span class="wr">{t['rank']}</span>
          <img class="wav" src="{e(asset(t.get("logo_local",""), t.get("logo",""), t["owner"]))}" alt="" loading="lazy">
          <div class="wt"><h3>{e(t['name'])}{chip}</h3><span>{e(t['owner'])}</span>{pw}</div>
          <span class="wp">{t['points_for']:.1f}
            <i>{t['wins']}-{t['losses']} · {'+' if t['points_for']-t['projected_total']>=0 else ''}{t['points_for']-t['projected_total']:.1f} vs proj</i>
          </span>
        </header>
        <div class="wbar">{seg}</div>
        <div class="wmain">
          <figure><img src="{e(asset(top.get("headshot_local",""), top.get("headshot",""), top["name"], "hs"))}" alt="" loading="lazy">
            <figcaption><b>{top['points']:.1f}</b><span>{e(top['name'])}</span></figcaption></figure>
          <p>{e(takes.get(str(t["team_id"]), "Write this team's take here."))}</p>
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
                  f'stroke="#1c2330" class="rg"/>' for r in range(1, n + 1))
    for t in teams:
        pts = [(fx(h["week"]), fy(h["ranks"][str(t["team_id"])])) for h in history]
        d = " ".join(f'{"M" if i==0 else "L"}{a:.1f},{b:.1f}' for i, (a, b) in enumerate(pts))
        col = "#9fb0ff" if t["rank"] == 1 else "#39425c"
        lc = "rl lead" if t["rank"] == 1 else "rl"
        svg += (f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.5" stroke-linecap="round" class="{lc}"/>'
                f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="4.5" fill="{col}" class="{lc} dot"/>'
                f'<text x="{pts[-1][0]+11:.1f}" y="{pts[-1][1]+4:.1f}" fill="#9aa6b2" class="rt" '
                f'font-size="11.5">{e(SH[t["team_id"]])}</text>')
    svg += "".join(f'<text x="{L-9}" y="{fy(r)+4:.1f}" fill="#6b7683" font-size="10" class="ra" '
                   f'text-anchor="end">{r}</text>' for r in (1, 6, 12) if r <= n)

    skin_css = load_skin(SKIN)

    # A week uses its own preview card when one exists, else the league image.
    card = ROOT_DATA.parent / "docs" / f"og-week-{data['week']}.png"
    og_img = f"og-week-{data['week']}.png" if card.exists() else "og-league.png"
    og_title = copy.get("og_title") or f"Week {data['week']}: {theme}"
    og_desc = copy.get("og_description") or copy.get("standfirst", "")[:200]

    # Ticker copy: scores first, then the week's outliers. The default skin
    # hides it; a broadcast-style skin scrolls it along the bottom.
    hi = max(teams, key=lambda t: t["points_for"])
    lo = min(teams, key=lambda t: t["points_for"])
    ticker_items = [f'{e(SH[m["away_id"]])} {m["away_score"]:.1f} — '
                    f'{e(SH[m["home_id"]])} {m["home_score"]:.1f}' for m in mus]
    ticker_items += [
        f'HIGH: {e(SH[hi["team_id"]])} {hi["points_for"]:.1f}',
        f'LOW: {e(SH[lo["team_id"]])} {lo["points_for"]:.1f}',
        f'CLOSEST: {mus[0]["margin"]:.1f} PTS',
    ]
    if copy.get("ticker"):
        ticker_items = []
        for line in copy["ticker"]:
            who, sep, msg = line.partition(": ")
            ticker_items.append(f'<b>{e(who)}:</b> <q>{e(msg)}</q>' if sep and len(who) < 28
                                else f'<em>{e(line)}</em>')
    ticker = "".join(f'<span>{it}</span>' for it in ticker_items)

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="theme-name" content="{e(theme)}" />
<title>Week {data['week']}: {e(theme)}</title>
<meta name="description" content="{e(og_desc)}" />
<meta property="og:type" content="article" />
<meta property="og:site_name" content="{e(data['league_name'])}" />
<meta property="og:url" content="{SITE}/weeks/week-{data['week']}.html" />
<meta property="og:title" content="{e(og_title)}" />
<meta property="og:description" content="{e(og_desc)}" />
<meta property="og:image" content="{SITE}/{og_img}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{e(og_title)}" />
<meta name="twitter:description" content="{e(og_desc)}" />
<meta name="twitter:image" content="{SITE}/{og_img}" />
<style>{skin_css}</style>
</head>
<body>
<div class="bar"><div class="bar-in">
  <div class="bm">Chach Champions</div>
  <nav class="bn"><a href="#scores">{lab("nav_scores")}</a><a href="#teams">{lab("nav_teams")}</a><a href="#positions">{lab("nav_positions")}</a><a href="#season">{lab("nav_season")}</a></nav>
</div></div>

<header class="hero"><div class="hero-in">
  <div>
    <p class="hk">Week {data['week']} · {e(theme)}</p>
    <h1>{e(copy.get("headline", "Opening weekend, and the board already looks nothing like the draft."))}</h1>
    <p class="hs">{e(copy.get("standfirst", "Write the week's framing here."))}</p>
  </div>
  <figure>
    <img src="{e(asset(best.get("headshot_local",""), best.get("headshot",""), best["name"], "hs"))}" alt="{e(best['name'])}" />
    <figcaption class="hcap"><b>{best['points']:.1f}</b>
      <span>{e(best['name'])} · {e(SH[best_team['team_id']])}'s best</span></figcaption>
  </figure>
</div></header>

<div class="wrap">
  <section id="scores">
    <p class="sk">{lab("sk_scores")}</p><h2>{lab("h2_scores")}</h2>
    <p class="sl">{e(copy.get("lede_scores", "Closest game first. Gold border means it was decided by under ten."))}</p>
    <div class="strip">
{strip}
    </div>
  </section>

  <section id="teams">
    <p class="sk">{lab("sk_teams")}</p><h2>{lab("h2_teams")}</h2>
    <p class="sl">{e(copy.get("lede_rankings", "The bar under each name splits that team's score by position."))}</p>
    <div class="ws">
{cards}
    </div>
  </section>

  <section id="positions">
    <p class="sk">{lab("sk_positions")}</p><h2>{lab("h2_positions")}</h2>
    <p class="sl">{e(copy.get("lede_positions", "Long orange means the backfield carried it."))}</p>
    <div class="chart"><div class="lg">{legend}</div>{prow}</div>
  </section>

  <section id="season">
    <p class="sk">{lab("sk_season")}</p><h2>{lab("h2_season")}</h2>
    <p class="sl">{lab("lede_season")}</p>
    <div class="chart">
      <svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="rank by week">{svg}</svg>
      <p class="cnote">{lab("cnote")}</p>
    </div>
  </section>

  <footer><p>Data pulled from ESPN on Monday night, once the last game is final.
    <a href="../index.html" style="color:var(--muted)">← All weeks</a></p></footer>
</div>

<div class="ticker" aria-hidden="true"><div class="ticker-in">{ticker}{ticker}</div></div>
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
    ap.add_argument("--skin", default="default",
                    help="stylesheet in scripts/skins/ — the week's look")
    ap.add_argument("--out", default="")
    ap.add_argument("--copy", default="",
                    help="copy file to use instead of data/copy-week-N.json (for practice runs)")
    a = ap.parse_args()

    globals()["PLACEHOLDER"] = a.placeholders
    globals()["SKIN"] = a.skin

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
    theme = a.theme or f"Week {a.week}"
    copy = load_copy(a.week, a.copy)
    layout = HERE / "layouts" / f"{a.skin}.py"
    if layout.exists():
        # A big theme week can bring its own page structure. Same data, same copy file.
        import importlib.util
        spec = importlib.util.spec_from_file_location(f"layout_{a.skin}", layout)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        helpers = {"asset": asset, "short_names": short_names, "POS_COLOR": POS_COLOR,
                   "POS_ORDER": POS_ORDER, "load_skin": load_skin, "SITE": SITE}
        out.write_text(mod.render(data, history, theme, copy, helpers))
    else:
        out.write_text(render(data, history, theme, copy))
    print(f"Wrote {out} — now edit the hero copy and the twelve takes.")


if __name__ == "__main__":
    main()
