"""Per-week detail: starting lineups, player scoring, matchups, positional splits.

The base pipeline only knew team totals. Everything visual — headshots, the
matchup board, the positional stacked bars — needs player-level data, which
lives behind mRoster for a specific scoringPeriodId.

Shapes produced here are mirrored exactly by mock_league.py so the page
templates can be built and reviewed before real games exist.
"""

from __future__ import annotations

# ESPN lineup slot ids. Anything not in BENCH_SLOTS started that week.
SLOT_NAMES = {
    0: "QB", 2: "RB", 3: "RB/WR", 4: "WR", 5: "WR/TE", 6: "TE",
    16: "D/ST", 17: "K", 23: "FLEX",
}
BENCH_SLOTS = {20, 21}  # 20 = bench, 21 = IR

POSITIONS = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "D/ST"}

HEADSHOT = "https://a.espncdn.com/i/headshots/nfl/players/full/{pid}.png"
# Defenses have no headshot; fall back to the NFL club logo.
TEAM_LOGO = "https://a.espncdn.com/i/teamlogos/nfl/500/{abbr}.png"


def headshot_url(player: dict) -> str:
    """Where to find this player's image, or '' if there isn't one."""
    pid = player.get("player_id")
    if player.get("position") == "D/ST":
        abbr = (player.get("pro_team") or "").lower()
        return TEAM_LOGO.format(abbr=abbr) if abbr and abbr != "?" else ""
    return HEADSHOT.format(pid=pid) if pid else ""


def parse_week(blob: dict, week: int) -> dict:
    """Pull starters, their points, and the week's matchups out of a league blob.

    Returns {team_id: {...}} plus a matchup list. Requires the blob to have
    been fetched with view=mRoster and scoringPeriodId set to `week`.
    """
    detail: dict[int, dict] = {}

    for team in blob.get("teams", []):
        entries = ((team.get("roster") or {}).get("entries")) or []
        starters, bench = [], []

        for e in entries:
            slot = e.get("lineupSlotId")
            pool = e.get("playerPoolEntry") or {}
            player = pool.get("player") or {}

            # appliedStatTotal on the entry is that player's score for the week.
            pts = e.get("playerPoolEntry", {}).get("appliedStatTotal")
            if pts is None:
                pts = pool.get("appliedStatTotal")

            projected = None
            for s in player.get("stats") or []:
                if s.get("scoringPeriodId") == week and s.get("statSourceId") == 1:
                    projected = s.get("appliedTotal")

            row = {
                "player_id": player.get("id"),
                "name": player.get("fullName", "—"),
                "position": POSITIONS.get(player.get("defaultPositionId"), "?"),
                "slot": SLOT_NAMES.get(slot, "BEN"),
                "points": round(pts or 0.0, 2),
                "projected": round(projected, 2) if projected is not None else None,
            }
            row["headshot"] = headshot_url(row)

            (bench if slot in BENCH_SLOTS else starters).append(row)

        starters.sort(key=lambda r: -r["points"])

        # Points by real position, so a flex RB counts toward RB.
        positional: dict[str, float] = {}
        for r in starters:
            positional[r["position"]] = round(
                positional.get(r["position"], 0.0) + r["points"], 2
            )

        detail[team["id"]] = {
            "starters": starters,
            "bench_points": round(sum(r["points"] for r in bench), 2),
            "positional": positional,
            "top_scorer": starters[0] if starters else None,
            "projected_total": round(
                sum(r["projected"] or 0 for r in starters), 2
            ) or None,
        }

    return detail


def parse_matchups(blob: dict, week: int, teams: dict) -> list[dict]:
    """The week's head-to-heads, richest-first for the results board."""
    out = []
    for m in blob.get("schedule", []):
        if m.get("matchupPeriodId") != week:
            continue
        home, away = m.get("home"), m.get("away")
        if not home or not away:
            continue

        hs = round(home.get("totalPoints", 0.0), 2)
        as_ = round(away.get("totalPoints", 0.0), 2)
        winner = m.get("winner", "UNDECIDED")

        out.append({
            "home_id": home["teamId"],
            "away_id": away["teamId"],
            "home": teams.get(home["teamId"], {}).get("name", "?"),
            "away": teams.get(away["teamId"], {}).get("name", "?"),
            "home_owner": teams.get(home["teamId"], {}).get("owner", ""),
            "away_owner": teams.get(away["teamId"], {}).get("owner", ""),
            "home_score": hs,
            "away_score": as_,
            "margin": round(abs(hs - as_), 2),
            "total": round(hs + as_, 2),
            "winner": winner,
            "final": winner != "UNDECIDED",
        })

    out.sort(key=lambda m: m["margin"])
    return out


def update_history(history: list[dict], rankings: dict) -> list[dict]:
    """Append this week's ranks so the season line chart can be drawn.

    Replaces the entry for a week if it is re-run, so a corrected week does
    not appear twice.
    """
    week = rankings["week"]
    entry = {
        "week": week,
        "ranks": {str(t["team_id"]): t["rank"] for t in rankings["teams"]},
        "scores": {str(t["team_id"]): t.get("last_result", {}).get("score")
                   if t.get("last_result") else None
                   for t in rankings["teams"]},
    }
    history = [h for h in history if h.get("week") != week]
    history.append(entry)
    history.sort(key=lambda h: h["week"])
    return history


def team_week_scores(detail: dict[int, dict]) -> dict[int, float]:
    """Each team's score for the week, summed from its starting lineup.

    ESPN's matchup totals sit at zero until it settles the scoring period,
    but the per-player numbers are correct as soon as games end. Summing the
    starters is therefore the reliable source for a same-night build.
    """
    return {
        tid: round(sum(s.get("points") or 0.0 for s in d.get("starters", [])), 2)
        for tid, d in detail.items()
    }


def apply_week_scores(blob: dict, week: int, scores: dict[int, float]) -> int:
    """Write roster-derived totals back into the schedule.

    Everything downstream — records, all-play, the power score — reads the
    schedule, so patching it once keeps one source of truth.
    """
    patched = 0
    for m in blob.get("schedule", []):
        if m.get("matchupPeriodId") != week:
            continue
        home, away = m.get("home"), m.get("away")
        if not home or not away:
            continue
        hs, as_ = scores.get(home.get("teamId")), scores.get(away.get("teamId"))
        if hs is None or as_ is None:
            continue
        home["totalPoints"], away["totalPoints"] = hs, as_
        if m.get("winner", "UNDECIDED") == "UNDECIDED":
            m["winner"] = "HOME" if hs > as_ else "AWAY" if as_ > hs else "TIE"
        patched += 1
    return patched
