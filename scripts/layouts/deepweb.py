"""Deep-web board layout: the week as an archived thread.

Every section is a post in one thread. Teams get their own replies, with
attached "files" (the manager avatars and player headshots the pipeline
already caches), greentext, post numbers and cross-links between the two
sides of a matchup.
"""

from __future__ import annotations

import hashlib
import html

e = html.escape

OP = 8231  # first post number in the thread; replies count up from here


def trip(seed: str) -> str:
    """A stable fake tripcode per manager, so the same name recurs weekly."""
    h = hashlib.sha256(seed.encode()).digest()
    alpha = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz0123456789./"
    return "!!" + "".join(alpha[b % len(alpha)] for b in h[:10])


def fsize(seed: str, lo: int = 18, hi: int = 340) -> str:
    n = int(hashlib.md5(seed.encode()).hexdigest()[:6], 16) % (hi - lo) + lo
    return f"{n} KB"


def render(data, history, theme, copy, h) -> str:
    asset, POS_COLOR, POS_ORDER = h["asset"], h["POS_COLOR"], h["POS_ORDER"]
    SITE, ROOT = h["SITE"], h["ROOT"]
    teams, mus, wk = data["teams"], data["matchups"], data["week"]
    n = len(teams)
    SH = h["short_names"](teams)
    by_id = {t["team_id"]: t for t in teams}
    takes = copy.get("takes", {})
    green = copy.get("green", {})
    labels = copy.get("labels", {})
    stamps = copy.get("stamps", {})
    times = copy.get("times", {})
    show_move = len(history) > 1
    for t in teams:
        t.setdefault("week_points", t["points_for"])
        t.setdefault("week_proj_diff", t["week_points"] - (t.get("projected_total") or 0))

    post_no = {t["team_id"]: OP + 6 + i for i, t in enumerate(teams)}
    opp = {}
    for m in mus:
        opp[m["home_id"]], opp[m["away_id"]] = m["away_id"], m["home_id"]

    def av(t):
        return e(asset(t.get("logo_local", ""), t.get("logo", ""), t["owner"]))

    def hs(p):
        return e(asset(p.get("headshot_local", ""), p.get("headshot", ""), p["name"], "hs"))

    def slug(v):
        return "".join(c.lower() if c.isalnum() else "_" for c in v).strip("_")[:28]

    def head(no, name, tripcode, when, subject="", extra=""):
        sub = f'<span class="subj">{e(subject)}</span> ' if subject else ""
        return (f'<div class="ph">{sub}<span class="nm">{e(name)}</span>'
                f'<span class="tc">{e(tripcode)}</span>'
                f'<span class="tm">{e(when)}</span>'
                f'<a class="no" href="#p{no}">No.{no}</a>{extra}</div>')

    def attach(src, fname, dims, seed):
        return (f'<div class="file"><span class="meta">File: <a href="{src}">{e(fname)}</a> '
                f'({fsize(seed)}, {dims})</span>'
                f'<img src="{src}" alt="" loading="lazy"></div>')

    # ---------- opening post ----------
    op_extra = ' <span class="sticky">[Sticky]</span> <span class="locked">[Archived]</span>'
    op = f'''<article class="post op" id="p{OP}">
  {head(OP, copy.get("op_name", "Anonymous"), trip("op-" + str(wk)), times.get("op", ""), copy.get("op_subject", ""), op_extra)}
  <div class="pb">
    <p class="lead">{e(copy.get("standfirst", ""))}</p>
    {"".join(f'<p class="gt">&gt;{e(x)}</p>' for x in copy.get("op_green", []))}
    <p class="sig">{e(copy.get("op_sign", ""))}</p>
  </div>
</article>'''

    # ---------- results post ----------
    rows = ""
    for m in mus:
        hw = m["winner"] == "HOME"
        W = by_id[m["home_id"] if hw else m["away_id"]]
        L = by_id[m["away_id"] if hw else m["home_id"]]
        ws = m["home_score"] if hw else m["away_score"]
        ls = m["away_score"] if hw else m["home_score"]
        rows += (f'<tr class="{"close" if m["margin"] < 10 else ""}">'
                 f'<td class="w"><a href="#p{post_no[W["team_id"]]}">{e(W["name"])}</a></td>'
                 f'<td class="sw">{ws:.2f}</td>'
                 f'<td class="vs">::</td>'
                 f'<td class="sl">{ls:.2f}</td>'
                 f'<td class="l"><a href="#p{post_no[L["team_id"]]}">{e(L["name"])}</a></td>'
                 f'<td class="d">&Delta;{m["margin"]:.2f}</td></tr>')
    results = f'''<article class="post" id="scores">
  {head(OP + 1, "Anonymous", trip("results"), times.get("results", ""), copy.get("subj_scores", "log"))}
  <div class="pb">
    <p>{e(copy.get("lede_scores", ""))}</p>
    <table class="log"><tbody>{rows}</tbody></table>
  </div>
</article>'''

    # ---------- one reply per team ----------
    replies = ""
    for t in teams:
        tid = t["team_id"]
        no = post_no[tid]
        diff = t["week_proj_diff"]
        top = t["top_scorer"]
        mv = ""
        if show_move and t.get("movement"):
            up = t["movement"] > 0
            mv = f'<span class="mv {"up" if up else "dn"}">{"+" if up else "-"}{abs(t["movement"])}</span>'
        bar = "".join(
            f'<span style="width:{max(0.0, t["positional"].get(p, 0)) / max(1.0, t["week_points"]) * 100:.2f}%;'
            f'background:{POS_COLOR[p]}" title="{p}"></span>'
            for p in POS_ORDER if t["positional"].get(p, 0) > 0)
        gl = "".join(f'<p class="gt">&gt;{e(x)}</p>' for x in green.get(str(tid), []))
        stamp = stamps.get(str(tid), "")
        o = opp.get(tid)
        xref = (f'<a class="ref" href="#p{post_no[o]}">&gt;&gt;{post_no[o]}</a>' if o in post_no else "")
        replies += f'''<article class="post rep{' marked' if stamp else ''}" id="p{no}">
  {head(no, "Anonymous", trip(t["owner"]), times.get(str(tid), ""), f'#{t["rank"]} {t["name"]}')}
  <div class="pb">
    {attach(av(t), f'{slug(t["name"])}_sigil.png', "192x192", t["name"])}
    <div class="tx">
      <p class="rp">{xref} {e(t["owner"])} &middot; <b>{t["week_points"]:.2f}</b> {mv}
        <span class="mt">rec {t["wins"]}-{t["losses"]} &middot; all-play {t.get("all_play", "")} &middot; {"+" if diff >= 0 else ""}{diff:.1f} vs proj</span></p>
      <div class="spec">{bar}</div>
      {gl}
      <p>{e(takes.get(str(tid), ""))}</p>
      <p class="pog"><img src="{hs(top)}" alt="" loading="lazy">
        <span>attachment: <b>{e(top["name"])}</b> &mdash; {top["points"]:.2f}</span></p>
      {f'<p class="stamp">{e(stamp)}</p>' if stamp else ''}
    </div>
  </div>
</article>'''

    # ---------- distribution ----------
    colmax = {p: max(t["positional"].get(p, 0) for t in teams) for p in POS_ORDER}
    hdr = "".join(f'<th><i style="background:{POS_COLOR[p]}"></i>{p}</th>' for p in POS_ORDER)
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
    positions = f'''<article class="post" id="positions">
  {head(OP + 2, "Anonymous", trip("positions"), times.get("positions", ""), copy.get("subj_positions", "distribution"))}
  <div class="pb">
    <p>{e(copy.get("lede_positions", ""))}</p>
    <div class="tw"><table class="mx"><thead><tr><th class="tn">unit</th>{hdr}<th class="tt">sum</th></tr></thead>
      <tbody>{prow}</tbody></table></div>
  </div>
</article>'''

    # ---------- tracking ----------
    weeks = [x["week"] for x in history]
    W_, H_, L_, R_, T_, B_ = 760, 320, 34, 116, 20, 24
    span = max(1, (weeks[-1] - weeks[0]) or 1)
    fx = lambda w: L_ + (0 if len(weeks) == 1 else (w - weeks[0]) / span * (W_ - L_ - R_))
    fy = lambda r: T_ + (r - 1) / (n - 1) * (H_ - T_ - B_)
    svg = "".join(f'<line x1="{L_}" y1="{fy(r):.1f}" x2="{W_-R_}" y2="{fy(r):.1f}" stroke="#1d2426"/>'
                  for r in range(1, n + 1))
    svg += "".join(f'<text x="{fx(w):.0f}" y="12" class="wl" text-anchor="middle">w{w}</text>' for w in weeks)
    for t in teams:
        pts = [(fx(x["week"]), fy(x["ranks"][str(t["team_id"])])) for x in history]
        d = " ".join(f'{"M" if i == 0 else "L"}{a:.1f},{b:.1f}' for i, (a, b) in enumerate(pts))
        lead = t["rank"] == 1
        col = "#7fdba0" if lead else "#3f4f4a"
        svg += (f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{2.6 if lead else 1.6}"/>'
                f'<rect x="{pts[-1][0]-3:.1f}" y="{pts[-1][1]-3:.1f}" width="6" height="6" fill="{col}"/>'
                f'<text x="{pts[-1][0]+10:.1f}" y="{pts[-1][1]+4:.1f}" class="nm">{e(SH[t["team_id"]])}</text>')
    svg += "".join(f'<text x="{L_-10}" y="{fy(r)+4:.1f}" class="ax" text-anchor="end">{r:02d}</text>'
                   for r in (1, 6, 12) if r <= n)
    season = f'''<article class="post" id="season">
  {head(OP + 3, "Anonymous", trip("season"), times.get("season", ""), copy.get("subj_season", "tracking"))}
  <div class="pb">
    <p>{e(labels.get("lede_season", ""))}</p>
    <div class="chart"><svg viewBox="0 0 {W_} {H_}" width="100%" role="img" aria-label="rank by week">{svg}</svg></div>
    <p class="note">{e(labels.get("cnote", ""))}</p>
  </div>
</article>'''

    tail = "".join(
        f'<article class="post small" id="x{i}">'
        f'{head(OP + 40 + i, "Anonymous", trip("tail" + str(i)), times.get("tail" + str(i), ""))}'
        f'<div class="pb"><p>{e(x)}</p></div></article>'
        for i, x in enumerate(copy.get("tail_posts", [])))

    card = ROOT / "docs" / f"og-week-{wk}.png"
    og_img = copy.get("og_image") or (f"og-week-{wk}.png" if card.exists() else "og-league.png")
    og_title = copy.get("og_title") or f"Week {wk}: {theme}"
    og_desc = copy.get("og_description") or copy.get("standfirst", "")[:200]

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
<style>{h["load_skin"]("deepweb")}</style>
</head>
<body>
<div class="scan" aria-hidden="true"></div>
<header class="board">
  <div class="board-in">
    <p class="url">{e(copy.get("host", ""))}</p>
    <h1 class="logo" data-t="{e(copy.get("board_name", ""))}">{e(copy.get("board_name", ""))}</h1>
    <p class="sub">{e(copy.get("board_sub", ""))}</p>
    <nav class="tabs"><a href="#scores">[ results ]</a><a href="#p{OP + 6}">[ entries ]</a>
      <a href="#positions">[ distribution ]</a><a href="#season">[ tracking ]</a>
      <a href="../index.html">[ archive ]</a></nav>
  </div>
</header>

<main class="thread">
  <p class="crumb">/ccl/ &mdash; week {wk} &mdash; {e(copy.get("thread_title", ""))}</p>
  {op}
  {results}
  {replies}
  {positions}
  {season}
  {tail}
  <p class="foot">Thread archived. {n} entries. Data pulled from ESPN on Monday night, once the last game is final.
    <a href="../index.html">[ back to archive ]</a></p>
</main>
</body>
</html>
'''
