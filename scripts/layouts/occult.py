"""Occult ledger layout: the week as a record kept by something else.

Each team gets a generated sigil (deterministic from its name, so the same
team carries the same mark every week), a station in the ring, and a verdict.
Nothing here is a real rite; the symbols are drawn geometry.
"""

from __future__ import annotations

import hashlib
import html
import math

e = html.escape

# unit -> planetary mark
MARK = {"QB": "☿", "RB": "♂", "WR": "♃", "TE": "♄",
        "K": "☾", "D/ST": "☉"}
ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


def _bytes(seed: str) -> list[int]:
    # doubled so a node count of 8 can index past the first digest
    d = hashlib.sha256(seed.encode()).digest()
    return list(d) + list(hashlib.sha256(d).digest())


def sigil(seed: str, size: int = 120, cls: str = "sig") -> str:
    """A drawn sigil: points on a ring joined in a fixed order, with terminals."""
    b = _bytes(seed)
    n = 5 + b[0] % 4                      # 5 to 8 nodes
    ring = 34
    pts = []
    for i in range(n):
        ang = (b[1 + i] / 255) * math.tau
        r = ring - (b[9 + i] % 9)
        pts.append((50 + r * math.cos(ang), 50 + r * math.sin(ang)))
    order = sorted(range(n), key=lambda i: b[17 + i])
    path = " ".join(f'{"M" if k == 0 else "L"}{pts[i][0]:.1f},{pts[i][1]:.1f}'
                    for k, i in enumerate(order))
    terms = ""
    for k, i in enumerate(order):
        x, y = pts[i]
        style = b[25 + k] % 4
        if style == 0:
            terms += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2"/>'
        elif style == 1:
            terms += (f'<line x1="{x-4:.1f}" y1="{y-4:.1f}" x2="{x+4:.1f}" y2="{y+4:.1f}"/>'
                      f'<line x1="{x-4:.1f}" y1="{y+4:.1f}" x2="{x+4:.1f}" y2="{y-4:.1f}"/>')
        elif style == 2:
            terms += f'<path d="M{x-5:.1f},{y+3:.1f} L{x:.1f},{y-5:.1f} L{x+5:.1f},{y+3:.1f} Z"/>'
        else:
            terms += (f'<path d="M{x:.1f},{y-5:.1f} A5,5 0 1,0 {x+0.1:.1f},{y-5:.1f}" '
                      f'transform="rotate({b[33+k] % 360},{x:.1f},{y:.1f})"/>')
    ticks = ""
    for i in range(24):
        a = i * math.tau / 24
        r1, r2 = 44, 47 if i % 2 == 0 else 45.5
        ticks += (f'<line x1="{50+r1*math.cos(a):.1f}" y1="{50+r1*math.sin(a):.1f}" '
                  f'x2="{50+r2*math.cos(a):.1f}" y2="{50+r2*math.sin(a):.1f}"/>')
    return (f'<svg class="{cls}" viewBox="0 0 100 100" width="{size}" height="{size}" '
            f'aria-hidden="true"><g class="ink">'
            f'<circle cx="50" cy="50" r="47.5" class="ring"/>'
            f'<circle cx="50" cy="50" r="41" class="ring2"/>'
            f'<g class="tick">{ticks}</g>'
            f'<path class="line" d="{path} Z"/>{terms}'
            f'<circle cx="50" cy="50" r="1.6" class="core"/></g></svg>')


def seal(teams, size: int = 340) -> str:
    """Twelve marks set around one ring, in rank order, first at the top."""
    n = len(teams)
    marks = ""
    for i, t in enumerate(teams):
        a = -math.tau / 4 + i * math.tau / n
        x, y = 50 + 37 * math.cos(a), 50 + 37 * math.sin(a)
        marks += (f'<g transform="translate({x:.1f},{y:.1f}) scale(0.115) translate(-50,-50)">'
                  f'{sigil(t["name"], 100, "inner")}</g>')
    rays = "".join(
        f'<line x1="50" y1="50" x2="{50+37*math.cos(-math.tau/4+i*math.tau/n):.1f}" '
        f'y2="{50+37*math.sin(-math.tau/4+i*math.tau/n):.1f}"/>' for i in range(n))
    return (f'<svg class="seal" viewBox="0 0 100 100" width="{size}" height="{size}" '
            f'aria-hidden="true"><g class="ink">'
            f'<circle cx="50" cy="50" r="48" class="ring"/><circle cx="50" cy="50" r="44" class="ring2"/>'
            f'<circle cx="50" cy="50" r="12" class="ring2"/>'
            f'<g class="rays">{rays}</g>{marks}'
            f'<circle cx="50" cy="50" r="2" class="core"/></g></svg>')


