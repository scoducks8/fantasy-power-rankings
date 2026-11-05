"""Group chat layout: the week as a chat server.

Channels down the side, each team's blurb is a message with a role badge and
reactions, results are bot embeds, playoff odds are a poll.
Copy keys: headline, standfirst, wasted_team, reply_team (posts as a reply to
wasted_team), takes{id}, reactions{id: [[emoji, count], ...]}, statuses{id},
lede_* keys, typing, footer, up_next, og_title, og_description.
"""

from __future__ import annotations

import html
import json
import zlib

e = html.escape
POS = ["QB", "RB", "WR", "TE", "K", "D/ST"]
POS_NAME = {"QB": "QB", "RB": "RB", "WR": "WR", "TE": "TE", "K": "K", "D/ST": "DEF"}
PCLS = {"QB": "qb", "RB": "rb", "WR": "wr", "TE": "te", "K": "k", "D/ST": "dst"}
ROLES = [("SIGMA 🗿", "r0"), ("RIZZLER 😏", "r1"), ("NPC 🤖", "r2"), ("GOOFY AHH 🤡", "r3")]
EMOJI = ["💀", "😭", "🔥", "🗿", "😂", "🫡", "🤡", "📉", "📈", "👀", "🙏", "😤"]


def fmt(v: float) -> str:
    return f"{v:.1f}"


def _reacts(tid: int, given: list | None) -> list:
    if given:
        return given
    h = zlib.crc32(str(tid).encode())
    out = []
    for i in range(3):
        out.append([EMOJI[(h >> (i * 4)) % len(EMOJI)], 3 + (h >> (i * 5)) % 40])
    seen, uniq = set(), []
    for em, c in out:
        if em not in seen:
            seen.add(em); uniq.append([em, c])
    return uniq


