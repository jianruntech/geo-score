#!/usr/bin/env python3
"""The confirmatory analysis of the preregistered validation plan (benchmark/PREREGISTRATION.md, section 11), as code.

    python3 benchmark/prereg/analysis.py analyze --round benchmark/prereg/round0 --wave 0 [--power-t 0.31] [--out F]
    python3 benchmark/prereg/analysis.py analyze --round ... --wave 1 --baseline-wave 0     # adds L1
    python3 benchmark/prereg/analysis.py power --round benchmark/prereg/round0               # the frozen design's power

What it reads, all under the round directory:

- sample.json, the frozen sample (draw.py): per category, the sampled sites with their watch entry (name, aliases,
  domains), stratum as drawn, whether the name is an ordinary word, and Tranco rank.
- runs/wave<N>/<category>/*.json, the watch run files (schema/watch.v1.json). For each engine, the answers come from
  the newest run file in which that engine was measured and not stopped; an engine with no such file has no answers
  in that category (the amendment of 2026-10-12 on reruns). An engine none of whose answers in the wave carries a
  citation, over at least 5 questions, failed for the wave and leaves it (plan section 7).
- readiness/wave<N>/run1/<site>.json and run2/<site>.json, the CLI's reports (schema/report.v2.json). A file without a
  `normalised` score is a run the CLI could not score.

The measures (section 6): X, the mean of the site's scored runs in the wave (both, when both scored); R, cited answers
over answered answers, every engine and ask pooled, `cited` for the run's brand and `competitors.<name>.cited` for the
others; N the same with `mentioned`, not for a site whose name is an ordinary word; A, over the answers that cite the
site and carry `spans`, the mean share by characters of the answer that a span with a URL the site owns supports
(`supported_share.chars` for the brand as saved; for every other site the same rule applied by this script to the same
spans, with `watch`'s own code, so every site is measured alike), and no A with fewer than 5 such answers.

The tests (section 11): P1, the mean over categories of Kendall's tau-b between X and R, a within-category permutation
test of X (10,000 permutations, two-sided, the observed one counted) and a 95% percentile bootstrap over categories
(10,000 draws); D, the mean of R(high) - R(low); S1 to S4 with Holm's correction as one family, S3 leaving the family
when fewer than 8 categories have 3 sites with an A. Every seed is recorded in the output. Standard library only.
"""
import argparse, datetime, glob, importlib.util, io, json, math, os, random, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
ALPHA = 0.05
PERMS = BOOTS = 10000
SEED = 20261012                 # the default seed of every permutation and bootstrap draw; recorded in the output
MIN_CATEGORIES = 12             # section 3: the minimum for the primary test
MIN_A_ANSWERS = 5               # section 10: fewer citing answers with an A leaves the site without an A
S3_MIN_CATEGORIES, S3_MIN_SITES = 8, 3
MOVED = 5                       # section 11, L1: a change in X of more than 5 points
L1_MIN_SITES = 10
CITATIONLESS_MIN = 5            # an engine with no citation over at least this many questions failed
UNLISTED_RANK = 1000001         # section 6: a site outside the Tranco list
PILLARS = (("Reachable", "g."), ("Understandable", "p1."), ("Content Citability", "p2."),
           ("Brand Credibility", "p3."), ("Answer Fit", "p4."))
STRATA = (("low", None, 51), ("mid", 51, 66), ("high", 66, None))     # the rubric's own cuts, section 5.3

WORDING = {
    "positive": "In this sample, sites with higher readiness were cited in more answers to their category's "
                "questions.",
    "null": "No association was detected; the design could detect a T at least as large as the recorded power "
            "figure{power}.",
    "negative": "Sites with higher readiness were cited in fewer answers. Reported as such, and opened as a rubric "
                "issue for the next version.",
}


def load_watch():
    spec = importlib.util.spec_from_file_location("geo_watch", os.path.join(ROOT, "cli", "geo_watch.py"))
    gw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gw)
    return gw


GW = load_watch()


