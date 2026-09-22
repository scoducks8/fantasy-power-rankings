"""Per-week numbers that sit beside the season totals.

points_for is the season total. The page talks about the week, so each team
also gets week_points (this week's score, from the matchup), week_proj_diff,
and all_play (this week's record against every other team's score).

    python scripts/week_fields.py --week 2     # patch an existing week file
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def add_week_fields(rankings: dict) -> dict:
    score = {}
    for m in rankings.get("matchups", []):
        score[m["home_id"]] = m["home_score"]
        score[m["away_id"]] = m["away_score"]
    teams = rankings["teams"]
    for t in teams:
        wp = score.get(t["team_id"], t["points_for"])
        t["week_points"] = round(wp, 2)
        if t.get("projected_total") is not None:
            t["week_proj_diff"] = round(wp - t["projected_total"], 2)
        w = sum(1 for o in teams if o is not t and score.get(o["team_id"], 0) < wp)
        l = sum(1 for o in teams if o is not t and score.get(o["team_id"], 0) > wp)
        t["all_play"] = f"{w}-{l}"
    return rankings


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    a = ap.parse_args()
    for name in (f"week-{a.week}.json", "latest.json"):
        p = ROOT / "data" / name
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        if d.get("week") != a.week:
            continue
        p.write_text(json.dumps(add_week_fields(d), indent=1))
        print(f"patched {name}")


if __name__ == "__main__":
    main()
