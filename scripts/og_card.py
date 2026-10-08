"""Link-preview card (1200x630) for a RuneScape-theme week.

Builds the card from the week's data plus the copy file, then screenshots it
with Playwright. Needs Chromium, so run it where Playwright is installed.

    python scripts/og_card.py --week 2 [--copy data/copy-week-2.json]

Writes docs/og-week-N.png, which the page picks up automatically.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
e = html.escape


def build_clean(week: int, copy_path: str) -> str:
    """Quiet editorial card: headline, one hero figure, the team behind it."""
    d = json.loads((ROOT / "data" / f"week-{week}.json").read_text())
    c = json.loads(Path(copy_path).read_text()) if copy_path else json.loads(
        (ROOT / "data" / f"copy-week-{week}.json").read_text())
    docs = (ROOT / "docs").as_uri()
    teams = d["teams"]
    score = {}
    for m in d["matchups"]:
        score[m["home_id"]], score[m["away_id"]] = m["home_score"], m["away_score"]
    top = max(teams, key=lambda t: score.get(t["team_id"], 0))
    lead = min(teams, key=lambda t: t["rank"])
    av = f'{docs}/{top["logo_local"]}' if top.get("logo_local") else ""
    lav = f'{docs}/{lead["logo_local"]}' if lead.get("logo_local") else ""
    fonts = f"{docs}/assets/fonts"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:I;font-weight:500;src:url({fonts}/inter-latin-500-normal.woff2)}}
@font-face{{font-family:I;font-weight:600;src:url({fonts}/inter-latin-600-normal.woff2)}}
@font-face{{font-family:I;font-weight:700;src:url({fonts}/inter-latin-700-normal.woff2)}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1200px;height:630px;overflow:hidden;background:#f9f9f7;color:#0b0b0b;font-family:I,system-ui,sans-serif;
  padding:64px 72px;display:grid;grid-template-columns:1fr 360px;gap:56px;align-items:center}}
.k{{font-size:20px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:#2a78d6}}
h1{{margin-top:18px;font-size:64px;line-height:1.06;font-weight:700;letter-spacing:-.03em}}
.lg{{margin-top:30px;font-size:22px;font-weight:500;color:#52514e;display:flex;align-items:center;gap:12px}}
.lg img{{width:40px;height:40px;border-radius:50%;object-fit:cover}}
.tile{{background:#fff;border:1px solid #e1e0d9;border-radius:24px;padding:34px 34px 30px;box-shadow:0 10px 30px rgba(0,0,0,.06)}}
.tl{{font-size:20px;font-weight:500;color:#52514e}}
.tv{{margin-top:10px;font-size:96px;font-weight:600;letter-spacing:-.04em;line-height:1}}
.tw{{margin-top:22px;display:flex;align-items:center;gap:14px;font-size:22px;font-weight:600}}
.tw img{{width:52px;height:52px;border-radius:50%;object-fit:cover}}
.ts{{margin-top:4px;font-size:18px;font-weight:500;color:#898781}}
</style></head><body>
<div>
  <div class="k">Week {week} power rankings</div>
  <h1>{e(c.get("headline", ""))}</h1>
  <div class="lg">{f'<img src="{lav}">' if lav else ''}<span>No. 1 {e(lead["name"])}, {lead["wins"]}-{lead["losses"]}</span></div>
</div>
<div class="tile">
  <div class="tl">Top score</div>
  <div class="tv">{score.get(top["team_id"], 0):.1f}</div>
  <div class="tw">{f'<img src="{av}">' if av else ''}<div>{e(top["name"])}<div class="ts">{e(top["owner"])}</div></div></div>
</div>
</body></html>"""


