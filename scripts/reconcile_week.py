"""Recompute a week's totals from its own roster data.

ESPN can leave matchup totals and season records at zero for hours after the
last game. Every starter's score is already correct in the week file, so this
rebuilds team scores, records, matchups and the power ranking from them —
no second API call, and safe to re-run once ESPN catches up.

    python scripts/reconcile_week.py --week 1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from power_rank import weights_for  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    a = ap.parse_args()

    path = DATA / f"week-{a.week}.json"
    data = json.loads(path.read_text())
    teams = data["teams"]
    week = data["week"]

    # 1. Team score = sum of its starting lineup.
    score = {t["team_id"]: round(sum(s.get("points") or 0.0
                                     for s in t.get("starters", [])), 2)
             for t in teams}
    if not any(score.values()):
        print("No starter points in this file - nothing to reconcile.")
        return 1

    # 2. Matchups.
    for m in data.get("matchups", []):
        hs, as_ = score[m["home_id"]], score[m["away_id"]]
        m["home_score"], m["away_score"] = hs, as_
        m["margin"] = round(abs(hs - as_), 2)
        m["total"] = round(hs + as_, 2)
        m["winner"] = "HOME" if hs > as_ else "AWAY" if as_ > hs else "TIE"
        m["final"] = True

    # 3. Records and opponent context.
    opp = {}
    for m in data["matchups"]:
        opp[m["home_id"]] = (m["away_id"], m["away"], m["away_score"], m["winner"] == "HOME")
        opp[m["away_id"]] = (m["home_id"], m["home"], m["home_score"], m["winner"] == "AWAY")

    n = len(teams)
    for t in teams:
        tid = t["team_id"]
        _, oname, oscore, won = opp[tid]
        t["points_for"] = score[tid]
        t["points_against"] = oscore
        t["wins"], t["losses"], t["ties"] = (1, 0, 0) if won else (0, 1, 0)
        t["streak"] = "W1" if won else "L1"
        t["last_result"] = {"result": "W" if won else "L", "score": score[tid],
                            "opponent_score": oscore, "opponent": oname}
        others = [s for k, s in score.items() if k != tid]
        beat = sum(1 for s in others if score[tid] > s)
        t["all_play"] = f"{beat}-{len(others) - beat}"
        t["all_play_pct"] = round(beat / len(others), 4)

    # 4. Power score on the adaptive weights for this week.
    W = weights_for(week)
    ordered_pf = sorted(teams, key=lambda x: x["points_for"])
    for t in teams:
        wp = 1.0 if t["wins"] else 0.0
        mo = wp                               # one game in, momentum is the result
        sc = ordered_pf.index(t) / (n - 1)    # points-for percentile
        luck = (t["all_play_pct"] - wp + 1) / 2
        t["components"] = {"win_pct": wp, "momentum": mo,
                           "scoring": round(sc, 4), "luck": round(luck, 4)}
        t["power_score"] = round(W["win_pct"] * wp + W["momentum"] * mo
                                 + W["scoring"] * sc + W["luck"] * luck, 4)

    teams.sort(key=lambda t: (-t["power_score"], -t["points_for"]))
    for i, t in enumerate(teams, 1):
        t["prev_rank"], t["rank"] = t.get("rank"), i
        t["movement"] = 0 if not t["prev_rank"] else t["prev_rank"] - i

    data["weights"] = W
    data["matchups"].sort(key=lambda m: m["margin"])
    path.write_text(json.dumps(data, indent=1))
    (DATA / "latest.json").write_text(json.dumps(data, indent=1))

    hist = DATA / "history.json"
    history = json.loads(hist.read_text()) if hist.exists() else []
    history = [h for h in history if h.get("week") != week]
    history.append({"week": week,
                    "ranks": {str(t["team_id"]): t["rank"] for t in teams},
                    "scores": {str(t["team_id"]): t["points_for"] for t in teams}})
    history.sort(key=lambda h: h["week"])
    hist.write_text(json.dumps(history, indent=1))

    print(f'{"#":>2} {"team":<24}{"owner":<18}{"rec":>5}{"PF":>8}{"all-play":>10}{"power":>8}')
    for t in teams:
        print(f'{t["rank"]:>2} {t["name"][:23]:<24}{t["owner"][:17]:<18}'
              f'{t["wins"]}-{t["losses"]:<3}{t["points_for"]:>8.1f}'
              f'{t["all_play"]:>10}{t["power_score"]:>8.3f}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
