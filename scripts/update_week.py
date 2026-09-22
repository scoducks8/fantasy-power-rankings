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
from week_fields import add_week_fields  # noqa: E402
from week_detail import (parse_week, parse_matchups, update_history,  # noqa: E402
                         team_week_scores, apply_week_scores)

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


def fallback_avatar(label: str, subdir: str, name: str) -> str:
    """Generate a lettered tile when a manager's logo cannot be fetched.

    Some custom uploads sit behind an endpoint that refuses server-side
    requests; a generated tile beats a broken image on the card.
    """
    initials = "".join(w[0] for w in label.split()[:2]).upper() or "?"
    hue = sum(ord(c) for c in label) % 360
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96">'
        f'<rect width="96" height="96" rx="18" fill="hsl({hue},32%,27%)"/>'
        f'<text x="48" y="61" font-size="34" font-weight="700" '
        f'fill="hsl({hue},48%,80%)" text-anchor="middle" '
        f'font-family="Helvetica,Arial,sans-serif">{initials}</text></svg>'
    )
    target = IMG_DIR / subdir / f"{name}.svg"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(svg)
    print(f"    generated tile for {label}")
    return f"assets/{subdir}/{name}.svg"


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

    week = (base.get("status") or {}).get("currentMatchupPeriod") or 0
    if not week:
        print("ESPN reports no current matchup period.", file=sys.stderr)
        return 0

    # Rosters first: the per-player numbers are correct as soon as games end,
    # while ESPN's matchup totals can stay at zero for hours afterwards.
    # ESPN rolls currentMatchupPeriod forward a day or so after MNF, so if the
    # current week has no actual points yet, the week to build is the one before.
    for attempt in (week, week - 1):
        if attempt < 1:
            break
        print(f"Fetching week {attempt} rosters ...")
        detail_blob = fetch_league(
            league_id, season, views=["mRoster", "mTeam", "mMatchupScore"],
            scoring_period=attempt,
        )
        detail = parse_week(detail_blob, attempt)
        scores = team_week_scores(detail)
        scored = sum(1 for v in scores.values() if v > 0)
        print(f"  week {attempt}: {scored}/{len(scores)} teams have points on the board")
        if scored:
            week = attempt
            break

    if scored == 0:
        print("No player scoring yet - nothing to rank.")
        return 0

    patched = apply_week_scores(base, week, scores)
    print(f"  patched {patched} matchups with roster-derived totals")

    prev = DATA_DIR / f"week-{week - 1}.json"
    rankings = build_rankings(base, season, prev_path=prev, include_live=True)
    if rankings["week"] != week:
        print(f"  NOTE: ranking built through week {rankings['week']}")
    if live:
        rankings["provisional"] = True

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

        slug = f'{t["team_id"]}-{slugify(t["name"])}'
        t["logo_local"] = (cache_image(t.get("logo", ""), "logos", slug)
                           or fallback_avatar(t["owner"] or t["name"], "logos", slug))
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
    add_week_fields(rankings)  # week score, week all-play, week vs projection

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
