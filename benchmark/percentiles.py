#!/usr/bin/env python3
"""Where the v1.1 band cuts fall in the benchmark's own distribution.

    python3 benchmark/percentiles.py           # writes benchmark/percentiles.json
    python3 benchmark/percentiles.py --check   # exit 1 when the committed file is not what the data gives

Offline, from results.json, with sensitivity.py's loader. For the whole field, for the sites no gate capped, and
for every sector with at least MIN_N scored sites: the percentile rank of every score from 0 to 100, the scores at
the usual percentiles, and the share at or above each cut. Then the pile-up at the gate cap, the sites that sit
within measurement noise of a cut (the retest SEM in reproducibility.json), and the cuts that would put a fixed
share of the field at or above each band. v1.1's cuts do not change here: rubric/bands-analysis.md weighs them
against these figures, and adopting a cut is a new rubric version.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import retest                                        # noqa: E402
from sensitivity import load, band_of, uncapped      # noqa: E402
from stats import MIN_N, _q                          # noqa: E402

OUT_JSON = os.path.join(HERE, "percentiles.json")
PERCENTILES = (10, 25, 50, 75, 90)
SHARES = (75, 50, 25, 10)      # the fixed-share candidates: the score this share of the field reaches
Z95 = 1.96


def pct_rank(xs, s):
    """Percentile rank of score s: the share of sites below it, plus half the share at it."""
    below = sum(1 for x in xs if x < s)
    at = sum(1 for x in xs if x == s)
    return round(100.0 * (below + 0.5 * at) / len(xs), 1)


def share(n, of):
    """A whole percentage from the counts, never from the rounded pct (85.49 must not print as 86)."""
    return "%d%%" % round(100.0 * n / of)


def group(xs, cuts):
    xs = sorted(xs)
    return {"n": len(xs),
            "percentiles": {"p%d" % q: round(_q(xs, q / 100.0), 1) for q in PERCENTILES},
            "at_or_above": {str(c): {"n": sum(1 for x in xs if x >= c),
                                     "pct": round(100.0 * sum(1 for x in xs if x >= c) / len(xs), 1)} for c in cuts},
            "percentile_rank": [pct_rank(xs, s) for s in range(101)]}


def cut_for(xs, share):
    """The highest whole-number cut that at least `share` percent of xs meet."""
    return max(c for c in range(101) if 100.0 * sum(1 for x in xs if x >= c) >= share * len(xs))


def compute():
    rub, res, sites = load()
    cuts = sorted(b["min_pct"] for b in rub["bands"] if b["min_pct"] > 0)
    names = {b["min_pct"]: b["name"] for b in rub["bands"]}
    scores = [s["normalised"] for s in sites]
    free = [s["normalised"] for s in sites if not s["gate_capped"]]
    by = {}
    for s in sites:
        by.setdefault(s["sector"], []).append(s["normalised"])
    cap = rub["gate_cap"]
    capped = [s for s in sites if s["gate_capped"]]
    cap_band = band_of(cap, rub)
    in_band = [s for s in sites if band_of(s["normalised"], rub) == cap_band]
    before = {}
    for s in capped:
        b = band_of(uncapped(s), rub)
        before[b] = before.get(b, 0) + 1
    h = retest.headline()
    window = round(Z95 * h["sem"], 1)

    def near(cs):
        """Sites no further than the window from a cut's boundary (cut - 0.5): within noise of the next band."""
        return sum(1 for x in scores if any(abs(x - (c - 0.5)) <= window for c in cs))

    def candidate(cs):
        return {"cuts": cs, "at_or_above": {str(c): sum(1 for x in scores if x >= c) for c in cs},
                "at_or_above_uncapped": {str(c): sum(1 for x in free if x >= c) for c in cs}, "near_any_cut": near(cs)}
    widths = {names[c]: (hi - c) for c, hi in zip(cuts[:-1], cuts[1:])}
    return {"generated_by": "benchmark/percentiles.py",
            "source": {"measured_at": res["measured_at"], "tool": res["tool"], "rubric_version": rub["rubric_version"],
                       "n_scored": len(sites)},
            "method": {"percentile_rank": "percent of sites below the score plus half of those at it, for every score "
                                          "0-100 (index = score)",
                       "percentiles": "linear interpolation between order statistics, as stats.py",
                       "groups": "overall: every scored site; uncapped: the sites no gate capped; sectors: those with at "
                                 "least %d scored sites" % MIN_N,
                       "near_cut": "sites within %s x SEM of a cut's boundary (cut - 0.5); SEM from reproducibility.json"
                                   % Z95,
                       "candidates": "v1.1's cuts, and the highest whole-number cuts that %s percent of all sites "
                                     "(shares_overall) or of the uncapped sites (shares_uncapped) reach; counts are of "
                                     "all sites unless named uncapped" % "/".join(str(x) for x in SHARES)},
            "cuts": {str(c): names[c] for c in cuts},
            "overall": group(scores, cuts),
            "uncapped": group(free, cuts),
            "sectors": {k: group(v, cuts) for k, v in sorted(by.items()) if len(v) >= MIN_N},
            "gate_cap": {"score": cap, "capped": len(capped),
                         "at_cap": sum(1 for x in scores if x == cap),
                         "at_cap_capped": sum(1 for s in capped if s["normalised"] == cap),
                         "band": cap_band, "band_n": len(in_band),
                         "band_capped": sum(1 for s in in_band if s["gate_capped"]),
                         "capped_by_band_before_cap": {b["name"]: before.get(b["name"], 0) for b in rub["bands"]}},
            "noise": {"sem": h["sem"], "window": window, "retest": "%s, %s" % (h["measured_at"], h["tool"]),
                      "retest_band_changes": h["band_changes"], "retest_compared": h["compared"],
                      "band_widths": widths, "near_cut": {str(c): near([c]) for c in cuts}, "near_any_cut": near(cuts)},
            "candidates": {"v1.1": candidate(cuts),
                           "shares_overall": candidate([cut_for(scores, sh) for sh in SHARES]),
                           "shares_uncapped": candidate([cut_for(free, sh) for sh in SHARES])}}


def render():
    return retest.dumps(compute()) + "\n"


def main(argv):
    text = render()
    if "--check" in argv:
        ok = os.path.exists(OUT_JSON) and retest._read(OUT_JSON) == text
        if not ok:
            print("benchmark/percentiles.json is not what percentiles.py derives from results.json "
                  "(python3 benchmark/percentiles.py)", file=sys.stderr)
        return 0 if ok else 1
    retest._write(OUT_JSON, text)
    d = json.loads(text)
    print("at or above %s: %s" % ("/".join(d["cuts"]), "/".join(share(v["n"], d["overall"]["n"])
                                                                 for v in d["overall"]["at_or_above"].values())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
