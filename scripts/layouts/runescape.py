"""RuneScape layout. A themed week can ship its own page structure.

The default renderer handles ordinary weeks. When a skin has a matching
module in scripts/layouts/, render_week.py hands the same data to it instead,
so a big theme week can look like a different site without forking the data
pipeline. Words still come from data/copy-week-N*.json.

Page: login screen, a game-client hero, Duel Arena results, a Hiscores table
plus an Adventurer's Log entry per team, a skills matrix, the XP tracker, and
a chatbox fixed along the bottom.
"""

from __future__ import annotations

import html

e = html.escape

SKILL = {"QB": "Magic", "RB": "Strength", "WR": "Ranged",
         "TE": "Defence", "K": "Agility", "D/ST": "Prayer"}

# 10x10 pixel icons. '#' outline, 'b' the position colour, 'w' white,
# 's' steel, 'g' gold, 'r' red. Anything else is transparent.
ICONS = {
    "QB": ["....#.....", "...#b#....", "...#b#....", "####b####.", "#bbbbbbb#.",
           ".#bbbbb#..", "..#bbb#...", ".#bb#bb#..", ".#b#.#b#..", ".##...##.."],
    "RB": ["..........", ".##....##.", "#bb#..#bb#", "#bb####bb#", "#bbbbbbbb#",
           "#bb####bb#", "#bb#..#bb#", ".##....##.", "..........", ".........."],
    "WR": [".......###", "........b#", ".......#b#", "......#b#.", ".....#b#..",
           "..#.#b#...", "..##b#....", "..#b#.....", ".#b###....", "#b#......."],
    "TE": ["..######..", ".#ssssss#.", ".#sbbbbs#.", ".#sbbbbs#.", ".#sbbbbs#.",
           ".#ssbbss#.", "..#sbbs#..", "..#ssss#..", "...#ss#...", "....##...."],
    "K":  ["..####....", "..#bb#....", "..#bb#....", "..#bb#....", "..#bb#....",
           "..#bb###..", "..#bbbbb#.", ".#bbbbbbb#", ".#bbbbbbb#", ".#########"],
    "D/ST": ["...####...", "...#bb#...", ".###bb###.", ".#bbbbbb#.", ".###bb###.",
             "...#bb#...", "...#bb#...", "...#bb#...", "...#bb#...", "...####..."],
    "swords": ["ss......ss", "#ss....ss#", ".#ss..ss#.", "..#ssss#..", "...#ss#...",
               "..#ssss#..", ".g#s..s#g.", "gg#....#gg", ".g......g.", ".........."],
    "skull": ["..######..", ".#wwwwww#.", "#wwwwwwww#", "#w##ww##w#", "#w##ww##w#",
              "#wwww#www#", ".#wwwwww#.", "..#w#w#w..", "..#wwwww..", "...#####.."],
    "star":  ["....g.....", "....g.....", "...ggg....", "gggggggggg", ".ggggggg..",
              "..ggggg...", "..gg.gg...", ".gg...gg..", ".g.....g..", ".........."],
    "chicken": ["...rr.....", "..#ww#....", ".#wwww#...", ".#w#ww#g..", "..#wwww#..",
                ".#wwwwww#.", "#wwwwwwww#", ".#wwwwww#.", "..##gg##..", "...g..g..."],
}


def pix(name: str, color: str = "#ffd24a", size: int = 20, cls: str = "px") -> str:
    pal = {"#": "#000", "b": color, "w": "#f4f1e6", "s": "#c3c9d1",
           "g": "#ffd24a", "r": "#c81e1e"}
    rows = ICONS[name]
    rects = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            ch = row[x]
            if ch in pal:
                run = 1
                while x + run < len(row) and row[x + run] == ch:
                    run += 1
                rects.append(f'<rect x="{x}" y="{y}" width="{run}" height="1" fill="{pal[ch]}"/>')
                x += run
            else:
                x += 1
    return (f'<svg class="{cls}" viewBox="0 0 {len(rows[0])} {len(rows)}" width="{size}" '
            f'height="{size}" shape-rendering="crispEdges" aria-hidden="true">{"".join(rects)}</svg>')


def combat(ps: float) -> int:
    return round(3 + (ps or 0) * 123)


