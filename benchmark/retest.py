#!/usr/bin/env python3
"""How much of one benchmark run is the site, and how much is the measurement?

    python3 benchmark/retest.py                       # re-derive reproducibility.json's figures and the
                                                      # tables in REPRODUCIBILITY.md from the committed records
    python3 benchmark/retest.py RUN_A RUN_B [RUN_C…]  # record a new study from run directories
    python3 benchmark/retest.py --check               # exit 1 when the committed files differ from that

A run directory is what `run.py --out DIR` writes: results.json plus raw/<site>.json. Each run carries the
tool, the date, the Python version and the vantage its operator declared with `run.py --vantage` (nothing
here looks an address up), and whether its pages were pinned with `run.py --urls-from-dir`. For every pair of
runs this reports the per-site differences; the shares identical, within ±2 and within ±5; ICC(A,1) and the
SEM; band changes and gate-cap flips; and, per check, the tier flips and the unobservable rate in each run.

The two runs of 2026-09-09 (a 1.1.x build, per-site totals only) stay in reproducibility.json under
"legacy", and get every figure that totals allow. No network, no randomness: the same records give the same
files byte for byte.
"""
import io, json, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, "reproducibility.json")
OUT_MD = os.path.join(HERE, "REPRODUCIBILITY.md")
RECORD_FIELDS = ["normalised", "band", "gate_capped", "gate_reason", "tiers"]
MARK = re.compile(r"(<!-- retest:([a-z-]+) -->\n)(.*?)(<!-- /retest:\2 -->)", re.S)


def _read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def _write(path, text):
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _rubric():
    return json.loads(_read(os.path.join(HERE, "..", "rubric", "v1.1.json")))


def band_of(score, bands):
    return next(b["name"] for b in bands if score >= b["min_pct"])


def raw_name(site):
    """benchmark/raw/<site>.json, named as run.py names it."""
    return re.sub(r"[^A-Za-z0-9.\-]+", "__", site.strip("/")) + ".json"


# ── reading run directories ────────────────────────────────────────────────

def load_run(path, label, checks):
    """One run directory as run metadata plus one record per scored site (see RECORD_FIELDS; tiers follow
    `checks`, None where the check was unobservable)."""
    res = json.loads(_read(os.path.join(path, "results.json")))
    recs = {}
    for r in res["results"]:
        if r.get("normalised") is None:
            continue
        fp = os.path.join(path, "raw", raw_name(r["site"]))
        if not os.path.exists(fp):
            raise SystemExit("%s: no raw report for %s (%s)" % (path, r["site"], fp))
        rep = json.loads(_read(fp))
        st = {c["id"]: c.get("points") if c.get("state") == "scored" else None for c in rep["checks"]}
        recs[r["site"]] = [r["normalised"], r["band"], bool(r.get("gate_capped")), r.get("gate_reason"),
                           [st.get(cid) for cid in checks]]
    meta = {"label": label, "tool": res.get("tool"), "measured_at": res.get("measured_at"),
            "python": res.get("python"), "measured_from": res.get("measured_from"),
            "pinned_from": res.get("pinned_from"), "n_listed": len(res["results"]), "n_scored": len(recs)}
    return meta, dict(sorted(recs.items()))


# ── statistics ─────────────────────────────────────────────────────────────

def icc_a1(rows):
    """ICC(A,1), two-way random effects, absolute agreement, single measurement (McGraw & Wong 1996), over
    rows of k scores (one row per site, one column per run). None when every score is the same."""
    n, k = len(rows), len(rows[0]) if rows else 0
    if n < 2 or k < 2:
        return None
    gm = sum(sum(r) for r in rows) / float(n * k)
    ssr = k * sum((sum(r) / float(k) - gm) ** 2 for r in rows)
    ssc = n * sum((sum(r[j] for r in rows) / float(n) - gm) ** 2 for j in range(k))
    sst = sum((x - gm) ** 2 for r in rows for x in r)
    msr, msc = ssr / (n - 1), ssc / (k - 1)
    mse = (sst - ssr - ssc) / ((n - 1) * (k - 1))
    den = msr + (k - 1) * mse + k * (msc - mse) / n
    return None if den == 0 else (msr - mse) / den


