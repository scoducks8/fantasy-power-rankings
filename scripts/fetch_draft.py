"""Pull the league's draft results plus per-player ADP and season projections.

Writes data/draft.json — everything a draft recap needs:
  - every pick in order, with the drafting team
  - each player's average draft position league-wide (for reach/value math)
  - each player's projected season total (for early roster strength)

Run via .github/workflows/draft.yml, or locally with LEAGUE_ID / SEASON /
ESPN_S2 / ESPN_SWID set.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))

from espn_client import fetch_league, EspnAuthError, BASE, HEADERS, _cookies  # noqa: E402
from power_rank import parse_teams  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

POSITIONS = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "D/ST"}

PRO_TEAMS = {
    0: "FA", 1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE", 6: "DAL",
    7: "DEN", 8: "DET", 9: "GB", 10: "TEN", 11: "IND", 12: "KC", 13: "LV",
    14: "LAR", 15: "MIA", 16: "MIN", 17: "NE", 18: "NO", 19: "NYG",
    20: "NYJ", 21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC", 25: "SF",
    26: "SEA", 27: "TB", 28: "WSH", 29: "CAR", 30: "JAX", 33: "BAL",
    34: "HOU",
}


def fetch_players(season: int, player_ids: list[int]) -> dict[int, dict]:
    """Look up drafted players in batches.

    The players endpoint needs an x-fantasy-filter header; asking for all
    players at once returns a very large payload, so we filter to just the
    ids we drafted and page through them.
    """
    out: dict[int, dict] = {}
    url = f"{BASE}/seasons/{season}/players"
    cookies = _cookies()

    for i in range(0, len(player_ids), 150):
        chunk = player_ids[i : i + 150]
        headers = dict(HEADERS)
        headers["x-fantasy-filter"] = json.dumps(
            {"players": {"filterIds": {"value": chunk}, "limit": len(chunk)}}
        )
        resp = requests.get(
            url,
            params={"scoringPeriodId": 0, "view": "players_wl"},
            headers=headers,
            cookies=cookies,
            timeout=45,
        )
        if resp.status_code in (401, 403):
            raise EspnAuthError(f"players endpoint returned {resp.status_code}")
        resp.raise_for_status()

        for p in resp.json():
            out[p["id"]] = p
        print(f"  players {i + len(chunk)}/{len(player_ids)}")

    return out


def projected_total(player: dict, season: int) -> float | None:
    """Season-long projection: statSourceId 1 = projected, split 0 = full season."""
    for s in player.get("stats") or []:
        if (
            s.get("statSourceId") == 1
            and s.get("statSplitTypeId") == 0
            and s.get("seasonId") == season
        ):
            total = s.get("appliedTotal")
            if total is not None:
                return round(total, 1)
    return None


def main() -> int:
    league_id = os.environ.get("LEAGUE_ID")
    season = int(os.environ.get("SEASON", "2026"))
    if not league_id:
        print("LEAGUE_ID is not set.", file=sys.stderr)
        return 1

    print(f"Fetching draft for league {league_id}, season {season} ...")
    try:
        blob = fetch_league(
            league_id, season, views=["mDraftDetail", "mTeam", "mSettings", "mRoster"]
        )
    except EspnAuthError as exc:
        print(f"AUTH FAILED: {exc}", file=sys.stderr)
        return 2

    draft = blob.get("draftDetail") or {}
    picks = draft.get("picks") or []

    if not picks:
        print("No draft picks found — has the league drafted yet?")
        DATA_DIR.mkdir(exist_ok=True)
        (DATA_DIR / "draft.json").write_text(
            json.dumps(
                {
                    "season": season,
                    "drafted": False,
                    "league_name": (blob.get("settings") or {}).get("name", ""),
                    "generated_at": datetime.now(timezone.utc).isoformat(
                        timespec="seconds"
                    ),
                },
                indent=2,
            )
        )
        return 0

    teams = parse_teams(blob)
    print(f"  {len(picks)} picks across {len(teams)} teams")

    player_ids = [p["playerId"] for p in picks if p.get("playerId")]
    players = fetch_players(season, player_ids)

    rows = []
    by_team = defaultdict(list)

    for pick in picks:
        pid = pick.get("playerId")
        info = players.get(pid, {})
        player = info.get("player", info) or {}

        adp = ((player.get("ownership") or {}).get("averageDraftPosition"))
        overall = pick.get("overallPickNumber")
        # Positive delta = taken later than the market (value).
        # Negative delta = taken earlier than the market (reach).
        delta = round(adp - overall, 1) if adp and overall else None

        row = {
            "overall": overall,
            "round": pick.get("roundId"),
            "round_pick": pick.get("roundPickNumber"),
            "team_id": pick.get("teamId"),
            "team": teams.get(pick.get("teamId"), {}).get("name", "?"),
            "owner": teams.get(pick.get("teamId"), {}).get("owner", ""),
            "player_id": pid,
            "player": player.get("fullName", f"Player {pid}"),
            "position": POSITIONS.get(player.get("defaultPositionId"), "?"),
            "pro_team": PRO_TEAMS.get(player.get("proTeamId"), "?"),
            "adp": round(adp, 1) if adp else None,
            "adp_delta": delta,
            "projected": projected_total(player, season),
            "keeper": bool(pick.get("keeper")),
            "bid": pick.get("bidAmount") or None,
        }
        rows.append(row)
        by_team[row["team_id"]].append(row)

    # Roster-level summary so the recap can rank teams on paper.
    team_summary = []
    for tid, team in teams.items():
        team_picks = by_team.get(tid, [])
        projected = [r["projected"] for r in team_picks if r["projected"]]
        deltas = [r["adp_delta"] for r in team_picks if r["adp_delta"] is not None]
        team_summary.append(
            {
                "team_id": tid,
                "team": team["name"],
                "owner": team["owner"],
                "logo": team["logo"],
                "picks": len(team_picks),
                "projected_total": round(sum(projected), 1) if projected else None,
                "avg_adp_delta": round(sum(deltas) / len(deltas), 2) if deltas else None,
                "positions": {
                    pos: sum(1 for r in team_picks if r["position"] == pos)
                    for pos in ["QB", "RB", "WR", "TE", "K", "D/ST"]
                },
            }
        )

    team_summary.sort(
        key=lambda t: t["projected_total"] or 0, reverse=True
    )

    out = {
        "season": season,
        "drafted": True,
        "league_name": (blob.get("settings") or {}).get("name", "Fantasy League"),
        "draft_type": (
            (blob.get("settings") or {}).get("draftSettings", {}).get("type")
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "teams": team_summary,
        "picks": sorted(rows, key=lambda r: r["overall"] or 0),
    }

    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "draft.json").write_text(json.dumps(out, indent=2))
    print(f"Wrote data/draft.json — {len(rows)} picks")

    reaches = sorted(
        [r for r in rows if r["adp_delta"] is not None], key=lambda r: r["adp_delta"]
    )
    print("\nBiggest reaches:")
    for r in reaches[:5]:
        print(f"  {r['player']:<24} pick {r['overall']:>3}  ADP {r['adp']:>5}  {r['adp_delta']:+.1f}")
    print("\nBest values:")
    for r in reaches[-5:][::-1]:
        print(f"  {r['player']:<24} pick {r['overall']:>3}  ADP {r['adp']:>5}  {r['adp_delta']:+.1f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