def render(data, history, theme, copy, h) -> str:
    asset, POS_COLOR, POS_ORDER = h["asset"], h["POS_COLOR"], h["POS_ORDER"]
    SITE, ROOT = h["SITE"], h["ROOT"]
    teams, mus, wk = data["teams"], data["matchups"], data["week"]
    n = len(teams)
    SH = h["short_names"](teams)
    by_id = {t["team_id"]: t for t in teams}
    takes, verdicts = copy.get("takes", {}), copy.get("verdicts", {})
    epithets = copy.get("epithets", {})
    labels = copy.get("labels", {})
    stamps = copy.get("stamps", {})
    show_move = len(history) > 1
    for t in teams:
        t.setdefault("week_points", t["points_for"])
        t.setdefault("week_proj_diff", t["week_points"] - (t.get("projected_total") or 0))

    def av(t):
        return e(asset(t.get("logo_local", ""), t.get("logo", ""), t["owner"]))

    def hs(p):
        return e(asset(p.get("headshot_local", ""), p.get("headshot", ""), p["name"], "hs"))

    # ---------- judgments ----------
    judg = ""
    for i, m in enumerate(mus, 1):
        hw = m["winner"] == "HOME"
        W = by_id[m["home_id"] if hw else m["away_id"]]
        L = by_id[m["away_id"] if hw else m["home_id"]]
        ws = m["home_score"] if hw else m["away_score"]
        ls = m["away_score"] if hw else m["home_score"]
        judg += f'''<div class="jd{' near' if m["margin"] < 10 else ''}">
  <div class="jn">{ROMAN[i]}</div>
  <div class="side keep">{sigil(W["name"], 74)}<b>{e(W["name"])}</b><span>{ws:.2f}</span><em>stands</em></div>
  <div class="cleave" aria-hidden="true">&#10013;</div>
  <div class="side lost">{sigil(L["name"], 74)}<b>{e(L["name"])}</b><span>{ls:.2f}</span><em>falls</em></div>
  <div class="jm">taken by {m["margin"]:.2f}</div>
</div>'''

    # ---------- the twelve ----------
    entries = ""
    for t in teams:
        tid = t["team_id"]
        diff = t["week_proj_diff"]
        top = t["top_scorer"]
        mv = ""
        if show_move and t.get("movement"):
            up = t["movement"] > 0
            mv = (f'<span class="mv {"up" if up else "dn"}">'
                  f'{"&#9650;" if up else "&#9660;"}{abs(t["movement"])}</span>')
        bar = "".join(
            f'<span style="width:{max(0.0, t["positional"].get(p, 0)) / max(1.0, t["week_points"]) * 100:.2f}%;'
            f'background:{POS_COLOR[p]}" title="{p}"></span>'
            for p in POS_ORDER if t["positional"].get(p, 0) > 0)
        stamp = stamps.get(str(tid), "")
        vlines = "".join(f'<li>{e(x)}</li>' for x in verdicts.get(str(tid), []))
        entries += f'''<article class="ent{' marked' if stamp else ''}{' first' if t["rank"] == 1 else ''}" id="t{tid}">
  <div class="mark">{sigil(t["name"], 132)}<span class="stn">station {ROMAN[t["rank"]]}</span></div>
  <div class="body">
    <header>
      <img class="face" src="{av(t)}" alt="" loading="lazy">
      <div class="names"><h3>{e(t["name"])}</h3>
        <p class="ep">{e(epithets.get(str(tid), ""))}</p>
        <p class="own">{e(t["owner"])}</p></div>
      <div class="off"><b>{t["week_points"]:.2f}</b>{mv}
        <span>{t["wins"]}-{t["losses"]} &middot; witnessed {t.get("all_play", "")} &middot; {"+" if diff >= 0 else ""}{diff:.1f} against the reckoning</span></div>
    </header>
    <div class="spec">{bar}</div>
    <ul class="verd">{vlines}</ul>
    <p class="take">{e(takes.get(str(tid), ""))}</p>
    <p class="giv"><img src="{hs(top)}" alt="" loading="lazy">
      <span>given by <b>{e(top["name"])}</b>, {top["points"]:.2f}</span></p>
    {f'<p class="stamp">{e(stamp)}</p>' if stamp else ''}
  </div>
</article>'''

    # ---------- division of offerings ----------
    colmax = {p: max(t["positional"].get(p, 0) for t in teams) for p in POS_ORDER}
    hdr = "".join(f'<th><i style="background:{POS_COLOR[p]}"></i><u>{MARK[p]}</u>{p}</th>'
                  for p in POS_ORDER)
    prow = ""
    for t in sorted(teams, key=lambda x: -x["week_points"]):
        cells = ""
        for p in POS_ORDER:
            v = t["positional"].get(p, 0)
            best = v == colmax[p] and v > 0
            w = max(0.0, v) / colmax[p] * 100 if colmax[p] else 0
            cells += (f'<td class="c{" hi" if best else ""}{" neg" if v < 0 else ""}">'
                      f'<span class="fill" style="width:{w:.1f}%;background:{POS_COLOR[p]}"></span>'
                      f'<b>{v:.1f}</b></td>')
        prow += f'<tr><th class="tn">{e(SH[t["team_id"]])}</th>{cells}<td class="tt">{t["week_points"]:.1f}</td></tr>'
    table = f'''<div class="tw"><table class="mx">
  <thead><tr><th class="tn">name</th>{hdr}<th class="tt">sum</th></tr></thead>
  <tbody>{prow}</tbody></table></div>'''

    # ---------- the wheel ----------
    weeks = [x["week"] for x in history]
    W_, H_, L_, R_, T_, B_ = 760, 330, 42, 120, 22, 26
    span = max(1, (weeks[-1] - weeks[0]) or 1)
    fx = lambda w: L_ + (0 if len(weeks) == 1 else (w - weeks[0]) / span * (W_ - L_ - R_))
    fy = lambda r: T_ + (r - 1) / (n - 1) * (H_ - T_ - B_)
    svg = "".join(f'<line x1="{L_}" y1="{fy(r):.1f}" x2="{W_-R_}" y2="{fy(r):.1f}" stroke="#241d14"/>'
                  for r in range(1, n + 1))
    svg += "".join(f'<text x="{fx(w):.0f}" y="13" class="wl" text-anchor="middle">{ROMAN[w]}</text>'
                   for w in weeks)
    for t in teams:
        pts = [(fx(x["week"]), fy(x["ranks"][str(t["team_id"])])) for x in history]
        d = " ".join(f'{"M" if i == 0 else "L"}{a:.1f},{b:.1f}' for i, (a, b) in enumerate(pts))
        lead = t["rank"] == 1
        col = "#c8a24a" if lead else "#4a4034"
        svg += (f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{2.4 if lead else 1.4}"/>'
                f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="3.4" fill="{col}"/>'
                f'<text x="{pts[-1][0]+11:.1f}" y="{pts[-1][1]+4:.1f}" class="nm">{e(SH[t["team_id"]])}</text>')
    svg += "".join(f'<text x="{L_-12}" y="{fy(r)+4:.1f}" class="ax" text-anchor="end">{ROMAN[r]}</text>'
                   for r in (1, 6, 12) if r <= n)

    card = ROOT / "docs" / f"og-week-{wk}.png"
    og_img = copy.get("og_image") or (f"og-week-{wk}.png" if card.exists() else "og-league.png")
    og_title = copy.get("og_title") or f"Week {wk}: {theme}"
    og_desc = copy.get("og_description") or copy.get("standfirst", "")[:200]
    glyphs = copy.get("glyph_rule", "✠ ✡ ⚸ ☦ ᚱ ✠")

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
<style>{h["load_skin"]("occult")}</style>
</head>
<body>
<div class="grain" aria-hidden="true"></div>