# ── statistics ────────────────────────────────────────────────────────────
def kendall_tau_b(x, y):
    """Kendall's tau-b of two equal-length sequences; None when either has no two distinct values."""
    n = len(x)
    c = d = tx = ty = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = (x[i] > x[j]) - (x[i] < x[j])
            dy = (y[i] > y[j]) - (y[i] < y[j])
            if dx == 0:
                tx += 1
            if dy == 0:
                ty += 1
            if dx * dy > 0:
                c += 1
            elif dx * dy < 0:
                d += 1
    n0 = n * (n - 1) // 2
    den = (n0 - tx) * (n0 - ty)
    return (c - d) / math.sqrt(den) if den > 0 else None


def holm(ps):
    """Holm's step-down adjusted p-values, in the order given."""
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out, top = [None] * len(ps), 0.0
    for rank, i in enumerate(order):
        top = max(top, min(1.0, (len(ps) - rank) * ps[i]))
        out[i] = top
    return out


def percentile_interval(stats):
    """The 2.5th and 97.5th percentiles of bootstrap replicates (as geo_watch reads them)."""
    s = sorted(stats)
    i = len(s) * 25 // 1000
    return [s[i], s[len(s) - 1 - i]]


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def association(cats, xkey, ykey, perms=PERMS, boots=BOOTS, seed=SEED):
    """P1's statistic and its test for any pair of site measures. cats: [(category id, [site dict])]; a site enters a
    category's tau when both measures are present. A category with no tau (fewer than two sites, or no two distinct
    values of either measure, as when no site is cited) is left out and counted."""
    used, left_out = [], []
    for cid, sites in cats:
        pairs = [(s[xkey], s[ykey]) for s in sites if s.get(xkey) is not None and s.get(ykey) is not None]
        tau = kendall_tau_b([p[0] for p in pairs], [p[1] for p in pairs]) if len(pairs) >= 2 else None
        if tau is None:
            left_out.append(cid)
        else:
            used.append((cid, pairs, tau))
    out = {"x": xkey, "y": ykey, "n_categories": len(used), "left_out": left_out,
           "tau": {cid: round(t, 6) for cid, _, t in used}, "T": None, "p": None, "ci": None,
           "minimum_met": len(used) >= MIN_CATEGORIES, "permutations": perms, "bootstrap": boots, "seed": seed}
    if not used:
        return out
    t_obs = mean(t for _, _, t in used)
    rng = random.Random(seed)
    hits = 0
    for _ in range(perms):
        acc = 0.0
        for _, pairs, _ in used:
            xs = [p[0] for p in pairs]
            rng.shuffle(xs)
            acc += kendall_tau_b(xs, [p[1] for p in pairs])
        if abs(acc / len(used)) >= abs(t_obs) - 1e-12:
            hits += 1
    taus = [t for _, _, t in used]
    out["T"] = round(t_obs, 6)
    if perms:
        out["p"] = round((hits + 1) / (perms + 1), 6)
    if boots:
        brng = random.Random(seed + 1)
        reps = [mean(brng.choices(taus, k=len(taus))) for _ in range(boots)]
        out["ci"] = [round(v, 6) for v in percentile_interval(reps)]
    return out


def difference_high_low(cats, ykey, boots=BOOTS, seed=SEED):
    """D: per category, mean R of the high stratum minus mean R of the low stratum (strata as drawn), averaged over
    the categories that have both, with the bootstrap over categories. Reported, not tested."""
    ds = {}
    for cid, sites in cats:
        hi = [s[ykey] for s in sites if s["stratum"] == "high" and s.get(ykey) is not None]
        lo = [s[ykey] for s in sites if s["stratum"] == "low" and s.get(ykey) is not None]
        if hi and lo:
            ds[cid] = mean(hi) - mean(lo)
    out = {"n_categories": len(ds), "by_category": {k: round(v, 6) for k, v in ds.items()}, "D": None, "ci": None}
    if ds and boots:
        vals = list(ds.values())
        rng = random.Random(seed + 2)
        reps = [mean(rng.choices(vals, k=len(vals))) for _ in range(boots)]
        out.update(D=round(mean(vals), 6), ci=[round(v, 6) for v in percentile_interval(reps)])
    return out


