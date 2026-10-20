"""Hyphy layout: a Bay Area sideshow flyer with E-40 as patron saint.

Photos: any .jpg/.jpeg/.png/.webp dropped in docs/assets/hyphy/ are used in
filename order and cycled. Captions come from copy["photo_captions"][filename].
With no photos the page shows labelled placeholder frames.

Copy keys: headline, standfirst, ticker[list], takes{id}, facts{id},
lede_scores, lede_rankings, lede_positions, lede_season, awards{key: text},
thizz_team (team id for Thizz Face of the Week), photo_captions{}, footer,
og_title, og_description, up_next (same shape as the clean layout).
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
TIERS = [("Hyphy Mode", "Ghost ridin' the standings"), ("Scrapin' On 'Em", "Candy paint, foil on the spokes"),
         ("Stuck in the Fog", "Karl rolled in"), ("Waiting on BART", "Next train: delayed")]
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def fmt(v: float) -> str:
    return f"{v:.1f}"


# ---------------------------------------------------------------- drawings
def scraper_bike(cls: str = "bike") -> str:
    """Original scraper bike: candy frame, tall bars, foil-wrapped spokes."""
    def wheel(cx: int) -> str:
        spokes = ""
        cols = ["#ff4d5e", "#ffb627", "#5be37d", "#39b8ff", "#b47cff", "#ff4d5e", "#ffb627", "#5be37d"]
        for i in range(16):
            ang = i * 22.5
            spokes += (f'<line x1="{cx}" y1="150" x2="{cx}" y2="96" stroke="{cols[i % 8]}" stroke-width="7" '
                       f'transform="rotate({ang} {cx} 150)" stroke-linecap="round" opacity=".9"/>')
        return (f'<g class="whl"><circle cx="{cx}" cy="150" r="58" fill="none" stroke="#2a2a30" stroke-width="10"/>'
                f'<g class="spin" style="transform-origin:{cx}px 150px">{spokes}'
                f'<circle cx="{cx}" cy="150" r="50" fill="none" stroke="url(#chrome)" stroke-width="5"/></g>'
                f'<circle cx="{cx}" cy="150" r="9" fill="url(#chrome)"/></g>')
    return f'''<svg class="{cls}" viewBox="0 0 400 220" role="img" aria-label="Scraper bike">
<defs><linearGradient id="chrome" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fafafa"/>
<stop offset=".45" stop-color="#9a9aa3"/><stop offset=".55" stop-color="#e8e8ee"/><stop offset="1" stop-color="#6b6b75"/></linearGradient>
<linearGradient id="candy" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff2a4f"/>
<stop offset=".5" stop-color="#c8102e"/><stop offset="1" stop-color="#ffb627"/></linearGradient></defs>
{wheel(88)}{wheel(312)}
<g stroke="url(#candy)" stroke-width="12" stroke-linecap="round" stroke-linejoin="round" fill="none">
<path d="M88 150 L170 150 L250 70 L140 70 Z"/><path d="M170 150 L120 52"/><path d="M250 70 L312 150"/>
<path d="M248 70 L262 24"/></g>
<path d="M232 26 Q262 6 292 18" stroke="url(#chrome)" stroke-width="8" fill="none" stroke-linecap="round"/>
<rect x="92" y="40" width="58" height="14" rx="7" fill="#111" stroke="#ffb627" stroke-width="3"/>
<circle cx="170" cy="150" r="14" fill="none" stroke="url(#chrome)" stroke-width="5"/>
</svg>'''


def shades(cls: str = "shades") -> str:
    return f'''<svg class="{cls}" viewBox="0 0 120 44" aria-hidden="true">
<path d="M4 10 Q60 0 116 10 L112 22 Q104 40 82 38 Q66 36 62 22 L58 22 Q54 36 38 38 Q16 40 8 22 Z" fill="#0b0b0d" stroke="url(#gold)" stroke-width="3"/>
<defs><linearGradient id="gold" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffb627"/><stop offset="1" stop-color="#ff4d5e"/></linearGradient></defs>
<path d="M18 16 L34 16" stroke="#fff" stroke-width="3" opacity=".55" stroke-linecap="round"/>
<path d="M72 16 L88 16" stroke="#fff" stroke-width="3" opacity=".55" stroke-linecap="round"/></svg>'''


SKYLINE = '''<svg class="skyline" viewBox="0 0 1200 180" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
<g fill="#16161b">
<rect x="0" y="150" width="1200" height="30"/>
<polygon points="128,150 150,40 172,150"/><rect x="146" y="70" width="8" height="80"/>
<rect x="60" y="110" width="40" height="40"/><rect x="200" y="96" width="34" height="54"/><rect x="240" y="120" width="44" height="30"/>
<rect x="300" y="84" width="26" height="66"/><rect x="330" y="108" width="40" height="42"/>
<rect x="960" y="100" width="30" height="50"/><rect x="996" y="118" width="46" height="32"/><rect x="1050" y="90" width="28" height="60"/>
<rect x="1086" y="112" width="60" height="38"/>
</g>
<g stroke="#2b2b33" stroke-width="3" fill="none">
<path d="M1150 150 L1150 30 M1140 150 L1150 30 L1160 150 M1132 70 L1168 70 M1136 90 L1164 90"/>
</g>
<g stroke="#3a3a44" fill="none">
<rect x="520" y="30" width="12" height="120" fill="#1d1d23" stroke="none"/><rect x="760" y="30" width="12" height="120" fill="#1d1d23" stroke="none"/>
<path d="M400 118 Q463 110 526 32 Q646 128 766 32 Q829 110 900 118" stroke-width="3"/>
<path d="M400 120 L900 120" stroke-width="6" stroke="#2b2b33"/>
<g class="cables" stroke-width="1.2">
<path d="M440 120 L440 113 M470 120 L470 104 M500 120 L500 76 M560 120 L560 66 M590 120 L590 88 M620 120 L620 104 M650 120 L650 110 M680 120 L680 104 M710 120 L710 88 M740 120 L740 66 M800 120 L800 76 M830 120 L830 104 M860 120 L860 113"/>
</g></g>
<g class="lights" fill="#ffb627"><circle cx="526" cy="32" r="2.5"/><circle cx="766" cy="32" r="2.5"/></g>
</svg>'''

CHAIN = '<div class="chain" aria-hidden="true"></div>'


def render(data, history, theme, copy, h) -> str:
    asset, SITE, ROOT = h["asset"], h["SITE"], h["ROOT"]
    teams, mus, wk = data["teams"], data["matchups"], data["week"]
    n = len(teams)
    SH = h["short_names"](teams)
    by_id = {t["team_id"]: t for t in teams}
    takes = copy.get("takes", {})
    facts = copy.get("facts", {})
    for t in teams:
        t.setdefault("week_points", t["points_for"])
        t.setdefault("week_proj_diff", t["week_points"] - (t.get("projected_total") or 0))

    def av(t):
        return e(asset(t.get("logo_local", ""), t.get("logo", ""), t["owner"]))

    def hs(p):
        return e(asset(p.get("headshot_local", ""), p.get("headshot", ""), p["name"], "hs"))

    # ---------- photos ----------
    pdir = ROOT / "docs" / "assets" / "hyphy"
    files = sorted(f.name for f in pdir.iterdir() if f.suffix.lower() in IMG_EXT) if pdir.exists() else []
    caps = copy.get("photo_captions", {})
    state = {"i": 0}

    def photo(cls: str = "", default_cap: str = "") -> str:
        i = state["i"]; state["i"] += 1
        tilt = [-3, 2.5, -1.5, 3, -2.5, 1.5][i % 6]
        if not files:
            return (f'<figure class="snap ph {cls}" style="--tilt:{tilt}deg"><div class="phbox">'
                    f'<span>E-40 photo #{i + 1}</span></div>'
                    f'<figcaption>{e(default_cap)}</figcaption></figure>')
        f = files[i % len(files)]
        return (f'<figure class="snap {cls}" style="--tilt:{tilt}deg"><img src="../assets/hyphy/{e(f)}" alt="E-40">'
                f'<figcaption>{e(caps.get(f, default_cap))}</figcaption></figure>')

    hero_photo = photo("heropic", copy.get("hero_caption", "Our patron saint"))

    def pos_payload(t):
        return e(json.dumps({"t": t["name"],
                             "rows": [[POS_NAME[p], f'{t["positional"].get(p, 0):.1f}', PCLS[p]] for p in POS],
                             "total": f'{t["week_points"]:.1f}'}))

    def stack(t, scale):
        segs = ""
        for p in POS:
            v = t["positional"].get(p, 0)
            if v > 0:
                segs += f'<span class="seg {PCLS[p]}" style="width:{v / scale * 100:.2f}%"></span>'
        return segs

    # ---------- awards ----------
    aw = copy.get("awards", {})
    best = None
    for t in teams:
        for s in t.get("starters", []):
            if best is None or s["points"] > best[0]["points"]:
                best = (s, t)
    close = min(mus, key=lambda m: m["margin"])
    cw = by_id[close["home_id"] if close["winner"] == "HOME" else close["away_id"]]
    cl = by_id[close["away_id"] if close["winner"] == "HOME" else close["home_id"]]
    movers = [t for t in teams if t.get("movement") is not None]
    riser = max(movers, key=lambda t: t["movement"]) if movers else None
    faller = min(movers, key=lambda t: t["movement"]) if movers else None
    thizz = by_id.get(int(copy["thizz_team"])) if copy.get("thizz_team") else max(teams, key=lambda t: t["week_proj_diff"])
    awards = [
        ("stunna", "Stunna Shades", f'{best[0]["name"]}', f'{fmt(best[0]["points"])} for {best[1]["name"]}', shades("ic")),
        ("thizz", "Thizz Face of the Week", thizz["name"], aw.get("thizz", f'{thizz["week_proj_diff"]:+.1f} vs projection'), '<span class="ic face" aria-hidden="true">&#128556;</span>'),
        ("side", "Sideshow of the Week", f'{cw["name"]} over {cl["name"]}', f'by {close["margin"]:.2f}', '<span class="ic donut" aria-hidden="true"></span>'),
    ]
    if riser and riser["movement"] > 0:
        awards.append(("scrape", "Scraper of the Week", riser["name"], f'up {riser["movement"]} to No. {riser["rank"]}', scraper_bike("ic mini")))
    if faller and faller["movement"] < 0:
        awards.append(("ghost", "Ghost Ride the Whip", faller["name"], f'down {-faller["movement"]} to No. {faller["rank"]}', '<span class="ic ghost" aria-hidden="true">&#128123;</span>'))
    glance = "".join(f'<div class="award {k}">{ic}<p class="al">{e(a)}</p><p class="av">{e(b)}</p>'
                     f'<p class="as">{e(aw.get(k + "_sub", c) if k != "thizz" else c)}</p></div>'
                     for k, a, b, c, ic in awards)

    # ---------- results ----------
    games = ""
    for m in sorted(mus, key=lambda m: m["margin"]):
        hw = m["winner"] == "HOME"
        W = by_id[m["home_id"] if hw else m["away_id"]]
        L = by_id[m["away_id"] if hw else m["home_id"]]
        ws = m["home_score"] if hw else m["away_score"]
        ls = m["away_score"] if hw else m["home_score"]
        side = m is close
        games += f'''<li class="game{' side' if side else ''}">
  {'<p class="gtag">Sideshow of the Week</p><span class="donuts" aria-hidden="true"></span>' if side else ''}
  <div class="gs win"><img src="{av(W)}" alt="" loading="lazy"><span class="nm">{e(W["name"])}</span><span class="sc">{fmt(ws)}</span></div>
  <div class="gs"><img src="{av(L)}" alt="" loading="lazy"><span class="nm">{e(L["name"])}</span><span class="sc">{fmt(ls)}</span></div>
  <p class="mg">{"Ghost ride finish: " + f"{m['margin']:.2f}" if m["margin"] < 10 else "Won by " + f"{m['margin']:.1f}"}</p>
</li>'''

    legend = "".join(f'<span class="lk"><i class="sw {PCLS[p]}"></i>{e(POS_NAME[p])}</span>' for p in POS)

    # ---------- rankings ----------
    show_move = len(history) > 1
    teams_sorted = sorted(teams, key=lambda t: t["rank"])
    per = max(1, round(n / 4))
    tier_html = ""
    photo_slots = {0: "Hyphy Mode activated", 1: "Checkin' the box score", 2: "Contemplatin' the fog", 3: "Even Sourdough Sam can't believe it"}
    for ti, (tname, tsub) in enumerate(TIERS):
        chunk = teams_sorted[ti * per:(ti + 1) * per] if ti < 3 else teams_sorted[3 * per:]
        if not chunk:
            continue
        cards = ""
        for t in chunk:
            tid = t["team_id"]
            mv = ""
            if show_move:
                m_ = t.get("movement") or 0
                if m_ > 0:
                    mv = f'<span class="sign up">Express &#9650;{m_}</span>'
                elif m_ < 0:
                    mv = f'<span class="sign dn">Delayed &#9660;{-m_}</span>'
                else:
                    mv = '<span class="sign eq">On time</span>'
            topp = t["top_scorer"]
            fact = facts.get(str(tid), "")
            badge = f'<div class="crown">{scraper_bike("mini")}<span>King of the Yay</span></div>' if t["rank"] == 1 else ""
            cards += f'''<article class="team r{t["rank"]}" id="t{tid}">
  {badge}<header class="th">
    <span class="rk">{t["rank"]}</span>
    <img class="lg" src="{av(t)}" alt="" loading="lazy">
    <div class="who"><h3>{e(t["name"])}</h3><p>{e(t["owner"])} &middot; {t["wins"]}-{t["losses"]}</p>{mv}</div>
    <div class="pts"><b>{fmt(t["week_points"])}</b><span>{"+" if t["week_proj_diff"] >= 0 else ""}{t["week_proj_diff"]:.1f} vs proj</span></div>
  </header>
  <div class="bar" tabindex="0" data-tip="{pos_payload(t)}" aria-label="Points by position">{stack(t, max(1.0, t["week_points"]))}</div>
  <p class="take">{e(takes.get(str(tid), ""))}</p>
  {f'<p class="fact"><span class="ft">40 Fact</span>{e(fact)}</p>' if fact else ""}
  <p class="pog"><img src="{hs(topp)}" alt="" loading="lazy"><span>Went stupid: <b>{e(topp["name"])}</b> {fmt(topp["points"])}</span></p>
</article>'''
        fog = ' fog' if ti == 3 else ''
        tier_html += f'''<div class="tier t{ti}{fog}">
  {CHAIN if ti else ""}
  <header class="tierh"><h3>{e(tname)}</h3><p>{e(tsub)}</p></header>
  {photo("tierpic", photo_slots.get(ti, "")) if ti in photo_slots else ""}
  <div class="teams">{cards}</div>
</div>'''

    # ---------- the build (scoring by position) ----------
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

    # ---------- bridge toll (bump chart) ----------
    weeks = [x["week"] for x in history]
    W_, H_, L_, R_, T_, B_ = 560, 380, 34, 150, 30, 16
    span = max(1, (weeks[-1] - weeks[0]) or 1)
    fx = lambda w: L_ + (0 if len(weeks) == 1 else (w - weeks[0]) / span * (W_ - L_ - R_))
    fy = lambda r: T_ + (r - 1) / (n - 1) * (H_ - T_ - B_)
    svg = "".join(f'<line class="grid" x1="{fx(w):.1f}" y1="{T_-8}" x2="{fx(w):.1f}" y2="{H_-B_+6}"/>'
                  f'<text class="wkl" x="{fx(w):.1f}" y="{T_-14}" text-anchor="middle">Wk {w}</text>'
                  for w in weeks)
    palette = ["#ff4d5e", "#ffb627", "#5be37d", "#39b8ff", "#b47cff", "#ff8fab",
               "#ffd166", "#06d6a0", "#8ecae6", "#cdb4db", "#f4a261", "#e9e9ee"]
    lines = ""
    for i, t in enumerate(sorted(teams, key=lambda x: -x["rank"])):
        tid = t["team_id"]
        col = palette[(t["rank"] - 1) % len(palette)]
        pts = [(fx(x["week"]), fy(x["ranks"][str(tid)])) for x in history]
        d = " ".join(f'{"M" if j == 0 else "L"}{a:.1f},{b:.1f}' for j, (a, b) in enumerate(pts))
        path_ranks = [x["ranks"][str(tid)] for x in history]
        tip = e(json.dumps({"t": t["name"], "rows": [[f"Week {w}", f"#{r}"] for w, r in zip(weeks, path_ranks)]}))
        dots = "".join(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="4"/>' for a, b in pts)
        lines += (f'<g class="ln" style="--c:{col}" data-team="{tid}" tabindex="0" data-tip="{tip}">'
                  f'<path class="hit" d="{d}"/><path class="stroke" d="{d}"/>{dots}'
                  f'<text x="{pts[-1][0]+12:.1f}" y="{pts[-1][1]+4.5:.1f}">{t["rank"]}. {e(SH[tid])}</text></g>')
    svg += lines
    svg += "".join(f'<text class="ax" x="{L_-14}" y="{fy(r)+4:.1f}" text-anchor="end">{r}</text>' for r in (1, n))

    # ---------- up next ----------
    nx = copy.get("up_next") or {}
    upnext, nxlink = "", ""
    if nx.get("games"):
        items = ""
        for g in nx["games"]:
            A, B = by_id[g["a"]], by_id[g["b"]]
            items += (f'<li class="nx{" gotw" if g.get("gotw") else ""}">'
                      f'{"<span class=nx-tag>Sideshow of the Week</span>" if g.get("gotw") else ""}'
                      f'<p class="nx-m"><span class="nx-u"><img src="{av(A)}" alt="">{e(A["name"])} <span class="nx-r">{A["wins"]}-{A["losses"]}</span></span>'
                      f'<span class="nx-u"><span class="nx-vs">vs</span><img src="{av(B)}" alt="">{e(B["name"])} <span class="nx-r">{B["wins"]}-{B["losses"]}</span></span></p>'
                      f'<p class="nx-t">{e(g["text"])}</p></li>')
        upnext = f'''<section id="next"><h2><span>Up next</span> {e(nx.get("title", f"Week {wk + 1}"))}</h2>
    {f'<p class="lede">{e(nx["intro"])}</p>' if nx.get("intro") else ""}<ul class="nxs">{items}</ul></section>'''
        nxlink = '<a href="#next">Next</a>'

    ticker_items = copy.get("ticker") or []
    if not ticker_items:
        for m in mus:
            hw = m["winner"] == "HOME"
            W = by_id[m["home_id"] if hw else m["away_id"]]
            L = by_id[m["away_id"] if hw else m["home_id"]]
            ticker_items.append(f'{SH[W["team_id"]]} {fmt(max(m["home_score"], m["away_score"]))}, '
                                f'{SH[L["team_id"]]} {fmt(min(m["home_score"], m["away_score"]))}')
    tick = "".join(f"<span>{e(x)}</span>" for x in ticker_items)

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
<style>{h["load_skin"]("hyphy")}</style>
</head>
<body>
<div class="radio" aria-label="Scores"><span class="station">THE YAY 40.0 FM</span><div class="tickwrap"><div class="tick">{tick}{tick}</div></div></div>
<nav class="top"><div class="top-in">
  <a class="brand" href="../index.html"><span class="full">{e(data["league_name"])}</span><span class="short">CCL</span></a>
  <div class="links"><a href="#results">Sideshow</a><a href="#rankings">Rankings</a><a href="#build">Build</a><a href="#trend">Toll</a>{nxlink}</div>
</div></nav>

<header class="hero">
  {SKYLINE}
  <div class="hero-in">
    <div class="htext">
      <p class="kicker">Week {wk} &middot; From the City to the Town{(" &middot; " + e(stamp)) if stamp else ""}</p>
      <h1>{e(copy.get("headline", ""))}</h1>
      <p class="tag">Niner Gang &middot; Hyphy Edition</p>
      <p class="dek">{e(copy.get("standfirst", ""))}</p>
    </div>
    {hero_photo}
  </div>
  <div class="fogband" aria-hidden="true"></div>
</header>

<main>
  <section class="awards" aria-label="Awards">{glance}</section>

  <section id="results">
    <h2><span>Sideshow</span> Results</h2>
    <p class="lede">{e(copy.get("lede_scores", ""))}</p>
    <ul class="games">{games}</ul>
  </section>

  <section id="rankings">
    <h2><span>Who's</span> Goin' Dumb</h2>
    <p class="lede">{e(copy.get("lede_rankings", ""))}</p>
    <div class="legend">{legend}</div>
    {tier_html}
  </section>

  <section id="build">
    <div class="buildhead">{scraper_bike("bike big")}<div><h2><span>The</span> Build</h2>
    <p class="lede">{e(copy.get("lede_positions", ""))}</p></div></div>
    <div class="legend">{legend}</div>
    <div class="pchart">{rows}</div>
    <details class="tview"><summary>Show as a table</summary>
      <div class="twrap"><table><thead><tr><th>Team</th>{thead}<th>Total</th></tr></thead><tbody>{trows}</tbody></table></div>
    </details>
  </section>

  <section id="trend">
    <h2><span>Bridge</span> Toll</h2>
    <p class="lede">{e(copy.get("lede_season", ""))}</p>
    <div class="trendgrid">
      <figure class="bumpwrap"><svg class="bump" viewBox="0 0 {W_} {H_}" role="img" aria-label="Power ranking by week for every team">{svg}</svg>
        <figcaption>Rank one at the top. Hover or tap a line to follow one team.</figcaption></figure>
      {photo("trendpic", copy.get("trend_caption", "Still the Yay's biggest fan"))}
    </div>
  </section>
{upnext}
  <footer class="foot">
    {photo("footpic", copy.get("foot_caption", "Last call. Everybody out the sideshow."))}
    <p class="sign-off">{e(copy.get("footer", "Stay hyphy, stay Faithful, keep scrapin'."))}</p>
    <p>Data from ESPN, pulled Monday night once the last game is final. <a href="../index.html">All weeks</a></p>
  </footer>
</main>
<script>{js}</script>
</body>
</html>
'''
