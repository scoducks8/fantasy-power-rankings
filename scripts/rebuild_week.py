"""Rebuild a week's rankings from the weekly files already in data/.

Records, streaks, all-play and the power score all come from the per-week
matchups on disk, so a bad ESPN pull cannot leave phantom games in a record.
Player detail (starters, positional, top scorer) is kept from the target week.

    python scripts/rebuild_week.py --week 3
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from power_rank import (weights_for, win_pct, momentum, streak,  # noqa: E402
                        scoring_percentile, all_play_pct)
from week_fields import add_week_fields  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def weeks_from_files(upto: int) -> dict[int, dict[int, dict]]:
    weeks: dict[int, dict[int, dict]] = {}
    for w in range(1, upto + 1):
        path = DATA / f"week-{w}.json"
        if not path.exists():
            continue
        bucket: dict[int, dict] = {}
        for m in json.loads(path.read_text()).get("matchups", []):
            hs, as_ = m["home_score"], m["away_score"]
            res_h = "W" if hs > as_ else "L" if as_ > hs else "T"
            res_a = {"W": "L", "L": "W", "T": "T"}[res_h]
            bucket[m["home_id"]] = {"score": hs, "opponent_id": m["away_id"],
                                    "opponent_score": as_, "result": res_h}
            bucket[m["away_id"]] = {"score": as_, "opponent_id": m["home_id"],
                                    "opponent_score": hs, "result": res_a}
        if bucket:
            weeks[w] = bucket
    return weeks


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    target = DATA / f"week-{a.week}.json"
    data = json.loads(target.read_text())
    weeks = weeks_from_files(a.week)
    if a.week not in weeks:
        sys.exit(f"No matchups on file for week {a.week}")

    teams = data["teams"]
    names = {t["team_id"]: t["name"] for t in teams}
    for t in teams:
        tid = t["team_id"]
        w = l = d = 0
        pf = pa = 0.0
        for res in weeks.values():
            r = res.get(tid)
            if not r:
                continue
            pf += r["score"]
            pa += r["opponent_score"]
            w += r["result"] == "W"
            l += r["result"] == "L"
            d += r["result"] == "T"
        t.update(wins=w, losses=l, ties=d,
                 points_for=round(pf, 2), points_against=round(pa, 2))

    W = weights_for(a.week)
    for t in teams:
        tid = t["team_id"]
        wp = win_pct(t)
        mo = momentum(tid, weeks)
        sc = scoring_percentile(t, teams)
        ap_ = all_play_pct(tid, weeks)
        luck = (ap_ - wp + 1) / 2
        t["streak"] = streak(tid, weeks)
        t["all_play_pct"] = round(ap_, 4)
        t["components"] = {"win_pct": round(wp, 4), "momentum": round(mo, 4),
                           "scoring": round(sc, 4), "luck": round(luck, 4)}
        t["power_score"] = round(W["win_pct"] * wp + W["momentum"] * mo
                                 + W["scoring"] * sc + W["luck"] * luck, 4)
        last = weeks[a.week].get(tid)
        t["last_result"] = ({"result": last["result"], "score": last["score"],
                             "opponent_score": last["opponent_score"],
                             "opponent": names.get(last["opponent_id"], "Bye")}
                            if last else None)

    teams.sort(key=lambda t: (-t["power_score"], -t["points_for"]))

    hist_path = DATA / "history.json"
    history = json.loads(hist_path.read_text()) if hist_path.exists() else []
    history = [h for h in history if h["week"] < a.week]
    prev = {}
    if history:
        prev = {int(k): v for k, v in history[-1]["ranks"].items()}
    for i, t in enumerate(teams, start=1):
        t["rank"] = i
        t["prev_rank"] = prev.get(t["team_id"])
        t["movement"] = (t["prev_rank"] - i) if t["prev_rank"] else 0

    data.update(week=a.week, provisional=False, weights=W,
                generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    add_week_fields(data)
    history.append({"week": a.week,
                    "ranks": {str(t["team_id"]): t["rank"] for t in teams},
                    "scores": {str(t["team_id"]): t["week_points"] for t in teams}})

    for t in teams:
        print(f'  {t["rank"]:>2}. {t["name"][:26]:<28}{t["week_points"]:>7.2f}  '
              f'{t["wins"]}-{t["losses"]}  {t["streak"]:<4} all-play {t["all_play"]}')
    if a.dry_run:
        print("dry run, nothing written")
        return
    target.write_text(json.dumps(data, indent=1))
    (DATA / "latest.json").write_text(json.dumps(data, indent=1))
    hist_path.write_text(json.dumps(history, indent=1))
    print(f"wrote week-{a.week}.json, latest.json and history.json "
          f"({len(history)} weeks)")


if __name__ == "__main__":
    main()
