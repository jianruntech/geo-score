#!/usr/bin/env python3
"""Does the hosted leaderboard show what benchmark/results.json says?

    python3 scripts/check_live.py [BASE]     # BASE defaults to $GEO_SITE_BASE, then the maintained mirror

The pages are generated from results.json, but a host only serves what was last deployed, and a
stale page is a wrong answer handed to every crawler that reads it. This fetches the English page at
BASE and reads the site count (the <title>, "N sites scored"), the median (the Dataset JSON-LD,
"Median M") and the measurement date (its dateModified), then compares them with the committed data.
BASE/llms.txt is read only for a figure the page does not carry, and only when the host serves it.
Exit 0 when they agree, 1 when they differ, 2 when the page cannot be fetched.
"""
import io, json, os, re, sys, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "benchmark"))
from build_page import DEFAULT_SITE as DEFAULT  # the pages' default host, defined once


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "geo-score-check-live"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def from_page(page):
    """Site count, median and date as the page itself states them; None for any it does not carry."""
    got = {"sites": None, "median": None, "measured": None}
    m = re.search(r"<title>[^<]*?(\d{2,4}) sites scored", page)
    got["sites"] = int(m.group(1)) if m else None
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        try:
            graph = json.loads(block).get("@graph", [])
        except ValueError:
            continue
        for node in graph:
            if node.get("@type") != "Dataset":
                continue
            m = re.search(r"Median (\d+(?:\.\d+)?)", node.get("description", ""))
            got["median"] = round(float(m.group(1))) if m else None
            got["measured"] = node.get("dateModified")
    return got


def from_llms(llms):
    got = {}
    m = re.search(r"(\d{2,4})[\s>]+well-known sites", llms)
    if m:
        got["sites"] = int(m.group(1))
    m = re.search(r"Median (\d+(?:\.\d+)?)", llms)
    if m:
        got["median"] = round(float(m.group(1)))
    return got


def main(argv):
    base = (argv[0] if argv else os.environ.get("GEO_SITE_BASE") or DEFAULT).rstrip("/")
    d = json.load(io.open(os.path.join(ROOT, "benchmark", "results.json"), encoding="utf-8"))
    want = {"sites": d["stats"]["n"], "median": round(d["stats"]["median"]), "measured": d["measured_at"]}
    try:
        page = fetch(base)
    except Exception as e:
        print("cannot fetch %s: %s" % (base, e), file=sys.stderr)
        return 2
    got = from_page(page)
    if None in got.values():
        # the page did not carry every figure; llms.txt may, where the host serves one (the mirror does not)
        try:
            extra = from_llms(fetch(base + "/llms.txt"))
        except Exception:
            extra = {}
        got.update({k: v for k, v in extra.items() if got.get(k) is None})
    bad = {k: (want[k], got[k]) for k in want if want[k] != got[k]}
    for k in want:
        print("%-9s committed %-12s live %-12s %s" % (k, want[k], got[k], "differs" if k in bad else "ok"))
    if bad:
        print("\n%s is stale: rebuild with python3 benchmark/build_page.py and redeploy docs/" % base)
        return 1
    print("\n%s matches benchmark/results.json" % base)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