def build_sportscenter(week: int, copy_path: str) -> str:
    """2000s SportsCenter card: chrome bar, big gold number, ticker of results."""
    d = json.loads((ROOT / "data" / f"week-{week}.json").read_text())
    c = json.loads(Path(copy_path).read_text()) if copy_path else json.loads(
        (ROOT / "data" / f"copy-week-{week}.json").read_text())
    docs = (ROOT / "docs").as_uri()
    teams = d["teams"]
    score = {}
    for m in d["matchups"]:
        score[m["home_id"]], score[m["away_id"]] = m["home_score"], m["away_score"]
    top = max(teams, key=lambda t: score.get(t["team_id"], 0))
    num = score.get(top["team_id"], 0)
    best = top.get("top_scorer") or {}
    av = f'{docs}/{top["logo_local"]}' if top.get("logo_local") else ""
    hs = f'{docs}/{best["headshot_local"]}' if best.get("headshot_local") else ""
    first = {}
    for t in teams:
        first.setdefault(t["owner"].split()[0], []).append(t)
    sh = {}
    for name, grp in first.items():
        for t in grp:
            parts = t["owner"].split()
            sh[t["team_id"]] = f"{name} {parts[-1][0]}." if len(grp) > 1 and len(parts) > 1 else name
    items = ""
    for i, m in enumerate(d["matchups"][:3]):
        hw = m["home_score"] >= m["away_score"]
        w, l = (m["home_id"], m["away_id"]) if hw else (m["away_id"], m["home_id"])
        ws, ls = max(m["home_score"], m["away_score"]), min(m["home_score"], m["away_score"])
        cls = ' class="hot"' if w == top["team_id"] else ""
        items += (f'<span{cls}>{e(sh[w]).upper()} {ws:.1f}, {e(sh[l]).upper()} {ls:.1f}</span>'
                  + ('<em>&#8226;</em>' if i < 2 else ""))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--red:#cc0000;--red2:#9b0000;--gold:#ffd24a;
  --cond:"Arial Narrow","Liberation Sans Narrow",Impact,Haettenschweiler,sans-serif}}
