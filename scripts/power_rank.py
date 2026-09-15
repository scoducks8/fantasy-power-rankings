"""Turn an ESPN league blob into a ranked, week-stamped power ranking.

Weighting follows the priority order we agreed on: record first, momentum
second, then scoring and luck as tiebreakers. Tune WEIGHTS to taste - the
numbers must sum to 1.0.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

# Weights ramp with sample size. In week 1 a record is one coin flip, so
# points scored carries more of the signal; by week 6 record leads, which is
# the priority order we want once it actually means something.
#
#            week 1                     week 6+
#   record     0.25  ---------------->    0.45
#   momentum   0.10  ---------------->    0.25
#   scoring    0.55  ---------------->    0.20
#   luck       0.10  (constant)           0.10
WEIGHT_START = {"win_pct": 0.25, "momentum": 0.10, "scoring": 0.55, "luck": 0.10}
WEIGHT_MATURE = {"win_pct": 0.45, "momentum": 0.25, "scoring": 0.20, "luck": 0.10}
RAMP_WEEKS = 6


def weights_for(week: int) -> dict[str, float]:
    """Blend from the small-sample weighting to the mature one."""
    r = min(1.0, max(0.0, (week - 1) / (RAMP_WEEKS - 1)))
    return {k: round(WEIGHT_START[k] + (WEIGHT_MATURE[k] - WEIGHT_START[k]) * r, 4)
            for k in WEIGHT_START}


WEIGHTS = WEIGHT_MATURE  # kept for anything importing the old name

MOMENTUM_DECAY = [0.5, 0.3, 0.2]  # most recent week first


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def parse_teams(blob: dict) -> dict[int, dict]:
    """Pull the team roster into a flat map keyed by ESPN's team id."""
    members = {m.get("id"): m for m in blob.get("members", [])}
    teams: dict[int, dict] = {}

    for t in blob.get("teams", []):
        # ESPN moved from location+nickname to a single name field; support both.
        name = t.get("name") or " ".join(
            filter(None, [t.get("location"), t.get("nickname")])
        ).strip()

        owner_ids = t.get("owners") or []
        owner_name = ""
        if owner_ids and owner_ids[0] in members:
            m = members[owner_ids[0]]
            owner_name = " ".join(
                filter(None, [m.get("firstName"), m.get("lastName")])
            ).strip()

        overall = (t.get("record") or {}).get("overall") or {}

        teams[t["id"]] = {
            "team_id": t["id"],
            "name": name or f"Team {t['id']}",
            "abbrev": t.get("abbrev", ""),
            "owner": owner_name,
            "logo": t.get("logo", ""),
            "wins": overall.get("wins", 0),
            "losses": overall.get("losses", 0),
            "ties": overall.get("ties", 0),
            "points_for": round(overall.get("pointsFor", 0.0), 2),
            "points_against": round(overall.get("pointsAgainst", 0.0), 2),
        }
    return teams


def side_points(side: dict) -> float:
    """Points for one side of a matchup.

    While a week is live ESPN leaves totalPoints at 0 and puts the running
    score in totalPointsLive, so check both before giving up.
    """
    for key in ("totalPoints", "totalPointsLive", "totalProjectedPointsLive"):
        v = side.get(key)
        if v:
            return float(v)
    return 0.0


def parse_weekly_results(blob: dict, include_live: bool = False) -> dict[int, dict[int, dict]]:
    """Map week -> team_id -> {score, opponent_id, result}.

    Completed matchups always count. With include_live, a week still in
    progress counts too — the result is derived from the scores on the board
    rather than from ESPN's winner flag, so a page can be built on Monday
    night and refreshed once the last game is final.

    Bye weeks (matchups with no away side) are skipped rather than counted.
    """
    weeks: dict[int, dict[int, dict]] = {}

    for m in blob.get("schedule", []):
        winner = m.get("winner", "UNDECIDED")
        if winner == "UNDECIDED":
            if not include_live:
                continue
            h, a = m.get("home") or {}, m.get("away") or {}
            hp, ap = side_points(h), side_points(a)
            if hp <= 0 and ap <= 0:
                continue  # not started — nothing to rank on
            winner = "HOME" if hp > ap else "AWAY" if ap > hp else "TIE"

        home, away = m.get("home"), m.get("away")
        if not home or not away:
            continue  # bye week

        week = m.get("matchupPeriodId")
        bucket = weeks.setdefault(week, {})

        h_pts = round(side_points(home), 2)
        a_pts = round(side_points(away), 2)

        bucket[home["teamId"]] = {
            "score": h_pts,
            "opponent_id": away["teamId"],
            "opponent_score": a_pts,
            "result": {"HOME": "W", "AWAY": "L"}.get(winner, "T"),
        }
        bucket[away["teamId"]] = {
            "score": a_pts,
            "opponent_id": home["teamId"],
            "opponent_score": h_pts,
            "result": {"AWAY": "W", "HOME": "L"}.get(winner, "T"),
        }

    return weeks


# --------------------------------------------------------------------------
# Ranking components
# --------------------------------------------------------------------------

