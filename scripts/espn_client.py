"""Thin client for ESPN's undocumented fantasy football v3 API.

Private leagues require two cookies pulled from a logged-in browser session:
  espn_s2  - long URL-encoded token
  SWID     - GUID wrapped in braces, e.g. {ABC12345-...}

These are read from the environment (ESPN_S2 / ESPN_SWID) so they can live in
GitHub Actions secrets and never touch the repo.
"""

from __future__ import annotations

import os
import sys
import requests

BASE = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"

# ESPN returns 403 to obviously-scripted user agents.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


class EspnAuthError(RuntimeError):
    """Raised when ESPN rejects our cookies - almost always means they expired."""


def _cookies() -> dict[str, str]:
    s2 = os.environ.get("ESPN_S2", "").strip()
    swid = os.environ.get("ESPN_SWID", "").strip()
    if not s2 or not swid:
        raise EspnAuthError(
            "ESPN_S2 and ESPN_SWID must be set. For a private league these come "
            "from your browser cookies. See README.md."
        )
    # SWID must include the surrounding braces.
    if not swid.startswith("{"):
        swid = "{" + swid.strip("{}") + "}"
    return {"espn_s2": s2, "SWID": swid}


def fetch_league(league_id: str, season: int, views: list[str] | None = None,
                 scoring_period: int | None = None) -> dict:
    """Fetch the league blob for a season.

    views control how much ESPN sends back. We ask for teams, per-matchup
    scores, and league settings - enough for records, weekly results and names.
    """
    views = views or ["mTeam", "mMatchupScore", "mSettings", "mStandings"]
    url = f"{BASE}/seasons/{season}/segments/0/leagues/{league_id}"
    params = [("view", v) for v in views]
    if scoring_period is not None:
        # mRoster returns the lineup and points for this specific week.
        params.append(("scoringPeriodId", scoring_period))

    resp = requests.get(
        url, params=params, headers=HEADERS, cookies=_cookies(), timeout=30
    )

    if resp.status_code in (401, 403):
        raise EspnAuthError(
            f"ESPN returned {resp.status_code}. Your espn_s2/SWID cookies have "
            "most likely expired - log in to ESPN again and refresh the repo "
            "secrets. See README.md for how to pull them."
        )
    if resp.status_code == 404:
        raise RuntimeError(
            f"League {league_id} not found for season {season}. Check LEAGUE_ID "
            "and that the season has started."
        )
    resp.raise_for_status()

    data = resp.json()
    # ESPN sometimes wraps a single league in a list.
    if isinstance(data, list):
        data = data[0]
    return data


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    league_id = os.environ.get("LEAGUE_ID")
    season = int(os.environ.get("SEASON", "2026"))
    if not league_id:
        sys.exit("Set LEAGUE_ID to smoke-test this module.")
    blob = fetch_league(league_id, season)
    print("League:", blob.get("settings", {}).get("name"))
    print("Teams:", len(blob.get("teams", [])))
    print("Current week:", blob.get("status", {}).get("currentMatchupPeriod"))