def sem_of(rows, icc):
    """Standard error of measurement: the SD of every score in the rows times sqrt(1 - ICC)."""
    xs = [x for r in rows for x in r]
    if icc is None or len(xs) < 2:
        return None
    return statistics.stdev(xs) * max(0.0, 1 - icc) ** 0.5


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def pair_totals(a, b, bands):
    """Figures two runs' per-site totals allow: {site: score} each, compared on the sites both scored."""
    both = sorted(set(a) & set(b))
    d = {s: b[s] - a[s] for s in both}
    n = len(both)
    rows = [[a[s], b[s]] for s in both]
    icc = icc_a1(rows)
    sem = sem_of(rows, icc)
    band_moves = [s for s in both if band_of(a[s], bands) != band_of(b[s], bands)]
    return {"compared": n,
            "identical": sum(1 for x in d.values() if x == 0),
            "within_2": sum(1 for x in d.values() if abs(x) <= 2),
            "within_5": sum(1 for x in d.values() if abs(x) <= 5),
            "identical_pct": pct(sum(1 for x in d.values() if x == 0), n),
            "within_2_pct": pct(sum(1 for x in d.values() if abs(x) <= 2), n),
            "within_5_pct": pct(sum(1 for x in d.values() if abs(x) <= 5), n),
            "mean_difference": round(float(statistics.mean(d.values())), 2) if d else None,
            "icc_a1": round(icc, 3) if icc is not None else None,
            "sem": round(sem, 2) if sem is not None else None,
            "band_changes": len(band_moves),
            "band_change_pct": pct(len(band_moves), n),
            "moved_over_5": [[s, a[s], b[s]] for s in sorted((s for s in both if abs(d[s]) > 5),
                                                             key=lambda s: (-abs(d[s]), s))],
            "differences": {s: d[s] for s in both}}


def _state(tier):
    return "unobservable" if tier is None else str(tier)


def analyse_study(study, bands):
    checks, runs, recs = study["checks"], study["runs"], study["records"]
    labels = [r["label"] for r in runs]
    out = {"pairs": [], "unobservable": {}}
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            ra, rb = recs[labels[i]], recs[labels[j]]
            p = pair_totals({s: v[0] for s, v in ra.items()}, {s: v[0] for s, v in rb.items()}, bands)
            p.pop("differences")                  # the records hold them
            both = sorted(set(ra) & set(rb))
            p["gate_flips"] = [[s, "capped — %s" % ra[s][3] if ra[s][2] else "not capped",
                                "capped — %s" % rb[s][3] if rb[s][2] else "not capped"]
                               for s in both if ra[s][2] != rb[s][2]]
            flips = {}
            for ci, cid in enumerate(checks):
                m = {}
                for s in both:
                    k = "%s→%s" % (_state(ra[s][4][ci]), _state(rb[s][4][ci]))
                    m[k] = m.get(k, 0) + 1
                moved = sum(v for k, v in m.items() if k.split("→")[0] != k.split("→")[1])
                flips[cid] = {"compared": len(both), "flips": moved, "flip_pct": pct(moved, len(both)),
                              "matrix": dict(sorted(m.items()))}
            p["tier_flips"] = flips
            out["pairs"].append(dict({"a": labels[i], "b": labels[j]}, **p))
    for ci, cid in enumerate(checks):
        out["unobservable"][cid] = {lb: pct(sum(1 for v in recs[lb].values() if v[4][ci] is None), len(recs[lb]))
                                    for lb in labels}
    common = sorted(set.intersection(*[set(recs[lb]) for lb in labels])) if labels else []
    rows = [[recs[lb][s][0] for lb in labels] for s in common]
    icc = icc_a1(rows)
    sem = sem_of(rows, icc)
    out["all_runs"] = {"sites_in_every_run": len(common), "icc_a1": round(icc, 3) if icc is not None else None,
                       "sem": round(sem, 2) if sem is not None else None}
    return out


def analyse_legacy(legacy, bands):
    ps = legacy["per_site"]
    p = pair_totals({s: v[0] for s, v in ps.items()}, {s: v[1] for s, v in ps.items()}, bands)
    p.pop("differences")
    return p


# ── writing ────────────────────────────────────────────────────────────────

def dumps(o, ind=0):
    """json.dumps(indent=1), except that a list holding no object stays on one line: a site's record, a pair
    of scores. A three-run study would otherwise be tens of thousands of lines."""
    pad = " " * (ind + 1)
    if isinstance(o, dict) and o:
        return "{\n" + ",\n".join(pad + json.dumps(k, ensure_ascii=False) + ": " + dumps(v, ind + 1)
                                  for k, v in o.items()) + "\n" + " " * ind + "}"
    if isinstance(o, list) and o and any(isinstance(x, dict) for x in o):
        return "[\n" + ",\n".join(pad + dumps(x, ind + 1) for x in o) + "\n" + " " * ind + "]"
    return json.dumps(o, ensure_ascii=False, separators=(", ", ": "))


