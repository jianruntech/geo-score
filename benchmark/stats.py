#!/usr/bin/env python3
"""Uncertainty for the leaderboard's headline numbers, from the committed results.json.

    python3 benchmark/stats.py      # writes benchmark/stats.json; no network, no re-scoring

A median of 314 sites and a median of 11 are printed the same way, and only one of them is
stable. This puts a 95% interval next to every median the README and the page quote: a seeded
percentile bootstrap (10,000 resamples), so the file is identical on every run. Sectors with
fewer than MIN_N scored sites get no median at all.
"""
import io, json, os, random, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
RESAMPLES, SEED, MIN_N = 10000, 20260909, 10


def _q(xs, q):
    xs = sorted(xs)
    i = (len(xs) - 1) * q
    lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def boot_median(xs, rng):
    n = len(xs)
    meds = [statistics.median([xs[rng.randrange(n)] for _ in range(n)]) for _ in range(RESAMPLES)]
    return [round(_q(meds, .025)), round(_q(meds, .975))]


def boot_gap(a, b, rng):
    """95% interval for median(b) - median(a), resampling each group independently."""
    na, nb = len(a), len(b)
    gaps = [statistics.median([b[rng.randrange(nb)] for _ in range(nb)])
            - statistics.median([a[rng.randrange(na)] for _ in range(na)]) for _ in range(RESAMPLES)]
    return [round(_q(gaps, .025)), round(_q(gaps, .975))]


def compute(results):
    ok = [r for r in results["results"] if r.get("normalised") is not None]
    scores = [r["normalised"] for r in ok]
    rng = random.Random(SEED)
    out = {"source": "benchmark/results.json", "measured_at": results["measured_at"], "tool": results["tool"],
           "method": "percentile bootstrap, %d resamples, seed %d; sectors below %d scored sites get no median"
                     % (RESAMPLES, SEED, MIN_N),
           "min_n": MIN_N,
           "overall": {"n": len(scores), "median": round(statistics.median(scores)), "ci": boot_median(scores, rng)},
           "sectors": {}}
    by = {}
    for r in ok:
        by.setdefault(r["sector"], []).append(r["normalised"])
    for k in sorted(by):
        v = by[k]
        out["sectors"][k] = ({"n": len(v), "median": round(statistics.median(v)), "ci": boot_median(v, rng)}
                             if len(v) >= MIN_N else {"n": len(v), "median": None, "ci": None})
    cn = [r["normalised"] for r in ok if r["sector"].startswith("China")]
    rest = [r["normalised"] for r in ok if not r["sector"].startswith("China")]
    out["china_gap"] = {"n_china": len(cn), "n_rest": len(rest), "median_china": round(statistics.median(cn)),
                        "median_rest": round(statistics.median(rest)),
                        "gap": round(statistics.median(rest) - statistics.median(cn)),
                        "ci": boot_gap(cn, rest, rng)}
    return out


def main():
    results = json.load(io.open(os.path.join(HERE, "results.json"), encoding="utf-8"))
    out = compute(results)
    with io.open(os.path.join(HERE, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    o, g = out["overall"], out["china_gap"]
    print("median %d (95%% CI %d–%d), n=%d; China gap %d points (95%% CI %d–%d)"
          % (o["median"], o["ci"][0], o["ci"][1], o["n"], g["gap"], g["ci"][0], g["ci"][1]))
    thin = [k for k, v in out["sectors"].items() if v["median"] is None]
    if thin:
        print("no median (n < %d): %s" % (MIN_N, ", ".join(thin)))


if __name__ == "__main__":
    main()
