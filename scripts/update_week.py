"""Weekly entry point: fetch ESPN, rank, cache images, write data/week-N.json.

Now pulls player-level detail (starting lineups, per-player points, matchups)
and caches manager avatars plus player headshots into the repo, so the page
never hotlinks ESPN and an archived week keeps the images it shipped with.

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

from espn_client import fetch_league, EspnAuthError, HEADERS  # noqa: E402
from power_rank import build_rankings, parse_teams  # noqa: E402
from week_detail import parse_week, parse_matchups, update_history  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
IMG_DIR = ROOT / "docs" / "assets"


def slugify(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", v.lower()).strip("-") or "x"


def cache_image(url: str, subdir: str, name: str) -> str:
    """Download once into the repo; return the site-relative path.

    Hotlinking means a week-3 page silently changes when somebody swaps their
    logo in week 10. Caching freezes each week's look.
    """
    if not url or not url.startswith("http"):
        return ""
    ext = ".png"
    for c in (".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"):
        if c in url.lower():
            ext = c
            break
    target = IMG_DIR / subdir / f"{name}{ext}"
    rel = f"assets/{subdir}/{name}{ext}"
    if target.exists():
        return rel
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        target.write_bytes(r.content)
        print(f"    cached {rel}")
        return rel
    except requests.RequestException as exc:
        print(f"    ! image failed {name}: {exc}")
        return ""


def main() -> int:
    league_id = os.environ.get("LEAGUE_ID")
    season = int(os.environ.get("SEASON", "2026"))
    if not league_id:
        print("LEAGUE_ID is not set.", file=sys.stderr)
        return 1

    print(f"Fetching league {league_id}, season {season} ...")
    try:
        base = fetch_league(league_id, season)
    except EspnAuthError as exc:
        print(f"AUTH FAILED: {exc}", file=sys.stderr)
        return 2

    DATA_DIR.mkdir(exist_ok=True)
    live = os.environ.get("INCLUDE_LIVE", "").lower() in ("1", "true", "yes")

    if live:
        # A week in progress needs mScoreboard for the running totals, and
        # ESPN only fills them in when asked for that specific period.
        current = (base.get("status") or {}).get("currentMatchupPeriod")
        if current:
            print(f"  live mode: refetching matchup period {current} ...")
            base = fetch_league(
                league_id, season,
                views=["mTeam", "mMatchupScore", "mSettings", "mScoreboard"],
                scoring_period=current,
            )

    preview = build_rankings(base, season, include_live=live)
    week = preview["week"]
    if week == 0:
        print("No matchups with points on the board yet - nothing to rank.")
        # Dump what ESPN actually sent so the next run does not have to guess.
        sched = base.get("schedule") or []
        print(f"  DIAG: schedule entries = {len(sched)}")
        print(f"  DIAG: status = {base.get('status')}")
        for m in sched[:3]:
            print(f"  DIAG: period={m.get('matchupPeriodId')} winner={m.get('winner')}")
            for side in ("home", "away"):
                sd = m.get(side) or {}
                pts = {k: v for k, v in sd.items() if "oint" in k.lower()}
                print(f"         {side}: teamId={sd.get('teamId')} pointish={pts}")
        return 0
    if preview.get("provisional"):
        print(f"  NOTE: week {week} still has unfinished games — "
              "these numbers are provisional.")

    prev = DATA_DIR / f"week-{week - 1}.json"
    rankings = build_rankings(base, season, prev_path=prev, include_live=live)

    # Second call: rosters for this scoring period carry the player-level data.
    print(f"Fetching week {week} rosters ...")
    detail_blob = fetch_league(
        league_id, season, views=["mRoster", "mTeam", "mMatchupScore"],
        scoring_period=week,
    )
    detail = parse_week(detail_blob, week)
    teams_map = parse_teams(base)
    matchups = parse_matchups(base, week, teams_map)

    print(f"Week {week}: {len(rankings['teams'])} teams, {len(matchups)} matchups")

    for t in rankings["teams"]:
        d = detail.get(t["team_id"], {})
        t["starters"] = d.get("starters", [])
        t["positional"] = d.get("positional", {})
        t["top_scorer"] = d.get("top_scorer")
        t["bench_points"] = d.get("bench_points")
        t["projected_total"] = d.get("projected_total")

        t["logo_local"] = cache_image(
            t.get("logo", ""), "logos", f'{t["team_id"]}-{slugify(t["name"])}'
        )
        top = t.get("top_scorer")
        if top and top.get("headshot"):
            top["headshot_local"] = cache_image(
                top["headshot"], "players", str(top.get("player_id") or slugify(top["name"]))
            )

    by_id = {t["team_id"]: t for t in rankings["teams"]}
    for m in matchups:
        m["home_logo"] = by_id.get(m["home_id"], {}).get("logo_local", "")
        m["away_logo"] = by_id.get(m["away_id"], {}).get("logo_local", "")
    rankings["matchups"] = matchups

    hist_path = DATA_DIR / "history.json"
    history = json.loads(hist_path.read_text()) if hist_path.exists() else []
    history = update_history(history, rankings)
    hist_path.write_text(json.dumps(history, indent=1))

    out = DATA_DIR / f"week-{week}.json"
    out.write_text(json.dumps(rankings, indent=1))
    (DATA_DIR / "latest.json").write_text(json.dumps(rankings, indent=1))
    print(f"Wrote {out.relative_to(ROOT)} and history.json ({len(history)} weeks)")

    for t in rankings["teams"]:
        top = (t.get("top_scorer") or {}).get("name", "—")
        print(f'  {t["rank"]:>2}. {t["name"][:26]:<28}{t["points_for"]:>7.1f}  top: {top}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
