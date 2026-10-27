"""Playoff odds by simulation, using the real remaining schedule.

    python3 scripts/playoff_odds.py --week 7

Reads data/week-1..N.json and data/schedule.json, writes data/odds-week-N.json.
Each team's weekly score is drawn from a normal distribution: its season
average pulled 45% toward the league average, with a spread halfway between
its own and the league's. Ties in the standings go to total points. 40,000
seasons.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--sims", type=int, default=40000)
    a = ap.parse_args()
    weeks = [json.loads((DATA / f"week-{w}.json").read_text()) for w in range(1, a.week + 1)]
    sched = json.loads((DATA / "schedule.json").read_text())
    reg, spots = sched["regular_season_weeks"], sched["playoff_teams"]
    T = {t["team_id"]: t for t in weeks[-1]["teams"]}
    sc, wins, pf = defaultdict(list), defaultdict(int), defaultdict(float)
    for d in weeks:
        for m in d["matchups"]:
            for x, sx, sy in ((m["home_id"], m["home_score"], m["away_score"]),
                              (m["away_id"], m["away_score"], m["home_score"])):
                sc[x].append(sx); pf[x] += sx; wins[x] += sx > sy
    league = [v for s in sc.values() for v in s]
    lm, lsd = st.mean(league), st.pstdev(league)
    mu = {t: lm + 0.55 * (st.mean(sc[t]) - lm) for t in T}
    sd = {t: 0.5 * st.pstdev(sc[t]) + 0.5 * lsd for t in T}
    games = [g for g in sched["games"] if a.week < g["week"] <= reg]
    random.seed(a.week * 101)
    po, top2, first, fw = defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(float)
    for _ in range(a.sims):
        w, p = dict(wins), dict(pf)
        for g in games:
            x, y = g["home_id"], g["away_id"]
            sx, sy = random.gauss(mu[x], sd[x]), random.gauss(mu[y], sd[y])
            p[x] += sx; p[y] += sy
            w[x if sx > sy else y] += 1
        ranked = sorted(T, key=lambda t: (-w[t], -p[t]))
        for i, t in enumerate(ranked):
            fw[t] += w[t]; po[t] += i < spots; top2[t] += i < 2
        first[ranked[0]] += 1
    n = a.sims
    out = {"week": a.week, "regular_season_weeks": reg, "playoff_teams": spots, "sims": n, "teams": {}}
    for t in T:
        out["teams"][str(t)] = {
            "playoffs": round(po[t] / n * 100, 1), "top2": round(top2[t] / n * 100, 1),
            "first": round(first[t] / n * 100, 1),
            "proj_wins": round(fw[t] / n, 1), "proj_losses": round(reg - fw[t] / n, 1),
        }
    (DATA / f"odds-week-{a.week}.json").write_text(json.dumps(out, indent=1))
    for t in sorted(T, key=lambda t: -po[t]):
        o = out["teams"][str(t)]
        print(f'{T[t]["name"][:24]:<24} {wins[t]}-{a.week - wins[t]}  proj {o["proj_wins"]}-{o["proj_losses"]}  '
              f'PO {o["playoffs"]:5.1f}%  top2 {o["top2"]:5.1f}%  1st {o["first"]:5.1f}%')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
