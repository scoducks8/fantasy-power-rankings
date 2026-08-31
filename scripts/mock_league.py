"""Generate a fake ESPN league blob so the pipeline can be tested and the
site previewed before real credentials (or real games) exist.

    python scripts/mock_league.py            # write data/week-N.json from fake data
    python scripts/mock_league.py --weeks 5  # simulate through week 5
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from power_rank import build_rankings  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

TEAM_NAMES = [
    "Cleats McGee", "The Wide Rights", "Sunday Scaries", "Bortles To Ashes",
    "Pain Train", "Hurts So Good", "Kupp Noodles", "Zero RB Truthers",
    "Waiver Wire Villains", "Punt Returns Only",
]


def make_blob(num_weeks: int, seed: int = 7) -> dict:
    rng = random.Random(seed)
    teams = []
    for i, name in enumerate(TEAM_NAMES, start=1):
        teams.append(
            {
                "id": i,
                "name": name,
                "abbrev": "".join(w[0] for w in name.split())[:4].upper(),
                "logo": "",
                "owners": [f"{{OWNER-{i}}}"],
                "record": {"overall": {"wins": 0, "losses": 0, "ties": 0,
                                       "pointsFor": 0.0, "pointsAgainst": 0.0}},
            }
        )

    # Give each team a hidden true strength so results aren't pure noise.
    strength = {t["id"]: rng.uniform(95, 125) for t in teams}
    schedule = []
    ids = [t["id"] for t in teams]

    for week in range(1, num_weeks + 1):
        order = ids[:]
        rng.shuffle(order)
        for a, b in zip(order[::2], order[1::2]):
            a_pts = round(rng.gauss(strength[a], 18), 1)
            b_pts = round(rng.gauss(strength[b], 18), 1)
            winner = "HOME" if a_pts > b_pts else "AWAY" if b_pts > a_pts else "TIE"

            schedule.append(
                {
                    "matchupPeriodId": week,
                    "winner": winner,
                    "home": {"teamId": a, "totalPoints": a_pts},
                    "away": {"teamId": b, "totalPoints": b_pts},
                }
            )

            for tid, own, opp, is_win in (
                (a, a_pts, b_pts, winner == "HOME"),
                (b, b_pts, a_pts, winner == "AWAY"),
            ):
                rec = next(t for t in teams if t["id"] == tid)["record"]["overall"]
                rec["pointsFor"] = round(rec["pointsFor"] + own, 1)
                rec["pointsAgainst"] = round(rec["pointsAgainst"] + opp, 1)
                if winner == "TIE":
                    rec["ties"] += 1
                elif is_win:
                    rec["wins"] += 1
                else:
                    rec["losses"] += 1

    return {
        "settings": {"name": "Mock Dynasty League"},
        "status": {"currentMatchupPeriod": num_weeks + 1},
        "teams": teams,
        "schedule": schedule,
        "members": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weeks", type=int, default=4)
    parser.add_argument("--season", type=int, default=2026)
    args = parser.parse_args()

    data_dir = ROOT / "data"
    data_dir.mkdir(exist_ok=True)

    # Build every week in sequence so movement arrows have prior files to read.
    for week in range(1, args.weeks + 1):
        blob = make_blob(week)
        prev = data_dir / f"week-{week - 1}.json"
        rankings = build_rankings(blob, args.season, prev_path=prev)
        for team in rankings["teams"]:
            team["logo_local"] = ""
        (data_dir / f"week-{week}.json").write_text(json.dumps(rankings, indent=2))
        if week == args.weeks:
            (data_dir / "latest.json").write_text(json.dumps(rankings, indent=2))

    final = json.loads((data_dir / "latest.json").read_text())
    print(f"Mock data through week {final['week']}:\n")
    print(f"  {'#':>2}  {'TEAM':<24} {'REC':<7} {'STRK':<5} {'PF':>7} {'SCORE':>6}  MOVE")
    for t in final["teams"]:
        move = (f"+{t['movement']}" if t["movement"] > 0
                else str(t["movement"]) if t["movement"] < 0 else "—")
        print(
            f"  {t['rank']:>2}  {t['name'][:24]:<24} "
            f"{t['wins']}-{t['losses']:<5} {t['streak']:<5} "
            f"{t['points_for']:>7.1f} {t['power_score']:>6.3f}  {move}"
        )


if __name__ == "__main__":
    main()
