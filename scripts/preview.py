"""Save the schedule and this week's projected lineups, for a week preview.

Run by .github/workflows/preview.yml. Writes data/schedule.json and
data/preview-week-N.json. Never touches the weekly rankings files.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from espn_client import fetch_league, EspnAuthError  # noqa: E402
from week_detail import parse_week  # noqa: E402
from update_week import save_schedule, DATA_DIR  # noqa: E402


def main() -> int:
    league_id = os.environ.get("LEAGUE_ID")
    season = int(os.environ.get("SEASON", "2026"))
    if not league_id:
        print("LEAGUE_ID is not set.", file=sys.stderr)
        return 1
    try:
        base = fetch_league(league_id, season)
    except EspnAuthError as exc:
        print(f"AUTH FAILED: {exc}", file=sys.stderr)
        return 2

    DATA_DIR.mkdir(exist_ok=True)
    save_schedule(base)

    week = int(os.environ.get("PREVIEW_WEEK") or 0) or \
        (base.get("status") or {}).get("currentMatchupPeriod") or 0
    if not week:
        print("No current matchup period.", file=sys.stderr)
        return 0

    blob = fetch_league(league_id, season, views=["mRoster", "mTeam"],
                        scoring_period=week)
    detail = parse_week(blob, week)
    teams = {}
    for tid, d in detail.items():
        teams[str(tid)] = {
            "projected_total": d["projected_total"],
            "points_so_far": round(sum(r["points"] for r in d["starters"]), 2),
            "starters": [
                {k: r[k] for k in ("name", "position", "slot", "points", "projected")}
                for r in d["starters"]
            ],
        }
    out = {
        "week": week,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "teams": teams,
    }
    (DATA_DIR / f"preview-week-{week}.json").write_text(json.dumps(out, indent=1))
    print(f"Saved preview for week {week}: {len(teams)} teams.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
