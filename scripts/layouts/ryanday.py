"""Ryan Day homage layout: an unsolicited fan shrine.

Photos come from data/photo-credits.json (fetched from Wikimedia Commons by
scripts/fetch_photos.py). Every photo prints its credit, because the Commons
licences require attribution. Without the manifest the page still builds, just
without pictures.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

e = html.escape

UNIT = {"QB": "Quarterbacks", "RB": "Running backs", "WR": "Receivers",
        "TE": "Tight ends", "K": "Special teams", "D/ST": "Defense"}


def load_photos(root: Path) -> list[dict]:
    path = root / "data" / "photo-credits.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return []


class Pool:
    """Hands out photos in order and keeps cycling when they run out."""

    def __init__(self, photos: list[dict]):
        self.photos = photos
        self.i = 0

    def next(self) -> dict | None:
        if not self.photos:
            return None
        p = self.photos[self.i % len(self.photos)]
        self.i += 1
        return p


def frame(p: dict | None, cls: str = "", cap: str = "") -> str:
    if not p:
        return ""
    caption = cap or p.get("title", "")
    return (f'<figure class="pic {cls}"><img src="../{e(p["file"])}" alt="{e(caption)}" loading="lazy">'
            f'<figcaption>{e(caption)}</figcaption></figure>')


def render(data, history, theme, copy, h) -> str:
    asset, POS_COLOR, POS_ORDER = h["asset"], h["POS_COLOR"], h["POS_ORDER"]
    SITE, ROOT = h["SITE"], h["ROOT"]
    teams, mus, wk = data["teams"], data["matchups"], data["week"]
    n = len(teams)
    SH = h["short_names"](teams)
    by_id = {t["team_id"]: t for t in teams}
    takes = copy.get("takes", {})
    notes = copy.get("scout", {})
    labels = copy.get("labels", {})
    show_move = len(history) > 1
    for t in teams:
        t.setdefault("week_points", t["points_for"])
        t.setdefault("week_proj_diff", t["week_points"] - (t.get("projected_total") or 0))

    photos = load_photos(ROOT)
    day = [p for p in photos if "ryan day" in p.get("term", "").lower()] or photos
    pool = Pool(day)
    hero_pic = pool.next()

    def av(t):
        return e(asset(t.get("logo_local", ""), t.get("logo", ""), t["owner"]))

    def hs(p):
        return e(asset(p.get("headshot_local", ""), p.get("headshot", ""), p["name"], "hs"))

    tabs = [("scores", "Scoreboard"), ("teams", "Power Rankings"),
            ("positions", "Report Card"), ("season", "Week by Week")]
    if photos:
        tabs.append(("gallery", "Photographs"))
    if copy.get("guestbook"):
        tabs.append(("guestbook", "Guestbook"))
    nav = "".join(f'<a href="#{a}">{e(b)}</a>' for a, b in tabs)

    # ---------- shrine facts ----------
    fact_pics = Pool([p for p in photos if p not in day] or photos)
    facts = ""
    for f in copy.get("facts", []):
        facts += (f'<div class="fact">{frame(fact_pics.next(), "sm")}'
                  f'<h3>{e(f["title"])}</h3><p>{e(f["text"])}</p></div>')

    brief = "".join(f'<div class="bi"><dt>{e(b["k"])}</dt><dd>{e(b["v"])}</dd></div>'
                    for b in copy.get("brief", []))
    line = ""
    for item in copy.get("timeline", []):
        line += (f'<li><span class="yr">{e(item["year"])}</span>'
                 f'<div class="ev">{e(item["text"])}</div></li>')
    tl_pics = "".join(frame(fact_pics.next(), "sm") for _ in range(min(3, len(photos))))

    # ---------- scoreboard ----------
    board = ""
    for m in mus:
        hw = m["winner"] == "HOME"
        W = by_id[m["home_id"] if hw else m["away_id"]]
        L = by_id[m["away_id"] if hw else m["home_id"]]
        ws = m["home_score"] if hw else m["away_score"]
        ls = m["away_score"] if hw else m["home_score"]
        board += f'''<div class="game{' close' if m['margin'] < 10 else ''}">
  <div class="row win"><img src="{av(W)}" alt="" loading="lazy"><span>{e(W["name"])}</span><b>{ws:.1f}</b></div>
  <div class="row"><img src="{av(L)}" alt="" loading="lazy"><span>{e(L["name"])}</span><b>{ls:.1f}</b></div>
  <div class="final">FINAL &middot; margin {m["margin"]:.1f}</div>
</div>'''

    # ---------- rankings ----------
    cards = ""
    for t in teams:
        top = t["top_scorer"]
        stickers = "".join('<i class="leaf" aria-hidden="true"></i>' for _ in range(t["wins"]))
        mv = ""
        if show_move and t.get("movement"):
            up = t["movement"] > 0
            mv = f'<span class="mv {"up" if up else "dn"}">{"&#9650;" if up else "&#9660;"}{abs(t["movement"])}</span>'
        bar = "".join(
            f'<span style="width:{max(0.0, t["positional"].get(p, 0)) / max(1.0, t["week_points"]) * 100:.2f}%;'
            f'background:{POS_COLOR[p]}" title="{p}"></span>'
            for p in POS_ORDER if t["positional"].get(p, 0) > 0)
        diff = t["week_proj_diff"]
        cards += f'''<article class="rk{' one' if t["rank"] == 1 else ''}" id="t{t["team_id"]}">
  <div class="rk-h">
    <span class="num">{t["rank"]}{mv}</span>
    <img class="hel" src="{av(t)}" alt="" loading="lazy">
    <div class="who"><h3>{e(t["name"])}</h3><span>{e(t["owner"])}</span>
      <div class="stick">{stickers}<em>{t["wins"]}-{t["losses"]}</em></div></div>
    <div class="pts"><b>{t["week_points"]:.1f}</b><span>{"+" if diff >= 0 else ""}{diff:.1f} vs proj &middot; all-play {t.get("all_play", "")}</span></div>
  </div>
  <div class="unitbar">{bar}</div>
  <div class="rk-b">
    {frame(pool.next(), "mug")}
    <div class="say">
      <p class="note"><b>{e(labels.get("scout_label", "Note"))}:</b> {e(notes.get(str(t["team_id"]), ""))}</p>
      <p>{e(takes.get(str(t["team_id"]), ""))}</p>
      <p class="star"><img src="{hs(top)}" alt="" loading="lazy"><span>Player of the game: <b>{e(top["name"])}</b>, {top["points"]:.1f}</span></p>
    </div>
  </div>
</article>'''

    # ---------- report card ----------
    colmax = {p: max(t["positional"].get(p, 0) for t in teams) for p in POS_ORDER}
    head = "".join(f'<th><span style="background:{POS_COLOR[p]}"></span>{e(UNIT[p])}<i>{p}</i></th>'
                   for p in POS_ORDER)
    rows = ""
    for t in sorted(teams, key=lambda x: -x["week_points"]):
        cells = ""
        for p in POS_ORDER:
            v = t["positional"].get(p, 0)
            best_in = v == colmax[p] and v > 0
            w = max(0.0, v) / colmax[p] * 100 if colmax[p] else 0
            cells += (f'<td class="c{" top" if best_in else ""}{" neg" if v < 0 else ""}">'
                      f'<span class="fill" style="width:{w:.1f}%;background:{POS_COLOR[p]}"></span>'
                      f'<b>{v:.1f}</b></td>')
        rows += f'<tr><th class="tm">{e(SH[t["team_id"]])}</th>{cells}<td class="tot">{t["week_points"]:.1f}</td></tr>'
    grid = f'''<div class="grid-wrap"><table class="grid">
  <thead><tr><th class="tm">Team</th>{head}<th class="tot">Total</th></tr></thead>
  <tbody>{rows}</tbody></table></div>'''

    # ---------- week by week ----------
    weeks = [x["week"] for x in history]
    W_, H_, L_, R_, T_, B_ = 760, 320, 34, 116, 18, 24
    span = max(1, (weeks[-1] - weeks[0]) or 1)
    fx = lambda w: L_ + (0 if len(weeks) == 1 else (w - weeks[0]) / span * (W_ - L_ - R_))
    fy = lambda r: T_ + (r - 1) / (n - 1) * (H_ - T_ - B_)
    svg = "".join(f'<line x1="{L_}" y1="{fy(r):.1f}" x2="{W_-R_}" y2="{fy(r):.1f}" stroke="#d8d2c8"/>'
                  for r in range(1, n + 1))
    svg += "".join(f'<text x="{fx(w):.0f}" y="12" class="wl" text-anchor="middle">WK {w}</text>'
                   for w in weeks)
    for t in teams:
        pts = [(fx(x["week"]), fy(x["ranks"][str(t["team_id"])])) for x in history]
        d = " ".join(f'{"M" if i == 0 else "L"}{a:.1f},{b:.1f}' for i, (a, b) in enumerate(pts))
        lead = t["rank"] == 1
        col = "#bb0000" if lead else "#8d8779"
        svg += (f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{3.5 if lead else 2}"/>'
                f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="4.5" fill="{col}"/>'
                f'<text x="{pts[-1][0]+11:.1f}" y="{pts[-1][1]+4:.1f}" class="nm">{e(SH[t["team_id"]])}</text>')
    svg += "".join(f'<text x="{L_-10}" y="{fy(r)+4:.1f}" class="ax" text-anchor="end">{r}</text>'
                   for r in (1, 6, 12) if r <= n)

    gallery = "".join(
        f'<figure class="gp"><img src="../{e(p["file"])}" alt="{e(p["title"])}" loading="lazy">'
        f'<figcaption>{e(p["title"])}<span>{e(p["author"])[:60]} &middot; {e(p["license"])}</span></figcaption></figure>'
        for p in photos)
    credits = "".join(
        f'<li><a href="{e(p["source"])}">{e(p["title"])}</a> by {e(p["author"])[:70]}, {e(p["license"])}</li>'
        for p in photos)
    guest = "".join(
        f'<li><b>{e(g.get("who", ""))}</b> <i>{e(g.get("when", ""))}</i><p>{e(g.get("text", ""))}</p></li>'
        for g in copy.get("guestbook", []))

    card = ROOT / "docs" / f"og-week-{wk}.png"
    og_img = copy.get("og_image") or (f"og-week-{wk}.png" if card.exists() else "og-league.png")
    og_title = copy.get("og_title") or f"Week {wk}: {theme}"
    og_desc = copy.get("og_description") or copy.get("standfirst", "")[:200]
    counter = f'{200000 + wk * 1111 + int(sum(t["week_points"] for t in teams))}'
    gb_block = (f'<section id="guestbook"><h2 class="banner">'
                f'{e(copy.get("guestbook_title", "Guestbook"))}</h2>'
                f'<ul class="gb">{guest}</ul></section>') if guest else ""
    cred_block = ('<details class="cred"><summary>Photo credits and licences</summary><ul>'
                  + credits + '</ul><p>' + e(copy.get("credits_note", "")) + '</p></details>') if photos else ""

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
<meta property="og:url" content="{SITE}/weeks/week-{wk}.html" />
<meta property="og:title" content="{e(og_title)}" />
<meta property="og:description" content="{e(og_desc)}" />
<meta property="og:image" content="{SITE}/{og_img}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content="{SITE}/{og_img}" />
<style>{h["load_skin"]("ryanday")}</style>
</head>
<body>
<div class="ticker"><div class="ticker-in">{e(copy.get("marquee", ""))} &nbsp; &#9733; &nbsp; {e(copy.get("marquee", ""))}</div></div>

<div class="bar"><div class="bar-in">
  <a class="site" href="../index.html">TheRyanDayPage<span>.geocities.com</span></a>
  <nav>{nav}</nav>
</div></div>

<header class="hero"><div class="hero-in{'' if hero_pic else ' solo'}">
  <div class="hero-tx">
    <p class="kick">Week {wk} Power Rankings &middot; Chach Champions League</p>
    <h1>{e(copy.get("headline", ""))}</h1>
    <p class="sub">{e(copy.get("standfirst", ""))}</p>
    <p class="hits">You are visitor number <b>{counter}</b> &middot; {e(copy.get("hits_note", "best viewed at 1024x768"))}</p>
  </div>
  {frame(hero_pic, "big", copy.get("hero_caption", ""))}
</div></header>

<div class="shrine"><div class="shrine-in">
  <h2 class="banner">{e(copy.get("shrine_title", "The life and career of Ryan Day"))}</h2>
  <p class="shrine-sub">{e(copy.get("shrine_sub", ""))}</p>
  <dl class="brief">{brief}</dl>
  <div class="tlwrap">
    <ol class="tl">{line}</ol>
    <div class="tlpics">{tl_pics}</div>
  </div>
  {f'<div class="facts">{facts}</div>' if facts else ''}
</div></div>

<main class="wrap">
  <section id="scores">
    <h2 class="banner">{e(labels.get("h_scores", "Saturday Scoreboard"))}</h2>
    <p class="lede">{e(copy.get("lede_scores", ""))}</p>
    <div class="board">{board}</div>
  </section>

  <section id="teams">
    <h2 class="banner">{e(labels.get("h_teams", "Coach Day's Power Rankings"))}</h2>
    <p class="lede">{e(copy.get("lede_rankings", ""))}</p>
    <div class="ranks">{cards}</div>
  </section>

  <section id="positions">
    <h2 class="banner">{e(labels.get("h_positions", "Position Group Report Card"))}</h2>
    <p class="lede">{e(copy.get("lede_positions", ""))}</p>
    {grid}
  </section>

  <section id="season">
    <h2 class="banner">{e(labels.get("h_season", "Week by Week"))}</h2>
    <p class="lede">{e(labels.get("lede_season", ""))}</p>
    <div class="panel"><svg viewBox="0 0 {W_} {H_}" width="100%" role="img" aria-label="rank by week">{svg}</svg>
      <p class="cnote">{e(labels.get("cnote", ""))}</p></div>
  </section>

  {f"""<section id="gallery">
    <h2 class="banner">{e(labels.get("h_gallery", "Photographs"))}</h2>
    <p class="lede">{e(copy.get("gallery_note", ""))}</p>
    <div class="gal">{gallery}</div>
  </section>""" if photos else ""}

  {gb_block}

  <footer>
    <p>Data pulled from ESPN on Monday night, once the last game is final.
      <a href="../index.html">Back to all weeks</a></p>
    {cred_block}
    <p class="disc">{e(copy.get("disclaimer", "An unofficial tribute page. Not affiliated with Ryan Day or Ohio State University."))}</p>
  </footer>
</main>
</body>
</html>
'''
