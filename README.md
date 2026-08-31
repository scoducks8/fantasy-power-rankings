# Fantasy Power Rankings

Weekly power rankings for an ESPN fantasy football league. A scheduled job
pulls the data every Tuesday; the weekly page gets a fresh theme by hand.

## How it fits together

```
data/week-N.json      <- written automatically every Tuesday
docs/weeks/week-N.html <- the themed page, written by hand from that data
docs/index.html        <- the hub, regenerated automatically
```

The data layer and the presentation layer are deliberately separate. The
scripts never touch the themed pages, so a bad week of copy can't break the
pipeline and a pipeline change can't restyle the archive.

## One-time setup

### 1. Create the repo

Make a new **public** repo on GitHub (free Pages requires public) and push
these files to it. Your league's scores and team names will be publicly
readable — that's normal for a rankings site, but worth knowing.

### 2. Find your league ID

Open your league on ESPN. The URL contains it:

```
https://fantasy.espn.com/football/league?leagueId=123456
                                                  ^^^^^^
```

### 3. Pull your ESPN cookies (private leagues only)

1. Log in to `fantasy.espn.com` in Chrome.
2. Open DevTools (`Cmd+Option+I`) → **Application** tab.
3. Left sidebar → **Storage** → **Cookies** → `https://fantasy.espn.com`.
4. Copy the full **Value** of two cookies:
   - `espn_s2` — a long URL-encoded string
   - `SWID` — a GUID **including the curly braces**

These are login tokens. Treat them like a password: they go in GitHub
secrets, never in a file you commit.

### 4. Add them to GitHub

In your repo → **Settings** → **Secrets and variables** → **Actions**:

| Where | Name | Value |
|---|---|---|
| Secrets | `ESPN_S2` | the long `espn_s2` value |
| Secrets | `ESPN_SWID` | the `{...}` SWID value |
| Variables | `LEAGUE_ID` | your league id |
| Variables | `SEASON` | `2026` |

### 5. Turn on Pages

Repo → **Settings** → **Pages** → Source: **Deploy from a branch**,
Branch: `main`, Folder: **`/docs`**. Save.

Your site lands at `https://<username>.github.io/<repo-name>/`.

## The weekly rhythm

Tuesday morning the workflow runs on its own and commits
`data/week-N.json`. Then:

```bash
python scripts/new_week.py --week 5 --theme "Lord of the Rings"
```

That scaffolds `docs/weeks/week-5.html` with every team's real numbers in
place and a commentary slot per team. Edit the palette at the top and write
the takes. Then:

```bash
python scripts/build_index.py   # picks up the new week for the hub
git add . && git commit -m "Week 5: Lord of the Rings" && git push
```

Pages redeploys in about a minute.

## Running it by hand

```bash
pip install -r requirements.txt
cp .env.example .env          # fill in your real values
set -a && source .env && set +a
python scripts/update_week.py
```

## Previewing without real data

```bash
python scripts/mock_league.py --weeks 5
python scripts/new_week.py --week 5 --theme "Test Theme"
python scripts/build_index.py
open docs/index.html
```

Delete `data/*.json` and `docs/weeks/*.html` before the real season starts
so mock weeks don't end up in the archive.

## Tuning the rankings

`scripts/power_rank.py` → `WEIGHTS`. They must sum to 1.0.

| Component | Default | What it measures |
|---|---|---|
| `win_pct` | 0.45 | Overall record |
| `momentum` | 0.25 | Last 3 weeks, recency-weighted |
| `scoring` | 0.20 | Points-for percentile vs the league |
| `luck` | 0.10 | All-play record minus actual record |

The `luck` term is what catches the team that's 2-4 while scoring the
second-most points in the league. Raise it if you want the rankings to
argue with the standings more.

## When it breaks

**The Tuesday build failed with an auth error.** Your `espn_s2` cookie
expired — they last roughly a season, sometimes less. Redo step 3 and update
the secrets.

**A logo is missing.** ESPN team logos are member uploads and sometimes
vanish. The page falls back to a blank tile; drop a replacement in
`docs/assets/logos/` using the same filename.

**No data written.** If no matchup has finished yet, `update_week.py` exits
cleanly without writing. Normal in the preseason.
