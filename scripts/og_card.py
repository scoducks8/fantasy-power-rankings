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
    a = ap.parse_args()
    out = Path(a.out) if a.out else ROOT / "docs" / f"og-week-{a.week}.png"
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fh:
        fh.write(build(a.week, a.copy))
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