def render(data, history, theme, copy, h) -> str:
    asset, SITE, ROOT = h["asset"], h["SITE"], h["ROOT"]
    teams, mus, wk = data["teams"], data["matchups"], data["week"]
    n = len(teams)
    SH = h["short_names"](teams)
    by_id = {t["team_id"]: t for t in teams}
    takes = copy.get("takes", {})
    wasted = int(copy["wasted_team"]) if copy.get("wasted_team") else None
    reply = int(copy["reply_team"]) if copy.get("reply_team") else None
    for t in teams:
        t.setdefault("week_points", t["points_for"])
        t.setdefault("week_proj_diff", t["week_points"] - (t.get("projected_total") or 0))
    stamp = "Today at 9:41 PM"

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

    def reacts(items):
        return '<div class="reacts">' + "".join(
            f'<button type="button" class="re" aria-pressed="false"><span>{em}</span><b>{c if c < 100 else "99+"}</b></button>'
            for em, c in items) + '<button type="button" class="re add" aria-label="Add reaction">&#9786;+</button></div>'

    def bot(body: str, cls: str = "") -> str:
        return (f'<div class="msg{" " + cls if cls else ""}"><div class="ava bot" aria-hidden="true">🤖</div>'
                f'<div class="mb"><p class="mh"><span class="un botn">ChachBot</span><span class="tag">BOT</span>'
                f'<span class="ts">{stamp}</span></p>{body}</div></div>')

    legend = "".join(f'<span class="lk"><i class="sw {PCLS[p]}"></i>{e(POS_NAME[p])}</span>' for p in POS)

    # ---------- #results ----------
    close = min(mus, key=lambda m: m["margin"])
    blow = max(mus, key=lambda m: m["margin"])
    embeds = ""
    for m in sorted(mus, key=lambda m: (0 if wasted in (m["home_id"], m["away_id"]) else 1, m["margin"])):
        hw = m["winner"] == "HOME"
        W = by_id[m["home_id"] if hw else m["away_id"]]
        L = by_id[m["away_id"] if hw else m["home_id"]]
        ws = m["home_score"] if hw else m["away_score"]
        ls = m["away_score"] if hw else m["home_score"]
        tag, col = "", "ok"
        if wasted and L["team_id"] == wasted:
            tag, col = "🚨 UNDEFEATED NO MORE", "hot"
        elif m is close:
            tag, col = "😰 CLOSEST GAME", "close"
        elif m is blow:
            tag, col = "☠️ BIGGEST L", "blow"
        embeds += f'''<div class="embed {col}">
  {f'<p class="et">{tag}</p>' if tag else ''}
  <div class="er win"><img src="{av(W)}" alt=""><span class="nm">{e(W["name"])}</span><b>{fmt(ws)}</b><span class="wl w">W</span></div>
  <div class="er"><img src="{av(L)}" alt=""><span class="nm">{e(L["name"])}</span><b>{fmt(ls)}</b><span class="wl l">L</span></div>
  <p class="ef">diff {m["margin"]:.2f}</p>
</div>'''
    results = bot(f'<p class="mt">{e(copy.get("lede_scores", ""))}</p><div class="embeds">{embeds}</div>')

    # ---------- #power-rankings ----------
    show_move = len(history) > 1
    ranked = sorted(teams, key=lambda t: t["rank"])
    per = max(1, round(n / 4))
    msgs = bot(f'<p class="mt">{e(copy.get("lede_rankings", ""))}</p><div class="legend">{legend}</div>')
    for i, t in enumerate(ranked):
        tid = t["team_id"]
        role, rc = ROLES[min(3, i // per)]
        mv = ""
        if show_move:
            m_ = t.get("movement") or 0
            mv = (f'<span class="mv up">+{m_ * 1000} aura</span>' if m_ > 0 else
                  f'<span class="mv dn">-{-m_ * 1000} aura</span>' if m_ < 0 else '<span class="mv eq">±0 aura</span>')
        topp = t["top_scorer"]
        rep = ""
        if tid == reply and wasted in by_id:
            rep = (f'<p class="reply"><span class="rl" aria-hidden="true"></span><img src="{av(by_id[wasted])}" alt="">'
                   f'<b>@{e(by_id[wasted]["name"])}</b> <span>{e((takes.get(str(wasted), "")[:60]).strip())}&hellip;</span></p>')
        stampw = '<span class="cooked" aria-label="Cooked">COOKED 💀</span>' if tid == wasted else ""
        msgs += f'''<div class="msg team{' isw' if tid == wasted else ''}" id="t{tid}">
  {rep}<img class="ava" src="{av(t)}" alt="">
  <div class="mb">
    <p class="mh"><span class="un">{e(t["name"])}</span><span class="role {rc}">{e(role)}</span><span class="ts">{stamp}</span></p>
    <p class="mt big">{e(takes.get(str(tid), ""))}</p>
    <div class="card">
      {stampw}
      <div class="ch"><span class="rk">#{t["rank"]}</span><div><p class="cn">{e(t["owner"])} &middot; {t["wins"]}-{t["losses"]}</p>{mv}</div>
        <p class="cp"><b>{fmt(t["week_points"])}</b><span>pts</span></p></div>
      <div class="bar" tabindex="0" data-tip="{pos_payload(t)}" aria-label="Points by position">{stack(t, max(1.0, t["week_points"]))}</div>
      <p class="mvp"><img src="{hs(topp)}" alt="" loading="lazy">MVP <b>{e(topp["name"])}</b> {fmt(topp["points"])}</p>
    </div>
    {reacts(_reacts(tid, copy.get("reactions", {}).get(str(tid))))}
  </div>
</div>'''

    # ---------- #copium (poll) ----------
    odds_path = ROOT / "data" / f"odds-week-{wk}.json"
    poll = ""
    if odds_path.exists():
        od = json.loads(odds_path.read_text())
        rows = ""
        for t in sorted(teams, key=lambda t: -od["teams"][str(t["team_id"])]["playoffs"]):
            p = od["teams"][str(t["team_id"])]["playoffs"]
            pct = ">99%" if p >= 99.5 else "<1%" if p < 1 else f"{p:.0f}%"
            vibe = "locked in 🔒" if p >= 90 else "sweating 😰" if p >= 50 else "coping 🫠" if p >= 10 else "it's over 🪦"
            rows += (f'<li class="po"><span class="pf" style="width:{max(1.5, p):.1f}%"></span>'
                     f'<span class="pl"><img src="{av(t)}" alt="">{e(t["name"])}<small>{vibe}</small></span><b>{pct}</b></li>')
        poll = bot(f'''<p class="mt">{e(copy.get("lede_odds", ""))}</p>
<div class="poll"><p class="pq">📊 who's making playoffs?? (the math version)</p><ol class="pos">{rows}</ol>
<p class="pn">{od["sims"]:,} simulated seasons &middot; top {od["playoff_teams"]} make it &middot; ties go to total points</p></div>''')

    # ---------- #loadout ----------
    mx = max(t["week_points"] for t in teams)
    rows, trows = "", ""
    for t in sorted(teams, key=lambda x: -x["week_points"]):
        rows += (f'<div class="prow" tabindex="0" data-tip="{pos_payload(t)}">'
                 f'<span class="pn2">{e(SH[t["team_id"]])}</span>'
                 f'<span class="pt"><span class="ps" style="width:calc((100% - 56px) * {t["week_points"] / mx:.4f})">'
                 f'{stack(t, max(1.0, t["week_points"]))}</span>'
                 f'<span class="pv">{fmt(t["week_points"])}</span></span></div>')
        trows += ("<tr><th>" + e(t["name"]) + "</th>" +
                  "".join(f'<td>{t["positional"].get(p, 0):.1f}</td>' for p in POS) +
                  f'<td class="tot">{fmt(t["week_points"])}</td></tr>')
    thead = "".join(f"<th>{POS_NAME[p]}</th>" for p in POS)
    loadout = bot(f'''<p class="mt">{e(copy.get("lede_positions", ""))}</p><div class="legend">{legend}</div>
<div class="pchart">{rows}</div><details class="tview"><summary>show as table 🤓</summary>
<div class="twrap"><table><thead><tr><th>Team</th>{thead}<th>Total</th></tr></thead><tbody>{trows}</tbody></table></div></details>''')

    # ---------- #the-grind ----------
    weeks = [x["week"] for x in history]
    W_, H_, L_, R_, T_, B_ = 560, 380, 34, 150, 30, 16
    span = max(1, (weeks[-1] - weeks[0]) or 1)
    fx = lambda w: L_ + (0 if len(weeks) == 1 else (w - weeks[0]) / span * (W_ - L_ - R_))
    fy = lambda r: T_ + (r - 1) / (n - 1) * (H_ - T_ - B_)
    svg = "".join(f'<line class="grid" x1="{fx(w):.1f}" y1="{T_-8}" x2="{fx(w):.1f}" y2="{H_-B_+6}"/>'
                  f'<text class="wkl" x="{fx(w):.1f}" y="{T_-14}" text-anchor="middle">W{w}</text>' for w in weeks)
    pal = ["#a78bfa", "#f472b6", "#34d399", "#60a5fa", "#fbbf24", "#f87171", "#22d3ee", "#c084fc", "#fb923c", "#4ade80", "#e879f9", "#e5e7eb"]
    for t in sorted(teams, key=lambda x: -x["rank"]):
        tid = t["team_id"]
        pts = [(fx(x["week"]), fy(x["ranks"][str(tid)])) for x in history]
        d = " ".join(f'{"M" if j == 0 else "L"}{a:.1f},{b:.1f}' for j, (a, b) in enumerate(pts))
        tip = e(json.dumps({"t": t["name"], "rows": [[f"Week {w}", f"#{x['ranks'][str(tid)]}"] for w, x in zip(weeks, history)]}))
        dots = "".join(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="4"/>' for a, b in pts)
        svg += (f'<g class="ln" style="--c:{pal[(t["rank"] - 1) % 12]}" data-team="{tid}" tabindex="0" data-tip="{tip}">'
                f'<path class="hit" d="{d}"/><path class="stroke" d="{d}"/>{dots}'
                f'<text x="{pts[-1][0]+12:.1f}" y="{pts[-1][1]+4.5:.1f}">{t["rank"]}. {e(SH[tid])}</text></g>')
    svg += "".join(f'<text class="ax" x="{L_-14}" y="{fy(r)+4:.1f}" text-anchor="end">{r}</text>' for r in (1, n))
    grind = bot(f'''<p class="mt">{e(copy.get("lede_season", ""))}</p>
<figure class="bumpwrap"><svg class="bump" viewBox="0 0 {W_} {H_}" role="img" aria-label="Power ranking by week for every team">{svg}</svg>
<figcaption>rank 1 at the top. hover or tap a line</figcaption></figure>''')

    # ---------- #next-week ----------
    nx = copy.get("up_next") or {}
    nextc = ""
    if nx.get("games"):
        items = ""
        for g in nx["games"]:
            A, B = by_id[g["a"]], by_id[g["b"]]
            items += (f'<div class="embed{" hot" if g.get("gotw") else ""}">{"<p class=et>🚨 MAIN EVENT</p>" if g.get("gotw") else ""}'
                      f'<p class="nxm"><img src="{av(A)}" alt="">{e(A["name"])} <span>{A["wins"]}-{A["losses"]}</span> <i>vs</i> '
                      f'<img src="{av(B)}" alt="">{e(B["name"])} <span>{B["wins"]}-{B["losses"]}</span></p>'
                      f'<p class="nxt">{e(g["text"])}</p></div>')
        nextc = bot(f'<p class="mt">{e(nx.get("intro", ""))}</p><div class="embeds">{items}</div>')

    # ---------- member list ----------
    sts = copy.get("statuses", {})
    members = "".join(
        f'<li><span class="mav"><img src="{av(t)}" alt=""><i class="st {"dnd" if t["team_id"] == wasted else "on"}"></i></span>'
        f'<span><b class="{ROLES[min(3, i // per)][1]}">{e(t["owner"])}</b><small>{e(sts.get(str(t["team_id"]), ""))}</small></span></li>'
        for i, t in enumerate(ranked))
    servers = "".join(f'<a class="sv" href="#t{t["team_id"]}" title="{e(t["name"])}"><img src="{av(t)}" alt=""></a>' for t in ranked)

    chans = [("announcements", "📢"), ("results", "🏈"), ("power-rankings", "🏆"), ("copium", "💊"),
             ("loadout", "🎒"), ("the-grind", "📈"), ("next-week", "⏭️")]
    if not poll:
        chans = [c for c in chans if c[0] != "copium"]
    if not nextc:
        chans = [c for c in chans if c[0] != "next-week"]
    chanlist = "".join(f'<a href="#{c}"><span>#</span>{c} {ic}</a>' for c, ic in chans)
    chips = "".join(f'<a href="#{c}">#{c}</a>' for c, ic in chans)

    def channel(cid: str, body: str, topic: str = "") -> str:
        return (f'<section class="chan" id="{cid}"><header class="chh"><span class="hash">#</span>{cid}'
                f'{f"<span class=topic>{e(topic)}</span>" if topic else ""}</header>'
                f'<div class="divider"><span>{e(copy.get("date_label", "today"))}</span></div>{body}</section>')

    card = ROOT / "docs" / f"og-week-{wk}.png"
    og_img = copy.get("og_image") or (f"og-week-{wk}.png" if card.exists() else "og-league.png")
    og_title = copy.get("og_title") or f"Week {wk}: {theme}"
    og_desc = copy.get("og_description") or copy.get("standfirst", "")[:200]

    announce = bot(f'''<p class="ping">@everyone</p><h1>{e(copy.get("headline", ""))}</h1>
<p class="mt big">{e(copy.get("standfirst", ""))}</p>''', "pinned")

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
  // reactions you can actually click
  document.querySelectorAll('.re:not(.add)').forEach(function(b){
    b.addEventListener('click',function(){var on=b.getAttribute('aria-pressed')==='true';var n=b.querySelector('b');
      if(n.textContent!=='99+'){n.textContent=String(parseInt(n.textContent,10)+(on?-1:1))}
      b.setAttribute('aria-pressed',on?'false':'true')});
  });
  document.querySelectorAll('.re.add').forEach(function(b){
    b.addEventListener('click',function(){var list=['💀','😭','🔥','🗿','🫡','🤡'];var em=list[Math.floor(Math.random()*list.length)];
      var nb=document.createElement('button');nb.type='button';nb.className='re';nb.setAttribute('aria-pressed','true');
      var s=document.createElement('span');s.textContent=em;var c=document.createElement('b');c.textContent='1';
      nb.appendChild(s);nb.appendChild(c);b.parentNode.insertBefore(nb,b)});
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
<style>{h["load_skin"]("chat")}</style>
</head>
<body>
<div class="app">
  <nav class="rail" aria-label="Teams"><a class="home" href="../index.html" title="All weeks">CCL</a><span class="sep"></span>{servers}</nav>
  <aside class="side">
    <header class="sname">{e(data["league_name"])} <span>&#9662;</span></header>
    <p class="cat">WEEK {wk} &middot; TEXT CHANNELS</p>
    <div class="chans">{chanlist}</div>
    <div class="me"><span class="mav"><span class="bubble">🤖</span><i class="st on"></i></span><span><b>ChachBot</b><small>posting rankings</small></span></div>
  </aside>
  <div class="main">
    <header class="topbar"><a class="back" href="../index.html">CCL</a><span class="hash">#</span>week-{wk}<span class="topic">{e(copy.get("topic", "power rankings drop. no cap"))}</span></header>
    <nav class="chips" aria-label="Channels">{chips}</nav>
    {channel("announcements", announce, "pinned 📌")}
    {channel("results", results, "every game this week")}
    {channel("power-rankings", msgs, "ranked by power score, aura shows who moved")}
    {channel("copium", poll, "playoff odds") if poll else ""}
    {channel("loadout", loadout, "points by position")}
    {channel("the-grind", grind, "rank by week")}
    {channel("next-week", nextc, "week {0} lobby".format(wk + 1)) if nextc else ""}
    <div class="typing" aria-hidden="true"><span class="dots"><i></i><i></i><i></i></span><b>{e(copy.get("typing", "someone is typing..."))}</b></div>
    <footer class="foot"><p>{e(copy.get("footer", "gg go next"))}</p><p>Data from ESPN, pulled Monday night once the last game is final. <a href="../index.html">All weeks</a></p></footer>
  </div>
  <aside class="members" aria-label="Members"><p class="cat">ONLINE · {n}</p><ul>{members}</ul></aside>
</div>
<script>{js}</script>
</body>
</html>
'''