def win_pct(team: dict) -> float:
    played = team["wins"] + team["losses"] + team["ties"]
    if played == 0:
        return 0.5
    return (team["wins"] + 0.5 * team["ties"]) / played


def momentum(team_id: int, weeks: dict[int, dict[int, dict]]) -> float:
    """Recency-weighted win rate over the last three completed weeks."""
    recent = sorted(weeks.keys(), reverse=True)[: len(MOMENTUM_DECAY)]
    if not recent:
        return 0.5

    total_weight = 0.0
    score = 0.0
    for weight, week in zip(MOMENTUM_DECAY, recent):
        entry = weeks[week].get(team_id)
        if not entry:
            continue
        value = {"W": 1.0, "T": 0.5, "L": 0.0}[entry["result"]]
        score += weight * value
        total_weight += weight

    return score / total_weight if total_weight else 0.5


def streak(team_id: int, weeks: dict[int, dict[int, dict]]) -> str:
    """Current run, e.g. 'W3' or 'L1'. Empty string before any games."""
    run_type, count = None, 0
    for week in sorted(weeks.keys(), reverse=True):
        entry = weeks[week].get(team_id)
        if not entry:
            continue
        if run_type is None:
            run_type, count = entry["result"], 1
        elif entry["result"] == run_type:
            count += 1
        else:
            break
    return f"{run_type}{count}" if run_type else ""


def scoring_percentile(team: dict, all_teams: list[dict]) -> float:
    """Where this team's total points-for sits in the league, 0.0-1.0."""
    if len(all_teams) < 2:
        return 0.5
    ordered = sorted(all_teams, key=lambda t: t["points_for"])
    index = next(
        i for i, t in enumerate(ordered) if t["team_id"] == team["team_id"]
    )
    return index / (len(ordered) - 1)


def all_play_pct(team_id: int, weeks: dict[int, dict[int, dict]]) -> float:
    """What the team's record would be if it played everyone every week.

    This is the 'you score the second-most points and somehow you're 2-4'
    detector - the most argued-about number in any league chat.
    """
    wins = 0.0
    games = 0
    for week, results in weeks.items():
        mine = results.get(team_id)
        if not mine:
            continue
        others = [r["score"] for tid, r in results.items() if tid != team_id]
        if not others:
            continue
        wins += sum(1 for s in others if mine["score"] > s)
        wins += 0.5 * sum(1 for s in others if mine["score"] == s)
        games += len(others)
    return wins / games if games else 0.5


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------

def build_rankings(blob: dict, season: int, prev_path: Path | None = None,
                   include_live: bool = False) -> dict:
    teams = parse_teams(blob)
    weeks = parse_weekly_results(blob, include_live=include_live)
    completed_week = max(weeks.keys()) if weeks else 0
    team_list = list(teams.values())
    W = weights_for(completed_week)

    for team in team_list:
        tid = team["team_id"]

        wp = win_pct(team)
        mo = momentum(tid, weeks)
        sc = scoring_percentile(team, team_list)
        ap = all_play_pct(tid, weeks)
        luck = (ap - wp + 1) / 2  # centre on 0.5 so it can push either way

        team["streak"] = streak(tid, weeks)
        team["all_play_pct"] = round(ap, 4)
        team["components"] = {
            "win_pct": round(wp, 4),
            "momentum": round(mo, 4),
            "scoring": round(sc, 4),
            "luck": round(luck, 4),
        }
        team["power_score"] = round(
            W["win_pct"] * wp
            + W["momentum"] * mo
            + W["scoring"] * sc
            + W["luck"] * luck,
            4,
        )

        last = weeks.get(completed_week, {}).get(tid)
        if last:
            opponent = teams.get(last["opponent_id"], {})
            team["last_result"] = {
                "result": last["result"],
                "score": last["score"],
                "opponent_score": last["opponent_score"],
                "opponent": opponent.get("name", "Bye"),
            }
        else:
            team["last_result"] = None

    team_list.sort(key=lambda t: (-t["power_score"], -t["points_for"]))

    previous = _load_previous(prev_path)
    for i, team in enumerate(team_list, start=1):
        team["rank"] = i
        prev_rank = previous.get(team["team_id"])
        team["prev_rank"] = prev_rank
        team["movement"] = (prev_rank - i) if prev_rank else 0

    return {
        "season": season,
        "week": completed_week,
        "provisional": bool(include_live and _has_open_games(blob, completed_week)),
        "league_name": (blob.get("settings") or {}).get("name", "Fantasy League"),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "weights": W,
        "teams": team_list,
    }


def _load_previous(path: Path | None) -> dict[int, int]:
    """Read last week's file so we can show movement arrows."""
    if not path or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    return {t["team_id"]: t["rank"] for t in data.get("teams", []) if "rank" in t}


def _has_open_games(blob: dict, week: int) -> bool:
    """True while any matchup in the week is still unfinished."""
    return any(m.get("matchupPeriodId") == week and m.get("winner") == "UNDECIDED"
               for m in blob.get("schedule", []))
