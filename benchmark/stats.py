#!/usr/bin/env python3
"""Uncertainty for the leaderboard's headline numbers, from the committed results.json.

    python3 benchmark/stats.py      # writes benchmark/stats.json; no network, no re-scoring

A median of 314 sites and a median of 11 are printed the same way, and only one of them is
stable. This puts a 95% interval next to every median the README and the page quote: a seeded
percentile bootstrap (10,000 resamples), so the file is identical on every run. Sectors with
fewer than MIN_N scored sites get no median at all.

china_gap_detail takes the China gap apart using the per-site reports in raw/: by language, within
matched sector families, by how the CLI reads each check, and with p3.knowledge-graph imputed.
"""
import io, json, os, random, re, statistics, sys

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


def _gap(group, vs, rng, name_group, name_vs):
    """median(vs) - median(group) with its bootstrap interval; no figure when either side is below MIN_N."""
    out = {"group": name_group, "vs": name_vs, "n_group": len(group), "n_vs": len(vs)}
    if len(group) < MIN_N or len(vs) < MIN_N:
        return dict(out, median_group=None, median_vs=None, gap=None, ci=None)
    return dict(out, median_group=round(statistics.median(group)), median_vs=round(statistics.median(vs)),
                gap=round(statistics.median(vs) - statistics.median(group)), ci=boot_gap(group, vs, rng))


# The headline gap groups sites by sector label. china_detail re-cuts it: by the language a site serves, within
# matched sector families, check by check by how the CLI reads each check, and with the one check that rarely
# observes Chinese brands imputed. Each family pairs China sectors with the rest-of-world sector nearest to them.
FAMILIES = [(["China / AI"], ["AI"]), (["China / cloud"], ["Cloud & DevOps"]),
            (["China / consumer"], ["Ecommerce"]), (["China / no-code", "China / enterprise"], ["SaaS / Productivity"])]
KG = "p3.knowledge-graph"


def china_detail(ok, rng):
    """The China gap decomposed, from the per-site reports in raw/. None when any of them is missing."""
    raw = {}
    for r in ok:
        fp = os.path.join(HERE, "raw", re.sub(r"[^A-Za-z0-9.\-]+", "__", r["site"].strip("/")) + ".json")
        if not os.path.exists(fp):
            return None
        raw[r["site"]] = json.load(io.open(fp, encoding="utf-8"))
    rub = json.load(io.open(os.path.join(HERE, "..", "rubric", "v1.1.json"), encoding="utf-8"))
    kg_max = next(c["points"] for c in rub["checks"] if c["id"] == KG)
    sys.path.insert(0, HERE)
    from validity import METHOD                   # how the CLI reads each check: by rule or by heuristic

    def china(r):
        return r["sector"].startswith("China")

    def zh(r):
        return str(raw[r["site"]].get("audience_language") or "").startswith("zh")

    def scores(rows):
        return [r["normalised"] for r in rows]

    langs = {}
    for r in ok:
        if not zh(r):
            k = raw[r["site"]].get("audience_language") or "und"
            langs[k] = langs.get(k, 0) + 1
    out = {"definition": "sector label: the %d China sectors against every other sector"
                         % len({r["sector"] for r in ok if china(r)}),
           "china_sectors": sorted({r["sector"] for r in ok if china(r)}),
           # audience_language as the CLI reported it; "other" is every non-Chinese language
           "crosstab": {"china": {"zh": sum(1 for r in ok if china(r) and zh(r)),
                                  "other": sum(1 for r in ok if china(r) and not zh(r))},
                        "rest": {"zh": sum(1 for r in ok if not china(r) and zh(r)),
                                 "other": sum(1 for r in ok if not china(r) and not zh(r))},
                        "other_languages": dict(sorted(langs.items()))},
           "by_language": _gap(scores([r for r in ok if zh(r)]), scores([r for r in ok if not zh(r)]), rng,
                               "zh", "other"),
           "china_zh_vs_rest_other": _gap(scores([r for r in ok if china(r) and zh(r)]),
                                          scores([r for r in ok if not china(r) and not zh(r)]), rng,
                                          "China sectors, zh", "other sectors, other languages")}
    fam = [_gap(scores([r for r in ok if r["sector"] in a]), scores([r for r in ok if r["sector"] in b]), rng,
                " + ".join(a), " + ".join(b)) for a, b in FAMILIES]
    shown = [f["gap"] for f in fam if f["gap"] is not None]
    out["families"] = {"pairs": fam, "range": [min(shown), max(shown)] if shown else None,
                       "suppressed": [f["group"] for f in fam if f["gap"] is None]}
    # Raw points: per check, the mean points of the rest minus the China sectors, over the sites where the check
    # was scored. The heuristic share bounds how much of the gap a heuristic misreading Chinese pages could explain.
    pts = {True: {}, False: {}}
    for r in ok:
        for c in raw[r["site"]]["checks"]:
            if c["state"] == "scored" and not c["id"].startswith("b."):
                pts[china(r)].setdefault(c["id"], []).append(c["points"])
    diff = {cid: statistics.mean(pts[False][cid]) - statistics.mean(pts[True][cid])
            for cid in sorted(pts[True]) if cid in pts[False]}
    by = {m: sum(v for cid, v in diff.items() if cid in ids) for m, ids in METHOD.items()}
    total = sum(diff.values())
    out["by_method"] = {"what": "mean points, other sectors minus China sectors, per check where scored, summed",
                        "total": round(total, 1), "rule": round(by["rule"], 1), "heuristic": round(by["heuristic"], 1),
                        "heuristic_share_pct": round(100 * by["heuristic"] / total) if total > 0 else None,
                        "checks": {cid: round(v, 2) for cid, v in diff.items()}}
    # p3.knowledge-graph leaves the denominator when a lookup fails. A Chinese-language site is looked up in
    # Chinese and English, twice the calls, and absence is concluded only when every lookup answered.
    unobs = {k: {"n": 0, "unobservable": 0} for k in ("zh", "other")}
    for r in ok:
        k = "zh" if zh(r) else "other"
        unobs[k]["n"] += 1
        unobs[k]["unobservable"] += next((1 for c in raw[r["site"]]["checks"]
                                          if c["id"] == KG and c["state"] != "scored"), 0)
    out["knowledge_graph"] = {"check": KG, "by_language": unobs,
                              "note": "zh sites are looked up in both zh and en, twice the lookups, and absence "
                                      "needs every lookup to answer, so a partial failure leaves it unobservable"}
    # the headline gap with the check scored wherever it was unobservable, at its floor and at its ceiling
    imputed = {}
    for val in (0, kg_max):
        norm = {}
        for r in ok:
            t, den = r["readiness"], r["observable_max"]
            if any(c["id"] == KG and c["state"] != "scored" for c in raw[r["site"]]["checks"]):
                t, den = t + val, den + kg_max
            n = min(100, round(100 * t / den)) if den else 0
            norm[r["site"]] = min(n, rub["gate_cap"]) if r.get("gate_capped") else n
        cn = [norm[r["site"]] for r in ok if china(r)]
        rest = [norm[r["site"]] for r in ok if not china(r)]
        imputed[str(val)] = {"median_china": round(statistics.median(cn)), "median_rest": round(statistics.median(rest)),
                             "gap": round(statistics.median(rest) - statistics.median(cn))}
    out["kg_imputed"] = imputed
    return out


def compute(results, detail=True):
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
    if detail:
        # after every figure above, so adding it leaves their intervals (same seed, same draws) unchanged
        out["china_gap_detail"] = china_detail(ok, rng)
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
