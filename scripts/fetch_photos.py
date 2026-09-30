"""Download freely-licensed photos from Wikimedia Commons for a themed week.

Only this repo's GitHub Actions runner can reach Wikimedia, so this runs in CI.
Every file keeps its credit line: Commons images are free to reuse but most
require attribution, so data/photo-credits.json travels with them and the page
prints the credits.

    python scripts/fetch_photos.py --out docs/assets/day
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "fantasy-power-rankings/1.0 (github.com/scoducks8)"}

# search term -> how many files to keep
# term -> how many files to keep. A required word filters look-alikes: there is
# a snooker player named Ryan Day, and searches otherwise return other coaches.
REQUIRE = {"Ryan Day football coach": ("ryan day",)}
BLOCK = ("snooker", "walden", "eckardt", "zook", "withers", "walters", "white house")

TERMS = {
    "Ryan Day football coach": 8,
    "Ohio State Buckeyes football head coach": 4,
    "Ohio Stadium": 5,
    "Ohio State Buckeyes marching band": 3,
    "Manchester New Hampshire": 4,
    "University of New Hampshire campus": 3,
    "Columbus Ohio skyline": 2,
    "Buckeye Aesculus glabra tree": 2,
}
BAD_LICENSE = re.compile(r"fair use|non-free|copyright", re.I)


def api(params: dict) -> dict:
    url = f"{API}?{urllib.parse.urlencode({**params, 'format': 'json'})}"
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as exc:  # network, HTTP error, bad JSON
        print(f"  ! api call failed: {exc}")
        print(f"    {url[:160]}")
        return {}


def search(term: str, limit: int) -> list[str]:
    data = api({"action": "query", "list": "search", "srsearch": term,
                "srnamespace": 6, "srlimit": limit * 3})
    return [x["title"] for x in data.get("query", {}).get("search", [])]


def info(titles: list[str]) -> dict:
    if not titles:
        return {}
    data = api({"action": "query", "titles": "|".join(titles), "prop": "imageinfo",
                "iiprop": "url|extmetadata|mime", "iiurlwidth": 900})
    return data.get("query", {}).get("pages", {})


def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", v.lower()).strip("-")[:60]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/assets/day")
    ap.add_argument("--credits", default="data/photo-credits.json")
    a = ap.parse_args()
    root = Path(__file__).resolve().parent.parent
    out = root / a.out
    out.mkdir(parents=True, exist_ok=True)

    credits, seen = [], set()
    for term, want in TERMS.items():
        kept = 0
        try:
            titles = search(term, want)
        except Exception as exc:
            print(f"{term}: search failed ({exc})")
            continue
        if not titles:
            print(f"{term}: no results")
            continue
        for chunk in [titles[i:i + 10] for i in range(0, len(titles), 10)]:
            for page in info(chunk).values():
                if kept >= want:
                    break
                ii = (page.get("imageinfo") or [{}])[0]
                meta = ii.get("extmetadata") or {}
                lic = (meta.get("LicenseShortName", {}) or {}).get("value", "")
                mime = ii.get("mime", "")
                url = ii.get("thumburl") or ii.get("url")
                name = page.get("title", "")
                if not url or name in seen:
                    continue
                if not mime.startswith("image/") or mime == "image/svg+xml":
                    continue
                if not lic or BAD_LICENSE.search(lic):
                    continue
                low = name.lower()
                if any(b in low for b in BLOCK):
                    print(f"  - skipped {name[5:]} (look-alike)")
                    continue
                need = REQUIRE.get(term)
                if need and not any(w in low for w in need):
                    print(f"  - skipped {name[5:]} (missing {need[0]})")
                    continue
                ext = ".jpg" if "jpeg" in mime else "." + mime.split("/")[-1]
                fname = f"{slug(name[5:])}{ext}"
                try:
                    req = urllib.request.Request(url, headers=UA)
                    with urllib.request.urlopen(req, timeout=40) as r:
                        blob = r.read()
                except Exception as exc:
                    print(f"  ! {name}: {exc}")
                    continue
                (out / fname).write_bytes(blob)
                author = re.sub("<[^>]+>", "", (meta.get("Artist", {}) or {}).get("value", "")).strip()
                credits.append({
                    "file": f"{a.out.split('docs/')[-1]}/{fname}",
                    "term": term,
                    "title": name[5:].rsplit(".", 1)[0].replace("_", " "),
                    "author": author or "Unknown",
                    "license": lic,
                    "source": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(name.replace(' ', '_'))}",
                })
                seen.add(name)
                kept += 1
                print(f"  saved {fname}  [{lic}] {author[:40]}")
        print(f"{term}: kept {kept}")

    (root / a.credits).write_text(json.dumps(credits, indent=1))
    print(f"\n{len(credits)} photos saved, credits written to {a.credits}")
    if not credits:
        print("No photos were downloaded. The page will build without them.")


if __name__ == "__main__":
    main()
