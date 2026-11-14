"""Ducks layout: an unhinged Oregon superfan runs the power rankings.

Green and yellow, diamond-plate texture, drawn feathers, a stadium scoreboard
in the hero. No school logos or mascot art, just colours and text.
Copy keys: headline, kicker, standfirst, ticker[list], scoreboard{home,home_score,
away,away_score,where}, tiers[4 x [name, sub]], takes{id}, lede_* keys, footer,
up_next, og_title, og_description.
"""

from __future__ import annotations

import html
import json

e = html.escape
POS = ["QB", "RB", "WR", "TE", "K", "D/ST"]
POS_NAME = {"QB": "Quarterback", "RB": "Running back", "WR": "Receiver",
            "TE": "Tight end", "K": "Kicker", "D/ST": "Defense"}
PCLS = {"QB": "qb", "RB": "rb", "WR": "wr", "TE": "te", "K": "k", "D/ST": "dst"}
TIERS = [["National Champions", "in our hearts"], ["Rose Bowl Bound", "smell the roses"],
         ["Bowl Eligible", "barely"], ["Beavers", "Corvallis energy"]]


def fmt(v: float) -> str:
    return f"{v:.1f}"


FEATHER = '''<svg class="feather" viewBox="0 0 40 120" aria-hidden="true"><path d="M20 118 L20 10" stroke="currentColor" stroke-width="2.5"/>
<path d="M20 10 C34 26 36 60 22 104 C8 60 6 26 20 10 Z" fill="currentColor" opacity=".9"/>
<path d="M20 30 L30 22 M20 44 L33 36 M20 58 L32 52 M20 72 L30 68 M20 30 L10 22 M20 44 L7 36 M20 58 L8 52 M20 72 L10 68" stroke="#0b3d2a" stroke-width="1.6" opacity=".55"/></svg>'''