<header class="rite">
  <p class="over">{e(copy.get("overline", ""))}</p>
  <h1>{e(copy.get("board_name", ""))}</h1>
  <p class="wkline">{e(copy.get("thread_title", ""))}</p>
  <div class="sealwrap">{seal(teams)}</div>
  <p class="rule" aria-hidden="true">{glyphs}</p>
  <p class="lead">{e(copy.get("standfirst", ""))}</p>
  <nav class="jump"><a href="#judgments">the judgments</a><a href="#twelve">the twelve</a>
    <a href="#offerings">the division</a><a href="#wheel">the wheel</a>
    <a href="../index.html">the archive</a></nav>
</header>

<main class="wrap">
  <section id="judgments">
    <h2>{e(labels.get("h_judgments", "The Six Judgments"))}</h2>
    <p class="sl">{e(copy.get("lede_scores", ""))}</p>
    <div class="judg">{judg}</div>
  </section>

  <section id="twelve">
    <h2>{e(labels.get("h_twelve", "The Twelve, In Order"))}</h2>
    <p class="sl">{e(copy.get("lede_rankings", ""))}</p>
    <div class="ents">{entries}</div>
  </section>

  <section id="offerings">
    <h2>{e(labels.get("h_offerings", "The Division of the Offering"))}</h2>
    <p class="sl">{e(copy.get("lede_positions", ""))}</p>
    {table}
  </section>

  <section id="wheel">
    <h2>{e(labels.get("h_wheel", "The Wheel"))}</h2>
    <p class="sl">{e(labels.get("lede_season", ""))}</p>
    <div class="panel"><svg viewBox="0 0 {W_} {H_}" width="100%" role="img" aria-label="station by week">{svg}</svg>
      <p class="note">{e(labels.get("cnote", ""))}</p></div>
  </section>

  <footer>
    <p class="rule" aria-hidden="true">{glyphs}</p>
    <p>{e(copy.get("closing", ""))}</p>
    <p class="small">Figures drawn from ESPN on Monday night, once the last game is final.
      <a href="../index.html">the archive</a></p>
  </footer>
</main>
</body>
</html>
'''
