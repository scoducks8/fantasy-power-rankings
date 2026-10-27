"""Wedding layout: the week as a wedding invitation and reception.

Copy keys: headline, standfirst, invite{line1,line2,line3}, newlywed_team,
newlywed_note, takes{id}, lede_scores, lede_rankings, lede_positions,
lede_odds, lede_season, footer, og_title, og_description, up_next.
Odds come from data/odds-week-N.json (scripts/playoff_odds.py) when present.
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
TABLES = [("Table One", "The Head Table"), ("Table Two", "Family of the Couple"),
          ("Table Three", "The Plus-Ones"), ("Table Four", "The Kids' Table")]
WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight",
         9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve", 13: "Thirteen", 14: "Fourteen"}


def fmt(v: float) -> str:
    return f"{v:.1f}"


def sprig(cls: str = "sprig", flip: bool = False) -> str:
    """Eucalyptus sprig, drawn as line art."""
    leaves = ""
    pts = [(30, 92, -30), (44, 80, 28), (56, 66, -26), (70, 54, 30), (82, 40, -24), (96, 30, 26), (108, 18, -20)]
    for x, y, r in pts:
        leaves += (f'<ellipse cx="{x}" cy="{y}" rx="11" ry="7" transform="rotate({r} {x} {y})" '
                   f'fill="var(--sage-l)" stroke="var(--sage)" stroke-width="1.2"/>')
    t = ' transform="scale(-1,1) translate(-130,0)"' if flip else ""
    return (f'<svg class="{cls}" viewBox="0 0 130 110" aria-hidden="true"><g{t}>'
            f'<path d="M14 104 Q60 70 118 10" fill="none" stroke="var(--sage)" stroke-width="1.6"/>{leaves}</g></svg>')


RINGS = '''<svg class="rings" viewBox="0 0 64 40" aria-hidden="true">
<circle cx="24" cy="22" r="14" fill="none" stroke="url(#gf)" stroke-width="4"/>
<circle cx="40" cy="22" r="14" fill="none" stroke="url(#gf)" stroke-width="4"/>
<path d="M36 6 l4 -5 l4 5 l-4 4 z" fill="#fff" stroke="#c9b27a" stroke-width="1"/>
<defs><linearGradient id="gf" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e9d49a"/>
<stop offset=".5" stop-color="#b08d57"/><stop offset="1" stop-color="#f3e3b3"/></linearGradient></defs></svg>'''

CAKE = '''<svg class="cake" viewBox="0 0 220 230" role="img" aria-label="Wedding cake">
<rect x="20" y="150" width="180" height="62" rx="6" fill="#fffdf8" stroke="#c9b27a" stroke-width="2"/>
<rect x="45" y="98" width="130" height="54" rx="6" fill="#fffdf8" stroke="#c9b27a" stroke-width="2"/>
<rect x="70" y="54" width="80" height="46" rx="6" fill="#fffdf8" stroke="#c9b27a" stroke-width="2"/>
<path d="M20 166 q15 10 30 0 t30 0 t30 0 t30 0 t30 0 t30 0" fill="none" stroke="#e8c9cf" stroke-width="3"/>
<path d="M45 112 q13 9 26 0 t26 0 t26 0 t26 0 t26 0" fill="none" stroke="#e8c9cf" stroke-width="3"/>
<path d="M70 66 q10 8 20 0 t20 0 t20 0 t20 0" fill="none" stroke="#e8c9cf" stroke-width="3"/>
<g fill="#c26d7c"><circle cx="110" cy="44" r="7"/><circle cx="98" cy="48" r="5" fill="#e8c9cf"/><circle cx="122" cy="48" r="5" fill="#e8c9cf"/></g>
<path d="M104 40 q6 -14 12 0" fill="none" stroke="#7d9a6e" stroke-width="2"/>
<rect x="8" y="212" width="204" height="8" rx="4" fill="#e9dfcf"/>
<g fill="#c9b27a">''' + "".join(f'<circle cx="{x}" cy="206" r="2"/>' for x in range(30, 200, 14)) + '''</g>
</svg>'''


def render(data, history, theme, copy, h) -> str:
    asset, SITE, ROOT = h["asset"], h["SITE"], h["ROOT"]
    teams, mus, wk = data["teams"], data["matchups"], data["week"]
    n = len(teams)
    SH = h["short_names"](teams)
    by_id = {t["team_id"]: t for t in teams}
    takes = copy.get("takes", {})
    newly = int(copy["newlywed_team"]) if copy.get("newlywed_team") else None
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

    # ---------- the ceremony (results) ----------
    close = min(mus, key=lambda m: m["margin"])
    games = ""
    for m in sorted(mus, key=lambda m: m["margin"]):
        hw = m["winner"] == "HOME"
        W = by_id[m["home_id"] if hw else m["away_id"]]
        L = by_id[m["away_id"] if hw else m["home_id"]]
        ws = m["home_score"] if hw else m["away_score"]
        ls = m["away_score"] if hw else m["home_score"]
        c = m is close
        games += f'''<li class="game{' close' if c else ''}">
  {'<p class="gtag">Speak now or forever hold your peace</p>' if c else ''}
  <div class="gs win"><img src="{av(W)}" alt="" loading="lazy"><span class="nm">{e(W["name"])}</span><span class="sc">{fmt(ws)}</span></div>
  <div class="gs"><img src="{av(L)}" alt="" loading="lazy"><span class="nm">{e(L["name"])}</span><span class="sc">{fmt(ls)}</span></div>
  <p class="mg">{"Decided by " + f"{m['margin']:.2f}" if m["margin"] < 10 else "Won by " + f"{m['margin']:.1f}"}</p>
</li>'''

    # ---------- the seating chart (rankings) ----------
    show_move = len(history) > 1
    ranked = sorted(teams, key=lambda t: t["rank"])
    per = max(1, round(n / 4))
    seating = ""
    for ti, (tname, tsub) in enumerate(TABLES):
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
                      f'<span class="mv dn">&#9660; {-m_}</span>' if m_ < 0 else '<span class="mv eq">Same seat</span>')
            topp = t["top_scorer"]
            nw = tid == newly
            note = copy.get("newlywed_note", "")
            ribbon = ((f'<div class="just">{RINGS}<span>Just married</span></div>'
                       + (f'<p class="nwnote">{e(note)}</p>' if note else "")) if nw else "")
            cards += f'''<article class="place{' newly' if nw else ''}{' first' if t['rank'] == 1 else ''}" id="t{tid}">
  {ribbon}<header class="th">
    <span class="rk">{t["rank"]}</span>
    <img class="lg" src="{av(t)}" alt="" loading="lazy">
    <div class="who"><h3>{e(t["name"])}</h3><p>{e(t["owner"])} &middot; {t["wins"]}-{t["losses"]} {mv}</p></div>
    <div class="pts"><b>{fmt(t["week_points"])}</b><span>{"+" if t["week_proj_diff"] >= 0 else ""}{t["week_proj_diff"]:.1f} vs projection</span></div>
  </header>
  <div class="bar" tabindex="0" data-tip="{pos_payload(t)}" aria-label="Points by position">{stack(t, max(1.0, t["week_points"]))}</div>
  <p class="take">{e(takes.get(str(tid), ""))}</p>
  <p class="pog"><img src="{hs(topp)}" alt="" loading="lazy"><span>Top performer <b>{e(topp["name"])}</b> {fmt(topp["points"])}</span></p>
</article>'''
        seating += f'''<div class="table t{ti}">
  <header class="tableh">{sprig("sprig sm")}<div><p class="tn">{e(tname)}</p><h3>{e(tsub)}</h3></div>{sprig("sprig sm", True)}</header>
  <div class="places">{cards}</div>
</div>'''

    # ---------- RSVPs (playoff odds) ----------
    odds_path = ROOT / "data" / f"odds-week-{wk}.json"
    rsvp = ""
    if odds_path.exists():
        od = json.loads(odds_path.read_text())
        cards = ""
        for t in sorted(teams, key=lambda t: -od["teams"][str(t["team_id"])]["playoffs"]):
            o = od["teams"][str(t["team_id"])]
            p = o["playoffs"]
            if p >= 90: reply, cls = "Joyfully accepts", "yes"
            elif p >= 60: reply, cls = "Accepts with pleasure", "yes"
            elif p >= 30: reply, cls = "Will try to make it", "maybe"
            elif p >= 10: reply, cls = "Checking the calendar", "maybe"
            else: reply, cls = "Regretfully declines", "no"
            pct = ">99%" if p >= 99.5 else "<1%" if p < 1 else f"{p:.0f}%"
            cards += f'''<li class="rsvp {cls}">
  <p class="rt">Kindly reply</p>
  <p class="rn"><img src="{av(t)}" alt="">{e(t["name"])}</p>
  <p class="rr"><span class="box">{"&#10003;" if cls == "yes" else "?" if cls == "maybe" else "&#10007;"}</span>{reply}</p>
  <p class="rp"><b>{pct}</b> to make the playoffs</p>
  <div class="meter" aria-hidden="true"><span style="width:{max(1.5, p):.1f}%"></span></div>
  <p class="rx">Now {t["wins"]}-{t["losses"]} &middot; projected {o["proj_wins"]:.0f}-{o["proj_losses"]:.0f}{f" &middot; first-round bye {o['top2']:.0f}%" if o["top2"] >= 1 else ""}</p>
</li>'''
        rsvp = f'''<section id="rsvp">
    <h2>R&eacute;pondez s'il vous pla&icirc;t</h2>
    <p class="lede">{e(copy.get("lede_odds", ""))}</p>
    <ul class="rsvps">{cards}</ul>
    <p class="note">Odds from {od["sims"]:,} simulated seasons on the real remaining schedule. Each team's scoring is pulled toward the league average, so nobody's hot or cold streak is taken at face value. Top {od["playoff_teams"]} make the playoffs and the top two get a first-round bye. Ties broken on total points.</p>
  </section>'''

    # ---------- the cake ----------
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
                  f'<text class="wkl" x="{fx(w):.1f}" y="{T_-14}" text-anchor="middle">Wk {w}</text>' for w in weeks)
    for t in sorted(teams, key=lambda x: -x["rank"]):
        tid = t["team_id"]
        pts = [(fx(x["week"]), fy(x["ranks"][str(tid)])) for x in history]
        d = " ".join(f'{"M" if j == 0 else "L"}{a:.1f},{b:.1f}' for j, (a, b) in enumerate(pts))
        tip = e(json.dumps({"t": t["name"], "rows": [[f"Week {w}", f"#{x['ranks'][str(tid)]}"] for w, x in zip(weeks, history)]}))
        dots = "".join(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="4"/>' for a, b in pts)
        cls = " lead" if t["rank"] == 1 else " newly" if tid == newly else ""
        svg += (f'<g class="ln{cls}" data-team="{tid}" tabindex="0" data-tip="{tip}">'
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
                      f'{"<span class=nx-tag>Main event</span>" if g.get("gotw") else ""}'
                      f'<p class="nx-m"><span class="nx-u"><img src="{av(A)}" alt="">{e(A["name"])} <span class="nx-r">{A["wins"]}-{A["losses"]}</span></span>'
                      f'<span class="nx-u"><span class="nx-vs">&amp;</span><img src="{av(B)}" alt="">{e(B["name"])} <span class="nx-r">{B["wins"]}-{B["losses"]}</span></span></p>'
                      f'<p class="nx-t">{e(g["text"])}</p></li>')
        upnext = f'''<section id="next"><h2>{e(nx.get("title", "Next on the itinerary"))}</h2>
    {f'<p class="lede">{e(nx["intro"])}</p>' if nx.get("intro") else ""}<ul class="nxs">{items}</ul></section>'''
        nxlink = '<a href="#next">Next week</a>'

    card = ROOT / "docs" / f"og-week-{wk}.png"
    og_img = copy.get("og_image") or (f"og-week-{wk}.png" if card.exists() else "og-league.png")
    og_title = copy.get("og_title") or f"Week {wk}: {theme}"
    og_desc = copy.get("og_description") or copy.get("standfirst", "")[:200]
    try:
        stamp = datetime.fromisoformat(data["generated_at"]).strftime("%B %-d, %Y")
    except Exception:
        stamp = ""
    inv = copy.get("invite", {})
    confetti = "".join(f'<i style="--x:{(i * 37) % 100}%;--d:{(i * 0.37) % 2.6:.2f}s;--r:{(i * 47) % 360}deg;--c:{["#e8c9cf", "#c9b27a", "#fff", "#c26d7c", "#a7bd9a"][i % 5]}"></i>'
                       for i in range(44))

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
<meta name="color-scheme" content="light" />
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
<style>{h["load_skin"]("wedding")}</style>
</head>
<body>
<div class="confetti" aria-hidden="true">{confetti}</div>
<nav class="top"><div class="top-in">
  <a class="brand" href="../index.html"><span class="full">{e(data["league_name"])}</span><span class="short">CCL</span></a>
  <div class="links"><a href="#ceremony">Ceremony</a><a href="#seating">Seating</a>{'<a href="#rsvp">RSVPs</a>' if rsvp else ''}<a href="#cake">Cake</a>{nxlink}</div>
</div></nav>

<header class="hero">
  <div class="invite">
    {sprig("sprig tl")}{sprig("sprig tr", True)}
    <p class="i1">{e(inv.get("line1", "Together with their families"))}</p>
    <p class="script">{e(data["league_name"])}</p>
    <p class="i2">{e(inv.get("line2", "request the honour of your presence at"))}</p>
    <p class="wk">Week {WORDS.get(wk, wk)}</p>
    <p class="i2">of the two thousand twenty-six season</p>
    <p class="i3">{e(inv.get("line3", stamp))}</p>
    <p class="i4">Reception to follow &middot; Open bar on the bench</p>
  </div>
  <div class="intro">
    <h1>{e(copy.get("headline", ""))}</h1>
    <p class="dek">{e(copy.get("standfirst", ""))}</p>
  </div>
</header>

<main>
  <section id="ceremony">
    <h2>The Ceremony</h2>
    <p class="lede">{e(copy.get("lede_scores", ""))}</p>
    <ul class="games">{games}</ul>
  </section>

  <section id="seating">
    <h2>The Seating Chart</h2>
    <p class="lede">{e(copy.get("lede_rankings", ""))}</p>
    <div class="legend">{legend}</div>
    {seating}
  </section>

  {rsvp}

  <section id="cake">
    <div class="cakehead">{CAKE}<div><h2>The Cake</h2><p class="lede">{e(copy.get("lede_positions", ""))}</p></div></div>
    <div class="legend">{legend}</div>
    <div class="pchart">{rows}</div>
    <details class="tview"><summary>Show as a table</summary>
      <div class="twrap"><table><thead><tr><th>Team</th>{thead}<th>Total</th></tr></thead><tbody>{trows}</tbody></table></div>
    </details>
  </section>

  <section id="trend">
    <h2>Rank by Week</h2>
    <p class="lede">{e(copy.get("lede_season", ""))}</p>
    <figure class="bumpwrap"><svg class="bump" viewBox="0 0 {W_} {H_}" role="img" aria-label="Power ranking by week for every team">{svg}</svg>
      <figcaption>Rank one at the top. Hover or tap a line to follow one team.</figcaption></figure>
  </section>
{upnext}
  <footer class="foot">
    {sprig("sprig sm")}
    <p class="script sm">{e(copy.get("footer", "With love and questionable lineup decisions"))}</p>
    <p>Data from ESPN, pulled Monday night once the last game is final. <a href="../index.html">All weeks</a></p>
  </footer>
</main>
<script>{js}</script>
</body>
</html>
'''
