#!/usr/bin/env python3
"""Score every site in sites.json and write results.json + README.md.

    python3 benchmark/run.py            # score everything
    python3 benchmark/run.py --limit 5  # a quick subset

Runs the CLI in-process. Live sites change, so re-running gives slightly different
numbers; every result records the date it was measured.
"""
import urllib.parse
import argparse, concurrent.futures as cf, importlib.util, io, json, os, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("gs", os.path.join(HERE, "..", "cli", "geo_score.py"))
gs = importlib.util.module_from_spec(spec); spec.loader.exec_module(gs)
gs.c.on = False

def one(site):
    base = site["url"] if "://" in site["url"] else "https://" + site["url"]
    host = base.split("://", 1)[1]
    attempts = [base] + ([("https://www." + host)] if not host.startswith("www.") else [])
    res = err = None
    for u in attempts:                       # some sites only answer on www
        try:
            res = gs.run(u, 8); break
        except Exception as e:
            err = e; time.sleep(1)
    try:
        if res is None: raise err or RuntimeError("unreachable")
        rows, total, den, bon, norm, bd, capped = gs.score(res)
        gaps = sorted([(mx - t, cid) for cid, _, _, t, mx, _ in rows if t is not None and t < mx],
                      reverse=True)[:3]
        gates = {cid: t for cid, _, _, t, _, _ in rows if cid.startswith("g.")}
        zero = [cid for cid, t in gates.items() if t == 0]
        reason = None
        if zero:
            # a robots.txt block is an editorial choice; a JS-only page is an accident.
            # Reporting them as the same "capped" is what makes the number useless.
            reason = ("blocks crawlers" if "g.robots" in zero else
                      "serves crawlers an error" if "g.reachable" in zero else
                      "content needs JavaScript")
        def _apex(u):
            h = urllib.parse.urlsplit(u if "://" in u else "https://" + u).netloc.lower()
            h = h.split(":")[0]
            return h[4:] if h.startswith("www.") else h
        landed = res.get("landed") or ""
        resolved = _apex(landed) if landed and _apex(landed) != _apex(site["url"]) else None
        return dict(site=site["url"], sector=site["sector"], readiness=total,
                    observable_max=den, normalised=norm, band=bd, gate_capped=capped,
                    resolved_to=resolved,
                    gates=gates, gate_reason=reason,
                    bonus=bon, top_gaps=[c for _, c in gaps],
                    pillars={p: [sum(r[3] for r in rows if r[1] == p and r[3] is not None),
                                 sum(r[4] for r in rows if r[1] == p and r[3] is not None)]
                             for p in dict.fromkeys(r[1] for r in rows)})
    except Exception as e:
        return dict(site=site["url"], sector=site["sector"], error=str(e)[:120])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int); ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    cfg = json.load(io.open(os.path.join(HERE, "sites.json"), encoding="utf-8"))
    sites = cfg["sites"][:a.limit] if a.limit else cfg["sites"]
    print("scoring %d sites…" % len(sites), file=sys.stderr)
    out = []
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        for i, r in enumerate(ex.map(one, sites), 1):
            out.append(r)
            print("  %2d/%d  %-20s %s" % (i, len(sites), r["site"],
                  r.get("error") or "%3d  %s" % (r["normalised"], r["band"])), file=sys.stderr)
    ok = [r for r in out if "error" not in r]
    ok.sort(key=lambda r: -r["normalised"])
    scores = [r["normalised"] for r in ok]
    stats = dict(n=len(ok), mean=round(statistics.mean(scores), 1),
                 median=statistics.median(scores), p25=_q(scores, .25), p75=_q(scores, .75),
                 min=min(scores), max=max(scores))
    by_sector = {}
    for r in ok: by_sector.setdefault(r["sector"], []).append(r["normalised"])
    payload = dict(rubric_version=gs.RUBRIC, tool="geo-score-cli/%s" % gs.__version__,
                   measured_at=time.strftime("%Y-%m-%d"), stats=stats,
                   sectors={k: dict(n=len(v), median=statistics.median(v)) for k, v in sorted(by_sector.items())},
                   results=ok + [r for r in out if "error" in r])
    io.open(os.path.join(HERE, "results.json"), "w", encoding="utf-8").write(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_readme(payload)
    print("\n%d sites · mean %s · median %s · range %d-%d"
          % (stats["n"], stats["mean"], stats["median"], stats["min"], stats["max"]), file=sys.stderr)
    print("next: python3 benchmark/build_page.py   (regenerates the public pages)", file=sys.stderr)

def _rubric():
    return json.load(io.open(os.path.join(HERE, "..", "rubric", "v1.1.json"), encoding="utf-8"))

def _q(xs, q):
    xs = sorted(xs); i = (len(xs) - 1) * q
    lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
    return round(xs[lo] + (xs[hi] - xs[lo]) * (i - lo), 1)

def write_readme(p):
    s, L = p["stats"], []
    A = L.append
    A("# The state of AI visibility\n")
    A("Every site below scored with the same open rubric, the same public tool and the same")
    A("eight-page sample. No private data, no vendor dashboards — [re-run it yourself](run.py).\n")
    A("**%d sites · median %s · mean %s · upper quartile %s · range %d–%d** · rubric %s · measured %s\n"
      % (s["n"], s["median"], s["mean"], s["p75"], s["min"], s["max"], p["rubric_version"], p["measured_at"]))
    ok = [x for x in p["results"] if "error" not in x]
    cn = [x["normalised"] for x in ok if x["sector"].startswith("China")]
    row = [x["normalised"] for x in ok if not x["sector"].startswith("China")]
    from collections import Counter
    gap = Counter(g for x in ok for g in x["top_gaps"])
    capped = [x for x in ok if x.get("gate_capped")]
    A("## A quarter of the field cannot be cited at all\n")
    A("**%d of %d sites have a gate check at zero** — a crawler cannot get the content, so"
      % (len(capped), len(ok)))
    A("nothing else on the page matters. These are two very different problems, and reporting")
    A("them as one number is what makes such a number useless:\n")
    _r = {}
    for x in capped: _r.setdefault(x.get("gate_reason") or "other", []).append(x["site"])
    A("| Why | Sites | Which |"); A("|---|:-:|---|")
    LBL = {"blocks crawlers": "**Deliberate** — `robots.txt` disallows retrieval crawlers",
           "serves crawlers an error": "**Deliberate or accidental** — the server returns 403 to crawlers",
           "content needs JavaScript": "**Accidental** — body copy only exists after JS runs",
           "other": "Other"}
    for k in ("blocks crawlers", "serves crawlers an error", "content needs JavaScript", "other"):
        if k in _r:
            A("| %s | %d | %s |" % (LBL[k], len(_r[k]), ", ".join(sorted(_r[k]))))
    A("\nThe first group made a choice. Several news and health publishers block AI crawlers by")
    A("name, and this rubric reports that as it is — a site that does not want to be quoted is")
    A("not misconfigured. The last group almost certainly did not choose it: their content is")
    A("there, a browser can see it, and a retrieval crawler gets an empty shell.\n")
    A("## What the spread shows\n")
    A("**Half the field sits between %s and %s.** The rubric is not grading on a curve — these"
      % (s["p25"], s["p75"]))
    A("are the scores that fall out of it, and they are consistent with the public benchmarks")
    A("it was [calibrated against](../rubric/calibration-v1.1.md).\n")
    if cn and row:
        import statistics as _st
        A("**Sites built for the Chinese market score %d points lower** — median %s against %s"
          % (round(_st.median(row) - _st.median(cn)), _st.median(cn), _st.median(row)))
        A("for everyone else. The gap is not content quality. It is `llms.txt`, `Organization`")
        A("schema, visible dates and bylines — conventions that spread through the English web")
        A("first and have not yet crossed over.\n")
    A("**The same few things are missing almost everywhere.** Counting only each site's three")
    A("largest gaps:\n")
    A("| Missing | Sites | What it costs |"); A("|---|:-:|:-:|")
    RBP = {c["id"]: c["points"] for c in _rubric()["checks"]}
    for k, v in gap.most_common(6):
        A("| `%s` | %d of %d | %d pts |" % (k, v, len(ok), RBP.get(k, 0)))
    A("\nNone of the top three is expensive. A date in a page template, an opening paragraph")
    A("that stands on its own, and one JSON-LD block are between them worth more than any")
    A("single pillar on this list.\n")
    A("## By sector\n")
    A("| Sector | Sites | Median |"); A("|---|:-:|:-:|")
    for k, v in sorted(p["sectors"].items(), key=lambda kv: -kv[1]["median"]):
        A("| %s | %d | **%s** |" % (k, v["n"], v["median"]))
    A("\n## Every site\n")
    A("| # | Site | Score | Band | Sector | Biggest gaps |")
    A("|:-:|---|:-:|---|---|---|")
    for i, r in enumerate([x for x in p["results"] if "error" not in x], 1):
        A("| %d | %s | **%d** | %s | %s | %s |" % (i, r["site"], r["normalised"], r["band"],
          r["sector"], " · ".join("`%s`" % g for g in r["top_gaps"])))
    errs = [r for r in p["results"] if "error" in r]
    if errs:
        A("\n### Not scored\n")
        for r in errs: A("- **%s** — %s" % (r["site"], r["error"]))
        A("\nA 403 to every client, a browser user-agent included, is bot protection working at the")
        A("TLS layer rather than on the user-agent string. It means a static fetch cannot observe")
        A("the site — not that the site blocks AI crawlers, which is a separate question this tool")
        A("cannot answer from outside.")
    A("\n## What this is not\n")
    A("These are **readiness** scores from a static fetch: whether an answer engine *can*")
    A("find, parse and cite the site. They do not measure whether one *does* — that depends")
    A("on competition and query intent, and no site-side audit can observe it.\n")
    A("Four checks worth 12 points need off-site search or human judgement and are left out")
    A("of the denominator, so these run a little lower than a full audit. The")
    A("[five reference audits](../examples/audits/v1.1/) score all 21 checks by hand.\n")
    A("Sites change. Every number here carries the date it was measured, and re-running")
    A("gives slightly different results — which is the point of publishing the tool alongside")
    A("the table.\n")
    io.open(os.path.join(HERE, "README.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

if __name__ == "__main__":
    main()
