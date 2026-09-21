"""Verified numbers for writing a week's copy.

Every claim in the blurbs ("fifth-best score", "beats three teams in all-play",
"lowest winning score") should come from this sheet, not from eyeballing.

    python scripts/fact_sheet.py --week 2
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POS = ["QB", "RB", "WR", "TE", "K", "D/ST"]


def ordinal(n: int) -> str:
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    a = ap.parse_args()
    d = json.loads((ROOT / "data" / f"week-{a.week}.json").read_text())
    teams = d["teams"]
    T = {t["team_id"]: t for t in teams}
    n = len(teams)
    by_score = sorted(teams, key=lambda t: -t["points_for"])
    score_rank = {t["team_id"]: i + 1 for i, t in enumerate(by_score)}

    wins, losses = [], []
    opp = {}
    for m in d["matchups"]:
        hw = m["winner"] == "HOME"
        w, l = (m["home_id"], m["away_id"]) if hw else (m["away_id"], m["home_id"])
        ws, ls = (m["home_score"], m["away_score"]) if hw else (m["away_score"], m["home_score"])
        wins.append((ws, w, l, m["margin"]))
        losses.append((ls, l, w, m["margin"]))
        opp[w], opp[l] = (l, ws, ls, "W"), (w, ls, ws, "L")

    print(f"WEEK {a.week}  (provisional={d.get('provisional')})")
    print(f"weights: {d.get('weights')}\n")

    print("SCORES, high to low (score rank / power rank / all-play / vs proj)")
    for t in by_score:
        diff = t["points_for"] - t["projected_total"]
        print(f"  {score_rank[t['team_id']]:>2}. {t['name'][:26]:<27}{t['points_for']:>7.2f}  "
              f"power #{t['rank']:<2} all-play {t.get('all_play','?'):<6} {diff:+.2f} vs proj  "
              f"record {t['wins']}-{t['losses']}  streak {t.get('streak','')}")

    print("\nMATCHUPS, closest first")
    for m in d["matchups"]:
        print(f"  {m['away'][:22]:<23}{m['away_score']:>7.2f}  at  {m['home'][:22]:<23}"
              f"{m['home_score']:>7.2f}   margin {m['margin']:.2f}")

    ws = sorted(wins)
    ls = sorted(losses, reverse=True)
    print(f"\n  lowest winning score:  {ws[0][0]:.2f} {T[ws[0][1]]['name']}")
    print(f"  highest losing score:  {ls[0][0]:.2f} {T[ls[0][1]]['name']}")
    print(f"  winning scores low to high: " + ", ".join(f"{s:.1f} {T[i]['name'][:14]}" for s, i, *_ in ws))

    print("\nPER TEAM")
    for t in teams:
        tid = t["team_id"]
        o = opp.get(tid)
        pos = t["positional"]
        print(f"\n  #{t['rank']} {t['name']}  ({t['owner']})")
        if o:
            print(f"    {o[3]} vs {T[o[0]]['name']} {o[1]:.2f}-{o[2]:.2f}  "
                  f"beats {sum(1 for x in teams if x['points_for'] < t['points_for'])} teams' scores")
        print(f"    move {t.get('movement', 0):+d} (was #{t.get('prev_rank')})  bench {t.get('bench_points')}")
        print("    by position: " + "  ".join(f"{p} {pos.get(p, 0):.1f}" for p in POS))
        starters = sorted(t["starters"], key=lambda s: -s["points"])
        print("    starters: " + ", ".join(f"{s['name']} ({s['slot']}) {s['points']:.1f}" for s in starters))

    print("\nPOSITION LEADERS / TRAILERS")
    for p in POS:
        ranked = sorted(teams, key=lambda t: -t["positional"].get(p, 0))
        print(f"  {p:<5} best {ranked[0]['positional'].get(p,0):.1f} {ranked[0]['name'][:18]:<19}"
              f"worst {ranked[-1]['positional'].get(p,0):.1f} {ranked[-1]['name'][:18]}")

    print("\nZEROS AND NEGATIVES IN STARTING LINEUPS")
    for t in teams:
        for s in t["starters"]:
            if s["points"] <= 0:
                print(f"  {s['points']:.1f}  {s['name']} ({s['slot']})  {t['name']}")

    allp = sorted((s for t in teams for s in t["starters"]), key=lambda s: -s["points"])[:8]
    print("\nTOP INDIVIDUAL SCORES")
    for s in allp:
        own = next(t for t in teams if s in t["starters"])
        print(f"  {s['points']:.1f}  {s['name']} ({s['slot']})  {own['name']}")


if __name__ == "__main__":
    main()
