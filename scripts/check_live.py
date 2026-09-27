#!/usr/bin/env python3
"""Does the hosted leaderboard show what benchmark/results.json says?

    python3 scripts/check_live.py [BASE]     # BASE defaults to $GEO_SITE_BASE, then the Pages URL

The pages are generated from results.json, but a host only serves what was last deployed, and a
stale page is a wrong answer handed to every crawler that reads it. This fetches BASE/llms.txt and
BASE/index.html, reads the site count, the median and the measurement date, and compares them with
the committed data. Exit 0 when they agree, 1 when they differ, 2 when the page cannot be fetched.
"""
import io, json, os, re, sys, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT = "https://jianruntech.github.io/geo-score"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "geo-score-check-live"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def main(argv):
    base = (argv[0] if argv else os.environ.get("GEO_SITE_BASE") or DEFAULT).rstrip("/")
    d = json.load(io.open(os.path.join(ROOT, "benchmark", "results.json"), encoding="utf-8"))
    want = {"sites": d["stats"]["n"], "median": round(d["stats"]["median"]), "measured": d["measured_at"]}
    try:
        llms, page = fetch(base + "/llms.txt"), fetch(base + "/")
    except Exception as e:
        print("cannot fetch %s: %s" % (base, e), file=sys.stderr)
        return 2
    got = {}
    m = re.search(r"(\d{2,4})[\s>]+well-known sites", llms)
    got["sites"] = int(m.group(1)) if m else None
    m = re.search(r"Median (\d+(?:\.\d+)?)", llms)
    got["median"] = round(float(m.group(1))) if m else None
    m = re.search(r"(20\d\d-\d\d-\d\d)", page)
    got["measured"] = m.group(1) if m else None
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