body{{width:1200px;height:630px;overflow:hidden;position:relative;color:#fff;font-family:var(--cond);
  background:repeating-linear-gradient(135deg,rgba(255,255,255,.015) 0 2px,transparent 2px 6px),
    linear-gradient(115deg,rgba(204,0,0,.34) 0%,transparent 46%),
    linear-gradient(180deg,#14294c 0%,#0a1730 60%,#060e1e 100%)}}
.bar{{height:48px;display:flex;align-items:center;justify-content:space-between;padding:0 26px;
  border-bottom:3px solid var(--red);
  background:linear-gradient(180deg,#f7f9fb 0%,#d6dce5 45%,#aab3c0 52%,#cbd3dd 100%)}}
.bar b{{font-size:20px;font-weight:900;font-style:italic;letter-spacing:.07em;text-transform:uppercase;color:#0a1730}}
.bar b:before{{content:"●";color:var(--red);font-style:normal;font-size:12px;margin-right:9px;vertical-align:2px}}
.bar i{{font-size:15px;font-weight:900;font-style:italic;letter-spacing:.13em;text-transform:uppercase;color:#43506b}}
.body{{display:grid;grid-template-columns:1fr 300px;gap:34px;padding:26px 34px 0;height:520px;align-items:center}}
.badge{{display:inline-block;background:linear-gradient(180deg,var(--red),var(--red2));font-size:17px;
  font-weight:900;font-style:italic;letter-spacing:.2em;text-transform:uppercase;padding:6px 18px 6px 14px;
  margin-bottom:16px;clip-path:polygon(0 0,100% 0,calc(100% - 12px) 100%,0 100%)}}
.num{{font-size:172px;line-height:.82;font-weight:900;font-style:italic;color:var(--gold);letter-spacing:-.035em;
  text-shadow:0 5px 0 rgba(0,0,0,.6),0 0 40px rgba(255,210,74,.28)}}
.head{{margin-top:14px;font-size:50px;line-height:1.0;font-weight:900;font-style:italic;text-transform:uppercase;
  letter-spacing:-.02em;text-shadow:0 3px 0 rgba(0,0,0,.6)}}
.faces{{display:flex;flex-direction:column;align-items:center;gap:7px}}
.ava{{width:200px;height:200px;border-radius:50%;object-fit:cover;background:#0d1c38;
  border:4px solid #c3cad4;box-shadow:0 0 0 5px var(--red),0 12px 34px rgba(0,0,0,.7)}}
.who{{font-size:28px;font-weight:900;font-style:italic;color:var(--gold);text-transform:uppercase;margin-top:6px;
  text-align:center;line-height:1}}
.mini{{position:relative;margin-top:10px}}
.mini img{{width:118px;height:118px;object-fit:cover;object-position:top center;border:3px solid #8e97a4;background:#0d1c38}}
.mini b{{position:absolute;left:0;right:0;bottom:0;padding:26px 7px 4px;
  background:linear-gradient(transparent,rgba(5,12,26,.95));font-size:23px;font-weight:900;font-style:italic;
  color:var(--gold);text-align:center}}
.cap{{font-size:13px;font-weight:800;letter-spacing:.11em;text-transform:uppercase;color:#9fb0c9;text-align:center;
  font-family:system-ui,sans-serif}}
.tick{{position:absolute;left:0;right:0;bottom:0;height:62px;display:flex;align-items:center;
  background:linear-gradient(180deg,#11203c,#060d1c);border-top:3px solid var(--red)}}
.tick .bug{{height:100%;display:flex;align-items:center;padding:0 20px;
  background:linear-gradient(180deg,var(--red),var(--red2));font-size:22px;font-weight:900;font-style:italic;letter-spacing:.1em}}
.tick .items{{display:flex;gap:22px;padding-left:22px;white-space:nowrap;overflow:hidden}}
.tick span{{font-size:17px;font-weight:800;color:#dbe6f5;letter-spacing:.05em}}
.tick span.hot{{color:var(--gold)}} .tick em{{color:var(--red);font-style:normal}}
</style></head><body>
<div class="bar"><b>Chach Champions League</b><i>Week {week} &middot; SportsCenter</i></div>
<div class="body">
  <div><div class="badge">Week {week} Power Rankings</div>
    <div class="num">{num:.1f}</div>
    <div class="head">{e(c.get("card_headline") or c.get("headline", ""))}</div></div>
  <div class="faces">
    {f'<img class="ava" src="{av}">' if av else ''}
    <div class="who">{e(top["name"])}</div>
    <div class="cap">{e(top["owner"])}</div>
    {f'<div class="mini"><img src="{hs}"><b>{best.get("points", 0):.1f}</b></div><div class="cap">{e(best.get("name", ""))} &middot; top scorer</div>' if hs else ''}
  </div>
</div>
<div class="tick"><div class="bug">CCL</div><div class="items">{items}</div></div>
</body></html>"""


def build_ryanday(week: int, copy_path: str) -> str:
    """Scarlet and gray card for the Ryan Day shrine week."""
    d = json.loads((ROOT / "data" / f"week-{week}.json").read_text())
    c = json.loads(Path(copy_path).read_text()) if copy_path else json.loads(
        (ROOT / "data" / f"copy-week-{week}.json").read_text())
    docs = (ROOT / "docs").as_uri()
    teams = d["teams"]
    lead = min(teams, key=lambda t: t["rank"])
    score = {}
    for m in d["matchups"]:
        score[m["home_id"]], score[m["away_id"]] = m["home_score"], m["away_score"]
    num = score.get(lead["team_id"], lead["points_for"])
    creds = ROOT / "data" / "photo-credits.json"
    photos = json.loads(creds.read_text()) if creds.exists() else []
    day = [p for p in photos if "ryan day" in p.get("term", "").lower()]
    pic = f'{docs}/{day[0]["file"]}' if day else ""
    credit = (day[0]["author"][:40] + " / " + day[0]["license"]) if day else "Week " + str(week)
    av = f'{docs}/{lead["logo_local"]}' if lead.get("logo_local") else ""
    fonts = f"{docs}/assets/fonts"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:G;src:url({fonts}/graduate-latin-400-normal.woff2)}}
@font-face{{font-family:A;src:url({fonts}/anton-latin-400-normal.woff2)}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1200px;height:630px;overflow:hidden;position:relative;color:#1d1d1d;
  font-family:"Trebuchet MS",sans-serif;
  background:repeating-linear-gradient(45deg,rgba(187,0,0,.06) 0 16px,transparent 16px 32px),#efece4}}
.top{{height:56px;background:#bb0000;color:#fff;font-family:G;font-size:19px;letter-spacing:.06em;
  display:flex;align-items:center;padding:0 32px;border-bottom:4px double #fff}}
.body{{display:grid;grid-template-columns:1fr 420px;height:574px}}
.left{{padding:28px 30px 28px 34px}}
.kick{{font-family:G;font-size:16px;color:#8a0000;letter-spacing:.07em;text-transform:uppercase}}
.head{{font-family:A;font-size:46px;line-height:1.02;text-transform:uppercase;color:#bb0000;margin:10px 0 0;
  text-shadow:2px 2px 0 #fff,4px 4px 0 rgba(0,0,0,.16)}}
.num{{font-family:A;font-size:104px;line-height:.94;color:#1d1d1d;margin-top:18px}}
.who{{font-family:G;font-size:21px;color:#5b5b5b;margin-top:2px}}
.right{{position:relative;padding:24px 30px 24px 0;display:flex;align-items:center}}
.pic{{background:#fff;padding:11px;border:1px solid #b9b2a4;box-shadow:6px 6px 0 rgba(0,0,0,.22);
  transform:rotate(-1.6deg);width:100%}}
.pic img{{display:block;width:100%;height:392px;object-fit:cover;border:1px solid #d6d0c4}}
.pic figcaption{{margin-top:8px;font-size:13px;color:#5b5b5b;font-style:italic;text-align:center}}
.noimg{{width:100%;height:392px;display:grid;place-items:center;background:#2b2b2b;color:#fff;
  font-family:G;font-size:26px;text-align:center;padding:24px;line-height:1.4}}
.hel{{position:absolute;right:42px;bottom:34px;width:92px;height:92px;border-radius:50%;
  border:4px solid #fff;box-shadow:0 0 0 3px #bb0000;object-fit:cover;background:#ddd}}
</style></head><body>
<div class="top">{e(c.get("card_strip", "A TRIBUTE PAGE"))}</div>
<div class="body">
  <div class="left">
    <div class="kick">Week {week} Power Rankings</div>
    <div class="head">{e(c.get("card_headline", ""))}</div>
    <div class="num">{num:.1f}</div>
    <div class="who">{e(lead["name"])} &middot; {e(lead["owner"])} &middot; {lead["wins"]}-{lead["losses"]}</div>
  </div>
  <div class="right"><figure class="pic">
    {f'<img src="{pic}">' if pic else '<div class="noimg">RYAN DAY<br>HEAD COACH, OHIO STATE</div>'}
    <figcaption>{e(credit)}</figcaption>
  </figure>{f'<img class="hel" src="{av}">' if av else ''}</div>
</div>
</body></html>"""


def build_occult(week: int, copy_path: str) -> str:
    """Card for the occult ledger: the seal, the title, the two figures."""
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "scripts" / "layouts"))
    import occult as _oc

    d = json.loads((ROOT / "data" / f"week-{week}.json").read_text())
    c = json.loads(Path(copy_path).read_text()) if copy_path else json.loads(
        (ROOT / "data" / f"copy-week-{week}.json").read_text())
    docs = (ROOT / "docs").as_uri()
    teams = d["teams"]
    lead = min(teams, key=lambda t: t["rank"])
    score = {}
    for m in d["matchups"]:
        score[m["home_id"]], score[m["away_id"]] = m["home_score"], m["away_score"]
    num = score.get(lead["team_id"], lead["points_for"])
    fonts = f"{docs}/assets/fonts"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:F;src:url({fonts}/unifrakturmaguntia-latin-400-normal.woff2)}}
@font-face{{font-family:C;font-weight:700;src:url({fonts}/cinzel-latin-700-normal.woff2)}}
@font-face{{font-family:C;font-weight:900;src:url({fonts}/cinzel-latin-900-normal.woff2)}}
@font-face{{font-family:G;src:url({fonts}/eb-garamond-latin-400-normal.woff2)}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1200px;height:630px;overflow:hidden;position:relative;color:#d8cfbd;font-family:G;
  background:radial-gradient(ellipse at 28% 45%,rgba(200,162,74,.13),transparent 55%),
    radial-gradient(ellipse at 90% 110%,rgba(143,31,36,.14),transparent 55%),#07070a}}
.wrap{{display:grid;grid-template-columns:1fr 430px;height:100%;align-items:center}}
.left{{padding:0 20px 0 62px}}
.over{{font-family:C;font-size:15px;letter-spacing:.34em;text-transform:uppercase;color:#6b6354}}
h1{{font-family:F;font-weight:400;font-size:64px;line-height:1.04;margin:10px 0 8px;color:#e7dfcd;
  text-shadow:0 0 30px rgba(200,162,74,.25)}}
.wk{{font-family:C;font-size:16px;letter-spacing:.24em;text-transform:uppercase;color:#c8a24a}}
.rule{{margin:22px 0 18px;font-size:17px;letter-spacing:1em;color:#8a6d28}}
.fig{{font-family:C;font-weight:900;font-size:64px;color:#c8a24a;line-height:1}}
.fig small{{display:block;font-family:C;font-weight:700;font-size:16px;letter-spacing:.14em;
  text-transform:uppercase;color:#9a907d;margin-top:8px}}
.head{{margin-top:22px;font-size:26px;font-style:italic;color:#b9b0a0}}
.seal svg{{display:block;filter:drop-shadow(0 0 26px rgba(200,162,74,.22))}}
.seal .ink{{fill:none;stroke:#c8a24a;stroke-width:1.1;stroke-linecap:round;stroke-linejoin:round}}
.seal .ring{{stroke:#8a6d28;stroke-width:.9}}
.seal .ring2{{stroke:#8a6d28;stroke-width:.5;stroke-dasharray:2 3}}
.seal .rays line,.seal .tick line{{stroke:#8a6d28;stroke-width:.5;opacity:.6}}
.seal .line{{stroke-width:1.3}}
.seal circle.core{{fill:#c8a24a;stroke:none}}
.grain{{position:absolute;inset:0;
  background:repeating-linear-gradient(0deg,rgba(0,0,0,.3) 0 1px,transparent 1px 2px);opacity:.5}}
</style></head><body>
<div class="wrap">
  <div class="left">
    <div class="over">{e(c.get("overline", ""))}</div>
    <h1>{e(c.get("board_name", ""))}</h1>
    <div class="wk">{e(c.get("thread_title", ""))}</div>
    <div class="rule">{e(c.get("glyph_rule", ""))}</div>
    <div class="fig">{num:.2f}<small>{e(lead["name"])} &middot; station I</small></div>
    <div class="head">{e(c.get("card_headline", ""))}</div>
  </div>
  <div class="seal">{_oc.seal(teams, 400)}</div>
</div>
<div class="grain"></div>
</body></html>"""


def build_deepweb(week: int, copy_path: str) -> str:
    """Card for the deep-web thread week: one post, cropped."""
    d = json.loads((ROOT / "data" / f"week-{week}.json").read_text())
    c = json.loads(Path(copy_path).read_text()) if copy_path else json.loads(
        (ROOT / "data" / f"copy-week-{week}.json").read_text())
    docs = (ROOT / "docs").as_uri()
    teams = d["teams"]
    lead = min(teams, key=lambda t: t["rank"])
    score = {}
    for m in d["matchups"]:
        score[m["home_id"]], score[m["away_id"]] = m["home_score"], m["away_score"]
    num = score.get(lead["team_id"], lead["points_for"])
    av = f'{docs}/{lead["logo_local"]}' if lead.get("logo_local") else ""
    fonts = f"{docs}/assets/fonts"
    green = c.get("op_green", [])[:3]
    lines = "".join(f'<p class="gt">&gt;{e(x)}</p>' for x in green)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:P;font-weight:400;src:url({fonts}/ibm-plex-mono-latin-400-normal.woff2)}}
@font-face{{font-family:P;font-weight:700;src:url({fonts}/ibm-plex-mono-latin-700-normal.woff2)}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1200px;height:630px;overflow:hidden;position:relative;font-family:P;color:#c3cfc9;
  background:radial-gradient(ellipse at 50% -20%,rgba(127,219,160,.08),transparent 60%),#080a0a}}
.scan{{position:absolute;inset:0;z-index:5;
  background:repeating-linear-gradient(0deg,rgba(0,0,0,.25) 0 1px,transparent 1px 3px)}}
.url{{padding:16px 40px 0;font-size:15px;color:#4d5956}}
.logo{{padding:4px 40px 0;font-size:44px;font-weight:700;color:#7fdba0;letter-spacing:.06em;
  text-shadow:0 0 22px rgba(127,219,160,.3)}}
.post{{margin:22px 40px 0;border:1px solid #2f3a3a;background:#121617}}
.ph{{display:flex;align-items:baseline;gap:10px;padding:9px 16px;background:#171c1d;
  border-bottom:1px solid #232b2c;font-size:17px}}
.subj{{color:#d8a657;font-weight:700}} .nm{{color:#4f9c6b}} .no{{margin-left:auto;color:#7d8a85;font-size:15px}}
.pb{{display:grid;grid-template-columns:150px 1fr;gap:20px;padding:18px 16px}}
.pb img{{width:150px;height:150px;object-fit:cover;border:1px solid #2f3a3a;filter:grayscale(.55)}}
.num{{font-size:74px;font-weight:700;color:#7fdba0;line-height:1}}
.who{{font-size:19px;color:#7d8a85;margin-top:4px}}
.gt{{color:#9cbb57;font-size:21px;margin-top:9px}}
.head{{margin:20px 40px 0;font-size:31px;color:#c3cfc9}}
.foot{{position:absolute;left:40px;bottom:22px;font-size:15px;color:#4d5956}}
</style></head><body>
<div class="url">{e(c.get("host", ""))}</div>
<div class="logo">{e(c.get("board_name", "the ledger"))}</div>
<div class="post">
  <div class="ph"><span class="subj">{e(c.get("op_subject", ""))}</span>
    <span class="nm">Anonymous</span><span class="no">No.8231 [Archived]</span></div>
  <div class="pb">
    {f'<img src="{av}">' if av else '<div></div>'}
    <div><div class="num">{num:.2f}</div>
      <div class="who">{e(lead["name"])} &middot; {e(lead["owner"])} &middot; {lead["wins"]}-{lead["losses"]}</div>
      {lines}</div>
  </div>
</div>
<div class="head">{e(c.get("card_headline", ""))}</div>
<div class="foot">chach champions league // week {week} // entries are permanent</div>
<div class="scan"></div>
</body></html>"""


def build(week: int, copy_path: str) -> str:
    d = json.loads((ROOT / "data" / f"week-{week}.json").read_text())
    c = json.loads(Path(copy_path).read_text()) if copy_path else json.loads(
        (ROOT / "data" / f"copy-week-{week}.json").read_text())
    teams = d["teams"]
    best = max((s for t in teams for s in t["starters"]), key=lambda s: s["points"])
    bt = next(t for t in teams if best in t["starters"])
    lead = min(teams, key=lambda t: t["rank"])
    week_score = {}
    for m in d["matchups"]:
        week_score[m["home_id"]], week_score[m["away_id"]] = m["home_score"], m["away_score"]
    best_score = c.get("card_number") or week_score.get(lead["team_id"], lead["points_for"])
    docs = (ROOT / "docs").as_uri()
    hs = f'{docs}/{best["headshot_local"]}' if best.get("headshot_local") else best.get("headshot", "")
    av = f'{docs}/{lead["logo_local"]}' if lead.get("logo_local") else ""
    chat = c.get("chat", [])[1:3] or ["Welcome to ChachScape."]
    lines = ""
    for ln in chat:
        if ln.startswith("From "):
            who, _, msg = ln[5:].partition(": ")
            lines += f'<p style="color:#007070">From {e(who)}: {e(msg)}</p>'
            continue
        who, sep, msg = ln.partition(": ")
        lines += (f'<p><b>{e(who)}:</b> <q>{e(msg)}</q></p>' if sep else f'<p>{e(ln)}</p>')
    fonts = f"{docs}/assets/fonts"
    headline = c.get("card_headline") or c.get("headline", "")
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:P;font-weight:400;unicode-range:U+0000-002C,U+002F,U+003A-FFFF;src:url({fonts}/pixelify-sans-latin-400-normal.woff2)}}
@font-face{{font-family:P;font-weight:700;unicode-range:U+0000-002C,U+002F,U+003A-FFFF;src:url({fonts}/pixelify-sans-latin-700-normal.woff2)}}
@font-face{{font-family:P;font-weight:400;unicode-range:U+002D-002E,U+0030-0039;size-adjust:70%;src:url({fonts}/press-start-2p-latin-400-normal.woff2)}}
@font-face{{font-family:P;font-weight:700;unicode-range:U+002D-002E,U+0030-0039;size-adjust:70%;src:url({fonts}/press-start-2p-latin-400-normal.woff2)}}
@font-face{{font-family:CD;src:url({fonts}/cinzel-decorative-latin-900-normal.woff2)}}
@font-face{{font-family:C;src:url({fonts}/cinzel-latin-900-normal.woff2)}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1200px;height:630px;overflow:hidden;position:relative;font-family:P;color:#fff;
  background:radial-gradient(ellipse at 20% 110%,#4a2206 0%,#140b04 55%,#050302 100%)}}
.glow{{position:absolute;width:420px;height:420px;border-radius:50%;
  background:radial-gradient(circle,rgba(255,140,20,.25),transparent 65%)}}
.left{{position:absolute;left:46px;top:34px;width:560px}}
.logo{{font-family:CD;font-size:66px;line-height:1;background:linear-gradient(180deg,#fffbd6,#ffe066 30%,#e0a100 55%,#8a5a00 80%,#ffd24a);
  -webkit-background-clip:text;color:transparent;filter:drop-shadow(3px 3px 0 #000) drop-shadow(0 0 2px #000)}}
.world{{margin-top:8px;font-size:22px;color:#ffff00;text-shadow:2px 2px 0 #000}}
.num{{margin-top:22px;font-size:150px;line-height:.85;font-weight:700;color:#ffff00;text-shadow:5px 5px 0 #000}}
.head{{margin-top:18px;font-family:C;font-size:38px;line-height:1.08;color:#ff981f;text-shadow:3px 3px 0 #000}}
.client{{position:absolute;right:40px;top:40px;width:500px;height:440px;border:4px solid #000;
  box-shadow:0 0 0 4px #564a39,0 0 0 7px #000,0 20px 40px rgba(0,0,0,.7);overflow:hidden;
  background:linear-gradient(115deg,transparent 38%,#8b7350 38.5%,#9c835c 45%,#8b7350 51%,transparent 51.5%),
    conic-gradient(#3d6a28 25%,#447330 0 50%,#3d6a28 0 75%,#447330 0) 0 0/20px 20px}}
.mo{{position:absolute;left:10px;top:8px;font-size:20px;text-shadow:2px 2px 0 #000}}
.mo span{{color:#ffff00}} .mo i{{font-style:normal;color:#00ff00}}
.tree{{position:absolute;border-radius:50%;background:radial-gradient(circle at 40% 35%,#4f8a36,#2c5a1c 60%,#1c3b12);border:3px solid #0d1c08}}
.char{{position:absolute;left:50%;bottom:0;transform:translateX(-50%);width:330px}}
.char img{{width:100%;display:block}}
.over{{position:absolute;left:50%;top:-4px;transform:translate(-50%,-100%);white-space:nowrap;
  font-size:30px;font-weight:700;color:#ffff00;text-shadow:3px 3px 0 #000}}
.splat{{position:absolute;left:-44px;top:44%;width:120px;height:120px;display:grid;place-items:center;
  background:#b80000;font-size:32px;font-weight:700;text-shadow:2px 2px 0 #000;
  clip-path:polygon(50% 0,63% 14%,82% 6%,82% 26%,100% 32%,88% 50%,100% 68%,82% 74%,82% 94%,63% 86%,50% 100%,37% 86%,18% 94%,18% 74%,0 68%,12% 50%,0 32%,18% 26%,18% 6%,37% 14%)}}
.name{{position:absolute;left:10px;bottom:10px;font-size:20px;color:#00ffff;text-shadow:2px 2px 0 #000}}
.av{{position:absolute;right:12px;top:44px;width:86px;height:86px;border-radius:50%;border:4px solid #000;
  box-shadow:0 0 0 3px #ffcf3f;object-fit:cover;background:#1a140d}}
.chat{{position:absolute;left:0;right:0;bottom:0;height:78px;border-top:4px solid #000;display:flex;
  background:radial-gradient(ellipse at 40% 30%,rgba(255,255,255,.25),transparent 70%),linear-gradient(180deg,#dccc9f,#c4b07e)}}
.chat .tab{{width:120px;display:grid;place-items:center;font-size:22px;color:#00ff00;text-shadow:2px 2px 0 #000;
  background:linear-gradient(180deg,#564a39,#2c2419);border-right:4px solid #000}}
.chat .log{{padding:8px 18px;font-size:23px;line-height:30px;color:#000}}
.chat q{{color:#0000c8}} .chat q:before,.chat q:after{{content:none}} .chat b{{font-weight:400}}
</style></head><body>
<div class="glow" style="left:-120px;top:-60px"></div>
<div class="left">
  <div class="logo">ChachScape</div>
  <div class="world">World {week} &middot; Week {week} Hiscores</div>
  <div class="num">{best_score:.1f}</div>
  <div class="head">{e(headline)}</div>
</div>
<div class="client">
  <div class="tree" style="left:18px;top:60px;width:110px;height:110px"></div>
  <div class="tree" style="right:26px;top:90px;width:90px;height:90px"></div>
  <div class="mo">Attack <span>{e(bt["name"])}</span> <i>(level-{round(3 + bt.get("power_score", 0) * 123)})</i></div>
  <div class="char"><div class="over">{e(c.get("overhead", "gg"))}</div><img src="{hs}"><div class="splat">{best["points"]:.1f}</div></div>
  <div class="name">{e(best["name"])}</div>
  {f'<img class="av" src="{av}">' if av else ''}
</div>
<div class="chat"><div class="tab">Public</div><div class="log">{lines}</div></div>
</body></html>'''


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--copy", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--style", default="runescape", choices=["runescape", "deepweb", "occult", "ryanday", "sportscenter", "clean"])
    a = ap.parse_args()
    out = Path(a.out) if a.out else ROOT / "docs" / f"og-week-{a.week}.png"
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fh:
        builder = {"deepweb": build_deepweb, "occult": build_occult, "ryanday": build_ryanday, "sportscenter": build_sportscenter, "clean": build_clean}.get(a.style, build)
        fh.write(builder(a.week, a.copy))
        src = fh.name
    js = f'''const {{chromium}}=require('playwright');(async()=>{{
const b=await chromium.launch({{executablePath:process.env.CHROMIUM||undefined}});
const p=await b.newPage({{viewport:{{width:1200,height:630}}}});
await p.goto('file://{src}');await p.waitForTimeout(900);
await p.screenshot({{path:'{out}'}});await b.close();}})();'''
    subprocess.run(["node", "-e", js], check=True)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