def chat_line(line: str) -> str:
    """Public chat is 'Name: msg'. 'From X: msg' is a private message,
    '... wishes to trade with you.' is a trade request, anything else is a
    game message."""
    if line.startswith("From "):
        who, _, msg = line[5:].partition(": ")
        return f'<p class="pm">From {e(who)}: {e(msg)}</p>'
    if line.endswith("wishes to trade with you."):
        return f'<p class="tr">{e(line)}</p>'
    who, sep, msg = line.partition(": ")
    if sep and len(who) < 28:
        return f'<p><b>{e(who)}:</b> <q>{e(msg)}</q></p>'
    return f'<p class="gm">{e(line)}</p>'


def render(data, history, theme, copy, h) -> str:
    asset, POS_COLOR, POS_ORDER = h["asset"], h["POS_COLOR"], h["POS_ORDER"]
    SITE = h["SITE"]
    teams, mus, wk = data["teams"], data["matchups"], data["week"]
    for t in teams:  # week-level numbers; points_for is the season total
        t.setdefault("week_points", t["points_for"])
        t.setdefault("week_proj_diff", t["week_points"] - (t.get("projected_total") or 0))
    n = len(teams)
    SH = h["short_names"](teams)
    by_id = {t["team_id"]: t for t in teams}
    takes = copy.get("takes", {})
    quests = copy.get("quests", {})
    duel_logs = copy.get("duels", {})
    show_move = len(history) > 1

    def av(t):
        return e(asset(t.get("logo_local", ""), t.get("logo", ""), t["owner"]))

    def hs(p):
        return e(asset(p.get("headshot_local", ""), p.get("headshot", ""), p["name"], "hs"))

    best = max((s for t in teams for s in t["starters"]), key=lambda s: s["points"])
    best_team = next(t for t in teams if best in t["starters"])
    best_mu = next(m for m in mus if best_team["team_id"] in (m["home_id"], m["away_id"]))
    foe = by_id[best_mu["away_id"] if best_mu["home_id"] == best_team["team_id"] else best_mu["home_id"]]
    best_skill = SKILL.get(best["position"], "Fantasy")

    # ---------- nav + login screen ----------
    nav = "".join(f'<a href="#{a}">{e(b)}</a>' for a, b in
                  [("scores", "Duel Arena"), ("teams", "Hiscores"),
                   ("positions", "Skills"), ("season", "XP Tracker")])

    login = f'''<header class="login"><div class="login-in">
  <div class="torch l" aria-hidden="true"><i></i></div><div class="torch r" aria-hidden="true"><i></i></div>
  <div class="brand">
    <span class="brand-sm">The Chach Champions League presents</span>
    <span class="brand-lg">ChachScape</span>
    <span class="brand-world">World {wk} &middot; Members &middot; {e(theme)}</span>
  </div>
  <div class="loginbox">
    <p class="lb-k">Welcome to ChachScape</p>
    <h1>{e(copy.get("headline", ""))}</h1>
    <p class="hs">{e(copy.get("standfirst", ""))}</p>
    <div class="lb-btns"><a class="sbtn" href="#scores">Enter the Duel Arena</a><a class="sbtn" href="#teams">View Hiscores</a></div>
  </div>
</div></header>'''

    # ---------- game client hero ----------
    dots = "".join(f'<i style="left:{l}%;top:{t}%"></i>' for l, t in
                   [(30, 28), (62, 22), (70, 48), (24, 60), (45, 72), (58, 64),
                    (38, 40), (75, 30), (20, 42), (66, 78), (50, 30)])
    stats = "".join(
        f'<div class="st">{pix(p, POS_COLOR[p], 18)}<span>{best_team["positional"].get(p, 0):.1f}</span></div>'
        for p in POS_ORDER)
    client = f'''<section class="client-wrap" aria-label="Top performance"><div class="client">
  <div class="vp">
    <div class="mo"><b>Attack</b> <span class="mo-n">{e(foe["name"])}</span> <span class="mo-l">(level-{combat(foe.get("power_score"))})</span> <i>/ 2 more options</i></div>
    <div class="scene" aria-hidden="true"><span class="tree t1"></span><span class="tree t2"></span><span class="tree t3"></span><span class="castle"></span></div>
    <div class="char">
      <div class="overhead">{e(copy.get("overhead", "gg"))}</div>
      <img src="{hs(best)}" alt="{e(best["name"])}">
      <span class="splat big">{best["points"]:.1f}</span>
    </div>
    <div class="vp-name">{e(best["name"])} <span>&middot; {e(best_team["name"])}</span></div>
  </div>
  <aside class="side">
    <div class="mm-wrap"><div class="minimap">{dots}<i class="me"></i></div><span class="compass">N</span></div>
    <div class="tabs"><span>{pix("swords", size=16)}</span><span class="on">{pix("star", size=16)}</span><span>{pix("TE", "#3987e5", 16)}</span><span>{pix("QB", "#9085e9", 16)}</span></div>
    <div class="stats">{stats}<div class="st tot">Total <b>{best_team["week_points"]:.1f}</b></div></div>
    <div class="acct"><b>{e(best_team["name"])}</b><span>Combat {combat(best_team.get("power_score"))}</span></div>
  </aside>
  <div class="lvlup">
    <div class="lv-ic">{pix(best["position"], POS_COLOR.get(best["position"], "#ffd24a"), 34)}</div>
    <div class="lv-tx"><b>Congratulations, you just advanced a {e(best_skill)} level.</b>
      <span>{e(best["name"])} is now level {int(best["points"])}.</span>
      <em>Click here to continue</em></div>
  </div>
</div></section>'''

    # ---------- duel arena ----------
    duels = ""
    for i, m in enumerate(mus, 1):
        hw = m["winner"] == "HOME"
        W = by_id[m["home_id"] if hw else m["away_id"]]
        Lz = by_id[m["away_id"] if hw else m["home_id"]]
        ws = m["home_score"] if hw else m["away_score"]
        ls = m["away_score"] if hw else m["home_score"]
        log = duel_logs.get(str(W["team_id"]), "")

        def fighter(t, sc, cls, tag):
            return (f'<div class="ft {cls}"><div class="ft-av"><img src="{av(t)}" alt="" loading="lazy">'
                    f'<span class="splat">{sc:.1f}</span></div>'
                    f'<b>{e(t["name"])}</b><span class="ft-o">{e(SH[t["team_id"]])} &middot; Combat {combat(t.get("power_score"))}</span>'
                    f'<em>{tag}</em></div>')
        duels += f'''<article class="duel{' tight' if m['margin'] < 10 else ''}">
  <div class="dl-h"><span>Duel {i}</span><span>Won by {m["margin"]:.1f}</span></div>
  <div class="dl-b">{fighter(W, ws, "win", "Victorious!")}<div class="vs">{pix("swords", size=30)}</div>{fighter(Lz, ls, "lose", "Oh dear, you are dead!")}</div>
  {f'<p class="dl-log">{e(log)}</p>' if log else ''}
</article>'''

    events = "".join(f'<li>{pix(ev.get("icon", "star"), size=18)}<span>{e(ev["text"])}</span></li>'
                     for ev in copy.get("random_events", []))
    events_html = (f'<aside class="events"><h3>Random events</h3><ul>{events}</ul></aside>'
                   if events else "")

    # ---------- hiscores table ----------
    rows = ""
    for t in teams:
        mv = ""
        if show_move and t.get("movement"):
            up = t["movement"] > 0
            mv = f'<span class="mv {"up" if up else "dn"}">{"▲" if up else "▼"}{abs(t["movement"])}</span>'
        rows += (f'<tr><td class="r">{t["rank"]}{mv}</td>'
                 f'<td class="nm"><a href="#t{t["team_id"]}"><img src="{av(t)}" alt="" loading="lazy">'
                 f'<span><b>{e(t["name"])}</b><i>{e(t["owner"])}</i></span></a></td>'
                 f'<td class="cb">{combat(t.get("power_score"))}</td>'
                 f'<td class="tl">{t["week_points"]:.1f}</td>'
                 f'<td class="ss">{t["points_for"]:.1f}</td>'
                 f'<td class="rc">{t["wins"]}-{t["losses"]}</td></tr>')
    table = f'''<div class="hstable">
  <div class="hs-top"><span>{pix("star", size=18)} Hiscores</span><em>Overall &middot; Week {wk}</em></div>
  <table><thead><tr><th>Rank</th><th>Account</th><th>Combat</th><th>Week</th><th>Season</th><th>W-L</th></tr></thead>
  <tbody>{rows}</tbody></table>
</div>'''

    # ---------- adventurer's log entries ----------
    logs = ""
    for t in teams:
        top = t["top_scorer"]
        first, last = t["rank"] == 1, t["rank"] == n
        diff = t["week_proj_diff"]
        skills = "".join(
            f'<div class="sk1">{pix(p, POS_COLOR[p], 16)}<span>{SKILL[p]}</span><b>{t["positional"].get(p, 0):.1f}</b></div>'
            for p in POS_ORDER)
        extra = ""
        if first and copy.get("rewards"):
            extra = ('<div class="rewards"><p>You are awarded:</p><ul>' +
                     "".join(f"<li>{e(r)}</li>" for r in copy["rewards"]) + "</ul></div>")
        if last:
            kept = sorted(t["starters"], key=lambda s: -s["points"])[:3]
            extra = ('<div class="kept"><p>Items kept on death</p><div>' +
                     "".join(f'<span><b>{s["points"]:.1f}</b>{e(s["name"])}</span>' for s in kept) +
                     "</div></div>")
        mvj = ""
        if show_move and t.get("movement"):
            up = t["movement"] > 0
            mvj = (f' <span class="mvj {"up" if up else "dn"}">{"▲" if up else "▼"}{abs(t["movement"])}'
                   f'</span>')
        banner = ('<div class="qc">Quest complete!</div>' if first else
                  '<div class="died">Oh dear, you are dead!</div>' if last else "")
        logs += f'''<article class="log{' first' if first else ''}{' last' if last else ''}" id="t{t["team_id"]}">
  <header class="lg-h">
    <span class="lg-r">{t["rank"]}</span>
    <img class="lg-av" src="{av(t)}" alt="" loading="lazy">
    <div class="lg-n"><h3>{e(t["name"])}{mvj}</h3><span>{e(t["owner"])} &middot; Combat <b>{combat(t.get("power_score"))}</b></span></div>
    <div class="lg-p"><b>{t["week_points"]:.1f}</b><span>{t["wins"]}-{t["losses"]} &middot; {"+" if diff >= 0 else ""}{diff:.1f} vs proj &middot; all-play {t.get("all_play", "")} &middot; season {t["points_for"]:.1f}</span></div>
  </header>
  {banner}
  <div class="scroll">
    <p class="qt">{e(quests.get(str(t["team_id"]), "Adventurer's Log"))}</p>
    <div class="sc-b">
      <figure class="port"><img src="{hs(top)}" alt="" loading="lazy"><span class="splat">{top["points"]:.1f}</span><figcaption>{e(top["name"])}</figcaption></figure>
      <p class="take">{e(takes.get(str(t["team_id"]), ""))}</p>
    </div>
    {extra}
  </div>
  <div class="skillrow">{skills}</div>
</article>'''

    # ---------- skills matrix ----------
    colmax = {p: max(t["positional"].get(p, 0) for t in teams) for p in POS_ORDER}
    head = "".join(f'<th>{pix(p, POS_COLOR[p], 18)}<span>{SKILL[p]}</span><i>{p}</i></th>'
                   for p in POS_ORDER)
    mrows = ""
    for t in sorted(teams, key=lambda x: -x["week_points"]):
        cells = ""
        for p in POS_ORDER:
            v = t["positional"].get(p, 0)
            boss = v == colmax[p] and v > 0
            w = max(0.0, v) / colmax[p] * 100 if colmax[p] else 0
            cells += (f'<td class="c{" boss" if boss else ""}{" neg" if v < 0 else ""}">'
                      f'<span class="fill" style="width:{w:.1f}%;background:{POS_COLOR[p]}"></span>'
                      f'<b>{v:.1f}</b></td>')
        mrows += f'<tr><th class="mn">{e(SH[t["team_id"]])}</th>{cells}<td class="mt">{t["week_points"]:.1f}</td></tr>'
    matrix = f'''<div class="mx-wrap"><table class="mx">
  <thead><tr><th class="mn">Account</th>{head}<th class="mt">Total</th></tr></thead>
  <tbody>{mrows}</tbody></table></div>'''

    # ---------- XP tracker ----------
    weeks = [x["week"] for x in history]
    W_, H_, L_, R_, T_, B_ = 760, 320, 30, 110, 18, 24
    span = max(1, (weeks[-1] - weeks[0]) or 1)
    fx = lambda w: L_ + (0 if len(weeks) == 1 else (w - weeks[0]) / span * (W_ - L_ - R_))
    fy = lambda r: T_ + (r - 1) / (n - 1) * (H_ - T_ - B_)
    svg = "".join(f'<line x1="{L_}" y1="{fy(r):.1f}" x2="{W_-R_}" y2="{fy(r):.1f}" stroke="#3d3326"/>'
                  for r in range(1, n + 1))
    for t in teams:
        pts = [(fx(x["week"]), fy(x["ranks"][str(t["team_id"])])) for x in history]
        d = " ".join(f'{"M" if i == 0 else "L"}{a:.1f},{b:.1f}' for i, (a, b) in enumerate(pts))
        col = "#ffff00" if t["rank"] == 1 else "#8a7757"
        svg += (f'<path d="{d}" fill="none" stroke="{col}" stroke-width="3" stroke-linecap="square"/>'
                f'<rect x="{pts[-1][0]-4:.1f}" y="{pts[-1][1]-4:.1f}" width="8" height="8" fill="{col}" stroke="#000"/>'
                f'<text x="{pts[-1][0]+12:.1f}" y="{pts[-1][1]+4:.1f}" class="xt">{e(SH[t["team_id"]])}</text>')
    svg += "".join(f'<text x="{L_-10}" y="{fy(r)+4:.1f}" class="xa" text-anchor="end">{r}</text>'
                   for r in (1, 6, 12) if r <= n)

    # ---------- chatbox ----------
    chat = "".join(chat_line(x) for x in copy.get("chat", []))
    labels = copy.get("labels", {})

    card = h["ROOT"] / "docs" / f"og-week-{wk}.png"
    og_img = copy.get("og_image") or (f"og-week-{wk}.png" if card.exists() else "og-league.png")
    og_title = copy.get("og_title") or f"Week {wk}: {theme}"
    og_desc = copy.get("og_description") or copy.get("standfirst", "")[:200]
    out_name = copy.get("page_name") or f"week-{wk}.html"

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="theme-name" content="{e(theme)}" />
<title>Week {wk}: {e(theme)}</title>
<meta name="description" content="{e(og_desc)}" />
<meta property="og:type" content="article" />
<meta property="og:site_name" content="{e(data['league_name'])}" />
<meta property="og:url" content="{SITE}/weeks/{out_name}" />
<meta property="og:title" content="{e(og_title)}" />
<meta property="og:description" content="{e(og_desc)}" />
<meta property="og:image" content="{SITE}/{og_img}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content="{SITE}/{og_img}" />
<style>{h["load_skin"]("runescape")}</style>
</head>
<body>
<div class="bar"><div class="bar-in"><a class="logo" href="../index.html">ChachScape</a><nav class="bn">{nav}</nav></div></div>
{login}
{client}
<main class="wrap">
  <section id="scores">
    <div class="ttl"><p class="sk">The Duel Arena</p><h2>Week {wk} stakes</h2></div>
    <p class="sl">{e(copy.get("lede_scores", ""))}</p>
    <div class="arena"><div class="duels">{duels}</div>{events_html}</div>
  </section>

  <section id="teams">
    <div class="ttl"><p class="sk">Hiscores</p><h2>Overall rankings</h2></div>
    <p class="sl">{e(copy.get("lede_rankings", ""))}</p>
    {table}
    <div class="ttl sub"><p class="sk">Adventurer's Log</p><h2>Quest journals</h2></div>
    <div class="logs">{logs}</div>
  </section>

  <section id="positions">
    <div class="ttl"><p class="sk">Skills tab</p><h2>Scoring by skill</h2></div>
    <p class="sl">{e(copy.get("lede_positions", ""))}</p>
    {matrix}
  </section>

  <section id="season">
    <div class="ttl"><p class="sk">XP tracker</p><h2>Rank by week</h2></div>
    <p class="sl">{e(labels.get("lede_season", ""))}</p>
    <div class="panel"><svg viewBox="0 0 {W_} {H_}" width="100%" role="img" aria-label="rank by week">{svg}</svg>
      <p class="cnote">{e(labels.get("cnote", ""))}</p></div>
  </section>

  <footer><p>Data pulled from ESPN on Monday night, once the last game is final.
    <a href="../index.html">Back to all weeks</a></p></footer>
</main>

<div class="chat" aria-hidden="true">
  <div class="chat-log"><div class="chat-in">{chat}{chat}</div></div>
  <div class="chat-tabs"><span>All</span><span>Game</span><span class="on">Public</span><span>Private</span><span>Clan</span><span>Trade</span><span class="rep">Report Abuse</span></div>
</div>
</body>
</html>
'''