def render(data, history, theme, copy, h) -> str:
    asset, SITE, ROOT = h["asset"], h["SITE"], h["ROOT"]
    teams, mus, wk = data["teams"], data["matchups"], data["week"]
    n = len(teams)
    SH = h["short_names"](teams)
    by_id = {t["team_id"]: t for t in teams}
    takes = copy.get("takes", {})
    tiers_cfg = copy.get("tiers") or TIERS
    ph = copy.get("photos", {})
    tier_imgs = ph.get("tiers", [])
    breaks = {b["after"]: b for b in ph.get("breaks", [])}

    def brk(after):
        b = breaks.get(after)
        if not b:
            return ""
        return (f'<figure class="brk"><img src="../assets/ducks/{e(b["img"])}" alt="{e(b.get("who", ""))}" loading="lazy" '
                f'style="object-position:{e(b.get("pos", "center 30%"))}">'
                f'<figcaption><b>{e(b.get("line", ""))}</b><span>{e(b.get("who", ""))}</span></figcaption></figure>')
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
        return "".join(f'<span class="seg {PCLS[p]}" style="width:{t["positional"].get(p, 0) / scale * 100:.2f}%"></span>'
                       for p in POS if t["positional"].get(p, 0) > 0)

    legend = "".join(f'<span class="lk"><i class="sw {PCLS[p]}"></i>{e(POS_NAME[p])}</span>' for p in POS)

    # ---------- results ----------
    close = min(mus, key=lambda m: m["margin"])
    blow = max(mus, key=lambda m: m["margin"])
    games = ""
    for m in sorted(mus, key=lambda m: m["margin"]):
        hw = m["winner"] == "HOME"
        W = by_id[m["home_id"] if hw else m["away_id"]]
        L = by_id[m["away_id"] if hw else m["home_id"]]
        ws = m["home_score"] if hw else m["away_score"]
        ls = m["away_score"] if hw else m["home_score"]
        tag = ('<p class="gtag">Instant classic</p>' if m is close else
               '<p class="gtag blow">Autzen-level beatdown</p>' if m is blow else "")
        games += f'''<li class="game{' close' if m is close else ''}">
  {tag}
  <div class="gs win"><img src="{av(W)}" alt="" loading="lazy"><span class="nm">{e(W["name"])}</span><span class="sc">{fmt(ws)}</span></div>
  <div class="gs"><img src="{av(L)}" alt="" loading="lazy"><span class="nm">{e(L["name"])}</span><span class="sc">{fmt(ls)}</span></div>
  <p class="mg">{"Decided by " + f"{m['margin']:.2f}" if m["margin"] < 10 else "Won by " + f"{m['margin']:.1f}"}</p>
</li>'''

    comps = copy.get("comps", {})

    def comp_html(tid):
        c = comps.get(str(tid))
        if not c:
            return ""
        return (f'<span class="comp"><img src="../assets/ducks/{e(c[0])}" alt="{e(c[1])}" loading="lazy">'
                f'<small>Ducks comp</small><b>{e(c[1])}</b></span>')

    # ---------- rankings ----------
    show_move = len(history) > 1
    ranked = sorted(teams, key=lambda t: t["rank"])
    per = max(1, round(n / 4))
    tiers = ""
    for ti, (tname, tsub) in enumerate(tiers_cfg):
        chunk = ranked[ti * per:(ti + 1) * per] if ti < 3 else ranked[3 * per:]
        if not chunk:
            continue
        cards = ""
        for t in chunk:
            tid = t["team_id"]
            mv = ""
            if show_move:
                m_ = t.get("movement") or 0
                mv = (f'<span class="mv up">&#9650; {m_}</span>' if m_ > 0 else
                      f'<span class="mv dn">&#9660; {-m_}</span>' if m_ < 0 else '<span class="mv eq">&ndash;</span>')
            topp = t["top_scorer"]
            cards += f'''<article class="card t{ti}" id="t{tid}">
  <header class="th">
    <span class="rk">{t["rank"]}</span>
    <img class="lg" src="{av(t)}" alt="" loading="lazy">
    <div class="who"><h3>{e(t["name"])}</h3><p>{e(t["owner"])} &middot; {t["wins"]}-{t["losses"]} {mv}</p></div>
    <div class="pts"><b>{fmt(t["week_points"])}</b><span>points</span></div>
  </header>
  <div class="bar" tabindex="0" data-tip="{pos_payload(t)}" aria-label="Points by position">{stack(t, max(1.0, t["week_points"]))}</div>
  <p class="take">{comp_html(tid)}{e(takes.get(str(tid), ""))}</p>
  <p class="pog"><img src="{hs(topp)}" alt="" loading="lazy"><span>Player of the game <b>{e(topp["name"])}</b> {fmt(topp["points"])}</span></p>
</article>'''
        tiers += f'''<div class="tier tr{ti}">
  {(f'<header class="tierban{" cut" if tier_imgs[ti][0].endswith(".png") else ""}" data-num="{e(tier_imgs[ti][3] if len(tier_imgs[ti]) > 3 else "")}"><img src="../assets/ducks/{e(tier_imgs[ti][0])}" alt="{e(tier_imgs[ti][1])}" loading="lazy" style="object-position:{e(tier_imgs[ti][2] if len(tier_imgs[ti]) > 2 else "center 30%")}{(";width:" + e(tier_imgs[ti][4])) if len(tier_imgs[ti]) > 4 else ""}"><div class="tbt"><h3>{e(tname)}</h3><p>{e(tsub)}</p><small>{e(tier_imgs[ti][1])}</small></div></header>') if ti < len(tier_imgs) else f'<header class="tierh"><h3>{e(tname)}</h3><p>{e(tsub)}</p></header>'}
  <div class="cards">{cards}</div>
</div>'''

    # ---------- road to the playoff ----------
    odds_path = ROOT / "data" / f"odds-week-{wk}.json"
    oddsec = ""
    if odds_path.exists():
        od = json.loads(odds_path.read_text())
        rows = ""
        for t in sorted(teams, key=lambda t: -od["teams"][str(t["team_id"])]["playoffs"]):
            p = od["teams"][str(t["team_id"])]["playoffs"]
            lab = ("Playoff lock" if p >= 90 else "On the bubble" if p >= 50 else
                   "Needs help" if p >= 10 else "Beaver territory")
            pct = ">99%" if p >= 99.5 else "<1%" if p < 1 else f"{p:.0f}%"
            rows += (f'<li class="od"><span class="on"><img src="{av(t)}" alt="">{e(t["name"])}'
                     f'<small>{t["wins"]}-{t["losses"]}</small></span>'
                     f'<span class="om" aria-hidden="true"><span style="width:{max(1.5, p):.1f}%"></span></span>'
                     f'<span class="op">{pct}</span><span class="ol">{lab}</span></li>')
        oddsec = f'''<section id="playoff">
    <h2>The Road to the Playoff</h2>
    <p class="lede">{e(copy.get("lede_odds", ""))}</p>
    <ol class="odds">{rows}</ol>
    <p class="note">Playoff odds from {od["sims"]:,} simulated seasons on the real remaining schedule. Top {od["playoff_teams"]} make it. Ties go to total points.</p>
  </section>'''

    # ---------- depth chart (positions) ----------
    mx = max(t["week_points"] for t in teams)
    rows, trows = "", ""
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

    # ---------- rank by week ----------
    weeks = [x["week"] for x in history]
    W_, H_, L_, R_, T_, B_ = 560, 380, 34, 150, 30, 16
    span = max(1, (weeks[-1] - weeks[0]) or 1)
    fx = lambda w: L_ + (0 if len(weeks) == 1 else (w - weeks[0]) / span * (W_ - L_ - R_))
    fy = lambda r: T_ + (r - 1) / (n - 1) * (H_ - T_ - B_)
    svg = "".join(f'<line class="grid" x1="{fx(w):.1f}" y1="{T_-8}" x2="{fx(w):.1f}" y2="{H_-B_+6}"/>'
                  f'<text class="wkl" x="{fx(w):.1f}" y="{T_-14}" text-anchor="middle">WK {w}</text>' for w in weeks)
    for t in sorted(teams, key=lambda x: -x["rank"]):
        tid = t["team_id"]
        pts = [(fx(x["week"]), fy(x["ranks"][str(tid)])) for x in history]
        d = " ".join(f'{"M" if j == 0 else "L"}{a:.1f},{b:.1f}' for j, (a, b) in enumerate(pts))
        tip = e(json.dumps({"t": t["name"], "rows": [[f"Week {w}", f"#{x['ranks'][str(tid)]}"] for w, x in zip(weeks, history)]}))
        dots = "".join(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="4"/>' for a, b in pts)
        svg += (f'<g class="ln{" lead" if t["rank"] == 1 else ""}" data-team="{tid}" tabindex="0" data-tip="{tip}">'
                f'<path class="hit" d="{d}"/><path class="stroke" d="{d}"/>{dots}'
                f'<text x="{pts[-1][0]+12:.1f}" y="{pts[-1][1]+4.5:.1f}">{t["rank"]}. {e(SH[tid])}</text></g>')
    svg += "".join(f'<text class="ax" x="{L_-14}" y="{fy(r)+4:.1f}" text-anchor="end">{r}</text>' for r in (1, n))

    # ---------- up next ----------
    nx = copy.get("up_next") or {}
    upnext, nxlink = "", ""
    if nx.get("games"):
        items = ""
        for g in nx["games"]:
            A, B = by_id[g["a"]], by_id[g["b"]]
            items += (f'<li class="nx{" gotw" if g.get("gotw") else ""}">'
                      f'{"<span class=nx-tag>Game of the week</span>" if g.get("gotw") else ""}'
                      f'<p class="nx-m"><span class="nx-u"><img src="{av(A)}" alt="">{e(A["name"])} <span class="nx-r">{A["wins"]}-{A["losses"]}</span></span>'
                      f'<span class="nx-u"><span class="nx-vs">vs</span><img src="{av(B)}" alt="">{e(B["name"])} <span class="nx-r">{B["wins"]}-{B["losses"]}</span></span></p>'
                      f'<p class="nx-t">{e(g["text"])}</p></li>')
        upnext = f'''<section id="next"><h2>{e(nx.get("title", "Up next"))}</h2>
    {f'<p class="lede">{e(nx["intro"])}</p>' if nx.get("intro") else ""}<ul class="nxs">{items}</ul></section>'''
        nxlink = '<a href="#next">Next</a>'

    sb = copy.get("scoreboard") or {}
    scoreboard = ""
    if sb:
        scoreboard = f'''<div class="board" role="img" aria-label="{e(sb.get('home', ''))} {e(str(sb.get('home_score', '')))}, {e(sb.get('away', ''))} {e(str(sb.get('away_score', '')))}">
  <p class="bt">{e(sb.get("label", "FINAL"))}</p>
  <div class="brow win"><span>{e(sb.get("home", ""))}</span><b>{e(str(sb.get("home_score", "")))}</b></div>
  <div class="brow"><span>{e(sb.get("away", ""))}</span><b>{e(str(sb.get("away_score", "")))}</b></div>
  <p class="bw">{e(sb.get("where", ""))}</p>
</div>'''
    tick = "".join(f"<span>{e(x)}</span>" for x in copy.get("ticker", []))
    # Commons photos fetched by scripts/fetch_photos.py --set ducks (optional)
    photos = []
    cp = ROOT / "data" / "photo-credits-ducks.json"
    if cp.exists():
        try:
            photos = [p for p in json.loads(cp.read_text()) if (ROOT / "docs" / p["file"]).exists()]
        except (ValueError, KeyError):
            photos = []
    by_term: dict = {}
    for p in photos:
        by_term.setdefault(p["term"], []).append(p)
    used = set()

    def take(term):
        for p in by_term.get(term, []):
            if p["file"] not in used:
                used.add(p["file"])
                return p
        return None

    leg = copy.get("legends") or []
    legends = ""
    if leg:
        cards = ""
        for item in leg:
            num, nm, note = item[0], item[1], item[2]
            lp = {"file": f"assets/ducks/{item[3]}"} if len(item) > 3 and item[3] else take(nm)
            img = f'<img src="../{e(lp["file"])}" alt="{e(nm)}" loading="lazy">' if lp else ""
            cards += (f'<div class="lgd{" hasimg" if lp else ""}">{img}<div class="lgt"><b>{e(str(num))}</b>'
                      f'<span>{e(nm)}</span><small>{e(note)}</small></div></div>')
        legends = f'<div class="legends" aria-label="Ducks legends"><p class="lt">Legends of Eugene</p><div class="lgs">{cards}</div></div>'
    band_terms = copy.get("photo_band", ["Autzen Stadium", "Oregon Ducks football", "Hayward Field", "Autzen Stadium", "Oregon Ducks football"])
    band_items = [p for p in (take(t) for t in band_terms) if p]
    band = ""
    if band_items:
        band = ('<div class="band" aria-label="Eugene">' +
                "".join(f'<figure><img src="../{e(p["file"])}" alt="{e(p["title"])}" loading="lazy"></figure>' for p in band_items) + '</div>')
    credit_line = ""
    if used:
        shown = [p for p in photos if p["file"] in used]
        credit_line = ('<p class="credits">Photos via Wikimedia Commons: ' +
                       "; ".join(f'<a href="{e(p["source"])}">{e(p["title"][:60])}</a> by {e(p["author"][:60])} ({e(p["license"])})' for p in shown) + '.</p>')
    feathers = "".join(f'<i class="fth" style="--x:{(i * 41) % 100}%;--d:{(i * .9) % 7:.1f}s;--s:{9 + (i * 3) % 7}s;--r:{(i * 53) % 360}deg">{FEATHER}</i>'
                       for i in range(10))

    card = ROOT / "docs" / f"og-week-{wk}.png"
    og_img = copy.get("og_image") or (f"og-week-{wk}.png" if card.exists() else "og-league.png")
    og_title = copy.get("og_title") or f"Week {wk}: {theme}"
    og_desc = copy.get("og_description") or copy.get("standfirst", "")[:200]

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
<meta name="color-scheme" content="dark" />
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
<style>{h["load_skin"]("ducks")}</style>
</head>
<body>
<div class="ticker" aria-hidden="true"><div class="tk">{tick}{tick}</div></div>
<nav class="top"><div class="top-in">
  <a class="brand" href="../index.html"><span class="full">{e(data["league_name"])}</span><span class="short">CCL</span></a>
  <div class="links"><a href="#results">Results</a><a href="#rankings">Rankings</a>{'<a href="#playoff">Playoff</a>' if oddsec else ''}<a href="#depth">Depth chart</a>{nxlink}</div>
</div></nav>

<header class="hero">
  {f'<div class="herophoto" aria-hidden="true" style="background-image:url(../assets/ducks/{e(ph["hero"])})"></div>' if ph.get("hero") else ""}
  <div class="ghost" aria-hidden="true">{e(copy.get("ghost", "DUCKS"))}</div>
  <div class="speed" aria-hidden="true"><i></i><i></i><i></i><i></i></div>
  <div class="hero-in">
    <div class="htext">
      <p class="kicker">{e(copy.get("kicker", f"Week {wk} power rankings"))}</p>
      <h1>{e(copy.get("headline", ""))}</h1>
      <p class="sub">{e(copy.get("subhead", ""))}</p>
      <p class="dek">{e(copy.get("standfirst", ""))}</p>
    </div>
    {scoreboard}
  </div>
  {legends}
</header>

<main>
  <section id="results">
    <h2>The Scoreboard</h2>
    <p class="lede">{e(copy.get("lede_scores", ""))}</p>
    <ul class="games">{games}</ul>
  </section>

  {band}
  {brk("results")}
  <section id="rankings">
    <h2>Power Rankings</h2>
    <p class="lede">{e(copy.get("lede_rankings", ""))}</p>
    <div class="legend">{legend}</div>
    {tiers}
  </section>

  {brk("rankings")}
  {oddsec}
  {brk("playoff")}

  <section id="depth">
    <h2>The Depth Chart</h2>
    <p class="lede">{e(copy.get("lede_positions", ""))}</p>
    <div class="legend">{legend}</div>
    <div class="pchart">{rows}</div>
    <details class="tview"><summary>Show as a table</summary>
      <div class="twrap"><table><thead><tr><th>Team</th>{thead}<th>Total</th></tr></thead><tbody>{trows}</tbody></table></div>
    </details>
  </section>

  {brk("depth")}
  <section id="trend">
    <h2>Rank by Week</h2>
    <p class="lede">{e(copy.get("lede_season", ""))}</p>
    <figure class="bumpwrap"><svg class="bump" viewBox="0 0 {W_} {H_}" role="img" aria-label="Power ranking by week for every team">{svg}</svg>
      <figcaption>Rank one at the top. Hover or tap a line to follow one team.</figcaption></figure>
  </section>
  {brk("trend")}
{upnext}
  {brk("next")}
  <footer class="foot">
    <p class="sco">{e(copy.get("footer", "Sco Ducks."))}</p>
    <p>Data from ESPN, pulled Monday night once the last game is final. <a href="../index.html">All weeks</a></p>
    {credit_line}
  </footer>
</main>
<script>{js}</script>
</body>
</html>
'''