def residualize(cats, xkey, zkey, outkey):
    """S2: within each category, X's residual from a least-squares fit on z (an intercept and a slope; with z
    constant, the intercept alone)."""
    for _, sites in cats:
        pts = [s for s in sites if s.get(xkey) is not None and s.get(zkey) is not None]
        if not pts:
            continue
        zs, xs = [s[zkey] for s in pts], [s[xkey] for s in pts]
        mz, mx = mean(zs), mean(xs)
        szz = sum((z - mz) ** 2 for z in zs)
        b = sum((z - mz) * (x - mx) for z, x in zip(zs, xs)) / szz if szz > 0 else 0.0
        for s in pts:
            s[outkey] = s[xkey] - (mx + b * (s[zkey] - mz))


# ── reading the round ─────────────────────────────────────────────────────
def read_json(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def load_runs(round_dir, wave, cid):
    """The answers of one category in one wave: {engine id: [samples]} from the newest run file in which each engine
    was measured and not stopped, plus a record of every file and what was used."""
    files = sorted(glob.glob(os.path.join(round_dir, "runs", "wave%d" % wave, cid, "*.json")))
    runs = []
    for p in files:
        r = read_json(p)
        if r.get("format") == GW.RUN_FORMAT:
            runs.append((r.get("run_id") or os.path.basename(p), r))
    runs.sort(key=lambda t: GW._run_sort_key(t[0]))
    chosen, record = {}, []
    for rid, r in runs:
        for e in r.get("engines") or []:
            ok = e.get("status") == "measured" and not e.get("stopped") and not r.get("interrupted")
            record.append({"run_id": rid, "engine": e.get("id"), "model": e.get("model"), "measured": ok,
                           "stopped": e.get("stopped"), "started_at": r.get("started_at")})
            if ok:
                chosen[e["id"]] = (rid, r)
    answers = {}
    for eid, (rid, r) in chosen.items():
        answers[eid] = [dict(s, _run=rid, _brand=r["brand"]["name"]) for s in r.get("samples") or []
                        if s.get("engine") == eid]
    return answers, record, {eid: rid for eid, (rid, _) in chosen.items()}


def hit(sample, name, field):
    if sample["_brand"] == name:
        return bool(sample.get(field))
    return bool((sample.get("competitors") or {}).get(name, {}).get(field))


def answer_share(sample, ent):
    """A for one answer and one site: the share by characters that a span with a URL the site owns supports, or None
    when the answer has no spans (not measured, never 0)."""
    spans = GW.spans_of(sample)
    if spans is None or not isinstance(sample.get("answer"), str):
        return None
    if sample["_brand"] == ent.name:
        v = sample.get("supported_share")
        if isinstance(v, dict) and isinstance(v.get("chars"), (int, float)):
            return float(v["chars"])
    owned = GW.owner_test(ent, GW._citation_list(sample.get("citations")), GW._citation_list(sample.get("sources_listed")))
    share = GW.answer_support(sample["answer"], spans, owned)
    return None if share is None else share["chars"]


def outcomes(site, samples):
    """R, N, A and their counts for one site over one category's answered answers."""
    ent = GW.Entity({"name": site["name"], "domains": site["domains"], "url_prefixes": site.get("url_prefixes") or [],
                     "aliases": site.get("aliases") or []})
    ok = [s for s in samples if s.get("status") == "ok"]
    cited = [s for s in ok if hit(s, site["name"], "cited")]
    out = {"answered": len(ok), "cited": len(cited), "R": (len(cited) / len(ok)) if ok else None}
    named = sum(1 for s in ok if hit(s, site["name"], "mentioned"))
    out["mentioned"] = named
    out["N"] = None if site.get("ordinary_word") or not ok else named / len(ok)
    with_any = [s for s in ok if s.get("citations")]
    out["R_given_any_citation"] = (sum(1 for s in with_any if hit(s, site["name"], "cited")) / len(with_any)) \
        if with_any else None
    shares = [a for a in (answer_share(s, ent) for s in cited) if a is not None]
    out["A_answers"] = len(shares)
    out["A"] = mean(shares) if len(shares) >= MIN_A_ANSWERS else None
    return out


def readiness(round_dir, wave, site_id):
    """X and what it rests on: the scored runs of the wave, the gate, the pillars."""
    runs = []
    for k in (1, 2):
        p = os.path.join(round_dir, "readiness", "wave%d" % wave, "run%d" % k, site_id + ".json")
        if not os.path.exists(p):
            continue
        rep = read_json(p)
        if isinstance(rep.get("normalised"), (int, float)):
            pillars = {}
            for name, prefix in PILLARS:
                pts = [c.get("points") for c in rep.get("checks") or []
                       if c.get("id", "").startswith(prefix) and c.get("state") == "scored"]
                pillars[name] = sum(v for v in pts if isinstance(v, (int, float)))
            runs.append({"run": k, "normalised": rep["normalised"], "gate_capped": bool(rep.get("gate_capped")),
                         "audited_at": rep.get("audited_at"), "pillars": pillars, "pages": len(rep.get("sampled_urls") or [])})
    if not runs:
        return {"X": None, "runs": [], "gate_zero": None}
    pil = {name: mean(r["pillars"][name] for r in runs) for name, _ in PILLARS}
    return {"X": mean(r["normalised"] for r in runs), "runs": runs, "gate_zero": any(r["gate_capped"] for r in runs),
            "difference": abs(runs[0]["normalised"] - runs[1]["normalised"]) if len(runs) == 2 else None,
            "pillars": pil}


def stratum_of(score):
    for name, lo, hi in STRATA:
        if (lo is None or score >= lo) and (hi is None or score < hi):
            return name
    return None


def collect(round_dir, wave):
    """Every category's sites with X, R, N and A, and the per-engine answers, for one wave."""
    sample = read_json(os.path.join(round_dir, "sample.json"))
    cats, engines_seen, files = [], {}, {}
    for c in sample["categories"]:
        answers, record, chosen = load_runs(round_dir, wave, c["id"])
        files[c["id"]] = {"runs": record, "used": chosen}
        for eid, rows in answers.items():
            e = engines_seen.setdefault(eid, {"answered": 0, "with_citations": 0, "questions": set()})
            for s in rows:
                if s.get("status") == "ok":
                    e["answered"] += 1
                    e["questions"].add((c["id"], s["query_id"]))
                    if s.get("citations"):
                        e["with_citations"] += 1
        cats.append((c, answers))
    failed = sorted(eid for eid, e in engines_seen.items()
                    if e["with_citations"] == 0 and len(e["questions"]) >= CITATIONLESS_MIN)
    out = []
    for c, answers in cats:
        pooled = [s for eid, rows in sorted(answers.items()) if eid not in failed for s in rows]
        sites = []
        for st in c["sites"]:
            row = {"id": st["id"], "name": st["name"], "stratum": st["stratum"],
                   "ordinary_word": bool(st.get("ordinary_word")),
                   "log10_rank": math.log10(st.get("tranco_rank") or UNLISTED_RANK)}
            row.update(outcomes(st, pooled))
            rd = readiness(round_dir, wave, st["site"])
            gate = rd["gate_zero"] if wave == 0 else readiness(round_dir, 0, st["site"])["gate_zero"]
            row.update(X=rd["X"], gate_zero=gate, readiness_runs=rd["runs"],
                       readiness_difference=rd.get("difference"), pillars=rd.get("pillars"))
            row["by_engine"] = {eid: outcomes(st, rows) for eid, rows in sorted(answers.items()) if eid not in failed}
            sites.append(row)
        out.append({"id": c["id"], "sites": sites, "answers": {k: len(v) for k, v in answers.items()},
                    "missing": not pooled})
    return sample, out, {"failed_engines": failed, "files": files,
                         "engines": {k: {"answered": v["answered"], "with_citations": v["with_citations"],
                                         "questions": len(v["questions"])} for k, v in engines_seen.items()}}


# ── the analyses ──────────────────────────────────────────────────────────
def wording(p1, s2, power_t):
    """The sentence section 11 fixes for P1's result, and the S2 sentence when popularity shrinks or removes it."""
    out = []
    if p1["T"] is None:
        return ["P1 could not be estimated: no category had a tau."]
    if p1["p"] < ALPHA and p1["T"] > 0:
        out.append(WORDING["positive"])
    elif p1["p"] < ALPHA and p1["T"] < 0:
        out.append(WORDING["negative"])
    else:
        out.append(WORDING["null"].format(power=" (T = %.2f)" % power_t if power_t is not None else ""))
    if not p1["minimum_met"]:
        out.append("Fewer than %d categories had a tau (%d), so the minimum for the primary test was not met."
                   % (MIN_CATEGORIES, p1["n_categories"]))
    if p1["p"] < ALPHA and s2.get("T") is not None:
        if s2["p_holm"] is None or s2["p_holm"] >= ALPHA:
            out.append("Allowing for popularity (S2), the association was no longer detected (T = %.2f%s)." % (
                s2["T"], ", Holm-adjusted p = %.3f" % s2["p_holm"] if s2["p_holm"] is not None else ""))
        elif abs(s2["T"]) < abs(p1["T"]):
            out.append("Allowing for popularity (S2), the association was smaller (T = %.2f against %.2f)."
                       % (s2["T"], p1["T"]))
    return out


def analyze(round_dir, wave, perms=PERMS, boots=BOOTS, seed=SEED, power_t=None, baseline_wave=None):
    sample, cats, info = collect(round_dir, wave)
    present = [c for c in cats if not c["missing"]]
    with_x = [(c["id"], [s for s in c["sites"] if s["X"] is not None]) for c in present]
    p1 = association(with_x, "X", "R", perms, boots, seed)
    p1["D"] = difference_high_low(with_x, "R", boots, seed)
    s1 = association([(cid, [s for s in ss if not s["gate_zero"]]) for cid, ss in with_x], "X", "R", perms, boots, seed)
    residualize(with_x, "X", "log10_rank", "X_resid")
    s2 = association(with_x, "X_resid", "R", perms, boots, seed)
    s3 = association(with_x, "X", "A", perms, boots, seed)
    s3_cats = sum(1 for _, ss in with_x if sum(1 for s in ss if s["A"] is not None) >= S3_MIN_SITES)
    s3["estimable"] = s3_cats >= S3_MIN_CATEGORIES
    s3["categories_with_3_sites_with_A"] = s3_cats
    s4 = association(with_x, "X", "N", perms, boots, seed)
    family = [("S1", s1), ("S2", s2), ("S3", s3), ("S4", s4)]
    family = [(k, v) for k, v in family if v["p"] is not None and (k != "S3" or s3["estimable"])]
    adj = holm([v["p"] for _, v in family])
    for (_, v), a in zip(family, adj):
        v["p_holm"] = round(a, 6)
    for v in (s1, s2, s3, s4):
        v.setdefault("p_holm", None)
    if not s3["estimable"]:
        s3["note"] = "not estimable: fewer than %d categories have %d sites with an A; S3 left the family" % (
            S3_MIN_CATEGORIES, S3_MIN_SITES)
    described = describe(cats, with_x, info, perms, boots, seed)
    out = {"format": "geo-score/prereg-results.v1", "plan": "benchmark/PREREGISTRATION.md", "wave": wave,
           "computed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "seed": seed, "permutations": perms, "bootstrap": boots, "engines": info["engines"],
           "failed_engines": info["failed_engines"], "run_files": info["files"],
           "categories_missing": [c["id"] for c in cats if c["missing"]],
           "P1": p1, "S1": s1, "S2": s2, "S3": s3, "S4": s4, "holm_family": [k for k, _ in family],
           "described": described, "categories": cats, "power_T": power_t}
    if baseline_wave is not None:
        out["L1"] = longitudinal(round_dir, baseline_wave, cats, perms, boots, seed)
    out["wording"] = wording(p1, s2, power_t)
    return out


def describe(cats, with_x, info, perms, boots, seed):
    d = {}
    engines = sorted({eid for c in cats for s in c["sites"] for eid in s["by_engine"]})
    per_engine = {}
    for eid in engines:
        rows = [(c["id"], [dict(s, R_e=s["by_engine"].get(eid, {}).get("R")) for s in c["sites"] if s["X"] is not None])
                for c in cats if not c["missing"]]
        r = association(rows, "X", "R_e", 0, boots, seed)
        per_engine[eid] = {"T": r["T"], "n_categories": r["n_categories"], "ci": r["ci"]}
    d["T_by_engine"] = per_engine
    strata = {}
    for name, _, _ in STRATA:
        ss = [s for _, sites in with_x for s in sites if s["stratum"] == name]
        strata[name] = {"sites": len(ss)}
        for k in ("R", "A", "N"):
            vals = [s[k] for s in ss if s[k] is not None]
            strata[name][k] = round(mean(vals), 6) if vals else None
            strata[name]["n_" + k] = len(vals)
    d["by_stratum"] = strata
    pil = {}
    for name, _ in PILLARS:
        rows = [(cid, [dict(s, P=(s["pillars"] or {}).get(name)) for s in sites]) for cid, sites in with_x]
        r = association(rows, "P", "R", 0, boots, seed)
        pil[name] = {"mean_tau": r["T"], "n_categories": r["n_categories"]}
    d["pillar_tau_with_R"] = pil
    d["R_given_any_citation"] = {s["id"] + "@" + cid: s["R_given_any_citation"] for cid, sites in with_x for s in sites}
    d["readiness_run_difference"] = summary([s["readiness_difference"] for _, sites in with_x for s in sites
                                             if s["readiness_difference"] is not None])
    d["engine_answers"] = info["engines"]
    return d


def summary(xs):
    if not xs:
        return {"n": 0}
    return {"n": len(xs), "mean": round(mean(xs), 4), "median": round(statistics.median(xs), 4), "max": max(xs),
            "above_5": sum(1 for v in xs if v > MOVED)}


def longitudinal(round_dir, baseline_wave, cats, perms, boots, seed):
    """L1: the change in X against the change in R, per category, between the baseline wave and this one. Tested only
    when at least 10 sites' X moved by more than 5 points."""
    _, base, _ = collect(round_dir, baseline_wave)
    before = {(c["id"], s["id"]): s for c in base for s in c["sites"]}
    rows, moved = [], 0
    for c in cats:
        ss = []
        for s in c["sites"]:
            b = before.get((c["id"], s["id"]))
            if b is None or None in (b["X"], s["X"], b["R"], s["R"]):
                continue
            dx, dr = s["X"] - b["X"], s["R"] - b["R"]
            moved += abs(dx) > MOVED
            ss.append({"id": s["id"], "dX": dx, "dR": dr})
        rows.append((c["id"], ss))
    tested = moved >= L1_MIN_SITES
    r = association(rows, "dX", "dR", perms if tested else 0, boots, seed)
    r.update(sites_moved=moved, tested=tested)
    if not tested:
        r.update(p=None, note="described, not tested: fewer than %d sites moved by more than %d points"
                 % (L1_MIN_SITES, MOVED))
    return r


# ── power ─────────────────────────────────────────────────────────────────
def simulate_category(rng, xs, beta, answers_per_q, n_questions):
    """One category's R under the power model: a site's log-odds of being cited in an answer is the category's base
    (normal, mean logit 0.1, sd 1) plus beta times its X standardised within the category plus a site effect (normal,
    sd 0.5); each question shifts every site's log-odds alike (normal, sd 1), and each of its answers is a draw."""
    base = math.log(0.1 / 0.9) + rng.gauss(0, 1)
    m = mean(xs)
    sd = statistics.pstdev(xs) or 1.0
    site = [base + beta * (x - m) / sd + rng.gauss(0, 0.5) for x in xs]
    qs = [rng.gauss(0, 1) for _ in range(n_questions)]
    rs = []
    for lo in site:
        k = 0
        for q in qs:
            p = 1 / (1 + math.exp(-(lo + q)))
            k += sum(1 for _ in range(answers_per_q) if rng.random() < p)
        rs.append(k / float(answers_per_q * n_questions))
    return rs


def power(design, betas, sims=200, perms=999, seed=SEED, answers_per_q=16, n_questions=10):
    """The frozen design's power: for each effect size, how often P1's permutation test rejects at alpha = 0.05, and
    the mean T it produces. design: [[X of each sampled site] per category]."""
    rng = random.Random(seed)
    rows = []
    for beta in betas:
        rejected, ts = 0, []
        for k in range(sims):
            cats = []
            for i, xs in enumerate(design):
                rs = simulate_category(rng, xs, beta, answers_per_q, n_questions)
                cats.append(("c%d" % i, [{"X": x, "R": r} for x, r in zip(xs, rs)]))
            r = association(cats, "X", "R", perms, 0, seed + 1000 + k)
            if r["T"] is None:
                continue
            ts.append(r["T"])
            rejected += r["p"] < ALPHA
        rows.append({"beta": beta, "power": rejected / float(sims), "mean_T": round(mean(ts), 4) if ts else None})
    detectable = None
    for a, b in zip(rows, rows[1:]):
        if a["power"] < 0.8 <= b["power"] and a["mean_T"] is not None and b["mean_T"] is not None:
            w = (0.8 - a["power"]) / (b["power"] - a["power"])
            detectable = round(a["mean_T"] + w * (b["mean_T"] - a["mean_T"]), 3)
            break
    if detectable is None and rows and rows[0]["power"] >= 0.8:
        detectable = rows[0]["mean_T"]
    return {"sims": sims, "permutations": perms, "seed": seed, "answers_per_question": answers_per_q,
            "questions": n_questions, "grid": rows, "smallest_T_with_80pct_power": detectable,
            "model": simulate_category.__doc__.strip()}


def design_of(round_dir):
    sample = read_json(os.path.join(round_dir, "sample.json"))
    return [[s["sampling_score"] for s in c["sites"]] for c in sample["categories"]]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    a1 = sub.add_parser("analyze")
    a1.add_argument("--round", required=True)
    a1.add_argument("--wave", type=int, default=0)
    a1.add_argument("--baseline-wave", type=int)
    a1.add_argument("--perms", type=int, default=PERMS)
    a1.add_argument("--boots", type=int, default=BOOTS)
    a1.add_argument("--seed", type=int, default=SEED)
    a1.add_argument("--power-t", type=float, help="the power figure registered by amendment")
    a1.add_argument("--out")
    a2 = sub.add_parser("power")
    a2.add_argument("--round", required=True)
    a2.add_argument("--sims", type=int, default=200)
    a2.add_argument("--perms", type=int, default=999)
    a2.add_argument("--seed", type=int, default=SEED)
    a2.add_argument("--betas", default="0,0.05,0.1,0.15,0.2,0.25,0.3,0.4,0.5,0.7,1.0")
    a2.add_argument("--out")
    a = ap.parse_args(argv)
    if a.cmd == "analyze":
        res = analyze(a.round, a.wave, a.perms, a.boots, a.seed, a.power_t, a.baseline_wave)
    elif a.cmd == "power":
        res = power(design_of(a.round), [float(b) for b in a.betas.split(",")], a.sims, a.perms, a.seed)
    else:
        ap.print_help()
        return 1
    text = json.dumps(res, ensure_ascii=False, indent=1) + "\n"
    if a.out:
        with io.open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
    if a.cmd == "analyze":
        p1 = res["P1"]
        print("P1: T = %s, p = %s, 95%% CI %s, %d categories" % (p1["T"], p1["p"], p1["ci"], p1["n_categories"]))
        for k in ("S1", "S2", "S3", "S4"):
            print("%s: T = %s, p = %s, Holm p = %s" % (k, res[k]["T"], res[k]["p"], res[k]["p_holm"]))
        print("\n".join(res["wording"]))
    else:
        print("smallest T detected with 80%% power at alpha 0.05: %s" % res["smallest_T_with_80pct_power"])
        if not a.out:
            sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
