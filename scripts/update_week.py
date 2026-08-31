"""Weekly entry point: fetch ESPN, rank, cache logos, write data/week-N.json.

Run by .github/workflows/weekly.yml every Tuesday morning, and by you locally
whenever you want to refresh mid-week.

    LEAGUE_ID=... SEASON=2026 ESPN_S2=... ESPN_SWID=... python scripts/update_week.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))

from espn_client import fetch_league, EspnAuthError  # noqa: E402
from power_rank import build_rankings  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LOGO_DIR = ROOT / "docs" / "assets" / "logos"


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "team"


def cache_logos(rankings: dict) -> None:
    """Download team logos into the repo.

    Hotlinking ESPN's CDN means an archived Week 3 page silently changes when
    somebody swaps their logo in Week 10. Caching freezes each week's look.
    """
    LOGO_DIR.mkdir(parents=True, exist_ok=True)

    for team in rankings["teams"]:
        url = team.get("logo")
        if not url or not url.startswith("http"):
            team["logo_local"] = ""
            continue

        ext = ".png"
        for candidate in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            if candidate in url.lower():
                ext = candidate
                break

        filename = f"{team['team_id']}-{slugify(team['name'])}{ext}"
        target = LOGO_DIR / filename

        if not target.exists():
            try:
                resp = requests.get(url, timeout=20)
                resp.raise_for_status()
                target.write_bytes(resp.content)
                print(f"  cached logo: {filename}")
            except requests.RequestException as exc:
                print(f"  ! logo failed for {team['name']}: {exc}")
                team["logo_local"] = ""
                continue

        team["logo_local"] = f"assets/logos/{filename}"


def main() -> int:
    league_id = os.environ.get("LEAGUE_ID")
    season = int(os.environ.get("SEASON", "2026"))

    if not league_id:
        print("LEAGUE_ID is not set.", file=sys.stderr)
        return 1

    print(f"Fetching league {league_id}, season {season} ...")
    try:
        blob = fetch_league(league_id, season)
    except EspnAuthError as exc:
        print(f"AUTH FAILED: {exc}", file=sys.stderr)
        return 2

    DATA_DIR.mkdir(exist_ok=True)

    # Peek at the completed week so we can load the prior file for movement.
    preview = build_rankings(blob, season)
    week = preview["week"]

    if week == 0:
        print("No completed matchups yet - nothing to rank.")
        return 0

    prev_path = DATA_DIR / f"week-{week - 1}.json"
    rankings = build_rankings(blob, season, prev_path=prev_path)

    print(f"Week {week}: ranking {len(rankings['teams'])} teams")
    cache_logos(rankings)

    out = DATA_DIR / f"week-{week}.json"
    out.write_text(json.dumps(rankings, indent=2))
    (DATA_DIR / "latest.json").write_text(json.dumps(rankings, indent=2))
    print(f"Wrote {out.relative_to(ROOT)}")

    for team in rankings["teams"]:
        arrow = (
            f"+{team['movement']}" if team["movement"] > 0
            else str(team["movement"]) if team["movement"] < 0
            else "-"
        )
        print(
            f"  {team['rank']:>2}. {team['name'][:28]:<28} "
            f"{team['wins']}-{team['losses']}  {team['streak']:<3} "
            f"score={team['power_score']:.3f}  move={arrow}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