def _f(x, suffix=""):
    return "—" if x is None else ("%s%s" % (x, suffix))


def _share(n, of):
    return "**%d** (%.1f%%)" % (n, 100.0 * n / of) if of else "—"


def _flip_label(state, reason):
    return state if not reason else "%s — %s" % (state, reason)


def blocks(doc):
    """The generated parts of REPRODUCIBILITY.md, keyed by marker name."""
    lg, la = doc["legacy"], doc["legacy"]["analysis"]
    r1, r2 = lg["runs"][0]["stats"], lg["runs"][1]["stats"]
    out = {}
    out["legacy-band"] = "\n".join([
        "| | |", "|---|---|",
        "| Measured | %s, %s |" % (lg["measured_at"], lg["tool"]),
        "| Sites in both runs | **%d** |" % la["compared"],
        "| Identical score | %s |" % _share(la["identical"], la["compared"]),
        "| Within ±2 | %s |" % _share(la["within_2"], la["compared"]),
        "| Within ±5 | %s |" % _share(la["within_5"], la["compared"]),
        "| Moved more than 5 | %s |" % _share(len(la["moved_over_5"]), la["compared"]),
        "| Band changed | %s |" % _share(la["band_changes"], la["compared"]),
        "| Gate-cap state flipped | **%d** |" % len(lg["gate_flips"]),
        "| ICC(A,1) | **%s** |" % _f(la["icc_a1"]),
        "| SEM | **%s** points |" % _f(la["sem"]),
        "",
        "Medians %s → %s, means %s → %s across the two runs." % (r1["median"], r2["median"], r1["mean"], r2["mean"]),
        ""])
    out["legacy-flips"] = "\n".join(["| Site | Run 1 | Run 2 |", "|---|---|---|"] + [
        "| %s | %s | %s |" % (g["site"], _flip_label(g["run1"], g.get("run1_reason")),
                               _flip_label(g["run2"], g.get("run2_reason"))) for g in lg["gate_flips"]] + [""])
    st = doc.get("study")
    if not st:
        out["study"] = ("No retest with the current tool is recorded yet. The runs cost nothing but time and are the "
                        "maintainer's to make (see [Reproducing this](#reproducing-this)); until then the only measured "
                        "band is the one above, and it describes a 1.1.x build.\n")
        return out
    an = st["analysis"]
    labels = [r["label"] for r in st["runs"]]
    L = ["| Run | Tool | Measured | Python | Vantage (declared) | Pages | Sites scored |",
         "|---|---|---|---|---|---|--:|"]
    for r in st["runs"]:
        L.append("| %s | %s | %s | %s | %s | %s | %d of %d |" % (
            r["label"], _f(r["tool"]), _f(r["measured_at"]), _f(r["python"]), _f(r["measured_from"]),
            ("pinned to %s's pages" % r["pinned_from"] if r["pinned_from"] in labels else
             "pinned to %s" % r["pinned_from"]) if r["pinned_from"] else "sampled", r["n_scored"], r["n_listed"]))
    L += ["", "| Pair | Sites | Identical | Within ±2 | Within ±5 | ICC(A,1) | SEM | Band changed | Gate flips |",
          "|---|--:|--:|--:|--:|--:|--:|--:|--:|"]
    for p in an["pairs"]:
        L.append("| %s–%s | %d | %s%% | %s%% | %s%% | %s | %s | %d | %d |" % (
            p["a"], p["b"], p["compared"], _f(p["identical_pct"]), _f(p["within_2_pct"]), _f(p["within_5_pct"]),
            _f(p["icc_a1"]), _f(p["sem"]), p["band_changes"], len(p["gate_flips"])))
    L += ["", "Across every run, on the %d sites all of them scored: ICC(A,1) %s, SEM %s points." % (
        an["all_runs"]["sites_in_every_run"], _f(an["all_runs"]["icc_a1"]), _f(an["all_runs"]["sem"])), ""]
    L += ["Tier flips per check (share of sites whose tier or observability changed), and the share of scored "
          "sites where the check was unobservable in each run:", ""]
    # a check no run could observe anywhere (the judgement checks) has nothing to show
    never = [cid for cid in st["checks"] if all(an["unobservable"][cid][lb] == 100.0 for lb in labels)]
    L += ["| Check | " + " | ".join("Flips %s–%s" % (p["a"], p["b"]) for p in an["pairs"]) + " | "
          + " | ".join("Unobservable %s" % lb for lb in labels) + " |",
          "|---|" + "--:|" * (len(an["pairs"]) + len(labels))]
    for cid in (c for c in st["checks"] if c not in never):
        L.append("| `%s` | " % cid + " | ".join("%s%%" % _f(p["tier_flips"][cid]["flip_pct"]) for p in an["pairs"])
                 + " | " + " | ".join("%s%%" % _f(an["unobservable"][cid][lb]) for lb in labels) + " |")
    if never:
        L += ["", "Not shown: %s, unobservable on every site in every run." % ", ".join("`%s`" % c for c in never)]
    L.append("")
    out["study"] = "\n".join(L)
    return out


