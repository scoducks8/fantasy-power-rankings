"""Is the NFL week actually over yet?

GitHub cron cannot listen for an event, so the weekly workflow polls instead.
It wakes up every half hour on Monday evening and asks ESPN's public, no-auth
scoreboard whether every game on the slate is final. Until Monday Night
Football ends this reports ready=false and the build job is skipped.

Writes ready= and week= to $GITHUB_OUTPUT when running inside Actions.
Always exits 0 so a "not yet" poll shows as a clean skip, not a red run.

    python scripts/nfl_status.py
    FORCE=true python scripts/nfl_status.py     # manual run, skip the gate
    NFL_WEEK=3 python scripts/nfl_status.py     # pin a week for testing
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
UA = {"User-Agent": "Mozilla/5.0 (fantasy-power-rankings bot)"}


def emit(ready: bool, week, reason: str) -> int:
    print(f"ready={str(ready).lower()}  week={week or '?'}  {reason}")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"ready={'true' if ready else 'false'}\n")
            fh.write(f"week={week or ''}\n")
    return 0


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    if os.environ.get("FORCE", "").strip().lower() == "true":
        return emit(True, os.environ.get("NFL_WEEK", ""), "forced run, gate skipped")

    url = SCOREBOARD
    pinned = os.environ.get("NFL_WEEK", "").strip()
    if pinned:
        url = f"{SCOREBOARD}?week={pinned}&seasontype=2"

    try:
        data = fetch(url)
    except Exception as exc:  # network, 5xx, bad JSON, anything
        return emit(False, "", f"scoreboard unreachable ({exc}), trying again next poll")

    week = (data.get("week") or {}).get("number")
    season_type = (data.get("season") or {}).get("type")
    events = data.get("events") or []

    if season_type != 2:
        return emit(False, week, f"season type {season_type} is not the regular season")
    if not events:
        return emit(False, week, "no games on the scoreboard")

    pending = []
    for ev in events:
        status = ((ev.get("status") or {}).get("type")) or {}
        if not status.get("completed"):
            label = status.get("detail") or status.get("state") or "scheduled"
            pending.append(f"{ev.get('shortName', '?')} [{label}]")

    if pending:
        shown = ", ".join(pending[:4])
        more = f" +{len(pending) - 4} more" if len(pending) > 4 else ""
        return emit(False, week, f"{len(pending)} of {len(events)} not final: {shown}{more}")

    if (ROOT / "data" / f"week-{week}.json").exists():
        return emit(False, week, "all games final but this week is already built")

    return emit(True, week, f"all {len(events)} games final")


if __name__ == "__main__":
    raise SystemExit(main())
