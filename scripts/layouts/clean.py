"""Clean layout: an editorial page built for reading.

One reading column, serif body text, quiet sans UI, light and dark modes.
Charts follow the dataviz method: validated position palette (light and dark
steps), thin marks with 2px surface gaps, a legend, one tooltip per row that
lists every series, and a table view for the position chart.
"""

from __future__ import annotations

import html
import json
from datetime import datetime

e = html.escape
POS = ["QB", "RB", "WR", "TE", "K", "D/ST"]
POS_NAME = {"QB": "Quarterback", "RB": "Running back", "WR": "Receiver",
            "TE": "Tight end", "K": "Kicker", "D/ST": "Defense"}
PCLS = {"QB": "qb", "RB": "rb", "WR": "wr", "TE": "te", "K": "k", "D/ST": "dst"}


def fmt(v: float) -> str:
    return f"{v:.1f}"


def render(data, history, theme, copy, h) -> str:
    asset, SITE, ROOT = h["asset"], h["SITE"], h["ROOT"]
    teams, mus, wk = data["teams"], data["matchups"], data["week"]
    n = len(teams)
    SH = h["short_names"](teams)
    by_id = {t["team_id"]: t for t in teams}
    takes = copy.get("takes", {})
    labels = copy.get("labels", {})
    for t in teams:
        t.setdefault("week_points", t["points_for"])
        t.setdefault("week_proj_diff", t["week_points"] - (t.get("projected_total") or 0))

    def av(t):
        return e(asset(t.get("logo_local", ""), t.get("logo", ""), t["owner"]))

    def hs(p):
        return e(asset(p.get("headshot_local", ""), p.get("headshot", ""), p["name"], "hs"))

    def pos_payload(t):
        return e(json.dumps({"t": t["name"],
                             "rows": [[POS_NAME[p], f'{t["positional"].get(p, 0):.1f}', PCLS[p]] for p in POS],
                             "total": f'{t["week_points"]:.1f}'}))

    def stack(t, scale):
        segs = ""
        for p in POS:
            v = t["positional"].get(p, 0)
            if v <= 0:
                continue
            segs += f'<span class="seg {PCLS[p]}" style="width:{v / scale * 100:.2f}%"></span>'
        return segs

    # ---------- at a glance ----------
    top = max(teams, key=lambda t: t["week_points"])
    close = min(mus, key=lambda m: m["margin"])
    cw = by_id[close["home_id"] if close["winner"] == "HOME" else close["away_id"]]
    cl = by_id[close["away_id"] if close["winner"] == "HOME" else close["home_id"]]
    unbeaten = [t for t in teams if t["losses"] == 0 and t["wins"] > 0]
    losers = []
    for m in mus:
        hw = m["winner"] == "HOME"
        losers.append((m["away_score"] if hw else m["home_score"], by_id[m["away_id"] if hw else m["home_id"]]))
    hl_score, hl_team = max(losers, key=lambda x: x[0])
    tiles = [
        ("Top score", fmt(top["week_points"]), top["name"]),
        ("Closest game", f'{close["margin"]:.2f}', f'{cw["name"]} over {cl["name"]}'),
        ("Highest losing score", fmt(hl_score), hl_team["name"]),
    ]
    if unbeaten:
        u = unbeaten[0]
        tiles.insert(1, ("Unbeaten", f'{u["wins"]}-0', ", ".join(x["name"] for x in unbeaten)))
    glance = "".join(f'<div class="tile"><p class="tl">{e(a)}</p><p class="tv">{e(b)}</p>'
                     f'<p class="ts">{e(c)}</p></div>' for a, b, c in tiles)

    # ---------- results ----------
    games = ""
    for m in mus:
        hw = m["winner"] == "HOME"
        W = by_id[m["home_id"] if hw else m["away_id"]]
        L = by_id[m["away_id"] if hw else m["home_id"]]
        ws = m["home_score"] if hw else m["away_score"]
        ls = m["away_score"] if hw else m["home_score"]
        games += f'''<li class="game{' close' if m["margin"] < 10 else ''}">
  <div class="side win"><img src="{av(W)}" alt="" loading="lazy"><span class="nm">{e(W["name"])}</span><span class="sc">{fmt(ws)}</span></div>
  <div class="side"><img src="{av(L)}" alt="" loading="lazy"><span class="nm">{e(L["name"])}</span><span class="sc">{fmt(ls)}</span></div>
  <p class="mg">{"Decided by " + f"{m['margin']:.2f}" if m["margin"] < 10 else "Won by " + f"{m['margin']:.1f}"}</p>
</li>'''

    legend = "".join(f'<span class="lk"><i class="sw {PCLS[p]}"></i>{e(POS_NAME[p])}</span>' for p in POS)

    # ---------- rankings ----------
    show_move = len(history) > 1
    cards = ""
    for t in teams:
        tid = t["team_id"]
        mv = ""
        if show_move and t.get("movement"):
            up = t["movement"] > 0
            mv = (f'<span class="mv {"up" if up else "dn"}" aria-label="{"up" if up else "down"} '
                  f'{abs(t["movement"])}">{"&#9650;" if up else "&#9660;"} {abs(t["movement"])}</span>')
        elif show_move:
            mv = '<span class="mv eq" aria-label="no change">&ndash;</span>'
        diff = t["week_proj_diff"]
        topp = t["top_scorer"]
        cards += f'''<article class="team{' first' if t['rank'] == 1 else ''}" id="t{tid}" data-team="{tid}">
  <header class="th">
    <span class="rk">{t["rank"]}</span>
    <img class="lg" src="{av(t)}" alt="" loading="lazy">
    <div class="who"><h3>{e(t["name"])}</h3>
      <p>{e(t["owner"])} <span class="dot">&middot;</span> {t["wins"]}-{t["losses"]} {mv}</p></div>
    <div class="pts"><b>{fmt(t["week_points"])}</b><span>{"+" if diff >= 0 else ""}{diff:.1f} vs projection</span></div>
  </header>
  <div class="bar" tabindex="0" data-tip="{pos_payload(t)}" aria-label="Points by position">{stack(t, max(1.0, t["week_points"]))}</div>
  <p class="take">{e(takes.get(str(tid), ""))}</p>
  <p class="pog"><img src="{hs(topp)}" alt="" loading="lazy"><span>Top performer <b>{e(topp["name"])}</b> {fmt(topp["points"])}</span></p>
</article>'''

    # ---------- scoring by position ----------
    mx = max(t["week_points"] for t in teams)
    rows = ""
    trows = ""
    for t in sorted(teams, key=lambda x: -x["week_points"]):
        rows += (f'<div class="prow" tabindex="0" data-tip="{pos_payload(t)}">'
                 f'<span class="pn">{e(SH[t["team_id"]])}</span>'
                 f'<span class="pt"><span class="ps" style="width:calc((100% - 56px) * {t["week_points"] / mx:.4f})">'
                 f'{stack(t, max(1.0, t["week_points"]))}</span>'
                 f'<span class="pv">{fmt(t["week_points"])}</span></span></div>')
        trows += ("<tr><th>" + e(t["name"]) + "</th>" +
                  "".join(f'<td>{t["positional"].get(p, 0):.1f}</td>' for p in POS) +
                  f'<td class="tot">{fmt(t["week_points"])}</td></tr>')
    thead = "".join(f"<th>{p}</th>" for p in POS)

    # ---------- rank by week (bump chart) ----------
    weeks = [x["week"] for x in history]
    W_, H_, L_, R_, T_, B_ = 560, 380, 34, 150, 30, 16
    span = max(1, (weeks[-1] - weeks[0]) or 1)
    fx = lambda w: L_ + (0 if len(weeks) == 1 else (w - weeks[0]) / span * (W_ - L_ - R_))
    fy = lambda r: T_ + (r - 1) / (n - 1) * (H_ - T_ - B_)
    svg = "".join(f'<line class="grid" x1="{fx(w):.1f}" y1="{T_-8}" x2="{fx(w):.1f}" y2="{H_-B_+6}"/>'
                  f'<text class="wkl" x="{fx(w):.1f}" y="{T_-14}" text-anchor="middle">Week {w}</text>'
                  for w in weeks)
    lines = ""
    for t in sorted(teams, key=lambda x: -x["rank"]):
        tid = t["team_id"]
        pts = [(fx(x["week"]), fy(x["ranks"][str(tid)])) for x in history]
        d = " ".join(f'{"M" if i == 0 else "L"}{a:.1f},{b:.1f}' for i, (a, b) in enumerate(pts))
        path_ranks = [x["ranks"][str(tid)] for x in history]
        tip = e(json.dumps({"t": t["name"], "rows": [[f"Week {w}", f"#{r}"] for w, r in zip(weeks, path_ranks)]}))
        dots = "".join(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="4"/>' for a, b in pts)
        lines += (f'<g class="ln{" lead" if t["rank"] == 1 else ""}" data-team="{tid}" tabindex="0" data-tip="{tip}">'
                  f'<path class="hit" d="{d}"/><path class="stroke" d="{d}"/>{dots}'
                  f'<text x="{pts[-1][0]+12:.1f}" y="{pts[-1][1]+4.5:.1f}">{t["rank"]}. {e(SH[tid])}</text></g>')
    svg += lines
    svg += "".join(f'<text class="ax" x="{L_-14}" y="{fy(r)+4:.1f}" text-anchor="end">{r}</text>'
                   for r in (1, n))

    card = ROOT / "docs" / f"og-week-{wk}.png"
    og_img = copy.get("og_image") or (f"og-week-{wk}.png" if card.exists() else "og-league.png")
    og_title = copy.get("og_title") or f"Week {wk}: {theme}"
    og_desc = copy.get("og_description") or copy.get("standfirst", "")[:200]
    try:
        stamp = datetime.fromisoformat(data["generated_at"]).strftime("%B %-d, %Y")
    except Exception:
        stamp = ""

    js = r"""
(function(){
  var tip=document.createElement('div');tip.className='tip';tip.setAttribute('role','tooltip');tip.hidden=true;
  document.body.appendChild(tip);
  function show(el,x,y){
    var d;try{d=JSON.parse(el.getAttribute('data-tip'))}catch(_){return}
    while(tip.firstChild)tip.removeChild(tip.firstChild);
    var h=document.createElement('p');h.className='tt';h.textContent=d.t;tip.appendChild(h);
    d.rows.forEach(function(r){var p=document.createElement('p');var k=document.createElement('span');
      k.textContent=r[0];if(r[2]){var i=document.createElement('i');i.className='key '+r[2];k.insertBefore(i,k.firstChild)}
      var v=document.createElement('b');v.textContent=r[1];p.appendChild(v);p.appendChild(k);tip.appendChild(p)});
    if(d.total!==undefined){var t=document.createElement('p');t.className='tsum';var b=document.createElement('b');
      b.textContent=d.total;var s=document.createElement('span');s.textContent='Total';t.appendChild(b);t.appendChild(s);tip.appendChild(t)}
    tip.hidden=false;place(x,y);
  }
  function place(x,y){var w=tip.offsetWidth,hh=tip.offsetHeight,vw=window.innerWidth;
    var l=Math.min(Math.max(8,x+14),vw-w-8),t=y-hh-14;if(t<8)t=y+18;
    tip.style.left=l+'px';tip.style.top=t+'px'}
  function hide(){tip.hidden=true}
  document.querySelectorAll('[data-tip]').forEach(function(el){
    el.addEventListener('pointermove',function(ev){show(el,ev.clientX,ev.clientY)});
    el.addEventListener('pointerleave',hide);
    el.addEventListener('focus',function(){var r=el.getBoundingClientRect();show(el,r.left+r.width/2,r.top)});
    el.addEventListener('blur',hide);
  });
  window.addEventListener('scroll',hide,{passive:true});
  var chart=document.querySelector('.bump');
  function hl(id){if(!chart)return;chart.classList.toggle('focus',!!id);
    chart.querySelectorAll('.ln').forEach(function(g){g.classList.toggle('on',g.getAttribute('data-team')===id)})}
  document.querySelectorAll('.bump .ln').forEach(function(g){
    var id=g.getAttribute('data-team');
    g.addEventListener('pointerenter',function(){hl(id)});g.addEventListener('pointerleave',function(){hl(null)});
    g.addEventListener('focus',function(){hl(id)});g.addEventListener('blur',function(){hl(null)});
  });
})();
"""

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="theme-name" content="{e(theme)}" />
<meta name="color-scheme" content="light dark" />
<title>Week {wk} power rankings &middot; {e(data["league_name"])}</title>
<meta name="description" content="{e(og_desc)}" />
<meta property="og:type" content="article" />
<meta property="og:site_name" content="{e(data['league_name'])}" />
<meta property="og:url" content="{SITE}/weeks/week-{wk}.html" />
<meta property="og:title" content="{e(og_title)}" />
<meta property="og:description" content="{e(og_desc)}" />
<meta property="og:image" content="{SITE}/{og_img}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content="{SITE}/{og_img}" />
<style>{h["load_skin"]("clean")}</style>
</head>
<body>
<nav class="top"><div class="top-in">
  <a class="brand" href="../index.html"><span class="full">{e(data["league_name"])}</span><span class="short">CCL</span></a>
  <div class="links"><a href="#results">Results</a><a href="#rankings">Rankings</a><a href="#positions">Positions</a><a href="#trend">Trend</a></div>
</div></nav>

<main>
  <header class="intro">
    <p class="kicker">Week {wk} power rankings{(" &middot; " + e(stamp)) if stamp else ""}</p>
    <h1>{e(copy.get("headline", ""))}</h1>
    <p class="dek">{e(copy.get("standfirst", ""))}</p>
  </header>

  <section class="glance" aria-label="At a glance">{glance}</section>

  <section id="results">
    <h2>Results</h2>
    <p class="lede">{e(copy.get("lede_scores", ""))}</p>
    <ul class="games">{games}</ul>
  </section>

  <section id="rankings">
    <h2>Power rankings</h2>
    <p class="lede">{e(copy.get("lede_rankings", ""))}</p>
    <div class="legend">{legend}</div>
    <div class="teams">{cards}</div>
  </section>

  <section id="positions">
    <h2>Scoring by position</h2>
    <p class="lede">{e(copy.get("lede_positions", ""))}</p>
    <div class="legend">{legend}</div>
    <div class="pchart">{rows}</div>
    <details class="tview"><summary>Show as a table</summary>
      <div class="twrap"><table><thead><tr><th>Team</th>{thead}<th>Total</th></tr></thead><tbody>{trows}</tbody></table></div>
    </details>
  </section>

  <section id="trend">
    <h2>Rank by week</h2>
    <p class="lede">{e(labels.get("lede_season", ""))}</p>
    <figure class="bumpwrap"><svg class="bump" viewBox="0 0 {W_} {H_}" role="img" aria-label="Power ranking by week for every team">{svg}</svg>
      <figcaption>{e(labels.get("cnote", ""))} Hover or tap a line to follow one team.</figcaption></figure>
  </section>

  <footer class="foot"><p>Data from ESPN, pulled Monday night once the last game is final.
    <a href="../index.html">All weeks</a></p></footer>
</main>
<script>{js}</script>
</body>
</html>
'''