def render_md(md, doc):
    got = blocks(doc)
    seen = set()

    def sub(m):
        seen.add(m.group(2))
        return m.group(1) + "\n" + got[m.group(2)] + "\n" + m.group(4)
    new = MARK.sub(sub, md)
    missing = sorted(set(got) - seen)
    if missing:
        raise SystemExit("REPRODUCIBILITY.md has no <!-- retest:%s --> block" % missing[0])
    return new


def derive(doc):
    """Recompute every derived figure in doc from its records, in place."""
    bands = _rubric()["bands"]
    lg = doc["legacy"]
    lg["analysis"] = analyse_legacy(lg, bands)
    # the counts published on 2026-09-09 must be what their own per-site pairs give
    for k in ("compared", "identical", "within_2", "within_5", "within_2_pct", "within_5_pct", "moved_over_5"):
        if k in lg and lg[k] != lg["analysis"][k]:
            raise SystemExit("legacy %s: recorded %r, but its per-site pairs give %r" % (k, lg[k], lg["analysis"][k]))
    if doc.get("study"):
        doc["study"]["analysis"] = analyse_study(doc["study"], bands)
    return doc


def headline(doc=None):
    """The figures the page footer quotes: the latest study's first pair, else the legacy runs."""
    doc = doc or json.loads(_read(OUT_JSON))
    st = doc.get("study")
    if st:
        p, ra = st["analysis"]["pairs"][0], st["runs"][0]
        return {"measured_at": ra["measured_at"], "tool": ra["tool"], "legacy": False, "compared": p["compared"],
                "within_5_pct": p["within_5_pct"], "identical_pct": p["identical_pct"], "gate_flips": len(p["gate_flips"])}
    lg, la = doc["legacy"], doc["legacy"]["analysis"]
    return {"measured_at": lg["measured_at"], "tool": lg["tool"], "legacy": True, "compared": la["compared"],
            "within_5_pct": la["within_5_pct"], "identical_pct": la["identical_pct"], "gate_flips": len(lg["gate_flips"])}


def main(argv):
    check = "--check" in argv
    args = [a for a in argv if a != "--check"]
    labels = None
    if "--labels" in args:
        i = args.index("--labels")
        labels = args[i + 1].split(","); del args[i:i + 2]
    doc = json.loads(_read(OUT_JSON))
    if args:
        if len(args) < 2:
            raise SystemExit("a study needs two or more run directories")
        labels = labels or [chr(ord("A") + i) for i in range(len(args))]
        if len(labels) != len(args):
            raise SystemExit("--labels names %d runs, %d directories given" % (len(labels), len(args)))
        checks = [c["id"] for c in _rubric()["checks"] if c["kind"] != "bonus"]
        runs, recs = [], {}
        for d, lb in zip(args, labels):
            meta, rr = load_run(d, lb, checks)
            runs.append(meta); recs[lb] = rr
        # a run pinned to another run's pages names that run, not a path on the operator's disk
        raw_dirs = {os.path.realpath(os.path.join(d, "raw")): lb for d, lb in zip(args, labels)}
        for r in runs:
            if r["pinned_from"]:
                r["pinned_from"] = raw_dirs.get(os.path.realpath(r["pinned_from"]), r["pinned_from"])
        doc["study"] = {"generated_by": "benchmark/retest.py", "checks": checks, "record_fields": RECORD_FIELDS,
                        "runs": runs, "records": recs}
    derive(doc)
    js = dumps(doc) + "\n"
    md = render_md(_read(OUT_MD), doc)
    if check:
        bad = [p for p, new in ((OUT_JSON, js), (OUT_MD, md)) if _read(p) != new]
        for p in bad:
            print("%s is not what retest.py derives from the committed records (python3 benchmark/retest.py)"
                  % os.path.relpath(p, os.path.join(HERE, "..")), file=sys.stderr)
        return 1 if bad else 0
    _write(OUT_JSON, js)
    _write(OUT_MD, md)
    h = headline(doc)
    print("%s, %s: %s of %d sites within ±5, %s identical" % (h["measured_at"], h["tool"], _f(h["within_5_pct"], "%"),
                                                               h["compared"], _f(h["identical_pct"], "%")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
